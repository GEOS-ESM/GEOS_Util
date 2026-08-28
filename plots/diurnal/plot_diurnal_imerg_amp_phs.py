#!/usr/bin/env python3
'''
Diurnal Precipitation Analysis Pipeline

This script compares diurnal precipitation cycles (Amplitude and Phase) between a
baseline model experiment, IMERG observational data, and optional comparison experiments.
It computes harmonics using FFT, regrids datasets to a common baseline grid, and generates
multi-panel map visualizations for specified seasons and regions.
'''

import argparse
import os
import glob
import sys
import numpy as np
import xarray as xr
import xesmf as xe
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
import cartopy.crs as ccrs
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import warnings

# Suppress expected xESMF and xarray warnings regarding lat boundaries and contiguous arrays
warnings.filterwarnings('ignore', message='Latitude is outside of')
warnings.filterwarnings('ignore', message='Input array is not C_CONTIGUOUS')
warnings.filterwarnings('ignore', message='All-NaN slice encountered')

# ==========================================================
# CONFIGURATION
# ==========================================================
# Threshold (mm/hr) below which the diurnal phase is considered statistical noise and masked out
AMP_THRESH = 0.025

# Standardized font sizes for consistent layouts across all generated plots
TITLE_SZ = 16
SUBTITLE_SZ = 12
LABEL_SZ = 11
TICK_SZ = 9

# Geographic bounds for regional zoom-in plots [lon_min, lon_max, lat_min, lat_max]
REGIONS = {
    'CONUS': [-120, -65, 25, 50],
    'Amazon': [-85, -40, -15, 10],
    'Central Africa': [-20, 40, -10, 20],
    'Maritime Continent': [95, 155, -12, 12]
}

# Calculated physical height/width aspect ratios to force uniform column widths in Cartopy
REGION_RATIOS = [0.454, 0.555, 0.500, 0.400]

