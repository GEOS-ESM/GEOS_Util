#!/usr/bin/env python3
'''
Residual Circulation (TEM Diagnostics) Processing and Plotting Pipeline

Processes monthly Transformed Eulerian Mean (TEM) diagnostic files to generate
days-in-month weighted seasonal climatologies. Performs strict date-alignment
(apples-to-apples) between a base experiment and comparison datasets (e.g.,
MERRA-2, ERA5, or other model runs) to ensure accurate differencing.

The pipeline operates entirely in-memory for speed and explicitly subsets
variables to maintain a minimal memory footprint.

Visualizations:
  - Module A: Zonal Mean Streamfunction and Residual Circulation contours
  - Module B: Eliassen-Palm (EP) Fluxes (Absolute and Differences)
  - Module C: WSTAR and Stratospheric Transport (Turn-Around Latitudes)

Usage:
    Typically invoked via a wrapper shell script. Requires arguments:
    -source, -expid, -plotsdir, -begdate, -enddate, -season, -cmpexp
'''
import os
import sys
import glob
import argparse
import gc
import numpy as np
import xarray as xr
import warnings
import scipy.ndimage
import matplotlib
matplotlib.use('Agg')  # Headless backend for batch cluster execution
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors

# Silence xarray/numpy warnings from all-NaN slices generated during subsetting
warnings.filterwarnings('ignore', message='All-NaN slice encountered')
warnings.filterwarnings('ignore', message='Mean of empty slice')


# ==========================================================
# CONFIGURATION
# ==========================================================
# Retunable constants shared across modules. Values used by only one figure live
# beside that figure's function instead (e.g. EP-flux vector tuning in Module B).

# Global matplotlib styling shared by every figure.
plt.rcParams.update({
    'figure.titlesize': 14,   # Main figure suptitle
    'axes.titlesize': 11,     # Individual subplot titles
    'axes.labelsize': 11,     # X/Y axis physical labels
    'xtick.labelsize': 9,     # X-axis geographic tick text
    'ytick.labelsize': 9,     # Y-axis pressure tick text
    'font.size': 9            # Fallback for text without an explicit size (e.g. contour inline labels)
})

# Secondary text sizes (primary axis/title styling lives in rcParams above).
FONT_ANNOTATION = 8   # colorbar ticks & labels, legends, quiver key, and inset panel titles
FONT_INSET = 7        # inset tick labels, inset colorbar ticks, and inset colorbar label

# Season name -> constituent calendar months. Single source of truth: also used
# to validate the -season argument and to advertise valid choices in the help text.
SEASON_MONTHS = {
    'ANN': list(range(1, 13)), 'DJF': [12, 1, 2], 'MAM': [3, 4, 5],
    'JJA': [6, 7, 8], 'SON': [9, 10, 11], 'JAN': [1], 'FEB': [2],
    'MAR': [3], 'APR': [4], 'MAY': [5], 'JUN': [6], 'JUL': [7],
    'AUG': [8], 'SEP': [9], 'OCT': [10], 'NOV': [11], 'DEC': [12]
}

# Month number -> 3-letter abbreviation for date labels.
MONTH_ABBR = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
              7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'}

