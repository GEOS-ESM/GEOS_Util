#!/usr/bin/env python3
'''
Residual Circulation (TEM Diagnostics) Plotting Pipeline

Processes monthly Transformed Eulerian Mean (TEM) diagnostic files to produce 
various plots. Some plots require strict date-alignment (apples-to-apples) 
between a base experiment and comparison datasets to ensure accurate 
differencing; others plot the full available datasets (climatologies).

The pipeline operates entirely in-memory for speed and explicitly subsets
variables from the TEM monthly files to maintain a minimal memory footprint.

Visualizations:
  - Module A: Zonal Mean Streamfunction and Residual Circulation 
  - Module B: Eliassen-Palm (EP) Fluxes and Divergence
  - Module C: WSTAR and Stratospheric Transport (Turn-Around Latitudes)

Usage:
    Typically invoked via a wrapper shell script. Requires arguments:
    -source, -expid, -plotsdir, -begdate, -enddate, -season, -cmpexp
'''

import argparse
import gc
import glob
import os
import sys
import warnings

import numpy as np
import scipy.ndimage
import xarray as xr

import matplotlib
matplotlib.use('Agg')  # Headless backend for batch cluster execution
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Silence xarray/numpy warnings from all-NaN slices generated during subsetting
warnings.filterwarnings('ignore', message='All-NaN slice encountered')
warnings.filterwarnings('ignore', message='Mean of empty slice')


# ==========================================================
# CONFIGURATION
# ==========================================================

# Global matplotlib styling shared by every figure.
plt.rcParams.update({
    'figure.titlesize': 14,   # Main figure suptitle
    'axes.titlesize': 11,     # Individual subplot titles
    'axes.labelsize': 11,     # X/Y axis physical labels
    'xtick.labelsize': 9,     # X-axis geographic tick text
    'ytick.labelsize': 9,     # Y-axis pressure tick text
    'font.size': 9            # Fallback for text without an explicit size
})

# Secondary text sizes
FONT_ANNOTATION = 8   # colorbar ticks & labels, legends, quiver key, etc.
FONT_INSET = 7        # for inset wstar plots: labels and tick labels

# Season names mapped to constituent calendar months
SEASON_MONTHS = {'ANN': list(range(1, 13)), 'DJF': [12, 1, 2], 
                 'MAM': [3, 4, 5], 'JJA': [6, 7, 8], 'SON': [9, 10, 11], 
                 'JAN': [1], 'FEB': [2], 'MAR': [3], 'APR': [4], 'MAY': [5], 
                 'JUN': [6], 'JUL': [7], 'AUG': [8], 'SEP': [9], 'OCT': [10], 
                 'NOV': [11], 'DEC': [12]}

# Month numbers mapped to 3-letter abbreviations for date labels
MONTH_ABBR = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
              7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'}