# Days per month (February is 28.25 to smoothly account for leap years in climatologies)
DAYS_IN_MONTH = {1: 31, 2: 28.25, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

VALID_SEASONS = ['ANN', 'DJF', 'MAM', 'JJA', 'SON', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def get_season_months(season_str):
    '''Maps a season abbreviation to its corresponding list of calendar months.'''
    s_map = {
        'ANN': list(range(1, 13)), 'DJF': [12, 1, 2], 'MAM': [3, 4, 5],
        'JJA': [6, 7, 8], 'SON': [9, 10, 11], 'JAN': [1], 'FEB': [2],
        'MAR': [3], 'APR': [4], 'MAY': [5], 'JUN': [6], 'JUL': [7],
        'AUG': [8], 'SEP': [9], 'OCT': [10], 'NOV': [11], 'DEC': [12]
    }
    return s_map[season_str.upper()]

def get_available_months(directory, file_pattern):
    '''Scans a directory for NetCDF files and extracts the 6-digit YYYYMM date strings.'''
    files = glob.glob(os.path.join(directory, file_pattern))
    valid_files = {}
    for f in files:
        parts = os.path.basename(f).split('.')
        if len(parts) >= 2:
            date_str = parts[-2]
            if date_str.isdigit() and len(date_str) == 6:
                valid_files[date_str] = f
    return valid_files

def generate_month_list(start_ym, end_ym):
    '''Generates a continuous sequence of YYYYMM strings between start and end dates.'''
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

def extract_12_month_clims(files_list, var_name, is_imerg=False):
    '''Reduces the full raw dataset into 12 distinct calendar month climatologies.'''
    if not files_list:
        return {m: None for m in range(1, 13)}

    # Open all files in a single pass to eliminate redundant file inspection overhead
    ds = xr.open_mfdataset(files_list, engine='netcdf4', data_vars='minimal', coords='minimal', compat='override')

    if is_imerg:
        ds = ds.drop_vars(['lon_bnds', 'lat_bnds'], errors='ignore')
        if 'bounds' in ds.lon.attrs: del ds.lon.attrs['bounds']
        if 'bounds' in ds.lat.attrs: del ds.lat.attrs['bounds']
        ds.coords['lon'] = (ds.coords['lon'] + 180) % 360 - 180
        ds = ds.sortby(ds.lon)

    clims = {}
    for m in range(1, 13):
        # Isolate the data belonging to this specific calendar month
        ds_month = ds.sel(time=(ds['time'].dt.month == m))
        
        if ds_month.time.size > 0:
            clims[m] = ds_month[var_name].groupby('time.hour').mean('time').compute()
        else:
            clims[m] = None

    ds.close()
    return clims

def compute_weighted_season(monthly_clims, target_months):
    '''Combines pre-computed monthly diurnal cycles, weighted proportionally by days-in-month.'''
    weighted_sum = None
    total_weight = 0.0
    for m in target_months:
        if monthly_clims.get(m) is not None:
            w = DAYS_IN_MONTH[m]
            if weighted_sum is None:
                weighted_sum = monthly_clims[m] * w
            else:
                weighted_sum += monthly_clims[m] * w
            total_weight += w

    if total_weight > 0:
        return weighted_sum / total_weight
    return None

def apply_mask(data, mask_array, threshold):
    '''Safely applies a NaN mask to data where the mask array falls below a threshold.'''
    return np.where(mask_array < threshold, np.nan, data)

def get_plot_metadata(metric, season, date_str, label1, label2, suffix, is_closeness, plotsdir):
    '''Abstracts text creation to ensure uniform plot titles and file naming conventions.'''
    m_title = 'Diurnal Precipitation Amplitude' if metric == 'amplitude' else 'Diurnal Precipitation Phase (Local Time)'

    if is_closeness:
        m_title = m_title.replace('Phase (Local Time)', 'Phase') + ' Closeness (Errors relative to IMERG)'

    title = f'{m_title} | {season} | {date_str}\n{label1} vs. {label2}'

    fname_base = f'precip_diurnal_{metric}_{suffix}'
    if is_closeness:
        fname_base += '_closeness_IMERG'
    filepath = os.path.join(plotsdir, f'{fname_base}.{season}.png')

    return title, filepath

def calculate_diurnal_harmonics(data):
    '''Applies FFT to extract the 1st (24-hour) and 2nd (12-hour) harmonics.'''
    mean_val = np.nanmean(data, axis=0)
    anomaly = data - mean_val[np.newaxis, :, :]
    fft_result = np.fft.fft(anomaly, axis=0)

    h1_fft, h2_fft = np.zeros_like(fft_result), np.zeros_like(fft_result)

    h1_fft[1,:,:], h1_fft[-1,:,:] = fft_result[1,:,:], fft_result[-1,:,:]
    h2_fft[2,:,:], h2_fft[-2,:,:] = fft_result[2,:,:], fft_result[-2,:,:]

    return {
        'harmonic_1': np.fft.ifft(h1_fft, axis=0).real,
        'harmonic_2': np.fft.ifft(h2_fft, axis=0).real
    }

def print_nan_summary(data, lats, name, season):
    '''Prints a clean summary of missing data (all-NaN slices) to replace numpy warnings.'''
    all_nan_mask = np.all(np.isnan(data), axis=0)
    nan_count = np.sum(all_nan_mask)

    if nan_count > 0:
        nan_lats = lats[np.any(all_nan_mask, axis=1)]
        north_lats = nan_lats[nan_lats >= 0]
        south_lats = nan_lats[nan_lats < 0]

        bands = []
        if len(north_lats) > 0: bands.append(f'{north_lats.min():.1f}°N to {north_lats.max():.1f}°N')
        if len(south_lats) > 0: bands.append(f'{abs(south_lats.max()):.1f}°S to {abs(south_lats.min()):.1f}°S')

        msg = f'[diurnal]   [INFO] {name} ({season}): Found {nan_count:,} all-NaN grid points.'
        if bands: msg += f' (Missing data spans {" and ".join(bands)})'
        print(msg)

def safe_phase_calc(h1, h2, lon_2d):
    '''Calculates hour of maximum precipitation (Phase) and shifts it to Local Solar Time.'''
    cmb = h1 + h2
    cmb_safe = np.where(np.isnan(cmb), -np.inf, cmb)
    idx = np.argmax(cmb_safe, axis=0).astype(float)
    idx[np.all(np.isnan(cmb), axis=0)] = np.nan
    return (idx + lon_2d / 15.0) % 24

def wrap_phase(diff):
    '''Mathematically wraps phase differences so errors are strictly between -12 and +12 hours.'''
    return (diff + 12) % 24 - 12

def compute_diurnal_metrics(clim_data, lats, lon_2d, name, season):
    '''Centralized function that runs all common mathematical operations on a dataset.'''
    harm = calculate_diurnal_harmonics(clim_data)
    print_nan_summary(harm['harmonic_1'], lats, name, season)

    amp = np.nanmax(np.abs(harm['harmonic_1'] + harm['harmonic_2']), axis=0)
    mean_val = np.nanmean(clim_data, axis=0)
    ratio = np.divide(amp, mean_val, out=np.full_like(amp, np.nan), where=(mean_val > 0))
    phs = safe_phase_calc(harm['harmonic_1'], harm['harmonic_2'], lon_2d)

    return {'amp': amp, 'ratio': ratio, 'phase': phs}


# ==========================================================
# PLOTTING FUNCTIONS
# ==========================================================
def format_map(ax, title, is_right_col=False, is_regional=False):
    '''Applies standard coastlines, titles, and latitude/longitude gridlines to Cartopy axes.'''
    ax.coastlines(color='black', linewidth=1)
    ax.set_anchor('N')

    pad = 6
    ax.set_title(title, fontsize=SUBTITLE_SZ, fontweight='bold', pad=pad)

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': TICK_SZ}
    gl.ylabel_style = {'size': TICK_SZ}

    if is_regional: gl.ylocator = MultipleLocator(5)
    if is_right_col: gl.left_labels = False

def extract_region(data, lon, lat, extent):
    '''Subsets the global data array to a specific geographic bounding box.'''
    lon_mask = (lon >= extent[0]) & (lon <= extent[1])
    lat_mask = (lat >= extent[2]) & (lat <= extent[3])
    lat_idx, lon_idx = np.where(lat_mask)[0], np.where(lon_mask)[0]

    if len(lat_idx) == 0 or len(lon_idx) == 0:
        return None, None, None

    lat_min, lat_max = lat_idx[0], lat_idx[-1] + 1
    lon_min, lon_max = lon_idx[0], lon_idx[-1] + 1
    return data[lat_min:lat_max, lon_min:lon_max], lon[lon_min:lon_max], lat[lat_min:lat_max]

def get_stats_text(data_unmasked, lats, is_closeness=False, is_phase=False):
    '''Calculates cosine latitude-weighted global statistics (Mean, Bias, RMSE, Std Dev).'''
    weights = np.cos(np.deg2rad(lats))
    weights_2d = np.tile(weights[:, np.newaxis], (1, data_unmasked.shape[1]))

    valid = ~np.isnan(data_unmasked)
    if not np.any(valid): return ''

    w_sum = np.nansum(weights_2d[valid])

    if is_phase and not is_closeness:
        rad = np.deg2rad(data_unmasked[valid] * 15.0)
        s = np.nansum(np.sin(rad) * weights_2d[valid])
        c = np.nansum(np.cos(rad) * weights_2d[valid])
        mean_hr = (np.rad2deg(np.arctan2(s, c)) / 15.0) % 24
        return f'Mean: {mean_hr:.1f}h'

    w_mean = np.nansum(data_unmasked[valid] * weights_2d[valid]) / w_sum

    if not is_closeness:
        return f'Mean: {w_mean:.3f}'

    w_rmse = np.sqrt(np.nansum((data_unmasked[valid]**2) * weights_2d[valid]) / w_sum)
    w_std = np.sqrt(np.nansum(((data_unmasked[valid] - w_mean)**2) * weights_2d[valid]) / w_sum)

    if is_phase:
        return f'Bias: {w_mean:+.1f}h | RMSE: {w_rmse:.1f}h | Std: {w_std:.1f}h'
    return f'Bias: {w_mean:+.3f} | RMSE: {w_rmse:.3f} | Std: {w_std:.3f}'

def add_stat_box(ax, text):
    '''Draws a semi-transparent text box with statistical annotations on the map.'''
    if text:
        ax.text(0.02, 0.05, text, transform=ax.transAxes, fontsize=TICK_SZ, fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.3'), zorder=10)

def draw_amplitude_plot(row1_l, row1_r, row2_l, row2_r, stat1_l, stat1_r, stat2_l, stat2_r, lons, lats, t_left, t_right, suptitle, out_filepath, is_closeness=False):
    '''Generates the 2x2 grid plotting the Absolute Amplitude and the Amplitude/Mean Ratio.'''
    lon_2d, lat_2d = np.meshgrid(lons, lats)

    if is_closeness:
        cmap1 = cmap2 = plt.get_cmap('bwr')
        vmax_r1, vmax_r2 = 0.10, 1.0  
        bounds_r1 = np.linspace(-vmax_r1 * 1.1, vmax_r1 * 1.1, 12)
        bounds_r2 = np.linspace(-vmax_r2 * 1.1, vmax_r2 * 1.1, 12)
        norm_r1 = mcolors.BoundaryNorm(bounds_r1, cmap1.N)
        norm_r2 = mcolors.BoundaryNorm(bounds_r2, cmap2.N)
        ticks_r1 = np.linspace(-vmax_r1, vmax_r1, 11)
        ticks_r2 = np.linspace(-vmax_r2, vmax_r2, 11)
        
        cbar_label1 = 'Error in Sum of 24-hr and 12-hr Cycle Amplitudes (mm/hr)'
        cbar_label2 = f'Amplitude / Mean Precip Error\n(Masked where IMERG native 24h+12h amplitude < {AMP_THRESH} mm/hr)'
    else:
        cmap1, cmap2 = plt.get_cmap('YlOrRd', 10), plt.get_cmap('YlGnBu', 10)
        vmax_r1, vmax_r2 = 0.20, 2.0  
        norm_r1 = mcolors.Normalize(vmin=0, vmax=vmax_r1)
        norm_r2 = mcolors.Normalize(vmin=0, vmax=vmax_r2)
        ticks_r1 = list(np.linspace(0, vmax_r1, 6))
        ticks_r2 = list(np.linspace(0, vmax_r2, 6))
        
        cbar_label1 = 'Sum of 24-hr and 12-hr Cycle Amplitudes (mm/hr)'
        cbar_label2 = f'Amplitude / Mean Precip\n(Masked where native 24h+12h amplitude < {AMP_THRESH} mm/hr)'

    fig, axes = plt.subplots(2, 2, figsize=(15, 11), subplot_kw={'projection': ccrs.PlateCarree()})
    fig.subplots_adjust(wspace=0.05, hspace=0.4, top=0.88, bottom=0.1, left=0.04, right=0.96)

    cb_kwargs = {'orientation': 'horizontal'}
    if is_closeness: cb_kwargs['drawedges'] = True

    # Row 1: Absolute Amplitude
    axes[0, 0].pcolormesh(lon_2d, lat_2d, row1_l, transform=ccrs.PlateCarree(), cmap=cmap1, norm=norm_r1)
    im2 = axes[0, 1].pcolormesh(lon_2d, lat_2d, row1_r, transform=ccrs.PlateCarree(), cmap=cmap1, norm=norm_r1)
    format_map(axes[0, 0], f'{t_left}: Amplitude')
    format_map(axes[0, 1], f'{t_right}: Amplitude', is_right_col=True)
    add_stat_box(axes[0, 0], stat1_l)
    add_stat_box(axes[0, 1], stat1_r)

    # Row 2: Amplitude / Mean Precip
    axes[1, 0].pcolormesh(lon_2d, lat_2d, row2_l, transform=ccrs.PlateCarree(), cmap=cmap2, norm=norm_r2)
    im4 = axes[1, 1].pcolormesh(lon_2d, lat_2d, row2_r, transform=ccrs.PlateCarree(), cmap=cmap2, norm=norm_r2)
    format_map(axes[1, 0], f'{t_left}: Amplitude / Mean Precip')
    format_map(axes[1, 1], f'{t_right}: Amplitude / Mean Precip', is_right_col=True)
    add_stat_box(axes[1, 0], stat2_l)
    add_stat_box(axes[1, 1], stat2_r)

    # Format and draw Colorbars
    for ax, im, ticks, clab in zip([axes[0, 0], axes[1, 0]], [im2, im4], [ticks_r1, ticks_r2], [cbar_label1, cbar_label2]):
        cax = inset_axes(ax, width='160%', height='5%', loc='lower left', bbox_to_anchor=(0.22, -0.18, 1, 1), bbox_transform=ax.transAxes)
        cb = fig.colorbar(im, cax=cax, ticks=ticks, **cb_kwargs)
        cb.set_label(clab, fontsize=LABEL_SZ, fontweight='bold')
        if is_closeness:
            cb.dividers.set_color('white')
            cb.dividers.set_linewidth(1)
            cb.outline.set_edgecolor('black')

    fig.suptitle(suptitle, fontsize=TITLE_SZ, fontweight='bold', y=0.97)
    plt.savefig(out_filepath, dpi=300)
    os.rename(out_filepath, out_filepath.replace('.png', '.gif'))
    plt.close(fig)

def draw_phase_plot(p_left, p_right, stat_l, stat_r, lons, lats, t_left, t_right, suptitle, out_filepath, is_closeness=False):
    '''Generates the multi-panel Phase plot, including global maps and forced-width regional zoom-ins.'''
    lon_2d, lat_2d = np.meshgrid(lons, lats)

    if is_closeness:
        cmap = plt.get_cmap('bwr')
        bounds = np.linspace(-12.5, 12.5, 26)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)
        ticks = np.arange(-12, 13, 3)
    else:
        soft_colors = ['#ff9999', '#ffcc99', '#ffff99', '#99ff99', '#99ccff', '#cc99ff', '#ff9999']
        cmap = mcolors.LinearSegmentedColormap.from_list('soft_cyclic', soft_colors, N=24)
        bounds = np.linspace(-0.5, 23.5, 25)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)
        ticks = np.arange(0, 25, 3)

    cbar_label = 'Phase Error (Local Hours)' if is_closeness else 'Local Time of Peak Precipitation (Hours)'

    fig = plt.figure(figsize=(16, 10))

    # 1. Independent Left Grid (Global Maps & Colorbar)
    gs_left = fig.add_gridspec(2, 1, left=0.02, right=0.50, top=0.88, bottom=0.15, hspace=0.18)
    ax_gm = fig.add_subplot(gs_left[0], projection=ccrs.PlateCarree())
    ax_gi = fig.add_subplot(gs_left[1], projection=ccrs.PlateCarree())

    # 2. Independent Right Grid (Regional Maps)
    gs_right = fig.add_gridspec(4, 2, left=0.52, right=0.98, top=0.88, bottom=0.05, height_ratios=REGION_RATIOS, wspace=0.05, hspace=0.18)

    # Draw and format the global maps
    ax_gm.pcolormesh(lon_2d, lat_2d, p_left, cmap=cmap, norm=norm)
    im_p = ax_gi.pcolormesh(lon_2d, lat_2d, p_right, cmap=cmap, norm=norm)
    format_map(ax_gm, f'{t_left}: Global')
    format_map(ax_gi, f'{t_right}: Global')
    add_stat_box(ax_gm, stat_l)
    add_stat_box(ax_gi, stat_r)

    for r_name, ext in REGIONS.items():
        rect = dict(fill=False, edgecolor='black', linestyle='--', lw=1.5, zorder=5)
        ax_gm.add_patch(Rectangle((ext[0], ext[2]), ext[1]-ext[0], ext[3]-ext[2], **rect))
        ax_gi.add_patch(Rectangle((ext[0], ext[2]), ext[1]-ext[0], ext[3]-ext[2], **rect))

    ax_cb = inset_axes(ax_gi, width='100%', height='5%', loc='lower center', bbox_to_anchor=(0, -0.22, 1, 1), bbox_transform=ax_gi.transAxes)
    cb_phs = fig.colorbar(im_p, cax=ax_cb, orientation='horizontal', drawedges=True, ticks=ticks)
    cb_phs.dividers.set_color('white')
    cb_phs.dividers.set_linewidth(1)
    cb_phs.outline.set_edgecolor('black')

    annot = f'\n(Masked where IMERG 24h+12h amplitude < {AMP_THRESH} mm/hr)' if is_closeness else f'\n(Masked where native 24h+12h amplitude < {AMP_THRESH} mm/hr)'
    cb_phs.set_label(f'{cbar_label}{annot}', fontsize=LABEL_SZ, fontweight='bold')

    # Draw the right column
    for row, (r_name, ext) in enumerate(REGIONS.items()):
        ax_rm = fig.add_subplot(gs_right[row, 0], projection=ccrs.PlateCarree())
        ax_ri = fig.add_subplot(gs_right[row, 1], projection=ccrs.PlateCarree())
        ax_rm.set_extent(ext, crs=ccrs.PlateCarree())
        ax_ri.set_extent(ext, crs=ccrs.PlateCarree())

        reg_l, lon_r, lat_r = extract_region(p_left, lons, lats, ext)
        if reg_l is not None: ax_rm.pcolormesh(lon_r, lat_r, reg_l, cmap=cmap, norm=norm)
        format_map(ax_rm, f'{t_left}: {r_name}', is_regional=True)

        reg_r, _, _ = extract_region(p_right, lons, lats, ext)
        if reg_r is not None: ax_ri.pcolormesh(lon_r, lat_r, reg_r, cmap=cmap, norm=norm)
        format_map(ax_ri, f'{t_right}: {r_name}', is_right_col=True, is_regional=True)

    fig.suptitle(suptitle, fontsize=TITLE_SZ, fontweight='bold', y=0.97)
    plt.savefig(out_filepath, dpi=300)
    os.rename(out_filepath, out_filepath.replace('.png', '.gif'))
    plt.close(fig)


# ==========================================================
# MAIN EXECUTION
# ==========================================================
def main():
    parser = argparse.ArgumentParser(description='Diurnal Precipitation Analysis Pipeline')
    parser.add_argument('-source', type=str, required=True, 
                        help='Path to the baseline experiment directory.')
    parser.add_argument('-plotsdir', type=str, required=True, 
                        help='Directory where the output plot files will be saved.')
    parser.add_argument('-begdate', type=str, required=True, 
                        help='Start date for the analysis period in YYYYMM format (use "NULL" for all available dates).')
    parser.add_argument('-enddate', type=str, required=True, 
                        help='End date for the analysis period in YYYYMM format (use "NULL" for all available dates).')
    parser.add_argument('-season', type=str, nargs='+', default=['ANN'], choices=VALID_SEASONS, 
                        help='One or more seasons to analyze (e.g., ANN JJA DJF). Default: ANN.')
    parser.add_argument('-cmpexp', type=str, nargs='*', default=[], 
                        help='Path(s) to one or more comparison experiment directories.')
    
    args, unknown = parser.parse_known_args()

    ignore_tags = ['MERRA2_MEANS', 'ERA5_Monthly', 'NULL']
    args.cmpexp = [exp for exp in args.cmpexp if not any(tag in exp for tag in ignore_tags)]

    base_exp = os.path.basename(os.path.normpath(args.source))
    os.makedirs(args.plotsdir, exist_ok=True)

    base_dir = os.path.join(args.source, 'tavg1_2d_prcp', 'diurnal')
    imerg_dir = '/discover/nobackup/projects/gmao/share/gmao_ops/verification/IMERG/diurnal'

    print('\n[diurnal] ' + '='*70)
    print('[diurnal]  DIURNAL PRECIPITATION PIPELINE')
    print('[diurnal] ' + '='*70)
    print(f'[diurnal]  Base Exp  : {base_exp}')
    print(f'[diurnal]  Base Path : {args.source}')
    print(f'[diurnal]  Plots Dir : {args.plotsdir}')
    print(f'[diurnal]  Req Dates : {args.begdate} to {args.enddate}' if args.begdate != 'NULL' else '[diurnal]  Req Dates : ALL AVAILABLE')
    print(f'[diurnal]  Seasons   : {", ".join(args.season)}')
    print(f'[diurnal]  Cmp Exps  : {len(args.cmpexp)} provided')
    print('[diurnal] ' + '-' * 70)

    # ------------------------------------------------------
    # 1. Dataset Initialization & Validation
    # ------------------------------------------------------
    datasets = {
        'Base': {
            'name': base_exp,
            'path': base_dir,
            'pattern': f'{base_exp}.tavg1_2d_prcp.diurnal.*.nc4',
            'is_imerg': False,
            'is_cmp': False
        },
        'IMERG': {
            'name': 'IMERG',
            'path': imerg_dir,
            'pattern': 'imerg_ave.diurnal.*.nc4',
            'is_imerg': True,
            'is_cmp': False
        }
    }
    
    for cmp_path in args.cmpexp:
        cmp_exp = os.path.basename(os.path.normpath(cmp_path))
        datasets[cmp_exp] = {
            'name': cmp_exp,
            'path': os.path.join(cmp_path, 'tavg1_2d_prcp', 'diurnal'),
            'pattern': f'{cmp_exp}.tavg1_2d_prcp.diurnal.*.nc4',
            'is_imerg': False,
            'is_cmp': True
        }

    for key, info in datasets.items():
        search_path = os.path.join(info['path'], '*') if info['is_imerg'] else info['path']
        info['files'] = get_available_months(search_path, info['pattern'])

    if args.begdate == 'NULL' or args.enddate == 'NULL':
        valid_months = sorted(list(set(datasets['Base']['files'].keys()) & set(datasets['IMERG']['files'].keys())))
    else:
        req_months = generate_month_list(args.begdate, args.enddate)
        valid_months = sorted(list(req_months & set(datasets['Base']['files'].keys()) & set(datasets['IMERG']['files'].keys())))

    if not valid_months:
        print('\n[diurnal] [!] ERROR: No overlapping months found between requested dates, Base Exp, and IMERG.')
        sys.exit(1)

    date_str = f'{valid_months[0]}-{valid_months[-1]}'
    print(f'[diurnal]  Base Exp Available  : {min(datasets["Base"]["files"].keys())} to {max(datasets["Base"]["files"].keys())} ({len(datasets["Base"]["files"])} months)')
    print(f'[diurnal]  IMERG Available     : {min(datasets["IMERG"]["files"].keys())} to {max(datasets["IMERG"]["files"].keys())} ({len(datasets["IMERG"]["files"])} months)')
    print(f'[diurnal]  Used for Analysis   : {valid_months[0]} to {valid_months[-1]} ({len(valid_months)} months)\n')

    avail_cal_months = set([int(ym[4:6]) for ym in valid_months])
    valid_seasons = []

    print('[diurnal] Validating requested seasons against available data...')
    for season in args.season:
        req_m = get_season_months(season)
        if set(req_m).issubset(avail_cal_months):
            valid_seasons.append(season)
        else:
            print(f'[diurnal]   [SKIP] Season \'{season}\': Missing calendar months {list(set(req_m) - avail_cal_months)}')

    if not valid_seasons:
        print('\n[diurnal] [!] ERROR: No requested seasons have complete data. Exiting.\n')
        sys.exit(1)

    print('\n[diurnal] Checking Comparison Experiments against baseline dates...')
    invalid_keys = []
    for key, info in datasets.items():
        if info['is_cmp']:
            if not set(valid_months).issubset(set(info['files'].keys())):
                print(f'[diurnal]   [SKIP] {key}\n[diurnal]          Reason: Missing required baseline months.')
                invalid_keys.append(key)
            else:
                print(f'[diurnal]   [OK]   {key}\n[diurnal]          Path: {info["path"]}')

    for k in invalid_keys:
        del datasets[k]

    print('[diurnal] ' + '-' * 70)

    # ------------------------------------------------------
    # 2. Regridder Initialization (Memory-Safe)
    # ------------------------------------------------------
    with xr.open_dataset(datasets['Base']['files'][valid_months[0]], engine='netcdf4') as tmp_b:
        lats, lons = tmp_b.lat.values, tmp_b.lon.values

    print(f'[diurnal] Detected Base Exp Grid: {len(lats)} lats x {len(lons)} lons')
    ds_grid_base = xr.Dataset({'lat': (['lat'], lats), 'lon': (['lon'], lons)})

    for key, info in datasets.items():
        if key == 'Base':
            info['regridder'] = None
            continue
        
        with xr.open_dataset(info['files'][valid_months[0]], engine='netcdf4') as tmp:
            t_lats = tmp.lat.values
            if info['is_imerg']:
                t_lons = (tmp.lon.values + 180) % 360 - 180
                t_lons.sort()
            else:
                t_lons = tmp.lon.values
        
        if len(t_lats) != len(lats) or len(t_lons) != len(lons):
            print(f'[diurnal] Building Regridder for {key}...')
            ds_grid_t = xr.Dataset({'lat': (['lat'], t_lats), 'lon': (['lon'], t_lons)})
            info['regridder'] = xe.Regridder(ds_grid_t, ds_grid_base, 'conservative_normed', periodic=True)
        else:
            info['regridder'] = None

    print('[diurnal] ' + '-' * 70)

    # ------------------------------------------------------
    # 3. Data Loading & 12-Month Reduction
    # ------------------------------------------------------
    print('[diurnal] Extracting 12 monthly climatologies for days-weighted seasonal math...')
    for key, info in datasets.items():
        var_name = 'APCP' if info['is_imerg'] else 'PRCP_TOT'
        files_list = [info['files'][m] for m in valid_months]
        info['monthly_clims'] = extract_12_month_clims(files_list, var_name, is_imerg=info['is_imerg'])

    print('[diurnal] ' + '-' * 70)
    lon_2d, lat_2d = np.meshgrid(lons, lats)

    # ==========================================================
    # SEASON LOOP (Math & Plotting)
    # ==========================================================
    for season in valid_seasons:
        print(f'[diurnal] Processing Season: {season}')
        t_months = get_season_months(season)

        # Apply proportional day-weights and compute unified metrics for all datasets
        for key, info in datasets.items():
            clim_raw = compute_weighted_season(info['monthly_clims'], t_months)
            clim = info['regridder'](clim_raw) if info['regridder'] else clim_raw
            info['metrics'] = compute_diurnal_metrics(clim.values, lats, lon_2d, info['name'], season)

        b_mets = datasets['Base']['metrics']
        i_mets = datasets['IMERG']['metrics']

        # A) BASE VS IMERG
        label_b_im = f'{base_exp} (Experiment)'
        label_im = 'IMERG'
        
        b_rat_msk = apply_mask(b_mets['ratio'], b_mets['amp'], AMP_THRESH)
        i_rat_msk = apply_mask(i_mets['ratio'], i_mets['amp'], AMP_THRESH)
        b_phs_msk = apply_mask(b_mets['phase'], b_mets['amp'], AMP_THRESH)
        i_phs_msk = apply_mask(i_mets['phase'], i_mets['amp'], AMP_THRESH)

        title_amp, out_amp = get_plot_metadata('amplitude', season, date_str, label_b_im, label_im, 'IMERG', False, args.plotsdir)
        draw_amplitude_plot(b_mets['amp'], i_mets['amp'], b_rat_msk, i_rat_msk, 
                            get_stats_text(b_mets['amp'], lats), get_stats_text(i_mets['amp'], lats),
                            get_stats_text(b_rat_msk, lats), get_stats_text(i_rat_msk, lats),
                            lons, lats, 'Experiment', 'IMERG', title_amp, out_amp)

        title_phs, out_phs = get_plot_metadata('phase', season, date_str, label_b_im, label_im, 'IMERG', False, args.plotsdir)
        draw_phase_plot(b_phs_msk, i_phs_msk,
                        get_stats_text(b_phs_msk, lats, is_phase=True), get_stats_text(i_phs_msk, lats, is_phase=True),
                        lons, lats, 'Experiment', 'IMERG', title_phs, out_phs)
        print(f'[diurnal]   -> Created Base vs IMERG Phase    : {os.path.basename(out_phs)}')

        # B) COMPARISON EXPERIMENTS
        for key, info in datasets.items():
            if not info['is_cmp']: continue
            print(f'\n[diurnal]   Evaluating Cmp Exp: {key}')
            
            c_mets = info['metrics']
            cmp_exp = info['name']
            
            label_b_cmp = f'{base_exp} (Exp1)'
            label_c_cmp = f'{cmp_exp} (Exp2)'
            
            c_rat_msk = apply_mask(c_mets['ratio'], c_mets['amp'], AMP_THRESH)
            c_phs_msk = apply_mask(c_mets['phase'], c_mets['amp'], AMP_THRESH)

            # Base vs Cmp
            c_title_amp, c_out_amp = get_plot_metadata('amplitude', season, date_str, label_b_cmp, label_c_cmp, cmp_exp, False, args.plotsdir)
            draw_amplitude_plot(b_mets['amp'], c_mets['amp'], b_rat_msk, c_rat_msk,
                                get_stats_text(b_mets['amp'], lats), get_stats_text(c_mets['amp'], lats),
                                get_stats_text(b_rat_msk, lats), get_stats_text(c_rat_msk, lats),
                                lons, lats, 'Exp1', 'Exp2', c_title_amp, c_out_amp)

            c_title_phs, c_out_phs = get_plot_metadata('phase', season, date_str, label_b_cmp, label_c_cmp, cmp_exp, False, args.plotsdir)
            draw_phase_plot(b_phs_msk, c_phs_msk,
                            get_stats_text(b_phs_msk, lats, is_phase=True), get_stats_text(c_phs_msk, lats, is_phase=True),
                            lons, lats, 'Exp1', 'Exp2', c_title_phs, c_out_phs)
            print(f'[diurnal]     -> Created Base vs Cmp Phase    : {os.path.basename(c_out_phs)}')

            # Closeness (Errors relative to IMERG)
            err_amp_b = b_mets['amp'] - i_mets['amp']
            err_amp_c = c_mets['amp'] - i_mets['amp']
            err_ratio_b = b_rat_msk - i_rat_msk
            err_ratio_c = c_rat_msk - i_rat_msk
            
            err_phs_b = wrap_phase(b_mets['phase'] - i_mets['phase'])
            err_phs_c = wrap_phase(c_mets['phase'] - i_mets['phase'])

            # Apply IMERG amplitude mask to error fields
            err_ratio_b = apply_mask(err_ratio_b, i_mets['amp'], AMP_THRESH)
            err_ratio_c = apply_mask(err_ratio_c, i_mets['amp'], AMP_THRESH)
            err_phs_b = apply_mask(err_phs_b, i_mets['amp'], AMP_THRESH)
            err_phs_c = apply_mask(err_phs_c, i_mets['amp'], AMP_THRESH)

            e_title_amp, e_out_amp = get_plot_metadata('amplitude', season, date_str, label_b_cmp, label_c_cmp, cmp_exp, True, args.plotsdir)
            draw_amplitude_plot(err_amp_b, err_amp_c, err_ratio_b, err_ratio_c,
                                get_stats_text(err_amp_b, lats, is_closeness=True), get_stats_text(err_amp_c, lats, is_closeness=True),
                                get_stats_text(err_ratio_b, lats, is_closeness=True), get_stats_text(err_ratio_c, lats, is_closeness=True),
                                lons, lats, 'Exp1 Error', 'Exp2 Error', e_title_amp, e_out_amp, is_closeness=True)

            e_title_phs, e_out_phs = get_plot_metadata('phase', season, date_str, label_b_cmp, label_c_cmp, cmp_exp, True, args.plotsdir)
            draw_phase_plot(err_phs_b, err_phs_c,
                            get_stats_text(err_phs_b, lats, is_closeness=True, is_phase=True), get_stats_text(err_phs_c, lats, is_closeness=True, is_phase=True),
                            lons, lats, 'Exp1 Error', 'Exp2 Error', e_title_phs, e_out_phs, is_closeness=True)
            print(f'[diurnal]     -> Created Closeness Phase      : {os.path.basename(e_out_phs)}')

        print('[diurnal] ')

    print('[diurnal] [SUCCESS] Diurnal analysis pipeline completed.\n')

if __name__ == '__main__':
    main()