# Days-in-month weights for seasonal averaging (Feb carries a leap-year fraction).
DAYS_IN_MONTH = {1: 31, 2: 28.25, 3: 31, 4: 30, 5: 31, 6: 30,
                 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

# Variables kept from the raw files; everything else is dropped to save memory.
TARGET_VARS = ['str', 'res', 'epfy', 'epfz', 'epfdiv', 'wstar', 'delp']

# Colors assigned to comparison datasets in Module C (the Base is always blue).
# Edit using standard Matplotlib color names or Hex codes.
CMP_COLORS = ['darkorange', 'forestgreen', 'crimson', 'magenta',
              'saddlebrown', 'hotpink', 'gray', 'olive', 'deepskyblue']

# Output resolution shared by every saved figure.
FIG_DPI = 300


# ==========================================================
# DATA PROCESSING HELPERS
# ==========================================================
def get_season_months(season_str):
    '''Maps a season string (e.g. DJF, ANN) to its constituent calendar months.'''
    season_upper = season_str.upper()
    if season_upper not in SEASON_MONTHS:
        print(f'[res] [!] ERROR: Unrecognized season {season_str!r}.')
        sys.exit(1)
    return SEASON_MONTHS[season_upper]


# ---- File / date discovery ----
def generate_month_list(start_ym, end_ym):
    '''Generates a continuous set of YYYYMM strings between two dates for verification.'''
    start_y, start_m = int(start_ym[:4]), int(start_ym[4:])
    end_y, end_m = int(end_ym[:4]), int(end_ym[4:])
    months = []
    y, m = start_y, start_m
    while y < end_y or (y == end_y and m <= end_m):
        months.append(f'{y:04d}{m:02d}')
        m += 1
        if m > 12:
            m = 1
            y += 1
    return set(months)


def get_available_months(directory, expid):
    '''Scans a TEM_Diag directory to catalog all generated YYYYMM monthly NetCDF files.'''
    search_path = os.path.join(directory, 'TEM_Diag', '*.TEM_Diag.monthly.*.nc*')
    files = glob.glob(search_path)
    valid_files = {}
    for f in files:
        parts = os.path.basename(f).split('.')
        if len(parts) >= 2:
            date_str = parts[-2]
            if date_str.isdigit() and len(date_str) == 6:
                valid_files[date_str] = f
    return valid_files


# ---- Monthly climatology & seasonal weighting ----
# extract_12_month_clims is expensive (disk I/O) and its result is reused across
# many seasons, so it stays separate from the cheap per-season weighting step.
def extract_12_month_clims(files_list):
    '''
    Groups monthly files by calendar month (1-12), subsets to target variables,
    and computes the time-mean per month to minimize memory footprint. Degenerate
    longitude dimensions are dropped to force 2D (lat/lev) processing.
    '''
    month_files = {m: [] for m in range(1, 13)}
    for f in files_list:
        ym = os.path.basename(f).split('.')[-2]
        month = int(ym[4:6])
        month_files[month].append(f)

    clims = {}
    for m in range(1, 13):
        if not month_files[m]:
            clims[m] = None
            continue
        # join='override' adopts the first file's coordinates. TEM_Diag files share
        # one grid; some sources (e.g. MERRA-2) carry sub-picodegree float jitter in
        # their lat values, which the outer-join default would otherwise flag.
        ds = xr.open_mfdataset(month_files[m], engine='netcdf4',
                               data_vars='minimal', coords='minimal',
                               compat='override', join='override')
        avail_vars = [v for v in TARGET_VARS if v in ds.data_vars]
        clims[m] = ds[avail_vars].mean(dim='time').squeeze(dim='lon', drop=True).compute()
        ds.close()
    return clims


def compute_weighted_season(monthly_clims, target_months):
    '''Weights pre-computed calendar months by their physical length (days) into a seasonal mean.'''
    weighted_sum = None
    total_weight = 0.0
    for m in target_months:
        if monthly_clims.get(m) is not None:
            w = DAYS_IN_MONTH[m]
            weighted_sum = monthly_clims[m] * w if weighted_sum is None else weighted_sum + monthly_clims[m] * w
            total_weight += w
    return weighted_sum / total_weight if total_weight > 0 else None

def is_reanalysis(dataset_name):
    '''True for reanalysis products (MERRA/ERA), which are excluded from turn-around plots.'''
    return 'MERRA' in dataset_name.upper() or 'ERA' in dataset_name.upper()

def align_datasets(ds_base, ds_cmp):
    '''
    Forces spatial alignment for differencing by interpolating the denser-grid
    dataset down onto the coarser grid (bilinear).
    '''
    size_base = ds_base.sizes.get('lat', 0) * ds_base.sizes.get('lev', 0)
    size_cmp = ds_cmp.sizes.get('lat', 0) * ds_cmp.sizes.get('lev', 0)
    if size_base <= size_cmp:
        ds_cmp = ds_cmp.interp(lev=ds_base.lev, lat=ds_base.lat,
                               method='linear', kwargs={'fill_value': 'extrapolate'})
    else:
        ds_base = ds_base.interp(lev=ds_cmp.lev, lat=ds_cmp.lat,
                                 method='linear', kwargs={'fill_value': 'extrapolate'})
    return ds_base, ds_cmp


# ---- Title / label string helpers ----
def format_date_str(ym_str, space=True):
    '''
    Converts a YYYYMM string to a month/year label. Default 'JAN 1986';
    pass space=False for the compact 'JAN1986' form.
    '''
    y = ym_str[:4]
    m = int(ym_str[4:6])
    sep = ' ' if space else ''
    return f'{MONTH_ABBR[m]}{sep}{y}'


def get_season_count_str(months_list, t_months):
    '''Fractional number of seasons present, for plot titles/legends.'''
    if not months_list:
        return '0'
    season_months = [m for m in months_list if int(m[4:6]) in t_months]
    num_seasons = len(season_months) / len(t_months)
    return f'{num_seasons:.1f}'.rstrip('0').rstrip('.')

def make_date_entry(months_list, t_months):
    '''Builds a complete date-label entry (start, end, season count) from a month list.'''
    return {
        'b_date': format_date_str(months_list[0]),
        'e_date': format_date_str(months_list[-1]),
        'n_seas': get_season_count_str(months_list, t_months),
    }


# ==========================================================
# PLOTTING HELPERS
# ==========================================================
def save_as_gif(fig, plotsdir, png_name):
    '''
    Saves a figure as PNG, then renames it to GIF (the wrapper tooling expects
    .gif outputs). Closes the figure afterward to free memory, and reports the
    finished file (indented to nest under the plot-group headers in the log).
    '''
    out_filepath = os.path.join(plotsdir, png_name)
    fig.savefig(out_filepath, dpi=FIG_DPI)
    gif_name = png_name.replace('.png', '.gif')
    os.rename(out_filepath, out_filepath.replace('.png', '.gif'))
    plt.close(fig)
    print(f'[res]         made {gif_name}')


def format_x_axis(ax):
    '''Applies symmetric geographic latitude labeling (-90 to +90).'''
    ax.set_xlim(-90, 90)
    ax.set_xticks([-90, -60, -30, 0, 30, 60, 90])
    ax.set_xticklabels(['90S', '60S', '30S', 'EQ', '30N', '60N', '90N'])


def format_y_axis(ax, scale='linear'):
    '''
    Applies pressure boundaries and targeted tick labeling, and enforces standard
    atmospheric orientation (1000 hPa at the bottom).
    '''
    if scale == 'log':
        ax.set_yscale('log')
        ticks = [1000, 500, 200, 100, 50, 20, 10, 5, 2, 1, 0.5, 0.1]
        ax.set_yticks(ticks)
        ax.set_yticklabels([str(t) for t in ticks])
    else:
        ticks = np.arange(100, 1001, 100)
        ax.set_yticks(ticks)
        ax.set_yticklabels([str(int(t)) for t in ticks])

    if not ax.yaxis_inverted():
        ax.invert_yaxis()

    ax.set_ylabel('Pressure (hPa)')
    ax.grid(True, linestyle=':', color='silver', alpha=0.7)


def relabel_colorbar_ticks(cbar, bounds, fmt='{:.1f}', axis='x'):
    '''
    Relabels colorbar ticks from a set of bound values, formatting each with fmt
    while forcing an exact '0' for the zero bound. Pass fmt='{:g}' to strip
    trailing zeros, or '{:.1f}' to force one decimal place. Set axis='y' for
    vertical colorbars.
    '''
    labels = [fmt.format(b) if b != 0 else '0' for b in bounds]
    if axis == 'x':
        cbar.ax.set_xticklabels(labels)
    else:
        cbar.ax.set_yticklabels(labels)


def get_symmetric_cmap(vmax_raw=None, num_bins=11, force_bounds=None):
    '''
    Builds a symmetric diverging colormap with a true-zero transparent center bin.

    For difference plots (dynamic boundaries) it rounds to clean half-bin widths
    (e.g. 0.1, 0.2, 0.5, 1.0, 2.0), guaranteeing colorbar labels never exceed one
    decimal place while keeping strictly equidistant bins. num_bins is forced odd
    so a true-zero center bin exists.
    '''
    if force_bounds is not None:
        bounds = force_bounds
    else:
        if num_bins % 2 == 0:
            num_bins += 1
        target_h = vmax_raw / num_bins
        # Candidate array of clean half-bin widths.
        nice_h = np.concatenate([np.array([1., 2., 5.]) * (10 ** exp) for exp in range(-4, 5)])
        h = nice_h[nice_h >= target_h][0]
        bounds = h * np.arange(-num_bins, num_bins + 2, 2)

    colors = plt.get_cmap('bwr')(np.linspace(0, 1, len(bounds) - 1))
    # Make the exact middle bin transparent (true zero).
    colors[(len(bounds) - 1) // 2] = [1.0, 1.0, 1.0, 0.0]

    custom_cmap = mcolors.ListedColormap(colors)
    return bounds, custom_cmap, mcolors.BoundaryNorm(bounds, custom_cmap.N)


def draw_labeled_contours(ax, lat, lev, data, clevs, inline_spacing=15):
    '''
    Draws solid/dashed black contour lines with inline numeric labels, skipping the
    zero contour and boxing each label in white for legibility. Integers render
    without decimals; sub-unit values keep one decimal place. Returns the ContourSet.
    '''
    cs = ax.contour(lat, lev, data, levels=clevs, colors='k', linewidths=1)
    levels_to_label = [l for l in cs.levels if l != 0]
    if levels_to_label:
        label_fmt = lambda x: f'{x:.1f}' if abs(x) < 1 else f'{x:.0f}'
        labels = ax.clabel(cs, levels=levels_to_label, inline=True, fmt=label_fmt,
                           inline_spacing=inline_spacing, use_clabeltext=True)
        for l in labels:
            l.set_bbox(dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
    return cs


def plot_contours(ax, lat, lev, data, clevs, use_cmap=False, norm=None, cmap='bwr', draw_lines=True):
    '''
    Renders a data field as either shaded contours (use_cmap=True) or a grey
    negative-region mask. Optionally overlays labeled black contour lines. Returns
    the filled mappable (or None when only the mask is drawn).
    '''
    plt.rcParams['contour.negative_linestyle'] = 'dashed'
    mappable = None

    if use_cmap:
        mappable = ax.contourf(lat, lev, data, levels=clevs, cmap=cmap, norm=norm, extend='both')
    else:
        ax.contourf(lat, lev, data, levels=[-np.inf, 0], colors=['lightgrey'], alpha=0.9)

    if draw_lines:
        draw_labeled_contours(ax, lat, lev, data, clevs)

    return mappable


def calculate_arrow_skip(lat_array, target_degrees=4.0):
    '''Index-slicing interval that yields roughly target_degrees of horizontal arrow spacing.'''
    if len(lat_array) < 2:
        return 1
    dlat = abs(lat_array[1] - lat_array[0])
    return max(1, int(round(target_degrees / float(dlat))))


# ==========================================================
# MODULE A: ZONAL STREAMFUNCTION & RESIDUAL CIRCULATION
# ==========================================================
def plot_str_and_res(ds_base, ds_cmp, plotsdir, season, expid, cmpid, dates):
    '''
    Four-panel side-by-side comparison (Base vs Comparison):
      Top row:    Meridional Streamfunction (linear scale)
      Bottom row: Residual Circulation (log scale, custom non-linear bins)
    'dates' is this pair's Time A (pairwise overlap) date entry.
    '''

    # --- Figure & panel layout ---
    # Every panel is placed manually below, so spacing is controlled by the panel
    # rectangles [left, bottom, width, height] rather than a subplots_adjust call.
    fig = plt.figure(figsize=(10, 7.5))
    w, h = 0.36, 0.33
    ax_exp_top = fig.add_axes([0.10, 0.52, w, h])
    ax_cmp_top = fig.add_axes([0.52, 0.52, w, h])
    cax_top    = fig.add_axes([0.90, 0.52, 0.015, h])
    ax_exp_bot = fig.add_axes([0.10, 0.10, w, h])
    ax_cmp_bot = fig.add_axes([0.52, 0.10, w, h])
    cax_bot    = fig.add_axes([0.90, 0.10, 0.015, h])

    # --- Titles ---
    # Format the suptitle from the experiment/comparison names and the pairwise date range.
    fig.suptitle(f"EXP: {expid}  vs  CMP: {cmpid}\n"
                 f"{season} ({dates['n_seas']}, actual): {dates['b_date']} "
                 f"\u2013 {dates['e_date']}", y=0.97)


    # Per-variable rendering rules: which axes, variable, display name, scale, and levels.
    plot_rules = [
        {'axes': (ax_exp_top, ax_cmp_top, cax_top), 'var': 'str',
         'name': r'Meridional Streamfunction ($10^9$ kg/s)',
         'scale': 'linear', 'clevs': np.arange(-20, 22, 2)},
        {'axes': (ax_exp_bot, ax_cmp_bot, cax_bot), 'var': 'res',
         'name': r'Residual Circulation ($10^9$ kg/s)',
         'scale': 'log',
         'clevs': [-50, -20, -10, -5, -2, -1, -0.5, -0.2, -0.1, 0,
                   0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50]},
    ]

    # --- Render each row (Base on the left, Comparison on the right) ---
    for rule in plot_rules:
        ax_e, ax_c, cax = rule['axes']
        v = rule['var']
        clevs = rule['clevs']
        norm = mcolors.BoundaryNorm(clevs, plt.get_cmap('bwr').N) if rule['scale'] == 'log' else None
        y_top = 0.1 if rule['scale'] == 'log' else 10

        # Base experiment panel.
        plot_contours(ax_e, ds_base.lat, ds_base.lev, ds_base[v], clevs, use_cmap=True, norm=norm)
        format_y_axis(ax_e, scale=rule['scale'])
        ax_e.set_ylim(1000, y_top)
        format_x_axis(ax_e)
        ax_e.set_title(f"EXP: {rule['name']}")

        # Comparison dataset panel.
        cf = plot_contours(ax_c, ds_cmp.lat, ds_cmp.lev, ds_cmp[v], clevs, use_cmap=True, norm=norm)
        format_y_axis(ax_c, scale=rule['scale'])
        ax_c.set_ylim(1000, y_top)
        ax_c.set_ylabel('')
        format_x_axis(ax_c)
        ax_c.set_title(f"CMP: {rule['name']}")

        # Shared vertical colorbar for this row.
        cbar = fig.colorbar(cf, cax=cax, orientation='vertical')
        cbar.ax.tick_params(labelsize=FONT_ANNOTATION)

    # --- Footer & save ---
    fig.text(0.10, 0.04, f'( EXPID: {expid} )', ha='left')
    save_as_gif(fig, plotsdir, f'zonal_{cmpid}_str_res.{season}.png')


def plot_str_or_res(var_name, ds_base, ds_cmp, plotsdir, season, expid, cmpid, dates):
    '''
    Three-panel vertical layout for a single variable:
      Top:    Absolute Base
      Middle: Absolute Comparison
      Bottom: Difference (Base - Comparison) shaded, overlaid with Base contours
    'dates' is this pair's Time A (pairwise overlap) date entry.
    '''
    var = var_name.lower()

    # Align grids so the difference is computed on a common grid.
    ds_base_aligned, ds_cmp_aligned = align_datasets(ds_base, ds_cmp)
    diff_data = ds_base_aligned[var] - ds_cmp_aligned[var]
    target_lat, target_lev = ds_base_aligned.lat, ds_base_aligned.lev
    exp_target_data = ds_base_aligned[var]

    # --- Figure & panel layout ---
    # Panels are placed manually below, so spacing is controlled by the panel
    # rectangles [left, bottom, width, height] rather than a subplots_adjust call.
    fig = plt.figure(figsize=(6.5, 11.5))
    l, w, h = 0.11, 0.78, 0.235
    axes = [
        fig.add_axes([l, 0.670, w, h]),
        fig.add_axes([l, 0.385, w, h]),
        fig.add_axes([l, 0.100, w, h]),
    ]
    cax = fig.add_axes([l, 0.060, w, 0.015])

    # Variable-specific display name and absolute contour levels.
    is_str = (var == 'str')
    title_str = r'Meridional Streamfunction' if is_str else r'Residual Circulation'
    base_clevs = np.arange(-20, 22, 2) if is_str else np.arange(-100, 105, 5)

    # --- Titles ---
    # Format the suptitle from the variable name and the pairwise date range.
    fig.suptitle(f'{title_str} ($10^9$ kg/s)\n'
                 f"{season} ({dates['n_seas']}, actual): {dates['b_date']} "
                 f"\u2013 {dates['e_date']}", y=0.97)

    # Top: absolute Base. Middle: absolute Comparison.
    plot_contours(axes[0], ds_base.lat, ds_base.lev, ds_base[var], base_clevs, use_cmap=False)
    axes[0].set_title(f'{expid}')

    plot_contours(axes[1], ds_cmp.lat, ds_cmp.lev, ds_cmp[var], base_clevs, use_cmap=False)
    axes[1].set_title(f'{cmpid}')

    # Bottom: difference shading with a true-zero transparent center bin.
    axes[2].set_title('Difference (Top-Middle) Shaded; EXP Contours')
    axes[2].contourf(target_lat, target_lev, exp_target_data,
                     levels=[-np.inf, 0], colors=['lightgrey'], alpha=0.9)

    vmax_raw = float(np.abs(diff_data).max())
    bounds, custom_cmap, norm = get_symmetric_cmap(vmax_raw=vmax_raw, num_bins=11)

    cf = axes[2].contourf(target_lat, target_lev, diff_data,
                          levels=bounds, norm=norm, cmap=custom_cmap, extend='both', zorder=2)
    cbar = fig.colorbar(cf, cax=cax, orientation='horizontal', ticks=bounds)
    cbar.ax.tick_params(labelsize=FONT_ANNOTATION)
    relabel_colorbar_ticks(cbar, bounds, fmt='{:.1f}', axis='x')

    # Overlay Base contours on the difference panel for structural context.
    draw_labeled_contours(axes[2], target_lat, target_lev, exp_target_data, base_clevs)

    # Shared axis formatting for all three panels.
    for ax in axes:
        format_y_axis(ax, scale='linear')
        ax.set_ylim(1000, 10)
        format_x_axis(ax)

    # --- Footer & save ---
    fig.text(0.04, 0.02, f'( EXPID: {expid} )', ha='left')
    save_as_gif(fig, plotsdir, f'zonal_{cmpid}_{var}.{season}.png')
    

# ==========================================================
# MODULE B: ELIASSEN-PALM FLUX
# ==========================================================
# Vector/colormap tuning used only by the EP-flux figures.
EP_ARROW_SCALE = 15          # Master quiver scale; smaller = longer arrows
EP_ARRFCT_MAIN = 100         # Z/Y aspect stretch for the main-domain panels
EP_ARRFCT_STRAT = 500        # Z/Y aspect stretch for the stratospheric panel
EP_REF_ARROW_MAIN = 2.5e9    # Reference-arrow magnitude for absolute (non-diff) main panels
EP_REF_ARROW_STRAT = 8e8     # Reference-arrow magnitude for absolute (non-diff) strat panel
EP_DIFF_PERCENTILE = 95      # Percentile used to size difference reference arrows (ignores outliers)


def prepare_single_ep_dataset(ds, smooth_sigma=1.0):
    '''
    Subsets EP variables, scales divergence by 10^-2 for plotting standardization,
    and applies a Gaussian filter to the divergence field to smooth numerical noise.
    '''
    d_out = ds[['epfy', 'epfz', 'epfdiv']].copy()
    d_out['epfdiv'] = d_out['epfdiv'] / 100.0

    if smooth_sigma > 0:
        d_out['epfdiv'].values = np.where(
            np.isnan(d_out['epfdiv'].values), np.nan,
            scipy.ndimage.gaussian_filter(d_out['epfdiv'].fillna(0), sigma=smooth_sigma)
        )
    return d_out


def plot_ep_flux_diagnostics(ds, title_str, plotsdir, out_filename, is_diff, season,
                             b_date, e_date, n_seas=None):
    '''
    Four-panel EP Flux figure: divergence (shading) plus flux vectors.
      Top-left:     Main domain      (log, 1000-0.8 hPa)
      Top-right:    Partial domain   (log, 1000-8 hPa)
      Bottom-left:  Troposphere zoom (linear, 1000-80 hPa)
      Bottom-right: Stratosphere zoom (log, 100-8 hPa)

    The date label is formatted here from the raw date pieces; difference plots add
    the season count in parentheses. Difference plots also derive a single global
    reference-arrow magnitude from the field percentile so the visual scale stays
    identical across panels.
    '''

    # --- Figure & panel layout ---
    # Panels and their colorbars are placed manually below, so spacing is controlled
    # by the panel rectangles [left, bottom, width, height], not a subplots_adjust call.
    fig = plt.figure(figsize=(10, 8))
    w, h = 0.40, 0.28
    axes = [
        fig.add_axes([0.08, 0.58, w, h]), fig.add_axes([0.55, 0.58, w, h]),
        fig.add_axes([0.08, 0.16, w, h]), fig.add_axes([0.55, 0.16, w, h]),
    ]
    # Horizontal colorbar axes sitting directly beneath each panel.
    caxes = [
        fig.add_axes([0.08, 0.51, w, 0.015]), fig.add_axes([0.55, 0.51, w, 0.015]),
        fig.add_axes([0.08, 0.09, w, 0.015]), fig.add_axes([0.55, 0.09, w, 0.015]),
    ]

    # --- Titles ---
    # Format this figure's date label; difference plots include the "actual" label.
    if is_diff:
        date_label = f'{season} ({n_seas}, actual): {b_date} \u2013 {e_date}'
    else:
        date_label = f'{season} ({n_seas}): {b_date} \u2013 {e_date}'
    fig.suptitle(f'Eliassen-Palm Flux (Vectors) and Divergence '
                 f'(Shaded, $10^{{-2}}$ $m^2/s^2$)\n{title_str}\n{date_label}', y=0.97)

    # --- Determine shading bins and reference-arrow magnitudes ---
    if is_diff:
        # Difference plots: derive reference arrows from a percentile to ignore outliers,
        # and derive symmetric shading bins from the field maxima in each domain.
        def get_ref(min_p, max_p, z_y):
            mask = (ds.lev.values <= min_p) & (ds.lev.values >= max_p)
            mags = np.sqrt(ds['epfy'].values[mask, :] ** 2 +
                           (-ds['epfz'].values[mask, :] * z_y) ** 2)
            p = np.nanpercentile(mags, EP_DIFF_PERCENTILE)
            exp = np.floor(np.log10(p)) if p > 0 else 1
            return np.round(p / (10 ** exp), 1) * (10 ** exp)

        ref_main = get_ref(1000, 0.8, 100)
        ref_strat = get_ref(100, 8, 500)

        vmax_main = float(np.abs(ds['epfdiv'].sel(lev=slice(None, 0.8))).max())
        bounds_main, cmap_main, norm_main = get_symmetric_cmap(vmax_raw=vmax_main, num_bins=11)

        vmax_strat = float(np.abs(ds['epfdiv'].sel(lev=slice(100, 8))).max())
        bounds_strat, cmap_strat, norm_strat = get_symmetric_cmap(vmax_raw=vmax_strat, num_bins=11)
    else:
        # Absolute plots: fixed shading bins and hardcoded reference arrows.
        ref_main, ref_strat = EP_REF_ARROW_MAIN, EP_REF_ARROW_STRAT
        bounds_main, cmap_main, norm_main = get_symmetric_cmap(force_bounds=np.linspace(-5.5, 5.5, 12))
        bounds_strat, cmap_strat, norm_strat = get_symmetric_cmap(force_bounds=np.linspace(-0.55, 0.55, 12))

    skip_x = calculate_arrow_skip(ds.lat.values, target_degrees=4.0)

    # --- Render each panel ---
    for i, ax in enumerate(axes):
        # Per-panel pressure limits and vertical scale.
        if i == 0:
            lims, scale = (1000, 0.8), 'log'
        elif i == 1:
            lims, scale = (1000, 8), 'log'
        elif i == 2:
            lims, scale = (1000, 80), 'linear'
        else:
            lims, scale = (100, 8), 'log'

        # The stratosphere panel uses its own bins; the rest share the main bins.
        bnds, c, nrm = (bounds_strat, cmap_strat, norm_strat) if i == 3 else \
                       (bounds_main, cmap_main, norm_main)

        # Shaded divergence (no black contour lines).
        cf = plot_contours(ax, ds.lat, ds.lev, ds['epfdiv'], bnds,
                           use_cmap=True, norm=nrm, cmap=c, draw_lines=False)
        cbar = fig.colorbar(cf, cax=caxes[i], orientation='horizontal', ticks=bnds)
        # Strip trailing zeros from the boundary labels for cleaner ticks.
        relabel_colorbar_ticks(cbar, bnds, fmt='{:g}', axis='x')
        cbar.ax.tick_params(labelsize=FONT_ANNOTATION)

        # Flux vectors. Vertical component is stretched (Z/Y) to preserve tilt meaning.
        U = ds['epfy'].values
        V = ds['epfz'].values
        arrfct = EP_ARRFCT_STRAT if i == 3 else EP_ARRFCT_MAIN
        ref_val = ref_strat if i == 3 else ref_main
        V_scaled = -V * arrfct

        # Thin the vector field in the vertical based only on levels visible in this panel.
        valid_idx = np.where((ds.lev.values >= lims[1]) & (ds.lev.values <= lims[0]))[0]
        skip_y = max(1, len(valid_idx) // 12)
        plot_idx = valid_idx[::skip_y]

        X, Y = np.meshgrid(ds.lat.values[::skip_x], ds.lev.values[plot_idx])
        U_sub = U[plot_idx, ::skip_x]
        V_sub = V_scaled[plot_idx, ::skip_x]

        q = ax.quiver(X, Y, U_sub, V_sub, pivot='middle', angles='uv',
                      color='black', alpha=0.9, width=0.003, headwidth=4, headlength=5,
                      scale=ref_val * EP_ARROW_SCALE)

        # Single-line reference key between the panel and its colorbar.
        ref_label = f'{ref_val:g}'.replace('+0', '').replace('+', '')
        ax.quiverkey(q, 0.73, -0.14, ref_val, f'{ref_label}  (Z/Y: {arrfct})',
                     labelpos='E', coordinates='axes', fontproperties={'size': FONT_ANNOTATION})

        format_y_axis(ax, scale)
        ax.set_ylim(lims[0], lims[1])
        format_x_axis(ax)

        # Drop redundant Y-axis labels from the right-hand column.
        if i in (1, 3):
            ax.set_ylabel('')

    save_as_gif(fig, plotsdir, out_filename)    
    
# ==========================================================
# MODULE C: TURN-AROUND LATS & VERTICAL PROFILES
# ==========================================================
def calculate_talats(ds, dataset_name):
    '''
    Calculates Turn-Around Latitudes (WSTAR/PSI zero-crossings) and extracts the
    stratospheric WSTAR subset. Returns None for reanalysis products (MERRA/ERA),
    which bypass the turn-around logic.
    '''
    if is_reanalysis(dataset_name):
        return None

    try:
        strat_ds = ds.sel(lev=slice(100, 20))
    except KeyError:
        return None

    # Pressure-weighted vertical integrals across the 100-20 hPa layer.
    weights = strat_ds['delp']
    wstar_int = (strat_ds['wstar'] * weights).sum(dim='lev') / weights.sum(dim='lev')
    res_int = (strat_ds['res'] * weights).sum(dim='lev') / weights.sum(dim='lev')

    lats = wstar_int.lat.values
    levs = strat_ds.lev.values
    wstar_1d = wstar_int.values
    res_1d = res_int.values
    wstar_2d = strat_ds['wstar'].values

    def find_zero_crossing(lats_slice, vals_slice):
        '''Linearly interpolated latitude where the profile first changes sign.'''
        for i in range(len(vals_slice) - 1):
            if vals_slice[i] * vals_slice[i + 1] <= 0:
                v1, v2 = vals_slice[i], vals_slice[i + 1]
                l1, l2 = lats_slice[i], lats_slice[i + 1]
                if v1 == v2:
                    return l1
                return l1 - v1 * (l1 - l2) / (v1 - v2)
        return np.nan

    # Vertically integrated turn-around boundaries (WSTAR zero-crossings).
    sh_mask = (lats >= -70) & (lats <= -15)
    nh_mask = (lats >= 15) & (lats <= 70)
    wstar_lat_sh = find_zero_crossing(lats[sh_mask], wstar_1d[sh_mask])
    wstar_lat_nh = find_zero_crossing(lats[nh_mask], wstar_1d[nh_mask])

    # PSI extrema: minimum in the SH, maximum in the NH.
    res_sh_mask = (lats >= -70) & (lats <= 0)
    res_nh_mask = (lats >= 0) & (lats <= 70)
    res_lat_sh = lats[res_sh_mask][np.argmin(res_1d[res_sh_mask])]
    res_lat_nh = lats[res_nh_mask][np.argmax(res_1d[res_nh_mask])]

    # Level-dependent boundaries across the pressure array.
    sh_lev, nh_lev = [], []
    for i in range(len(levs)):
        w_lev = wstar_2d[i, :]
        sh_lev.append(find_zero_crossing(lats[sh_mask], w_lev[sh_mask]))
        nh_lev.append(find_zero_crossing(lats[nh_mask], w_lev[nh_mask]))

    return {
        'lats': lats, 'levs': levs,
        'wstar_1d': wstar_1d, 'res_1d': res_1d, 'wstar_2d': wstar_2d,
        'wstar_lat_sh': wstar_lat_sh, 'wstar_lat_nh': wstar_lat_nh,
        'res_lat_sh': res_lat_sh, 'res_lat_nh': res_lat_nh,
        'wstar_lat_sh_lev': np.array(sh_lev), 'wstar_lat_nh_lev': np.array(nh_lev),
    }


def plot_latitudinal_talats_summary(talats_dict, base_expid, color_map, season, plotsdir, dates, is_time_b=False):
    '''
    Stacked 1D latitude profiles with turn-around annotations:
      Top:    Vertically integrated WSTAR
      Bottom: Vertically integrated PSI (residual streamfunction)
    is_time_b selects the climatology (Time B) variant, which shows each dataset's
    own date range in the legend. The Time A variant shows one shared range (the
    common window) in the title. Dates are read from the 'dates' map by name.
    '''
    valid_dicts = {k: v for k, v in talats_dict.items() if v is not None}
    if not valid_dicts:
        return

    prefix = 'WSTAR_B' if is_time_b else 'WSTAR'
    out_filename = f'{prefix}_Turn_Around_Lats.{season}.png'

    # --- Figure & panel layout ---
    # Outer margins and inter-panel spacing; hspace sets the vertical gap between
    # the WSTAR and PSI panels. bottom leaves room for the legend below the panels.
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax_w, ax_p = axes[0], axes[1]
    plt.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.18, hspace=0.22)

    # Average turn-around latitudes across datasets (for the annotation lines).
    avg_w_sh = np.nanmean([d['wstar_lat_sh'] for d in valid_dicts.values() if not np.isnan(d['wstar_lat_sh'])])
    avg_w_nh = np.nanmean([d['wstar_lat_nh'] for d in valid_dicts.values() if not np.isnan(d['wstar_lat_nh'])])
    avg_p_sh = np.nanmean([d['res_lat_sh'] for d in valid_dicts.values() if not np.isnan(d['res_lat_sh'])])
    avg_p_nh = np.nanmean([d['res_lat_nh'] for d in valid_dicts.values() if not np.isnan(d['res_lat_nh'])])

    # --- Titles ---
    # The Time A variant shows one shared (common-window) range drawn from the base;
    # the Time B variant carries per-dataset ranges in the legend instead. Both panels
    # share the same second line, so build it once.
    if not is_time_b:
        d = dates[base_expid]
        shared_date = f" ({d['n_seas']}): {d['b_date']} \u2013 {d['e_date']}"
    else:
        shared_date = ''
    subtitle = f'{season}{shared_date}, Levels: 100\u201320 hPa'

    ax_w.set_title(f'Vertically Integrated Residual Vertical Velocity (WSTAR)\n{subtitle}')
    ax_p.set_title(f'Vertically Integrated Residual Mean Meridional Streamfunction (PSI)\n{subtitle}')

    # Shared axis styling for both panels.
    for ax in (ax_w, ax_p):
        format_x_axis(ax)
        ax.axhline(0, color='grey', linewidth=0.75, zorder=1)
        ax.grid(True, linestyle=':', color='silver', alpha=0.7)
    ax_w.tick_params(labelbottom=True)
    ax_w.set_ylabel('(mm/sec)')
    ax_p.set_ylabel(r'($10^9$ kg/s)')

    max_name_len = max(len(n) for n in valid_dicts.keys())

    # --- Plot each dataset's profiles, building a monospaced legend string ---
    for name, data in valid_dicts.items():
        color, prefix_id = color_map.get(name, ('grey', 'Unknown'))
        lw, zorder = (2.0, 5) if name == base_expid else (1.5, 2)

        sh_val, nh_val = data['wstar_lat_sh'], data['wstar_lat_nh']
        talats_str = f' ({sh_val:>6.2f}, {nh_val:>5.2f})'

        # Time B legends carry each dataset's own date range.
        if is_time_b:
            d = dates[name]
            leg_date = f" {d['b_date']} \u2013 {d['e_date']}: {d['n_seas']}"
        else:
            leg_date = ''

        leg_name = f'{prefix_id}: {name:<{max_name_len}}{talats_str}{leg_date}'
        ax_w.plot(data['lats'], data['wstar_1d'] * 1000, color=color, lw=lw, zorder=zorder, label=leg_name)
        ax_p.plot(data['lats'], data['res_1d'], color=color, lw=lw, zorder=zorder)

    # Overlay the multi-dataset mean profile in black.
    avg_wstar_1d = np.mean([d['wstar_1d'] for d in valid_dicts.values()], axis=0)
    avg_res_1d = np.mean([d['res_1d'] for d in valid_dicts.values()], axis=0)
    if base_expid in valid_dicts:
        ax_w.plot(valid_dicts[base_expid]['lats'], avg_wstar_1d * 1000, color='black', lw=2.0, zorder=4)
        ax_p.plot(valid_dicts[base_expid]['lats'], avg_res_1d, color='black', lw=2.0, zorder=4)

    # --- Annotate average turn-around latitudes with boxed labels ---
    box_style = dict(facecolor='white', alpha=1.0, edgecolor='black', boxstyle='round,pad=0.2')

    def annotate_turnarounds(ax, lat_sh, lat_nh):
        if np.isnan(lat_sh) or np.isnan(lat_nh):
            return
        for lat in (lat_sh, lat_nh):
            ax.axvline(lat, color='black', linestyle='--', linewidth=1.5, alpha=0.9, zorder=9)
            y0, y1 = ax.get_ylim()
            y_pos = y0 + (y1 - y0) * 0.95
            ax.text(lat, y_pos, f'{lat:.2f} deg', color='black', ha='center', va='center',
                    zorder=10, bbox=box_style)

    annotate_turnarounds(ax_w, avg_w_sh, avg_w_nh)
    annotate_turnarounds(ax_p, avg_p_sh, avg_p_nh)

    # --- Legend & save ---
    handles, labels = ax_w.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.15),
                ncol=1, frameon=True, prop={'family': 'monospace', 'size': FONT_ANNOTATION})
    save_as_gif(fig, plotsdir, out_filename)
    
def plot_wstar_profiles(data_dict, base_expid, plot_cmps, color_map, season, method,
                        plotsdir, dates, is_summary, is_time_b=False):
    '''
    Vertical WSTAR pressure profiles (main panel) alongside a column of per-dataset
    inset contours. 'method' selects how each level's latitude band is bounded:
      'avrg' - shared averaged turn-around lats
      'indv' - each dataset's own turn-around lats
      'levl' - level-dependent turn-around lats
    is_summary selects the multi-dataset summary variant (shared title range from the
    base entry) versus the 1-vs-1 pairwise variant (range from the single comparison).
    Dates are read from the 'dates' map by name.
    '''
    plot_keys = [base_expid] + plot_cmps
    valid_keys = [k for k in plot_keys if data_dict.get(k) is not None]

    if not is_summary and (plot_cmps[0] not in valid_keys):
        return
    if not valid_keys:
        return

    # Filename varies with the plot variant and Time A vs Time B.
    prefix = 'WSTAR_B' if is_time_b else 'WSTAR'
    method_map = {'avrg': 'Averaged', 'indv': 'Individual', 'levl': 'Level-Dependent'}
    m_str = method_map.get(method, method)
    if is_summary:
        out_filename = f'{prefix}_using_{m_str}_TALATS.{season}.png'
    else:
        out_filename = f'WSTAR_using_{m_str}_TALATS.{plot_cmps[0]}.{base_expid}.{season}.png'

    # --- Figure & panel layout ---
    # Outer margins and inter-panel spacing. wspace sets the gap between the main
    # panel and the inset column; hspace sets the vertical gap between the insets.
    # These are set before adding axes so the later get_position() colorbar resolves.
    max_insets = 5
    fig = plt.figure(figsize=(10, 11))
    plt.subplots_adjust(left=0.08, right=0.95, top=0.93, bottom=0.08, wspace=0.3, hspace=0.35)
    gs = fig.add_gridspec(max_insets, 3)
    ax_main = fig.add_subplot(gs[:, :-1])

    # --- Titles ---
    # Time A shows one shared range: the common window (summary, keyed by base) or the
    # single comparison's pairwise window (1-vs-1). Time B carries dates in the legend.
    if not is_time_b:
        d = dates[base_expid] if is_summary else dates[plot_cmps[0]]
        shared_date = f" ({d['n_seas']}): {d['b_date']} \u2013 {d['e_date']}"
    else:
        shared_date = ''

    ax_main.set_title(f'Residual Vertical Velocity (WSTAR) using {m_str} Turn-Around Lats\n'
                      f'{season}{shared_date}')
    ax_main.set_xlabel('(mm/sec)')
    ax_main.set_ylabel('Pressure (hPa)')

    # Shared averaged turn-around lats (used by the 'avrg' method and inset lines).
    avg_sh = np.nanmean([data_dict[k]['wstar_lat_sh'] for k in valid_keys
                         if not np.isnan(data_dict[k]['wstar_lat_sh'])])
    avg_nh = np.nanmean([data_dict[k]['wstar_lat_nh'] for k in valid_keys
                         if not np.isnan(data_dict[k]['wstar_lat_nh'])])

    # +1 so the longest name still has two spaces before the turn-around values.
    max_name_len = max(len(n) for n in valid_keys) + 1
    y_ticks = [100, 90, 80, 70, 60, 50, 40, 30, 20]

    # --- Plot each dataset: main-panel profile + its inset contour ---
    for i, name in enumerate(valid_keys):
        data = data_dict[name]
        color, prefix_id = color_map.get(name, ('grey', 'Unknown'))
        lw = 2.0 if name == base_expid else 1.5

        # Legend label: turn-around lats only shown for the averaged/individual methods.
        if method in ('avrg', 'indv'):
            sh_bound, nh_bound = data['wstar_lat_sh'], data['wstar_lat_nh']
            talats_str = f' ({sh_bound:>6.2f}, {nh_bound:>5.2f})'
        else:
            talats_str = ''

        # Time B legends carry each dataset's own date range.
        if is_time_b:
            d = dates[name]
            leg_date = f" {d['b_date']} \u2013 {d['e_date']}: {d['n_seas']}"
        else:
            leg_date = ''

        leg_name = f'{prefix_id}: {name:<{max_name_len}}{talats_str}{leg_date}'

        # Build the vertical profile by averaging WSTAR within the method's lat band at each level.
        lats = data['lats']
        w_profile = np.zeros(len(data['levs']))
        for lev_idx in range(len(data['levs'])):
            w_row = data['wstar_2d'][lev_idx, :]
            if method == 'avrg':
                sh_bound, nh_bound = avg_sh, avg_nh
            elif method == 'indv':
                sh_bound, nh_bound = data['wstar_lat_sh'], data['wstar_lat_nh']
            else:  # 'levl'
                sh_bound, nh_bound = data['wstar_lat_sh_lev'][lev_idx], data['wstar_lat_nh_lev'][lev_idx]

            if np.isnan(sh_bound):
                sh_bound = -90
            if np.isnan(nh_bound):
                nh_bound = 90

            mask = (lats >= sh_bound) & (lats <= nh_bound)
            w_profile[lev_idx] = np.nanmean(w_row[mask]) * 1000

        ax_main.plot(w_profile, data['levs'], color=color, lw=lw, label=leg_name)

        # Inset contour of the full 2D WSTAR field, with the turn-around lats overlaid.
        ax_in = fig.add_subplot(gs[i, 2])
        cf = ax_in.contourf(data['lats'], data['levs'], data['wstar_2d'] * 1000,
                            levels=np.linspace(-2, 2, 11), cmap='bwr', extend='both')

        t_title = f'{prefix_id}: {name}'
        if method in ('avrg', 'indv'):
            sh_draw, nh_draw = (avg_sh, avg_nh) if method == 'avrg' else \
                               (data['wstar_lat_sh'], data['wstar_lat_nh'])
            if not np.isnan(sh_draw):
                ax_in.axvline(sh_draw, color='black', linewidth=1.5)
                ax_in.axvline(nh_draw, color='black', linewidth=1.5)
                t_title += f'\nTALATS: {sh_draw:.1f}, {nh_draw:.1f}'
        elif method == 'levl':
            ax_in.plot(data['wstar_lat_sh_lev'], data['levs'], color='black',
                       linewidth=1.5, marker='.', markersize=4)
            ax_in.plot(data['wstar_lat_nh_lev'], data['levs'], color='black',
                       linewidth=1.5, marker='.', markersize=4)

        ax_in.set_title(t_title, fontsize=FONT_ANNOTATION, color=color, fontweight='normal', pad=3)

        # Inset pressure axis: label only 100/50/20 hPa to avoid crowding.
        ax_in.set_yscale('log')
        ax_in.set_yticks(y_ticks)
        ax_in.set_yticklabels([str(t) if t in (100, 50, 20) else '' for t in y_ticks], fontsize=FONT_INSET)
        ax_in.set_ylim(100, 20)
        ax_in.grid(True, linestyle=':', color='silver', alpha=0.7, which='both')
        format_x_axis(ax_in)
        ax_in.set_xticklabels(['90S', '60S', '30S', 'EQ', '30N', '60N', '90N'], fontsize=FONT_INSET)
        ax_in.set_ylabel('')

        # Create a colorbar dynamically positioned below the final inset.
        if i == len(valid_keys) - 1:
            pos = ax_in.get_position()
            cax = fig.add_axes([pos.x0, pos.y0 - 0.04, pos.width, 0.01])
            cbar = fig.colorbar(cf, cax=cax, orientation='horizontal')
            cbar.ax.tick_params(labelsize=7)
            cbar.set_label('WSTAR (mm/sec)', fontsize=FONT_INSET)

    # --- Main-panel axis styling ---
    ax_main.set_yscale('log')
    ax_main.set_yticks(y_ticks)
    ax_main.set_yticklabels([str(t) for t in y_ticks])
    ax_main.set_ylim(100, 20)
    ax_main.grid(True, linestyle=':', color='silver', alpha=0.7, which='both')

    x_min, x_max = ax_main.get_xlim()
    ax_main.set_xlim(x_min - abs(x_min) * 0.05, x_max + abs(x_max) * 0.05)
    ax_main.legend(loc='lower left', prop={'family': 'monospace', 'size': FONT_ANNOTATION})

    save_as_gif(fig, plotsdir, out_filename)

# ==========================================================
# MAIN EXECUTION
# ==========================================================
def main():
    # Build the season help text from the single source of truth in config.
    valid_seasons = ', '.join(SEASON_MONTHS.keys())

    parser = argparse.ArgumentParser(
        description='Residual Circulation (TEM Diagnostics) processing and plotting pipeline.')
    parser.add_argument('-source', required=True,
                        help='Root directory containing the base experiment TEM_Diag files.')
    parser.add_argument('-expid', required=True,
                        help='Base experiment identifier.')
    parser.add_argument('-plotsdir', required=True,
                        help='Output directory for generated plots.')
    parser.add_argument('-begdate', required=True,
                        help='Start date YYYYMM, or NULL to use all available months.')
    parser.add_argument('-enddate', required=True,
                        help='End date YYYYMM, or NULL to use all available months.')
    parser.add_argument('-season', required=True,
                        help=f'One or more space-separated seasons. Valid: {valid_seasons}')
    parser.add_argument('-cmpexp', required=True,
                        help='Space-separated comparison paths (optional colon-suffixed), or NULL.')
    args = parser.parse_args()

    print('\n[res] ' + '=' * 70)
    print('[res]  RESIDUAL CIRCULATION PIPELINE (TEM Diagnostics)')
    print('[res] ' + '=' * 70)
    print(f'[res]  Base experiment: {args.expid}')
    if args.begdate != 'NULL':
        print(f'[res]  Requested date range: {args.begdate} to {args.enddate}')
    else:
        print('[res]  Requested date range: all available months')

    # ---- 1. Find the base experiment's data and pick the months to use ----
    print('\n[res] STEP 1: Locating the base experiment data...')
    base_dict = get_available_months(args.source, args.expid)
    if not base_dict:
        print(f'[res]   No data found for {args.expid}. Nothing to plot; exiting cleanly.')
        sys.exit(0)

    if args.begdate == 'NULL' or args.enddate == 'NULL':
        base_valid_months = sorted(base_dict.keys())
        print('[res]   No date range requested, so using every month the base experiment has.')
    else:
        req_months = generate_month_list(args.begdate, args.enddate)
        base_valid_months = sorted(req_months & set(base_dict.keys()))
        print('[res]   Keeping only the requested months that the base experiment actually has.')
    print(f'[res]   Base experiment will use {len(base_valid_months)} months '
          f'({base_valid_months[0]} to {base_valid_months[-1]}).')

    # ---- 2. Check each comparison dataset and see how it overlaps the base ----
    print('\n[res] STEP 2: Checking the comparison datasets...')
    valid_cmps = {}
    if args.cmpexp and args.cmpexp != 'NULL':
        requested_paths = [p for p in args.cmpexp.split() if p not in ('', 'NULL')]
        print(f'[res]   {len(requested_paths)} comparison dataset(s) requested.')
        for c_idx, p in enumerate(requested_paths, start=1):
            clean_path = p.split(':')[0]
            cmpid = os.path.basename(clean_path)

            # Normalize well-known reanalysis directory names to friendly labels.
            if cmpid == 'MERRA2_MEANS':
                cmpid = 'MERRA-2'
            if cmpid == 'ERA5_Monthly':
                cmpid = 'ERA5'
            # Avoid a name clash when a comparison shares the base experiment's name.
            if cmpid == args.expid:
                cmpid = f'{cmpid}_cmp'

            print(f'[res]   ({c_idx} of {len(requested_paths)}) {cmpid}: looking for its data...')
            print(f'[res]       Searching: {clean_path}')
            cmp_dict = get_available_months(clean_path, cmpid)
            if not cmp_dict:
                print(f'[res]       No TEM_Diag data found for {cmpid}; it will be skipped.')
                continue

            # Its own record (used for climatology plots over its full history).
            cmp_climo = sorted(cmp_dict.keys())


            # The months it shares one-to-one with the base (used for direct comparisons).
            cmp_actual = sorted(set(base_valid_months) & set(cmp_climo))

            valid_cmps[cmpid] = {'dict': cmp_dict, 'actual': cmp_actual, 'climo': cmp_climo}
            print(f'[res]       Found data. Its own record covers {len(cmp_climo)} months '
                  f'({cmp_climo[0]} to {cmp_climo[-1]}).')
            if cmp_actual:
                print(f'[res]       It shares {len(cmp_actual)} months with the base '
                      f'({cmp_actual[0]} to {cmp_actual[-1]}) for direct comparison.')
            else:
                print('[res]       It shares no months with the base, so no direct-comparison '
                      'plots can be made for it.')
    else:
        print('[res]   No comparison datasets requested.')

    # ---- 3. Work out the shared time period common to the base and all comparisons ----
    # The combined comparison plots put every dataset on one figure, so they must all
    # cover the same months. Starting from the base window, each non-reanalysis
    # comparison is checked in turn: if it overlaps the running shared period it stays
    # (shrinking that period as needed); if it does not overlap, it is left out.
    # Earlier comparisons take priority. Reanalysis products never take part.
    print('\n[res] STEP 3: Finding the shared time period for the combined comparison plots...')
    common_months = set(base_valid_months)
    common_cmps = []
    print(f'[res]   Starting from the base experiment: {len(common_months)} months '
          f'({base_valid_months[0]} to {base_valid_months[-1]}).')

    for cmpid, info in valid_cmps.items():
        if is_reanalysis(cmpid):
            print(f'[res]   {cmpid}: left out (reanalysis products are not included in these plots).')
            continue

        overlap = common_months & set(info['actual'])
        if overlap:
            common_months = overlap
            common_cmps.append(cmpid)
            ms = sorted(common_months)
            print(f'[res]   {cmpid}: overlaps -> shared period is now {len(common_months)} months '
                  f'({ms[0]} to {ms[-1]}).')
        else:
            print(f'[res]   {cmpid}: does not overlap the current shared period -> left out.')

    common_valid_months = sorted(common_months)
    make_time_a_summary = len(common_cmps) > 0
    if make_time_a_summary:
        included = ', '.join([args.expid] + common_cmps)
        print(f'[res]   Shared time period: {len(common_valid_months)} months '
              f'({common_valid_months[0]} to {common_valid_months[-1]}).')
        print(f'[res]   Datasets sharing this period: {included}.')
    else:
        print('[res]   No comparison dataset shares a time period with the base, so the '
              'combined comparison plots will be skipped.')
        
    # ---- 4. Date labels, gathered once and reused everywhere ----
    # dates_actual : base-vs-comparison shared months, per comparison (direct comparisons)
    # dates_common : the single shared time period (combined comparison plots)
    # dates_climo  : each dataset's own record, per dataset (combined climatology plots)
    dates_actual, dates_common, dates_climo = {}, {}, {}

    # Turn-around-latitude results, kept separately for each kind of plot.
    talats_actual_dict = {}   # base-vs-comparison shared months -> direct comparison profiles
    talats_common_dict = {}   # shared time period -> combined comparison plots
    talats_climo_dict = {}     # full record -> combined climatology plots

    # Give the base and each comparison a plotting color and short role label.
    all_cmps = list(valid_cmps.keys())
    color_map = {args.expid: ('blue', 'Base')}
    for idx, cmp_name in enumerate(all_cmps):
        color_map[cmp_name] = (CMP_COLORS[idx % len(CMP_COLORS)], f'Cmp{idx + 1}')

    seasons = args.season.strip().strip("'").split()

    # ---- 5. Read and seasonally average the base experiment ----
    print('\n[res] STEP 4: Reading and seasonally averaging the base experiment...')
    b_monthly_climo = extract_12_month_clims([base_dict[m] for m in base_valid_months])
    b_monthly_common = (extract_12_month_clims([base_dict[m] for m in common_valid_months])
                        if make_time_a_summary else None)

    print(f"[res]   Making the base experiment's plots for: {', '.join(seasons)}")
    for s_idx, season in enumerate(seasons, start=1):
        t_months = get_season_months(season)
        print(f'[res]   Season {season} ({s_idx} of {len(seasons)}):')

        # Base turn-around lats over its full record (for the combined climatology plots).
        b_climo_ds = compute_weighted_season(b_monthly_climo, t_months)
        if b_climo_ds is not None:
            talats_climo_dict[args.expid] = calculate_talats(b_climo_ds, args.expid)
            dates_climo[args.expid] = make_date_entry(base_valid_months, t_months)

            print(f'[res]     Creating Eliassen-Palm (EP) flux plot for the base experiment:')
            ds_base_ep = prepare_single_ep_dataset(b_climo_ds, smooth_sigma=1.0)
            plot_ep_flux_diagnostics(
                ds_base_ep, f'{args.expid}', args.plotsdir, f'EP_Flux_{args.expid}.{season}.png',
                is_diff=False, season=season,
                b_date=dates_climo[args.expid]['b_date'], e_date=dates_climo[args.expid]['e_date'], n_seas=dates_climo[args.expid]['n_seas'])
            del ds_base_ep
            gc.collect()

        # Base turn-around lats over the shared period (for the combined comparison plots).
        if make_time_a_summary:
            b_common_ds = compute_weighted_season(b_monthly_common, t_months)
            if b_common_ds is not None:
                talats_common_dict[args.expid] = calculate_talats(b_common_ds, args.expid)
                dates_common[args.expid] = make_date_entry(common_valid_months, t_months)
            del b_common_ds
            gc.collect()

    # ---- 6. Process each comparison dataset and make its comparison plots ----
    print('\n[res] STEP 5: Making the comparison plots, one dataset at a time...')
    for c_idx, (cmpid, info) in enumerate(valid_cmps.items(), start=1):
        print(f'[res]   Comparison dataset {cmpid} ({c_idx} of {len(valid_cmps)}):')

        # Read each set of months this comparison needs (reading the files only once each).
        print('[res]     Reading and seasonally averaging its data...')
        cmp_monthly_climo = extract_12_month_clims([info['dict'][m] for m in info['climo']]) if info['climo'] else None
        cmp_monthly_actual = extract_12_month_clims([info['dict'][m] for m in info['actual']]) if info['actual'] else None
        b_monthly_actual = extract_12_month_clims([base_dict[m] for m in info['actual']]) if info['actual'] else None
        cmp_monthly_common = (extract_12_month_clims([info['dict'][m] for m in common_valid_months])
                              if (make_time_a_summary and cmpid in common_cmps) else None)

        # A dataset's reanalysis status is fixed, so decide once here (not per season).
        cmp_makes_talats = not is_reanalysis(cmpid)
        if not cmp_makes_talats:
            print(f'[res]     {cmpid}: no residual vertical velocity & turn-around '
                  f'latitude plots (reanalysis products are not included).')

        for s_idx, season in enumerate(seasons, start=1):
            t_months = get_season_months(season)
            print(f'[res]     Season {season} ({s_idx} of {len(seasons)}):')

            # Its own climatology: an EP-flux plot over its full record.
            if cmp_monthly_climo:
                cmp_ds_climo = compute_weighted_season(cmp_monthly_climo, t_months)
                if cmp_ds_climo is not None:
                    talats_climo_dict[cmpid] = calculate_talats(cmp_ds_climo, cmpid)
                    dates_climo[cmpid] = make_date_entry(info['climo'], t_months)

                    print('[res]       Creating Eliassen-Palm (EP) flux plot over its full record:')
                    ds_cmp_ep = prepare_single_ep_dataset(cmp_ds_climo, smooth_sigma=1.0)
                    plot_ep_flux_diagnostics(
                        ds_cmp_ep, f'{cmpid}', args.plotsdir, f'EP_Flux_{cmpid}.{season}.png',
                        is_diff=False, season=season,
                        b_date=dates_climo[cmpid]['b_date'], e_date=dates_climo[cmpid]['e_date'], n_seas=dates_climo[cmpid]['n_seas'])
                    del ds_cmp_ep
                    gc.collect()

            # Shared time period: recompute its turn-around lats for the combined plots.
            if cmp_monthly_common:
                cmp_ds_common = compute_weighted_season(cmp_monthly_common, t_months)
                if cmp_ds_common is not None:
                    talats_common_dict[cmpid] = calculate_talats(cmp_ds_common, cmpid)
                del cmp_ds_common
                gc.collect()

            # Shared months with the base: the direct base-vs-comparison plots.
            if cmp_monthly_actual and b_monthly_actual:
                cmp_ds_actual = compute_weighted_season(cmp_monthly_actual, t_months)
                b_ds_actual = compute_weighted_season(b_monthly_actual, t_months)

                if cmp_ds_actual is not None and b_ds_actual is not None:
                    talats_actual_dict[cmpid] = calculate_talats(cmp_ds_actual, cmpid)
                    talats_actual_dict[args.expid] = calculate_talats(b_ds_actual, args.expid)
                    dates_actual[cmpid] = make_date_entry(info['actual'], t_months)

                    print('[res]       Creating streamfunction & residual circulation plots:')
                    plot_str_and_res(b_ds_actual, cmp_ds_actual, args.plotsdir, season,
                                     args.expid, cmpid, dates_actual[cmpid])
                    plot_str_or_res('STR', b_ds_actual, cmp_ds_actual, args.plotsdir, season,
                                    args.expid, cmpid, dates_actual[cmpid])
                    plot_str_or_res('RES', b_ds_actual, cmp_ds_actual, args.plotsdir, season,
                                    args.expid, cmpid, dates_actual[cmpid])

                    print('[res]       Creating Eliassen-Palm (EP) flux difference plots:')
                    aligned_b, aligned_c = align_datasets(b_ds_actual, cmp_ds_actual)
                    prep_b = prepare_single_ep_dataset(aligned_b, smooth_sigma=1.0)
                    prep_c = prepare_single_ep_dataset(aligned_c, smooth_sigma=1.0)
                    ds_diff_ep = prep_b - prep_c
                    plot_ep_flux_diagnostics(
                        ds_diff_ep, f'{args.expid} minus {cmpid}', args.plotsdir,
                        f'EP_Flux_diff_{args.expid}-{cmpid}.{season}.png', is_diff=True, season=season,
                        b_date=dates_actual[cmpid]['b_date'], e_date=dates_actual[cmpid]['e_date'],
                        n_seas=dates_actual[cmpid]['n_seas'])
                    plot_ep_flux_diagnostics(
                        -ds_diff_ep, f'{cmpid} minus {args.expid}', args.plotsdir,
                        f'EP_Flux_diff_{cmpid}-{args.expid}.{season}.png', is_diff=True, season=season,
                        b_date=dates_actual[cmpid]['b_date'], e_date=dates_actual[cmpid]['e_date'],
                        n_seas=dates_actual[cmpid]['n_seas'])

                    if cmp_makes_talats:
                        print('[res]       Creating residual vertical velocity & turn-around latitude plots:')
                        for method in ('levl', 'avrg', 'indv'):
                            plot_wstar_profiles(talats_actual_dict, args.expid, [cmpid], color_map,
                                                season, method, args.plotsdir, dates_actual,
                                                is_summary=False, is_time_b=False)

                    del cmp_ds_actual, b_ds_actual, prep_b, prep_c, aligned_b, aligned_c, ds_diff_ep
                    gc.collect()

    # ---- 7. Combined plots that place every dataset on one figure ----
    print('\n[res] STEP 6: Making the combined summary plots...')
    for s_idx, season in enumerate(seasons, start=1):
        print(f'[res]   Season {season} ({s_idx} of {len(seasons)}):')

        # Combined comparison plots over the shared time period (only if it exists).
        if make_time_a_summary:
            print('[res]     Creating combined comparison plots over the shared time period:')
            plot_latitudinal_talats_summary(talats_common_dict, args.expid, color_map,
                                            season, args.plotsdir, dates_common, is_time_b=False)
            for method in ('levl', 'avrg', 'indv'):
                plot_wstar_profiles(talats_common_dict, args.expid, common_cmps, color_map,
                                    season, method, args.plotsdir, dates_common,
                                    is_summary=True, is_time_b=False)
        else:
            print('[res]     Skipping the combined comparison plots '
                  '(no comparison dataset shares a time period with the base).')

        # Combined climatology plots: each dataset over its own full record.
        print("[res]     Creating combined climatology plots (each dataset's full record):")
        plot_latitudinal_talats_summary(talats_climo_dict, args.expid, color_map,
                                        season, args.plotsdir, dates_climo, is_time_b=True)
        for method in ('levl', 'avrg', 'indv'):
            plot_wstar_profiles(talats_climo_dict, args.expid, all_cmps, color_map,
                                season, method, args.plotsdir, dates_climo,
                                is_summary=True, is_time_b=True)

    print('\n[res] ' + '=' * 70)
    print('[res]  DONE. All residual circulation plots have been generated.')
    print('[res] ' + '=' * 70 + '\n')


if __name__ == '__main__':
    main()