# Days-in-month weights for seasonal averaging
DAYS_IN_MONTH = {1: 31, 2: 28.25, 3: 31, 4: 30, 5: 31, 6: 30,
                 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

# Variables kept from the raw files; everything else is dropped to save memory.
TARGET_VARS = ['str', 'res', 'epfy', 'epfz', 'epfdiv', 'wstar', 'delp']

# Colors assigned to comparison datasets in Module C (base exp is always blue)
CMP_COLORS = ['darkorange', 'forestgreen', 'crimson', 'magenta',
              'saddlebrown', 'hotpink', 'gray', 'olive', 'deepskyblue']

# Output resolution shared by every saved figure
FIG_DPI = 300


# ==========================================================
# DATA PROCESSING HELPERS
# ==========================================================

def is_reanalysis(dataset_name):
    '''True for MERRA & ERA, which are excluded from turn-around lats plots.'''
    return 'MERRA' in dataset_name.upper() or 'ERA' in dataset_name.upper()

# ---- File / date discovery ----

def generate_month_list(start_ym, end_ym):
    '''Generates a continuous set of YYYYMM strings between two dates.'''
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
    '''Scans a TEM_Diag directory to catalog YYYYMM monthly NetCDF files.'''
    search_path = os.path.join(directory, 'TEM_Diag', 
                               '*.TEM_Diag.monthly.*.nc*')
    files = glob.glob(search_path)
    valid_files = {}
    for f in files:
        parts = os.path.basename(f).split('.')
        if len(parts) >= 2:
            date_str = parts[-2]
            if date_str.isdigit() and len(date_str) == 6:
                valid_files[date_str] = f
    return valid_files


# ---- Dataset averaging and alignment ----

def extract_12_month_clims(files_list):
    '''
    Groups monthly files by calendar month (1-12), subsets to target variables,
    and computes the time-mean per month to minimize memory footprint. 
    Degenerate longitude dimensions are dropped for 2D (lat/lev) processing.
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
        # Utilizing join='override' adopts the first file's coordinates. 
        # Some sources (e.g. MERRA-2) carry sub-picodegree float jitter in 
        # their lat values, which the outer-join default would otherwise flag.
        ds = xr.open_mfdataset(month_files[m], engine='netcdf4',
                               data_vars='minimal', coords='minimal',
                               compat='override', join='override')
        avail_vars = [v for v in TARGET_VARS if v in ds.data_vars]
        clims[m] = ds[avail_vars].mean(dim='time').squeeze(
            dim='lon', drop=True).compute()
        ds.close()
    return clims

def compute_weighted_season(monthly_clims, target_months):
    '''Weights calendar months by their lengths (days) into a seasonal mean.'''
    weighted_sum = None
    total_weight = 0.0
    for m in target_months:
        if monthly_clims.get(m) is not None:
            w = DAYS_IN_MONTH[m]
            weighted_sum = (monthly_clims[m] * w if weighted_sum is None 
                            else weighted_sum + monthly_clims[m] * w)
            total_weight += w
    return weighted_sum / total_weight if total_weight > 0 else None

def align_datasets(ds_base, ds_cmp):
    '''
    Forces spatial alignment for differencing by interpolating the denser-grid
    dataset down onto the coarser grid (bilinear) in lat and lev dimensions.
    '''
    size_base = ds_base.sizes.get('lat', 0) * ds_base.sizes.get('lev', 0)
    size_cmp = ds_cmp.sizes.get('lat', 0) * ds_cmp.sizes.get('lev', 0)
    if size_base <= size_cmp:
        ds_cmp = ds_cmp.interp(
            lev=ds_base.lev, lat=ds_base.lat, method='linear', 
            kwargs={'fill_value': 'extrapolate'})
    else:
        ds_base = ds_base.interp(
            lev=ds_cmp.lev, lat=ds_cmp.lat, method='linear', 
            kwargs={'fill_value': 'extrapolate'})
    return ds_base, ds_cmp

# ==========================================================
# PLOTTING HELPERS
# ==========================================================

def save_as_gif(fig, plotsdir, png_name):
    '''
    Saves a figure as PNG, then renames it to GIF (for syncing with website). 
    Closes the figure to free memory, and reports the finished file in the log.
    '''
    out_filepath = os.path.join(plotsdir, png_name)
    fig.savefig(out_filepath, dpi=FIG_DPI)
    gif_name = png_name.replace('.png', '.gif')
    os.rename(out_filepath, out_filepath.replace('.png', '.gif'))
    plt.close(fig)
    print(f'[res]         made {gif_name}')

# ---- Axis formatting helpers ----

def format_x_axis(ax, fontsize=None):
    '''
    Applies symmetric geographic latitude labeling (-90 to +90).
    Pass fontsize to shrink the tick labels (else defaults to global).
    '''
    ax.set_xlim(-90, 90)
    ax.set_xticks([-90, -60, -30, 0, 30, 60, 90])
    ax.set_xticklabels(['90S', '60S', '30S', 'EQ', '30N', '60N', '90N'], 
                       fontsize=fontsize)

def format_y_axis(ax, scale='linear'):
    '''
    Applies pressure boundaries and targeted tick labeling with grid, and 
    enforces standard atmospheric orientation (1000 hPa at the bottom).
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
    
# ---- Colorbar/colormap helpers ----

def relabel_colorbar_ticks(cbar, bounds, fmt='{:.1f}', axis='x'):
    '''
    Relabels colorbar ticks from a set of bound values, formatting with fmt.
    Pass fmt='{:g}' to strip trailing zeros, or '{:.1f}' to force one decimal 
    place. Set axis='y' for vertical colorbars.
    '''
    labels = [fmt.format(b) if b != 0 else '0' for b in bounds]
    if axis == 'x':
        cbar.ax.set_xticklabels(labels)
    else:
        cbar.ax.set_yticklabels(labels)

def get_symmetric_cmap(vmax_raw=None, num_bins=11, force_bounds=None):
    '''
    Builds a symmetric diverging colormap with a transparent center zero bin.
    For difference plots (dynamic boundaries) it rounds to clean half-bin 
    widths (e.g. 0.1, 0.2, 0.5, 1.0, 2.0), guaranteeing colorbar labels never 
    exceed one decimal place while keeping strictly equidistant bins. num_bins 
    is forced odd so a true-zero center bin exists.
    '''
    if force_bounds is not None:
        bounds = force_bounds
    else:
        if num_bins % 2 == 0:
            num_bins += 1
        target_h = vmax_raw / num_bins
        # Candidate array of clean half-bin widths.
        nice_h = np.concatenate([np.array([1., 2., 5.]) * (10 ** exp) 
                                 for exp in range(-4, 5)])
        h = nice_h[nice_h >= target_h][0]
        bounds = h * np.arange(-num_bins, num_bins + 2, 2)
    colors = plt.get_cmap('bwr')(np.linspace(0, 1, len(bounds) - 1))
    # Make the exact middle bin transparent (true zero).
    colors[(len(bounds) - 1) // 2] = [1.0, 1.0, 1.0, 0.0]
    custom_cmap = mcolors.ListedColormap(colors)
    return bounds, custom_cmap, mcolors.BoundaryNorm(bounds, custom_cmap.N)

# ---- Contours and quivers helpers ----

def draw_labeled_contours(ax, lat, lev, data, clevs, inline_spacing=15):
    '''
    Draws solid/dashed black contour lines with inline numeric labels, skipping
    the zero contour and boxing each label in white for legibility. Integers 
    render without decimals; sub-unit values keep one decimal place. 
    Returns the ContourSet.
    '''
    cs = ax.contour(lat, lev, data, levels=clevs, colors='k', linewidths=1)
    levels_to_label = [l for l in cs.levels if l != 0]
    if levels_to_label:
        label_fmt = lambda x: f'{x:.1f}' if abs(x) < 1 else f'{x:.0f}'
        labels = ax.clabel(cs, levels=levels_to_label, inline=True, 
                           fmt=label_fmt, inline_spacing=inline_spacing, 
                           use_clabeltext=True)
        for l in labels:
            l.set_bbox(dict(facecolor='white', alpha=0.8, edgecolor='none', 
                            pad=1))
    return cs

def plot_contours(ax, lat, lev, data, clevs, use_cmap=False, norm=None, 
                  cmap='bwr', draw_lines=True):
    '''
    Renders a data field as either shaded contours (use_cmap=True) or a grey
    negative-region mask. Optionally overlays labeled black contour lines. 
    Returns the filled mappable (or None when only the mask is drawn).
    '''
    plt.rcParams['contour.negative_linestyle'] = 'dashed'
    mappable = None
    if use_cmap:
        mappable = ax.contourf(lat, lev, data, levels=clevs, cmap=cmap, 
                               norm=norm, extend='both')
    else:
        ax.contourf(lat, lev, data, levels=[-np.inf, 0], colors=['lightgrey'], 
                    alpha=0.9)
    if draw_lines:
        draw_labeled_contours(ax, lat, lev, data, clevs)
    return mappable

def calculate_arrow_skip(lat_array, target_degrees=4.0):
    '''Interval yielding roughly target_degrees of horizontal arrow spacing.'''
    if len(lat_array) < 2:
        return 1
    dlat = abs(lat_array[1] - lat_array[0])
    return max(1, int(round(target_degrees / float(dlat))))

# ---- Date/season string helpers ----

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

def get_dates(months_list, t_months):
    '''Builds a date entry (start, end, season count) from a month list.'''
    return {'b_date': format_date_str(months_list[0]),
            'e_date': format_date_str(months_list[-1]),
            'n_seas': get_season_count_str(months_list, t_months)}

# ==========================================================
# MODULE A: ZONAL STREAMFUNCTION & RESIDUAL CIRCULATION
# ==========================================================

def plot_str_and_res(ds_base, ds_cmp, plotsdir, season, expid, cmpid, dates):
    '''
    Four-panel side-by-side comparison (Base vs Comparison):
      Top row:    Meridional Streamfunction (linear scale)
      Bottom row: Residual Circulation (log scale, custom non-linear bins)
    'dates' is this pair's pairwise overlap date entry
    '''

    # Figure and panel layout
    fig = plt.figure(figsize=(10, 7.5))
    w, h = 0.36, 0.33
    ax_exp_top = fig.add_axes([0.10, 0.52, w, h])
    ax_cmp_top = fig.add_axes([0.52, 0.52, w, h])
    cax_top    = fig.add_axes([0.90, 0.52, 0.015, h])
    ax_exp_bot = fig.add_axes([0.10, 0.10, w, h])
    ax_cmp_bot = fig.add_axes([0.52, 0.10, w, h])
    cax_bot    = fig.add_axes([0.90, 0.10, 0.015, h])

    # Main title
    fig.suptitle(
        f'EXP: {expid}  vs  CMP: {cmpid}\n{season} ({dates["n_seas"]}, '
        f'actual): {dates["b_date"]} \u2013 {dates["e_date"]}', y=0.97)


    # Per-variable rendering rules: axes, var, display name, scale, and levels
    plot_rules = [{'axes': (ax_exp_top, ax_cmp_top, cax_top), 'var': 'str',
                   'name': r'Meridional Streamfunction ($10^9$ kg/s)',
                   'scale': 'linear', 'clevs': np.arange(-20, 22, 2)},
                  {'axes': (ax_exp_bot, ax_cmp_bot, cax_bot), 'var': 'res',
                   'name': r'Residual Circulation ($10^9$ kg/s)',
                   'scale': 'log',
                   'clevs': [-50, -20, -10, -5, -2, -1, -0.5, -0.2, -0.1, 0,
                             0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50]}]

    # Render each row (Base on the left, Comparison on the right)
    for rule in plot_rules:
        ax_e, ax_c, cax = rule['axes']
        v = rule['var']
        clevs = rule['clevs']
        norm = (mcolors.BoundaryNorm(clevs, plt.get_cmap('bwr').N) 
                if rule['scale'] == 'log' else None)
        y_top = 0.1 if rule['scale'] == 'log' else 10

        # Base experiment panel
        plot_contours(ax_e, ds_base.lat, ds_base.lev, ds_base[v], clevs, 
                      use_cmap=True, norm=norm)
        format_y_axis(ax_e, scale=rule['scale'])
        ax_e.set_ylim(1000, y_top)
        format_x_axis(ax_e)
        ax_e.set_title(f'EXP: {rule["name"]}')

        # Comparison dataset panel with shared vertical colorbar for row
        cf = plot_contours(ax_c, ds_cmp.lat, ds_cmp.lev, ds_cmp[v], clevs, 
                           use_cmap=True, norm=norm)
        format_y_axis(ax_c, scale=rule["scale"])
        ax_c.set_ylim(1000, y_top)
        ax_c.set_ylabel('')
        format_x_axis(ax_c)
        ax_c.set_title(f"CMP: {rule['name']}")
        cbar = fig.colorbar(cf, cax=cax, orientation='vertical')
        cbar.ax.tick_params(labelsize=FONT_ANNOTATION)

    # Footer and save
    fig.text(0.10, 0.04, f'( EXPID: {expid} )', ha='left')
    save_as_gif(fig, plotsdir, f'zonal_{cmpid}_str_res.{season}.png')

def plot_str_or_res(
        var, ds_base, ds_cmp, plotsdir, season, expid, cmpid, dates):
    '''
    Three-panel vertical layout for a single variable:
      Top:    Absolute Base
      Middle: Absolute Comparison
      Bottom: Difference (Base-Comparison) shaded, overlaid with Base contours
    'dates' is this pair's pairwise overlap date entry
    '''

    # Align grids so the difference is computed on a common grid
    ds_base_aligned, ds_cmp_aligned = align_datasets(ds_base, ds_cmp)
    diff_data = ds_base_aligned[var] - ds_cmp_aligned[var]
    target_lat, target_lev = ds_base_aligned.lat, ds_base_aligned.lev
    exp_target_data = ds_base_aligned[var]

    # Figure and panel layout
    fig = plt.figure(figsize=(6.5, 11.5))
    l, w, h = 0.11, 0.78, 0.235
    axes = [
        fig.add_axes([l, 0.670, w, h]),
        fig.add_axes([l, 0.385, w, h]),
        fig.add_axes([l, 0.100, w, h]),
    ]
    cax = fig.add_axes([l, 0.060, w, 0.015])

    # Variable-specific (str or res) display name and absolute contour levels
    is_str = (var == 'str')
    title_str = (r'Meridional Streamfunction' if is_str 
                 else r'Residual Circulation')
    base_clevs = np.arange(-20, 22, 2) if is_str else np.arange(-100, 105, 5)

    # Main title 
    fig.suptitle(
        f'{title_str} ($10^9$ kg/s)\n{season} ({dates["n_seas"]}, actual): '
        f'{dates["b_date"]} \u2013 {dates["e_date"]}', y=0.97)

    # Top: absolute base
    plot_contours(axes[0], ds_base.lat, ds_base.lev, ds_base[var], base_clevs, 
                  use_cmap=False)
    axes[0].set_title(f'{expid}')
    
    # Middle: absolute comparison
    plot_contours(axes[1], ds_cmp.lat, ds_cmp.lev, ds_cmp[var], base_clevs, 
                  use_cmap=False)
    axes[1].set_title(f'{cmpid}')
    
    # Bottom: difference shading and overlaid base contours
    axes[2].set_title('Difference (Top-Middle) Shaded; EXP Contours')
    axes[2].contourf(target_lat, target_lev, exp_target_data,
                     levels=[-np.inf, 0], colors=['lightgrey'], alpha=0.9)
    vmax_raw = float(np.abs(diff_data).max())
    bounds, custom_cmap, norm = get_symmetric_cmap(vmax_raw=vmax_raw)
    cf = axes[2].contourf(target_lat, target_lev, diff_data, levels=bounds, 
                          norm=norm, cmap=custom_cmap, extend='both', zorder=2)
    cbar = fig.colorbar(cf, cax=cax, orientation='horizontal', ticks=bounds)
    cbar.ax.tick_params(labelsize=FONT_ANNOTATION)
    relabel_colorbar_ticks(cbar, bounds, fmt='{:.1f}', axis='x')
    draw_labeled_contours(axes[2], target_lat, target_lev, exp_target_data, 
                          base_clevs)

    # Shared axis formatting
    for ax in axes:
        format_y_axis(ax, scale='linear')
        ax.set_ylim(1000, 10)
        format_x_axis(ax)

    # Footer and save
    fig.text(0.04, 0.02, f'( EXPID: {expid} )', ha='left')
    save_as_gif(fig, plotsdir, f'zonal_{cmpid}_{var}.{season}.png')
    

# ==========================================================
# MODULE B: ELIASSEN-PALM FLUX
# ==========================================================

def prepare_single_ep_dataset(ds):
    '''
    Subsets EP variables, scales divergence by 10^-2 for plotting 
    standardization, and applies a Gaussian filter (sigma=1) to the divergence
    field to smooth numerical noise.
    '''
    d_out = ds[['epfy', 'epfz', 'epfdiv']].copy()
    d_out['epfdiv'] = d_out['epfdiv'] / 100.0
    d_out['epfdiv'].values = np.where(
        np.isnan(d_out['epfdiv'].values), np.nan,
        scipy.ndimage.gaussian_filter(d_out['epfdiv'].fillna(0), sigma=1.0))
    return d_out

def plot_ep_flux_diagnostics(ds, title_str, plotsdir, out_filename, is_diff, 
                             season, b_date, e_date, n_seas):
    '''
    Four-panel EP Flux figure: divergence (shading) plus flux vectors
      Top-left:     Main domain       (log, 1000-0.8 hPa)
      Top-right:    Partial domain    (log, 1000-8 hPa)
      Bottom-left:  Troposphere zoom  (linear, 1000-80 hPa)
      Bottom-right: Stratosphere zoom (log, 100-8 hPa)

    Full dataset (climatology) dates are used for absolute plots; this pair's 
    pairwise overlap dates are used for difference plots. The first 3 subplots 
    use a common reference arrow value and colorbar maximum while the 
    bottom-right (stratosphere zoom) uses a smaller value: these are fixed for 
    the absolute plots and derived from the field for difference plots.
    '''

    # Figure and panel layout (axes are [left, bottom, width, height])
    fig = plt.figure(figsize=(10, 8))
    w,    h    = 0.40, 0.28  # Subplot width and height
    l_c1, l_c2 = 0.08, 0.55  # Left location for columns 1 and 2
    axes       = [fig.add_axes([l_c1, 0.58, w, h]), 
                  fig.add_axes([l_c2, 0.58, w, h]),
                  fig.add_axes([l_c1, 0.16, w, h]), 
                  fig.add_axes([l_c2, 0.16, w, h])]
    
    # Horizontal colorbar axes sitting directly beneath each subplot
    h_cb  = 0.015  # Colorbar height
    caxes = [fig.add_axes([l_c1, 0.51, w, h_cb]),
             fig.add_axes([l_c2, 0.51, w, h_cb]),
             fig.add_axes([l_c1, 0.09, w, h_cb]), 
             fig.add_axes([l_c2, 0.09, w, h_cb])]

    # Main title
    if is_diff:
        date_label = f'{season} ({n_seas}, actual): {b_date} \u2013 {e_date}'
    else:
        date_label = f'{season} ({n_seas}): {b_date} \u2013 {e_date}'
    fig.suptitle(f'Eliassen-Palm Flux (Vectors) and Divergence (Shaded, '
                 f'$10^{{-2}}$ $m^2/s^2$)\n{title_str}\n{date_label}', y=0.97)

    # Determine shading bins and reference-arrow magnitudes
    if is_diff:  # Difference plots: derive reference arrow magnitude from 95th 
                 # pctl and shading bins from maxima, separate for the first 3
                 # subplots (main) versus the lower right (stratosphere zoom).
        def get_ref(min_p, max_p, z_y):
            mask = (ds.lev.values <= min_p) & (ds.lev.values >= max_p)
            mags = np.sqrt(ds['epfy'].values[mask, :] ** 2 +
                           (-ds['epfz'].values[mask, :] * z_y) ** 2)
            p = np.nanpercentile(mags, 95)
            exp = np.floor(np.log10(p)) if p > 0 else 1
            return np.round(p / (10 ** exp), 1) * (10 ** exp)
        
        # First 3 subplots (main)
        ref_main = get_ref(1000, 0.8, 100)
        vmax_main = float(np.abs(ds['epfdiv'].sel(lev=slice(None, 0.8))).max())
        bounds_main,  cmap_main,  norm_main  = get_symmetric_cmap(
            vmax_raw=vmax_main)
        
        # Lower-right subplot (stratosphere zoom)
        ref_strat = get_ref(100, 8, 500)
        vmax_strat = float(np.abs(ds['epfdiv'].sel(lev=slice(100, 8))).max())
        bounds_strat, cmap_strat, norm_strat = get_symmetric_cmap(
            vmax_raw=vmax_strat)
        
    else:  # Absolute plots: fixed shading bins and hardcoded reference arrows
        ref_main, ref_strat = 2.5e9, 8e8
        bounds_main,  cmap_main,  norm_main  = get_symmetric_cmap(
            force_bounds=np.linspace(-5.5, 5.5, 12))
        bounds_strat, cmap_strat, norm_strat = get_symmetric_cmap(
            force_bounds=np.linspace(-0.55, 0.55, 12))
    
    # Thin the vector field in the horizontal based on target lat spacing
    skip_x = calculate_arrow_skip(ds.lat.values, target_degrees=4.0)

    # Render each panel
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

        # Bottom-right panel uses its own bins; the rest share the main bins.
        bnds, c, nrm = ((bounds_strat, cmap_strat, norm_strat) if i == 3 
                        else (bounds_main, cmap_main, norm_main))

        # Shaded divergence and colorbar
        cf = plot_contours(ax, ds.lat, ds.lev, ds['epfdiv'], bnds,
                           use_cmap=True, norm=nrm, cmap=c, draw_lines=False)
        cbar = fig.colorbar(cf, cax=caxes[i], orientation='horizontal', 
                            ticks=bnds)
        relabel_colorbar_ticks(cbar, bnds, fmt='{:g}', axis='x')
        cbar.ax.tick_params(labelsize=FONT_ANNOTATION)

        # Flux vectors: vertical component is stretched (Z/Y)
        U = ds['epfy'].values
        V = ds['epfz'].values
        arrfct = 500 if i == 3 else 100
        ref_val = ref_strat if i == 3 else ref_main
        V_scaled = -V * arrfct

        # Thin the vector field in the vertical based levels visible in panel
        valid_idx = np.where((ds.lev.values >= lims[1]) & 
                             (ds.lev.values <= lims[0]))[0]
        skip_y = max(1, len(valid_idx) // 12)
        plot_idx = valid_idx[::skip_y]
        
        # Create the vectors
        X, Y = np.meshgrid(ds.lat.values[::skip_x], ds.lev.values[plot_idx])
        U_sub = U[plot_idx, ::skip_x]
        V_sub = V_scaled[plot_idx, ::skip_x]
        q = ax.quiver(X, Y, U_sub, V_sub, pivot='middle', angles='uv',
                      color='black', alpha=0.9, width=0.003, headwidth=4, 
                      headlength=5, scale=ref_val * 15)

        # Quiver magnitude and Z/Y reference between each panel and colorbar
        ref_label = f'{ref_val:g}'.replace('+0', '').replace('+', '')
        ax.quiverkey(q, 0.73, -0.14, ref_val, f'{ref_label}  (Z/Y: {arrfct})',
                     labelpos='E', coordinates='axes', 
                     fontproperties={'size': FONT_ANNOTATION})

        # Format axes and labels
        format_y_axis(ax, scale)
        ax.set_ylim(lims[0], lims[1])
        format_x_axis(ax)
        if i in (1, 3): ax.set_ylabel('')
    
    # Save
    save_as_gif(fig, plotsdir, out_filename)    
    
# ==========================================================
# MODULE C: TURN-AROUND LATS & VERTICAL PROFILES
# ==========================================================

def calc_talats(ds, dataset_name):
    '''
    Extracts the stratospheric (100 - 20 hPa) dataset subset and calculates 
    Turn-Around Latitudes (TALATS): WSTAR zero-crossings (both vertically
    integrated and level-dependent) and residual streamfunction (PSI) extrema.
    Returns a dict with the following keys (or None for MERRA/ERA):
    Coordinates
        'lats'              1D array of latitudes
        'levs'              1D array of pressure levels (hPa), 100 down to 20
    Vertically integrated profiles (pressure-weighted over 100-20 hPa)
        'wstar_1d'          WSTAR (m/s) vs lat
        'res_1d'            Residual streamfunction (PSI, (10^9 kg/s)) vs lat
    Full 2D field
        'wstar_2d'          WSTAR (m/s) on the (lev, lat) grid
    Turn-around latitudes from the vertically integrated WSTAR
        'wstar_lat_sh'      SH zero-crossing (searched over -70 to -15)
        'wstar_lat_nh'      NH zero-crossing (searched over  15 to  70)
    Extrema latitudes from the vertically integrated residual streamfunction
        'res_lat_sh'        Latitude of the PSI minimum in the SH (-70 to 0)
        'res_lat_nh'        Latitude of the PSI maximum in the NH (0 to 70)
    Level-dependent turn-around latitudes (one value per pressure level)
        'wstar_sh_lev'      SH WSTAR zero-crossing at each level
        'wstar_nh_lev'      NH WSTAR zero-crossing at each level
    '''
    if is_reanalysis(dataset_name):
        return None
    
    # Pressure-weighted vertical integrals across the 100-20 hPa layer.
    strat_ds = ds.sel(lev=slice(100, 20))
    weights = strat_ds['delp']
    wstar_int = ((strat_ds['wstar'] * weights).sum(dim='lev') 
                 / weights.sum(dim='lev'))
    res_int   = ((strat_ds['res']   * weights).sum(dim='lev') 
                 / weights.sum(dim='lev'))
    
    # Extract data values
    lats = wstar_int.lat.values
    levs =  strat_ds.lev.values
    res_1d   =   res_int.values
    wstar_1d = wstar_int.values
    wstar_2d = strat_ds['wstar'].values

    # PSI extrema: minimum in the SH, maximum in the NH
    res_sh_mask = (lats >= -70) & (lats <= 0)
    res_nh_mask = (lats >= 0) & (lats <= 70)
    res_lat_sh = lats[res_sh_mask][np.argmin(res_1d[res_sh_mask])]
    res_lat_nh = lats[res_nh_mask][np.argmax(res_1d[res_nh_mask])]

    def find_zero_crossing(lats_slice, vals_slice):
        '''Linearly interpolated latitude where profile first changes sign.'''
        for i in range(len(vals_slice) - 1):
            if vals_slice[i] * vals_slice[i + 1] <= 0:
                v1, v2 = vals_slice[i], vals_slice[i + 1]
                l1, l2 = lats_slice[i], lats_slice[i + 1]
                if v1 == v2:
                    return l1
                return l1 - v1 * (l1 - l2) / (v1 - v2)
        return np.nan

    # WSTAR zero-crossings: vertically integrated turn-around boundaries
    sh_mask = (lats >= -70) & (lats <= -15)
    nh_mask = (lats >= 15) & (lats <= 70)
    wstar_lat_sh = find_zero_crossing(lats[sh_mask], wstar_1d[sh_mask])
    wstar_lat_nh = find_zero_crossing(lats[nh_mask], wstar_1d[nh_mask])

    # Level-dependent boundaries across the pressure array
    sh_lev, nh_lev = [], []
    for i in range(len(levs)):
        w_lev = wstar_2d[i, :]
        sh_lev.append(find_zero_crossing(lats[sh_mask], w_lev[sh_mask]))
        nh_lev.append(find_zero_crossing(lats[nh_mask], w_lev[nh_mask]))

    return {'lats': lats, 'levs': levs,
        'wstar_1d': wstar_1d, 'res_1d': res_1d, 'wstar_2d': wstar_2d,
        'wstar_lat_sh': wstar_lat_sh, 'wstar_lat_nh': wstar_lat_nh,
        'res_lat_sh': res_lat_sh, 'res_lat_nh': res_lat_nh,
        'wstar_sh_lev': np.array(sh_lev), 'wstar_nh_lev': np.array(nh_lev)}

def plot_latitudinal_talats_summary(talats_dict, base_expid, color_map, season, 
                                    plotsdir, dates, is_climo=False):
    '''
    Stacked 1D latitude stratospheric profiles with turn-around annotations:
      Top:    Vertically integrated WSTAR (scaled by 1000 --> mm/s)
      Bottom: Vertically integrated PSI (residual streamfunction)
    is_climo selects the climatology (full dataset) variant, which shows each 
    dataset's own date range in the legend. The comparison (non-climo) variant 
    shows one shared range (the common window) in the title. 
    Dates are read from the 'dates' map by name.
    '''
    prefix = 'WSTAR_B' if is_climo else 'WSTAR'
    out_filename = f'{prefix}_Turn_Around_Lats.{season}.png'
    
    # Retrieve valid (non-MERRA/ERA) datasets for plotting
    valid_dicts = {k: v for k, v in talats_dict.items() if v is not None}
    if not valid_dicts:
        return

    # Figure and panel layout
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax_w, ax_p = axes[0], axes[1]
    plt.subplots_adjust(
        left=0.08, right=0.95, top=0.92, bottom=0.18, hspace=0.22)

    # Average turn-around latitudes across datasets (for the annotation lines)
    avg_w_sh = np.nanmean([d['wstar_lat_sh'] for d in valid_dicts.values()])
    avg_w_nh = np.nanmean([d['wstar_lat_nh'] for d in valid_dicts.values()])
    avg_p_sh = np.nanmean([d['res_lat_sh'] for d in valid_dicts.values()])
    avg_p_nh = np.nanmean([d['res_lat_nh'] for d in valid_dicts.values()])

    # Subplot titles (no "main" title)
    if not is_climo:  # One shared (common-window) date range in title
        d = dates[base_expid]
        shared_date = f" ({d['n_seas']}): {d['b_date']} \u2013 {d['e_date']}"
    else:  # Individual dataset full date ranges reserved for legend
        shared_date = ''
    subtitle = f'{season}{shared_date}, Levels: 100\u201320 hPa'
    ax_w.set_title(f'Vertically Integrated Residual Vertical Velocity '
                   f'(WSTAR)\n{subtitle}')
    ax_p.set_title(f'Vertically Integrated Residual Mean Meridional '
                   f'Streamfunction (PSI)\n{subtitle}')

    # Axis formatting and grid
    for ax in (ax_w, ax_p):
        format_x_axis(ax)
        ax.axhline(0, color='grey', linewidth=0.75, zorder=1)
        ax.grid(True, linestyle=':', color='silver', alpha=0.7)
    ax_w.tick_params(labelbottom=True)
    ax_w.set_ylabel('(mm/sec)')
    ax_p.set_ylabel(r'($10^9$ kg/s)')

    # Plot each dataset's profiles, creating a monospaced legend string
    max_name_len = max(len(n) for n in valid_dicts.keys()) + 1
    for name, data in valid_dicts.items():
        
        # Establish color, line width, and plot order for dataset
        color, prefix_id = color_map[name]
        lw, zorder = (2.0, 5) if name == base_expid else (1.5, 2)
        
        # Legend includes exp id/name, talats, and (if is_climo) date string 
        sh_val, nh_val = data['wstar_lat_sh'], data['wstar_lat_nh']
        talats_str = f' ({sh_val:>6.2f}, {nh_val:>5.2f})'
        if is_climo:  # Each dataset's own date range for climatology plots
            d = dates[name]
            leg_date = f" {d['b_date']} \u2013 {d['e_date']}: {d['n_seas']}"
        else:
            leg_date = ''
        leg_name = f'{prefix_id}: {name:<{max_name_len}}{talats_str}{leg_date}'
        
        # Plot data
        ax_w.plot(data['lats'], data['wstar_1d'] * 1000, color=color, lw=lw, 
                  zorder=zorder, label=leg_name)
        ax_p.plot(data['lats'], data['res_1d'],          color=color, lw=lw, 
                  zorder=zorder)

    # Overlay the multi-dataset mean profile in black
    avg_wstar_1d = np.mean([d['wstar_1d'] 
                            for d in valid_dicts.values()], axis=0)
    avg_res_1d   = np.mean([d['res_1d']   
                            for d in valid_dicts.values()], axis=0)
    avg_lats = next(iter(valid_dicts.values()))['lats']
    ax_w.plot(avg_lats, avg_wstar_1d * 1000, color='black', lw=2.0, zorder=4)
    ax_p.plot(avg_lats, avg_res_1d, color='black', lw=2.0, zorder=4)

    # Annotate average turn-around latitudes with boxed labels
    box_style = dict(facecolor='white', alpha=1.0, edgecolor='black', 
                     boxstyle='round,pad=0.2')
    def annotate_turnarounds(ax, lat_sh, lat_nh):
        if np.isnan(lat_sh) or np.isnan(lat_nh):
            return
        for lat in (lat_sh, lat_nh):
            ax.axvline(lat, color='black', linestyle='--', linewidth=1.5, 
                       alpha=0.9, zorder=9)
            y0, y1 = ax.get_ylim()
            y_pos = y0 + (y1 - y0) * 0.95
            ax.text(lat, y_pos, f'{lat:.2f} deg', color='black', ha='center', 
                    va='center', zorder=10, bbox=box_style)
    annotate_turnarounds(ax_w, avg_w_sh, avg_w_nh)
    annotate_turnarounds(ax_p, avg_p_sh, avg_p_nh)

    # Draw legend and save
    handles, labels = ax_w.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.15), 
               ncol=1, frameon=True, 
               prop={'family': 'monospace', 'size': FONT_ANNOTATION})
    save_as_gif(fig, plotsdir, out_filename)
    
def plot_wstar_profiles(data_dict, base_expid, plot_cmps, color_map, season, 
                        method, plotsdir, dates, is_summary, is_climo=False):
    '''
    Vertical WSTAR pressure profiles (main panel) alongside a column of 
    per-dataset inset contours. WSTAR is scaled by 1000 --> mm/s
    'method' selects how each level's latitude band is bounded:
      'avrg' - shared averaged turn-around lats
      'indv' - each dataset's own turn-around lats
      'levl' - level-dependent turn-around lats
    is_summary selects the multi-dataset summary variant versus the 1-on-1 
    pairwise variant (comparison-specifc date range string shown in the title). 
    is_climo selects between using each dataset's full date range for the 
    summary plots (date strings in the legend) versus using a common shared
    date range (date string in the title).
    Dates are read from the 'dates' map by name.
    '''

    # Retrieve valid (non-MERRA/ERA) datasets for plotting
    valid_keys = [k for k in [base_expid] + plot_cmps 
                  if data_dict.get(k) is not None]
    if not valid_keys:
        return
    # Require valid comparison dataset for 1-on-1 plots
    if not is_summary and plot_cmps[0] not in valid_keys:
        return

    # Filename varies with the plot variant (summary vs 1-on-1) and if is_climo
    prefix = 'WSTAR_B' if is_climo else 'WSTAR'
    method_map = {
        'avrg': 'Averaged', 'indv': 'Individual', 'levl': 'Level-Dependent'}
    m_str = method_map.get(method, method)
    if is_summary:
        out_filename = f'{prefix}_using_{m_str}_TALATS.{season}.png'
    else:
        out_filename = (f'WSTAR_using_{m_str}_TALATS.{plot_cmps[0]}'
                        f'.{base_expid}.{season}.png')

    # Figure and panel layout 
    fig = plt.figure(figsize=(10, 11))
    plt.subplots_adjust(left=0.08, right=0.95, top=0.93, bottom=0.08, 
                        wspace=0.3, hspace=0.35)
    gs = fig.add_gridspec(5, 3)  # Make space for up to 5 inset plots
    ax_main = fig.add_subplot(gs[:, :-1])

    # Main title
    if not is_climo:  # One shared date range in title
        d = dates[base_expid] if is_summary else dates[plot_cmps[0]]
        shared_date = f" ({d['n_seas']}): {d['b_date']} \u2013 {d['e_date']}"
    else:  # Individual dataset full date ranges reserved for legend
        shared_date = ''
    ax_main.set_title(f'Residual Vertical Velocity (WSTAR) using {m_str} '
                      f'Turn-Around Lats\n{season}{shared_date}')

    # Shared (main plot and insets) y ticks and averaged turn-around lats
    y_ticks = [100, 90, 80, 70, 60, 50, 40, 30, 20]
    avg_sh = np.nanmean([data_dict[k]['wstar_lat_sh'] for k in valid_keys])
    avg_nh = np.nanmean([data_dict[k]['wstar_lat_nh'] for k in valid_keys])

    # Plot each dataset's profile and inset, creating a monospace legend string
    max_name_len = max(len(n) for n in valid_keys) + 1
    for i, name in enumerate(valid_keys):
        data = data_dict[name]
        color, prefix_id = color_map[name]
        lw = 2.0 if name == base_expid else 1.5

        # Legend labels
        if method in ('avrg', 'indv'):  # TALATS shown for averaged/individual
            sh_bound, nh_bound = data['wstar_lat_sh'], data['wstar_lat_nh']
            talats_str = f' ({sh_bound:>6.2f}, {nh_bound:>5.2f})'
        else:  #  TALATS not included level-dependent method
            talats_str = ''
        if is_climo:  # Each dataset's own date range for climatology plots
            d = dates[name]
            leg_date = f" {d['b_date']} \u2013 {d['e_date']}: {d['n_seas']}"
        else:
            leg_date = ''
        leg_name = f'{prefix_id}: {name:<{max_name_len}}{talats_str}{leg_date}'

        # Vertical profile (main): averaged WSTAR within the method's lat band
        lats = data['lats']
        w_profile = np.zeros(len(data['levs']))
        for lev_idx in range(len(data['levs'])):
            w_row = data['wstar_2d'][lev_idx, :]
            if method == 'avrg':
                sh_bound, nh_bound = avg_sh, avg_nh
            elif method == 'indv':
                sh_bound, nh_bound = data['wstar_lat_sh'], data['wstar_lat_nh']
            else:  # 'levl'
                sh_bound = data['wstar_sh_lev'][lev_idx]
                nh_bound = data['wstar_nh_lev'][lev_idx]
            if np.isnan(sh_bound): sh_bound = -90
            if np.isnan(nh_bound): nh_bound = 90
            mask = (lats >= sh_bound) & (lats <= nh_bound)
            w_profile[lev_idx] = np.nanmean(w_row[mask]) * 1000
        ax_main.plot(
            w_profile, data['levs'], color=color, lw=lw, label=leg_name)

        # Inset contour of the full 2D WSTAR field, with TALATS overlaid
        ax_in = fig.add_subplot(gs[i, 2])
        cf = ax_in.contourf(
            data['lats'], data['levs'], data['wstar_2d'] * 1000,
            levels=np.linspace(-2, 2, 11), cmap='bwr', extend='both')
        t_title = f'{prefix_id}: {name}'
        if method in ('avrg', 'indv'):  # TALATS included in subtitle
            sh_draw, nh_draw = (
                (avg_sh, avg_nh) if method == 'avrg' 
                else (data['wstar_lat_sh'], data['wstar_lat_nh']))
            if not np.isnan(sh_draw):
                ax_in.axvline(sh_draw, color='black', linewidth=1.5)
                ax_in.axvline(nh_draw, color='black', linewidth=1.5)
                t_title += f'\nTALATS: {sh_draw:.1f}, {nh_draw:.1f}'
        elif method == 'levl':  # TALATS excluded from subtitle
            ax_in.plot(data['wstar_sh_lev'], data['levs'], color='black',
                       linewidth=1.5, marker='.', markersize=4)
            ax_in.plot(data['wstar_nh_lev'], data['levs'], color='black',
                       linewidth=1.5, marker='.', markersize=4)


        # Inset title, grid, and axes formatting
        ax_in.set_title(t_title, fontsize=FONT_ANNOTATION, color=color, 
                        fontweight='normal', pad=3)
        ax_in.set_yscale('log')
        ax_in.set_yticks(y_ticks)
        ax_in.set_yticklabels([str(t) if t in (100, 50, 20) 
                               else '' for t in y_ticks], fontsize=FONT_INSET)
        ax_in.set_ylim(100, 20)
        ax_in.set_ylabel('')
        ax_in.grid(True, linestyle=':', color='silver', alpha=0.7, 
                   which='both')
        format_x_axis(ax_in, fontsize=FONT_INSET)

        # Create a colorbar dynamically positioned below the final inset
        if i == len(valid_keys) - 1:
            pos = ax_in.get_position()
            cax = fig.add_axes([pos.x0, pos.y0 - 0.04, pos.width, 0.01])
            cbar = fig.colorbar(cf, cax=cax, orientation='horizontal')
            cbar.ax.tick_params(labelsize=FONT_INSET)
            cbar.set_label('WSTAR (mm/sec)', fontsize=FONT_INSET)

    # Main plot grid and axis styling
    ax_main.set_xlabel('(mm/sec)')
    ax_main.set_ylabel('Pressure (hPa)')
    ax_main.set_yscale('log')
    ax_main.set_yticks(y_ticks)
    ax_main.set_yticklabels([str(t) for t in y_ticks])
    ax_main.set_ylim(100, 20)
    ax_main.grid(True, linestyle=':', color='silver', alpha=0.7, which='both')
    x_min, x_max = ax_main.get_xlim()
    ax_main.set_xlim(x_min - abs(x_min) * 0.05, x_max + abs(x_max) * 0.05)
    
    # Draw legend and save
    ax_main.legend(loc='lower left', 
                   prop={'family': 'monospace', 'size': FONT_ANNOTATION})
    save_as_gif(fig, plotsdir, out_filename)

# ==========================================================
# MAIN EXECUTION
# ==========================================================
def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Residual (TEM Diagnostics) plotting pipeline')
    parser.add_argument('-source', required=True,
                        help='Root directory for the base experiment')
    parser.add_argument('-expid', required=True,
                        help='Base experiment identifier')
    parser.add_argument('-plotsdir', required=True,
                        help='Output directory for generated plots')
    parser.add_argument('-begdate', required=True,
                        help='Start date YYYYMM, or NULL')
    parser.add_argument('-enddate', required=True,
                        help='End date YYYYMM, or NULL')
    parser.add_argument('-season', nargs='+', required=True,
                        choices=list(SEASON_MONTHS.keys()),
                        help='One or more space-separated seasons')
    parser.add_argument('-cmpexp', nargs='*', default=[],
                        help=('Comparison dataset root directories, '
                              'space-separated (optionally colon-suffixed)'))

    args = parser.parse_args()
    
    # Print opening summary
    print('\n[res] ' + '=' * 70)
    print('[res]  RESIDUAL CIRCULATION PLOTTING PIPELINE (TEM Diagnostics)')
    print('[res] ' + '=' * 70)
    print(f'[res]  Base experiment: {args.expid}')
    if args.begdate != 'NULL':
        print(f'[res]  Requested date range: {args.begdate} to {args.enddate}')
    else:
        print('[res]  Requested date range: all available months')

    # 1. Find the base experiment's data and select the months to use
    print('\n[res] STEP 1: Locating the base experiment data...')
    base_dict = get_available_months(args.source, args.expid)
    if not base_dict:
        print(f'[res]   No data found for {args.expid}. Nothing to plot.')
        sys.exit(0)
    if args.begdate == 'NULL' or args.enddate == 'NULL':
        base_months = sorted(base_dict.keys())
        print('[res]   No dates requested; using all base experiment months.')
    else:
        req_months = generate_month_list(args.begdate, args.enddate)
        base_months = sorted(req_months & set(base_dict.keys()))
        print('[res]   Keeping intersection of available & requested months.')
    print(f'[res]   Base experiment will use {len(base_months)} months '
          f'({base_months[0]} to {base_months[-1]}).')

    # 2. Check each comparison dataset and determine overlap with base
    print('\n[res] STEP 2: Checking the comparison datasets...')
    
    # Strip colon-suffixes and drop any NULL placeholders.
    req_paths = [p.split(':')[0] for p in args.cmpexp if 'NULL' not in p]
    valid_cmps = {}
    if not req_paths:
        print('[res]   No comparison datasets requested.')
    else:
        print(f'[res]   {len(req_paths)} comparison dataset(s) requested.')
        for c_idx, clean_path in enumerate(req_paths, start=1):

            # Derive a display id, renaming reanalysis products and avoiding
            # a clash with the base experiment's own name.
            cmpid = os.path.basename(clean_path)
            if cmpid == 'MERRA2_MEANS': cmpid = 'MERRA-2'
            if cmpid == 'ERA5_Monthly': cmpid = 'ERA5'
            if cmpid == args.expid: cmpid = f'{cmpid}_cmp'
            print(f'[res]   ({c_idx} of {len(req_paths)}) {cmpid}: '
                  f'looking for its data...')
            print(f'[res]       Searching: {clean_path}')
            cmp_dict = get_available_months(clean_path, cmpid)
            if not cmp_dict:
                print(f'[res]       No TEM_Diag data found for {cmpid}; '
                      f'it will be skipped.')
                continue

            # Define comparison dataset's full record (for climatology plots)
            cmp_climo = sorted(cmp_dict.keys())
            # Define overlap with base exp (used for direct comparisons).
            cmp_actual = sorted(set(base_months) & set(cmp_climo))

            # Report summary of data ranges
            valid_cmps[cmpid] = {'dict': cmp_dict, 'actual': cmp_actual, 
                                 'climo': cmp_climo}
            print(f'[res]       Found data. Its own record covers '
                  f'{len(cmp_climo)} months ({cmp_climo[0]} to '
                  f'{cmp_climo[-1]}).')
            if cmp_actual:
                print(f'[res]       It shares {len(cmp_actual)} months with '
                      f'the base ({cmp_actual[0]} to {cmp_actual[-1]}) for '
                      f'direct comparison.')
            else:
                print('[res]       It shares no months with the base, so no '
                      'direct-comparison plots can be made for it.')

    # 3. Determine the optimal common time period for the base and cmp exps
    # Starting from the base window, each non-reanalysis comparison is checked 
    # in turn: if it overlaps the running shared period it stays (shrinking 
    # that period as needed); if it does not overlap, it is left out.
    print('\n[res] STEP 3: Finding the shared time period for the combined '
          'comparison plots...')
    common_months = set(base_months)
    common_cmps = []
    print(f'[res]   Starting from the base experiment: {len(common_months)} '
          f'months ({base_months[0]} to {base_months[-1]}).')
    for cmpid, info in valid_cmps.items():
        if is_reanalysis(cmpid):
            print(f'[res]   {cmpid}: left out (reanalysis products are not '
                  f'included in these plots).')
            continue
        overlap = common_months & set(info['actual'])
        if overlap:
            common_months = overlap
            common_cmps.append(cmpid)
            ms = sorted(common_months)
            print(f'[res]   {cmpid}: overlaps -> shared period is now '
                  f'{len(common_months)} months ({ms[0]} to {ms[-1]}).')
        else:
            print(f'[res]   {cmpid}: does not overlap the current shared '
                  f'period -> left out.')
    common_months = sorted(common_months)
    make_summary = len(common_cmps) > 0
    if make_summary:
        included = ', '.join([args.expid] + common_cmps)
        print(f'[res]   Shared time period: {len(common_months)} months '
              f'({common_months[0]} to {common_months[-1]}).')
        print(f'[res]   Datasets sharing this period: {included}.')
    else:
        print('[res]   No comparison dataset shares a time period with the '
              'base, so the combined comparison plots will be skipped.')
        
    # Initialize dictionaries for date label components and turn-around lats
    # dates_actual: base-vs-comparison shared months, per direct comparison
    # dates_common: the single shared time period (combined comparison plots)
    # dates_climo : each dataset's full record, per dataset (climatology plots)
    dates_actual, dates_common, dates_climo = {}, {}, {}
    talats_actual,  talats_common, talats_climo = {}, {}, {}

    # Assign each exp a plotting color and role label (Base, Cmp1, Cmp2, etc.)
    all_cmps = list(valid_cmps.keys())
    color_map = {args.expid: ('blue', 'Base')}
    for idx, cmp_name in enumerate(all_cmps):
        color_map[cmp_name] = (CMP_COLORS[idx % len(CMP_COLORS)], 
                               f'Cmp{idx + 1}')
    seasons = args.season

    # 4. Process the base experiment data and make base plots
    print('\n[res] STEP 4: Processing the base experiment...')
    print('[res]   Reading and seasonally averaging the base experiment data')
    b_monthly_climo = extract_12_month_clims(
        [base_dict[m] for m in base_months])
    b_monthly_common = (extract_12_month_clims(
        [base_dict[m] for m in common_months]) if make_summary else None)
    
    # Make base exp plots by season
    print(f'[res]   Making the base experiment plots for: '
          f'{", ".join(seasons)}')
    for s_idx, season in enumerate(seasons, start=1):
        t_months = SEASON_MONTHS[season]
        print(f'[res]   Season {season} ({s_idx} of {len(seasons)}):')

        # Calculate base exp seasonal average and TALATS over its full record
        base_climo_ds = compute_weighted_season(b_monthly_climo, t_months)
        if base_climo_ds is not None:
            talats_climo[args.expid] = calc_talats(base_climo_ds, args.expid)
            dates_climo[args.expid]  = get_dates(base_months, t_months)
            
            # Make base exp EP flux plots
            print('[res]     Making Eliassen-Palm (EP) flux plot for the base '
                  'experiment:')
            base_ep = prepare_single_ep_dataset(base_climo_ds)
            plot_ep_flux_diagnostics(
                base_ep, f'{args.expid}', args.plotsdir, 
                f'EP_Flux_{args.expid}.{season}.png',
                is_diff=False, season=season,
                b_date=dates_climo[args.expid]['b_date'], 
                e_date=dates_climo[args.expid]['e_date'], 
                n_seas=dates_climo[args.expid]['n_seas'])
            
            # Clean-up
            del base_ep  
            gc.collect()

        # Calculate base seasonal average and TALATS over the common period
        if make_summary:
            base_common_ds = compute_weighted_season(b_monthly_common, 
                                                     t_months)
            if base_common_ds is not None:
                talats_common[args.expid] = calc_talats(base_common_ds, 
                                                        args.expid)
                dates_common[args.expid] = get_dates(common_months, t_months)
                
            # Clean-up
            del base_common_ds
            gc.collect()

    # 5. Process each comparison dataset and make its solo and comparison plots 
    print('\n[res] STEP 5: Processing each comparison dataset...')
    # Loop through comparison datasets
    for c_idx, (cmpid, info) in enumerate(valid_cmps.items(), start=1):
        print(f'[res]   Comparison dataset {cmpid} ({c_idx} of '
              f'{len(valid_cmps)}):')

        # Extract each needed set of months (including base_actual)
        print('[res]     Reading and seasonally averaging its data...')
        cmp_monthly_climo   = (extract_12_month_clims(
            [info['dict'][m] for m in info['climo']]) 
            if info['climo'] else None)
        cmp_monthly_actual  = (extract_12_month_clims(
            [info['dict'][m] for m in info['actual']]) 
            if info['actual'] else None)
        base_monthly_actual = (extract_12_month_clims(
            [base_dict[m] for m in info['actual']]) 
            if info['actual'] else None)
        cmp_monthly_common  = (extract_12_month_clims(
            [info['dict'][m] for m in common_months]) 
            if (make_summary and cmpid in common_cmps) else None)

        # Check and note that WSTAR and TALATS plots are skipped for reanalysis
        cmp_makes_talats = not is_reanalysis(cmpid)
        if not cmp_makes_talats:
            print(f'[res]     {cmpid}: no WSTAR and TALATS plots made for '
                  f'reanalysis products')
        
        # Loop over seasons
        for s_idx, season in enumerate(seasons, start=1):
            t_months = SEASON_MONTHS[season]
            print(f'[res]     Season {season} ({s_idx} of {len(seasons)}):')

            # Calculate seasonal average and TALATS over its full record
            if cmp_monthly_climo:
                cmp_climo_ds = compute_weighted_season(cmp_monthly_climo, 
                                                       t_months)
                if cmp_climo_ds is not None:
                    talats_climo[cmpid] = calc_talats(cmp_climo_ds, cmpid)
                    dates_climo[cmpid] = get_dates(info['climo'], t_months)
                    
                    # Make cmp exp climatology EP flux plots
                    print('[res]       Creating Eliassen-Palm (EP) flux plot '
                          'over its full record:')
                    cmp_ep = prepare_single_ep_dataset(cmp_climo_ds)
                    plot_ep_flux_diagnostics(
                        cmp_ep, f'{cmpid}', args.plotsdir, 
                        f'EP_Flux_{cmpid}.{season}.png', is_diff=False, 
                        season=season, b_date=dates_climo[cmpid]['b_date'], 
                        e_date=dates_climo[cmpid]['e_date'], 
                        n_seas=dates_climo[cmpid]['n_seas'])
                    
                    # Clean-up
                    del cmp_ep
                    gc.collect()

            # Calculate seasonal average and TALATS over the common period 
            if cmp_monthly_common:
                cmp_ds_common = compute_weighted_season(cmp_monthly_common, 
                                                        t_months)
                if cmp_ds_common is not None:
                    talats_common[cmpid] = calc_talats(cmp_ds_common, cmpid)
                    
                # Clean-up
                del cmp_ds_common
                gc.collect()

            # Calculate base/cmp seasonal average and TALATS for actual shared
            if cmp_monthly_actual and base_monthly_actual:
                cmp_actual_ds  = compute_weighted_season(cmp_monthly_actual, 
                                                         t_months)
                base_ds_actual = compute_weighted_season(base_monthly_actual, 
                                                         t_months)
                
                # Make all base/cmp comparison plots for this cmp dataset
                if cmp_actual_ds is not None and base_ds_actual is not None:
                    talats_actual[cmpid] = calc_talats(cmp_actual_ds, cmpid)
                    talats_actual[args.expid] = calc_talats(base_ds_actual, 
                                                            args.expid)
                    dates_actual[cmpid] = get_dates(info['actual'], t_months)
                    
                    # Make streamfunction and residual comparison plots
                    print('[res]       Creating streamfunction and residual '
                          'circulation plots:')
                    plot_str_and_res(base_ds_actual, cmp_actual_ds, 
                                     args.plotsdir, season, args.expid, cmpid, 
                                     dates_actual[cmpid])
                    plot_str_or_res('str', base_ds_actual, cmp_actual_ds, 
                                    args.plotsdir, season, args.expid, cmpid, 
                                    dates_actual[cmpid])
                    plot_str_or_res('res', base_ds_actual, cmp_actual_ds, 
                                    args.plotsdir, season, args.expid, cmpid, 
                                    dates_actual[cmpid])
                    
                    # Make EP flux difference plots
                    print('[res]       Creating Eliassen-Palm (EP) flux '
                          'difference plots:')
                    aligned_base, aligned_cmp = align_datasets(
                        base_ds_actual, cmp_actual_ds)
                    prep_base = prepare_single_ep_dataset(aligned_base)
                    prep_cmp  = prepare_single_ep_dataset(aligned_cmp)
                    ds_diff_ep = prep_base - prep_cmp
                    plot_ep_flux_diagnostics(  # Base minus cmp
                        ds_diff_ep, f'{args.expid} minus {cmpid}', 
                        args.plotsdir,
                        f'EP_Flux_diff_{args.expid}-{cmpid}.{season}.png', 
                        is_diff=True, season=season,
                        b_date=dates_actual[cmpid]['b_date'], 
                        e_date=dates_actual[cmpid]['e_date'],
                        n_seas=dates_actual[cmpid]['n_seas'])
                    plot_ep_flux_diagnostics(  # Cmp minus base
                        -ds_diff_ep, f'{cmpid} minus {args.expid}', 
                        args.plotsdir,
                        f'EP_Flux_diff_{cmpid}-{args.expid}.{season}.png', 
                        is_diff=True, season=season,
                        b_date=dates_actual[cmpid]['b_date'], 
                        e_date=dates_actual[cmpid]['e_date'],
                        n_seas=dates_actual[cmpid]['n_seas'])
                    
                    # Make WSTAR and TALATS 1-on-1 comparison plots
                    if cmp_makes_talats:
                        print('[res]       Creating WSTAR and TALATS plots:')
                        for method in ('levl', 'avrg', 'indv'):
                            plot_wstar_profiles(
                                talats_actual, args.expid, [cmpid], color_map,
                                season, method, args.plotsdir, dates_actual,
                                is_summary=False, is_climo=False)
                    
                    # Clean-up
                    del cmp_actual_ds, base_ds_actual, prep_base, prep_cmp 
                    del aligned_base, aligned_cmp, ds_diff_ep
                    gc.collect()

    # 6. Combined comparison and climatology plots (all datasets on one figure)
    print('\n[res] STEP 6: Making the combined summary plots...')
    
    # Loop over seasons
    for s_idx, season in enumerate(seasons, start=1):
        print(f'[res]   Season {season} ({s_idx} of {len(seasons)}):')

        # WSTAR and TALATS summary plots over the common period
        if make_summary:
            print('[res]     Creating combined comparison plots over the '
                  'shared time period:')
            plot_latitudinal_talats_summary(
                talats_common, args.expid, color_map, season, args.plotsdir, 
                dates_common, is_climo=False)
            for method in ('levl', 'avrg', 'indv'):
                plot_wstar_profiles(
                    talats_common, args.expid, common_cmps, color_map, 
                    season, method, args.plotsdir, dates_common, 
                    is_summary=True, is_climo=False)
        else:
            print('[res]     Skipping the combined comparison plots '
                  '(no comparison dataset overlaps in time with the base).')

        # Make combined climatology plots: full record for each dataset
        print('[res]     Creating combined climatology plots utilizing the '
              'full record for each dataset:')
        plot_latitudinal_talats_summary(
            talats_climo, args.expid, color_map, season, args.plotsdir, 
            dates_climo, is_climo=True)
        for method in ('levl', 'avrg', 'indv'):
            plot_wstar_profiles(
                talats_climo, args.expid, all_cmps, color_map, season, method, 
                args.plotsdir, dates_climo, is_summary=True, is_climo=True)
    
    # Print summary message
    print('\n[res] ' + '=' * 70)
    print('[res]  DONE. All residual circulation plots have been generated.')
    print('[res] ' + '=' * 70 + '\n')


if __name__ == '__main__':
    main()
