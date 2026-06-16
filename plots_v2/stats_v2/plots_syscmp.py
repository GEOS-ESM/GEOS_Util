#!/usr/bin/env python3
'''
Creates static and animated plotsys (individual) and syscmp (comparison) plots 
for global statistics data.
'''

# ================== IMPORTS ==================

import argparse
import glob
import io
import numpy as np
import os
import re
import sys
import warnings
import xarray as xr
import yaml

import matplotlib
matplotlib.use('Agg') 
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap, Normalize
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.util import add_cyclic_point

from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
from scipy import stats
from typing import Any, Dict

# ================== PLOT CONFIGURATION ==================

# Colormap choice (uncomment choice)
# c_cmap = plt.cm.RdBu_r(np.linspace(0, 1, 21))
# c_cmap = plt.cm.bwr(np.linspace(0, 1, 21)) 
c_cmap = [  # Custom spectral-like colormap
    (0.40, 0.00, 0.60),  # 0 vivid deep purple
    (0.30, 0.05, 0.78),  # 1 purple
    (0.17, 0.15, 0.95),  # 2 bright purple-blue
    (0.05, 0.40, 1.00),  # 3 bright blue
    (0.05, 0.65, 1.00),  # 4 cyan-blue
    (0.10, 0.80, 1.00),  # 5 cyan
    (0.30, 0.90, 1.00),  # 6 light cyan
    (0.60, 0.95, 1.00),  # 7 very light cyan
    (0.85, 0.98, 1.00),  # 8 near white cyan
    (0.95, 0.99, 1.00),  # 9 almost white cyan
    (1.00, 1.00, 1.00),  # 10 white
    (1.00, 1.00, 0.85),  # 11 pale yellow
    (1.00, 0.95, 0.60),  # 12 light yellow
    (1.00, 0.85, 0.30),  # 13 golden yellow
    (1.00, 0.70, 0.10),  # 14 bright orange
    (1.00, 0.55, 0.00),  # 15 orange
    (1.00, 0.40, 0.00),  # 16 red-orange
    (0.95, 0.25, 0.00),  # 17 strong red
    (0.80, 0.15, 0.00),  # 18 deep red
    (0.65, 0.05, 0.00),  # 19 very deep red
    (0.45, 0.00, 0.00),  # 20 darkest red (bold maroon)
]
        
# Variables metadata
vars_title_map = {'H': 'hght', 'U': 'uwnd', 'V': 'vwnd', 'T': 'tmpu', 
                  'Q': 'sphu', 'P': 'slp', 'PS': 'sfcp', 'Q2M': 'sphu', 
                  'T2M': 'tmpu', 'U10M': 'uwnd', 'V10M': 'vwnd', 
                  'D2M': 'dwpt', 'AOD': 'aod', 'LOGAOD': 'lnaod', 
                  'PM25': 'pm25'}
vars_long_map = {'H': 'Heights', 'U': 'U-Wind', 'V': 'V-Wind', 
                 'T': 'Temperature', 'Q': 'Specific Humidity',
                 'P': 'Sea-Level Pressure', 'PS': 'Surface Pressure',
                 'Q2M': '2m Specific Humidity', 'T2M': '2m Temperature', 
                 'U10M': '10m U-Wind', 'V10M': '10m V-Wind', 
                 'D2M': '2m Dew Point', 
                 'AOD': 'Total Aerosol Extinction AOT [550 nm]', 
                 'LOGAOD': 'log(AOD+0.01)', 'PM25': 'PM2.5 Total Mass'}
vars_unit_map = {'H': 'm', 'U': 'm/s', 'V': 'm/s', 'T': 'K', 'Q': 'g/kg', 
                 'P': 'hPa', 'PS': 'hPa', 'Q2M': 'g/kg', 'T2M': 'K', 
                 'U10M': 'm/s', 'V10M': 'm/s', 'D2M': 'K', 'AOD': '', 
                 'LOGAOD': '', 'PM25': 'µg/m3'}

# Lists of levels/styles for signiicance contours on comp plots
# Lists can be empty but must be defined. Levels should be like 0.9 or 0.95.
sig_levs = [0.90]
styles = ['solid']

# ================== UTILITY FUNCTIONS ==================

def check_coastline_data():
    '''Check if cartopy coastline data is available by trying to use it'''
    try:
        # Create a minimal test figure
        fig = plt.figure(figsize=(1,1))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.add_feature(cfeature.COASTLINE)
        # Force the download/data access by saving to a buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=10)  # Very low DPI for speed
        buffer.close()
        plt.close(fig)
        return True
    except Exception as e:
        print(f'ERROR: CARTOPY MAP DATA NOT FOUND\nTechnical error: {e}')
        command = ('python -c \'import matplotlib.pyplot as plt; '
                   'import cartopy.crs as ccrs; '
                   'fig = plt.figure(); '
                   'ax = plt.axes(projection=ccrs.PlateCarree()); '
                   'ax.coastlines(); '
                   'plt.savefig("test.png"); '
                   'import os; '
                   'os.remove("test.png"); '
                   'print("Map data downloaded successfully")\'')
        
        print(f'''
    This script requires coastline data that must be downloaded first.
    To fix this, please run the following command ON A LOGIN NODE:
    
        {command}
    
    This downloads ~2MB of coastline data
    to ~/.local/share/cartopy/
    You only need to do this once, then you can
    run this script.
    
    Script execution halted.''')
        sys.exit(1)

def load_stats_data(yaml_file: str, exp: int, process: str, part: int
                    ) -> Dict[str, Any]:
    '''
    Load statistics data from files specified in the YAML configuration.
    Validates that all requested init dates, leads, variables, levels, and 
    statistics exist for each experiment file.
    Parameters (come directly from script arguments):
    - yaml_file: YAML config file (full path)
    - exp: integer selecting model from config
    - process: 'indiv' or 'comp' (individual or comparison plots)
    - part: integer selecting variable(s) (0: all 2d vars, 1+: each 3d var)
    
    Returns a dictionary containing statistics data and configutation:
        - 'raw': Nested dict [coll][exp] of raw statistics arrays
        - 'avg': Nested dict [coll][exp] of avg statistics arrays
        - 'glo': Nested dict [coll][exp] of glo avg statistics arrays
        - 'date_nms': List of initialization dates as strings ('%Y%m%d')
        - 'leads': List of lead time hours
        - 'fcst_names': List of forecast model names
        - 'ana_names':  List of analysis model names
        - 'clim_names': List of climatology model names
        - 'fcst_length': Forecast length in days
        - 'fcst_interval': Forecast interval in hours
        - 'fvars': Dict of variable lists by collection
        - 'levels': List of pressure levels
        - 'lats': List of latitudes
        - 'lons': List of longitudes
        - 'collections': List of non-empty collection names
        - 'is_3d': Dict mapping collections to dim (3d or not) 
        - 'plot_stats': List of statistics to be plotted
        - 'season': Season string
        - 'year': Year integer
        - 'plot_dpi': Plot DPI setting
        - 'out_suffix': suffix for plots directory name
    '''
    
    # Open YAML configuration file
    if not os.path.exists(yaml_file):
        sys.exit(f'ERROR: YAML configuration file not found: {yaml_file}')
    try:
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        sys.exit(f'ERROR: Failed to read YAML file {yaml_file}: {e}')
    
    # Extract parameters from YAML, checking for required
    print(f'Extracting parameters from YAML configuration file: {yaml_file}')
    params = config.get('parameters', {})
    if not params:
        sys.exit(f'ERROR: No "parameters" section found in YAML file: '
                 f'{yaml_file}')
    required_params = ['season', 'year']
    missing_required = []
    for param in required_params:
        if param not in params:
            missing_required.append(param)
    if missing_required:
        sys.exit(f'ERROR: Missing required parameters in YAML file: '
                 f'{missing_required}')

    def parse_file_specification(file_spec):
        '''Parse file spec: allow glob patterns and comma-separated list'''
        if isinstance(file_spec, list):
            # Already a list
            all_files = []
            for item in file_spec:
                expanded = glob.glob(item)
                if expanded:
                    all_files.extend(expanded)
                else:
                    all_files.append(item)
            return all_files
        elif isinstance(file_spec, str):
            # Check for presence of commas (comma-separated list)
            if ',' in file_spec:
                files = [f.strip() for f in file_spec.split(',')]
                all_files = []
                for file_item in files:
                    expanded = glob.glob(file_item)
                    if expanded:
                        all_files.extend(expanded)
                    else:
                        all_files.append(file_item)
                return all_files
            else:  # Single file
                files = glob.glob(file_spec)
                if not files:
                    files = [file_spec]
                return files
        else:
            sys.exit(f'ERROR: Invalid file specification type: '
                     f'{type(file_spec)}')
    
    # Get experiment file paths and validate they exist
    all_exp_file_lists = []
    exp_idx = 0
    while f'sys_exp{exp_idx}' in params:
        file_spec = params[f'sys_exp{exp_idx}']
        file_list = parse_file_specification(file_spec)
        file_list = sorted(set(file_list))
        missing_files = []
        for file_path in file_list:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        if missing_files:
            sys.exit(f'ERROR: Files not found for sys_exp{exp_idx}:\n' + 
                     '\n'.join(f'  {f}' for f in missing_files))
        all_exp_file_lists.append(file_list)
        exp_idx += 1
    
    # Filter experiments based on exp parameter and check for required specs
    if exp is None:  # No exp parameter
        # Process all experiments
        original_exp_indices = list(range(len(all_exp_file_lists)))
        exp_file_lists = all_exp_file_lists
        if process == 'indiv' and len(exp_file_lists) < 1:
            sys.exit('ERROR: At least exp0 must be specified in config for '
                     'indiv plots')
        if process == 'comp' and len(exp_file_lists) < 2:
            sys.exit('ERROR: At least exp0 and exp1 must be specified in '
                     'config for comp plots')
    else:  # Specified exp parameter
        # Filter to specific experiment(s)
        if process == 'indiv': 
            exp_ids = [exp]
        elif process == 'comp': 
            exp_ids = [0, exp]
        exp_file_lists = []
        original_exp_indices = []
        for exp_id in exp_ids:
            if exp_id < len(all_exp_file_lists):
                exp_file_lists.append(all_exp_file_lists[exp_id])
                original_exp_indices.append(exp_id)
            else:
                sys.exit(f'ERROR: sys_exp{exp_id} not found in YAML config')
                
    # Print experiment files summary
    print(f'Found {len(exp_file_lists)} experiments:')
    for i, file_list in enumerate(exp_file_lists):
        print(f'  exp{i}: {len(file_list)} files')
        if len(file_list) <= 5:  # Show all files if 5 or fewer
            for f in file_list:
                print(f'    {os.path.basename(f)}')
        else:  # Show first 3 and last 2 if more than 5
            for f in file_list[:3]:
                print(f'   {os.path.basename(f)}')
            print(f'    ... ({len(file_list)-5} more files)')
            for f in file_list[-2:]:
                print(f'    {os.path.basename(f)}')

    # Set defaults for optional parameters
    plot_dpi = params.get('plot_dpi', 300)
    out_suffix = params.get('suffix', '')
    
    # Define statistics to plot based on process
    if process == 'indiv':
        plot_stats = [
            'f', 'f_c', 'me', 'acorr', 'rms', 'rms_bar', 'rms_amp', 'rms_phz']  
    elif process == 'comp':
        plot_stats = ['me', 'acorr', 'rms', 'rms_bar', 'rms_amp', 'rms_phz']  

    # Initialize variable lists from config
    fvars = {
        'de3d': params.get('3d_vars_default', []),
        'de2d': params.get('2d_vars_default', []),
        'sl2d': params.get('2d_vars_slices',  []),
        'ae2d': params.get('2d_vars_aerosol', [])
    }
    
    # Check that at least some variables are specified
    all_vars = []
    for var_list in fvars.values():
        all_vars.extend(var_list)
    if not all_vars:
        sys.exit('ERROR: No variables specified. At least one of '
                 '3d_vars_default, 2d_vars_default, 2d_vars_slices or'
                 '2d_vars_aerosol must be provided.')
    
    # Determine which collections are non-empty and store them
    collections = [coll for coll, vars_list in fvars.items() if vars_list]
    # Create dictionary to track which collections are 3D
    is_3d = {coll: (int(coll[-2]) == 3) for coll in collections}
    
    # Format variable names based on collection prefix
    for key in fvars:
        if key.startswith('de') or key.startswith('ae'):
            # For collections beginning with 'de' or 'ae', make all uppercase
            fvars[key] = [var.upper() for var in fvars[key]]
        elif key.startswith('sl'):
            # For 'sl', format as uppercase before numbers, lowercase after
            formatted_vars = []
            for var in fvars[key]:
                # Find the first digit in the variable name
                match = re.search(r'\d', var)
                if match:
                    digit_pos = match.start()
                    # Uppercase before the digit, lowercase after
                    new_var = var[:digit_pos].upper() + var[digit_pos:].lower()
                    formatted_vars.append(new_var)
                else:
                    # If no digit found, return an error
                    sys.exit(f'ERROR: Variable "{var}" in collection "{key}" '
                             f'must contain at least one digit.')
            fvars[key] = formatted_vars
    
    # Get requested levels
    requested_levels = [int(level) for level in params.get('levels', [])]
    
    # Get date/time parameters for validation (if provided)
    fcst_length = params.get('fcst_length')
    fcst_interval = params.get('fcst_interval')
    fcst_spacing = params.get('fcst_spacing')
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    
    # Check that all files have compatible configurations
    fcst_names = []
    ana_names = []
    clim_names = []
    
    def merge_experiment_files(file_list, exp_name):
        '''Merge multiple files for a single experiment with overlap 
        validation and weighted averaging'''
        if len(file_list) == 1:
            print(f'Loading single file for {exp_name}...')
        else:
            print(f'Merging {len(file_list)} files for {exp_name}...')
        
        # Open all datasets and collect exclusion metadata as needed
        datasets = []
        experiment_excluded_dates = set()
        files_with_exclusions = 0
        for f in file_list:
            ds = xr.open_dataset(f)
            datasets.append(ds)
            # Check for exclusion pattern and collect metadata
            basename = os.path.basename(f)
            excl_match = re.search(r'excl(\d+)', basename)
            if excl_match:
                files_with_exclusions += 1
                if 'excluded_dates' not in ds.attrs:
                    # Clean up before exit
                    for ds_cleanup in datasets:
                        ds_cleanup.close()
                    sys.exit(f'ERROR: File {basename} contains '
                             f'"excl{excl_match.group(1)}" pattern but '
                             f'missing "excluded_dates" attribute in metadata')
                excluded_dates_str = ds.attrs['excluded_dates']
                # Parse excluded dates (handle both string and list formats)
                if isinstance(excluded_dates_str, (list, np.ndarray)):
                    # Already a list/array, convert to strings and strip
                    excluded_list = [str(item).strip() 
                                     for item in excluded_dates_str]
                else:
                    # String format - parse comma-separated values
                    if ',' in excluded_dates_str:
                        excluded_list = [d.strip() for d 
                                         in excluded_dates_str.split(',')]
                    else:
                        excluded_list = [excluded_dates_str.strip()]
                # Convert to standard format (YYYYMMDD only)
                for date_str in excluded_list:
                    if len(date_str) > 8 and '_' in date_str:
                        formatted_date = date_str.split('_')[0]
                    else:
                        formatted_date = date_str[:8]
                    experiment_excluded_dates.add(formatted_date)
        
        if len(datasets) > 1: # multiple files
            # Validate no overlap between datasets
            all_dates = []
            date_counts = []
            for i, ds in enumerate(datasets):
                file_dates = set(ds.init_date.values)
                date_counts.append(len(file_dates))
                
                # Check for overlap with previously processed files
                overlap = set(all_dates) & file_dates
                if overlap:
                    overlap_strs = [d.astype('datetime64[us]').astype(
                        datetime).strftime('%Y%m%d') for d in overlap]
                    # Clean up
                    for ds_cleanup in datasets:
                        ds_cleanup.close()
                    sys.exit(f'ERROR: Duplicate dates found in {exp_name} '
                             f'files:\n'
                             f'  File {i}: {os.path.basename(file_list[i])}\n'
                             f'  Overlapping dates: {overlap_strs}')
                all_dates.extend(file_dates)
            
            # Separate variables by whether they have init_date dimension
            first_ds = datasets[0]
            vars_with_init_date = []
            vars_avg = []
            vars_glo = [] 
            vars_non_avg_without_init = []
            
            for var_name in first_ds.data_vars:
                if 'init_date' in first_ds[var_name].dims:
                    vars_with_init_date.append(var_name)
                elif var_name.endswith('_avg'):
                    vars_avg.append(var_name)
                elif var_name.endswith('_glo'):
                    vars_glo.append(var_name)
                else:
                    vars_non_avg_without_init.append(var_name)
            
            # Merge variables with init_date dimension (regular concatenation)
            ds_with_init = xr.concat([ds[vars_with_init_date] 
                                      for ds in datasets], 
                                    dim='init_date').sortby('init_date')
            
            # Weighted averaging for _avg and _glo variables
            total_dates = sum(date_counts)
            ds_avg_weighted = (datasets[0][vars_avg] 
                               * (date_counts[0]/total_dates))
            for i in range(1, len(datasets)):
                weight = date_counts[i] / total_dates
                ds_avg_weighted = (ds_avg_weighted + datasets[i][vars_avg] 
                                   * weight)
            ds_glo_weighted = (datasets[0][vars_glo] 
                               * (date_counts[0]/total_dates))
            for i in range(1, len(datasets)):
                weight = date_counts[i] / total_dates
                ds_glo_weighted = (ds_glo_weighted + datasets[i][vars_glo] 
                                   * weight)
            
            # For non-_avg/glo variables without init_date, use first dataset
            ds_non_avg = first_ds[vars_non_avg_without_init]
            # Combine everything back together
            merged_ds = xr.merge([ds_with_init, ds_avg_weighted, 
                                  ds_glo_weighted, ds_non_avg])
            
            # Close individual datasets
            for ds in datasets:
                ds.close()
        
        else:  # Single file case - skip merge operations
            merged_ds = datasets[0]
        
        # Report result
        final_dates = merged_ds.init_date.values
        first_date = final_dates[0].astype('datetime64[us]').astype(
            datetime).strftime('%Y%m%d')
        last_date = final_dates[-1].astype('datetime64[us]').astype(
            datetime).strftime('%Y%m%d')
        if len(datasets) > 1:
            print(f'Merged dataset: {len(final_dates)} init dates from '
                  f'{first_date} to {last_date}')
            print(f'Averaged variables weighted by date counts: {date_counts}')
        else:
            print(f'Dataset contains {len(final_dates)} init dates from '
                  f'{first_date} to {last_date}')
        
        return merged_ds, experiment_excluded_dates, files_with_exclusions
    
    for exp_idx, file_list in enumerate(exp_file_lists):
        # Check all exp files for consistency, then store representative values
        exp_fcst = None
        exp_ana = None  
        exp_clim = None
        exp_suffix = None
        
        for file_idx, exp_file in enumerate(file_list):
            basename = os.path.basename(exp_file)
            parts = basename.split('_')
            
            # Files should be as: stats_global_FCST_ANA_CLIM_[dates]_[suffix]
            if len(parts) < 6 or parts[0] != 'stats' or parts[1] != 'global':
                sys.exit(f'ERROR: File format not recognized: {basename}\n'
                         f'Expected: '
                         f'stats_global_FCST_ANA_CLIM_[dates]_[suffix]')
            # Extract model names
            file_fcst = parts[2]
            file_ana = parts[3]
            file_clim = parts[4]
            # Extract suffix after date range
            suffix_parts = parts[5:]
            # Ignore exclusions for consistency check, as chunks can differ
            clean_suffix = [p for p in suffix_parts[1:] if not p.startswith('excl')]
            file_suffix = '_'.join(clean_suffix)
            
            # Validate consistency with expected values from first file
            if file_idx == 0:
                exp_fcst = file_fcst
                exp_ana = file_ana
                exp_clim = file_clim
                exp_suffix = file_suffix
            else:
                # Check required consistency (models and suffix)
                if (file_fcst != exp_fcst or file_ana != exp_ana or 
                    file_clim != exp_clim or file_suffix != exp_suffix):
                    sys.exit(f'ERROR: Inconsistent configuration within '
                             f'exp{exp_idx}:\n  Expected: '
                             f'{exp_fcst}_{exp_ana}_{exp_clim}_{exp_suffix}\n'
                             f'  Found: {file_fcst}_{file_ana}_{file_clim}_'
                             f'{file_suffix}\n  File: {basename}')
        
        # Store values
        fcst_names.append(exp_fcst)
        ana_names.append(exp_ana)
        clim_names.append(exp_clim)
    
    # Extract timing and resolution parameters for compatibility checking
    exp_flex_configs = []
    exp_inflex_configs = []
    for i, file_list in enumerate(exp_file_lists):
        # Parts after date range
        suffix_config_parts = os.path.basename(file_list[0]).split('_')[6:]
        # Separate flexible parameters (len/int) from inflexible (spc/res)
        flex_parts = []
        inflex_parts = []
        for p in suffix_config_parts:
            if p.startswith('len') or p.startswith('int'):
                flex_parts.append(p)
            elif p.startswith('spc') or ('x' in p and not p.startswith('excl')):
                inflex_parts.append(p)
        exp_flex_configs.append('_'.join(flex_parts))
        exp_inflex_configs.append('_'.join(inflex_parts))
        
    # Check timing and resolution parameter compatibility
    if (len(set(exp_flex_configs)) == 1 and len(set(exp_inflex_configs)) == 1):
        print(f'Verified all {len(exp_file_lists)} experiments have identical '
              f'configurations: {exp_flex_configs[0]}_{exp_inflex_configs[0]}')
    elif len(set(exp_inflex_configs)) == 1:
        # Same spacing/resolution, different timing - proceed with warning
        print('WARNING: Experiments have different forecast timing parameters '
              'but compatible spacing and resolution configurations:')
        for i in range(len(exp_file_lists)):
            print(f'  exp{i}: {exp_flex_configs[i]}')
        print('Proceeding with lead time validation for each experiment...')
    else:
        # Incompatible spacing and/or resolution - exit with error
        error_msg = ('ERROR: Experiments have incompatible forecast spacing '
                     'and/or resolution:\n')
        for i in range(len(exp_file_lists)):
            error_msg += f'  exp{i}: {exp_inflex_configs[i]}\n'
        error_msg += ('Spacing (spc*) and grid resolution must be identical '
                      'across all experiments.')
        sys.exit(error_msg)
        
    print('Models:')
    for i, (f, a, c) in enumerate(zip(fcst_names, ana_names, clim_names)):
        print(f'  exp{i}: {f}(F) / {a}(A) / {c}(C)')
    
    # If fcst_length or fcst_interval not provided, deduce from exp0
    exp0_basename = os.path.basename(exp_file_lists[0][0])  # First file
    ds_exp0 = None
    if not fcst_length or not fcst_interval:
        print('Forecast length and/or interval not specified in YAML. '
              'Deducing from exp0...')
        # Open exp0 to extract timing information
        print(f'Analyzing {exp0_basename} for timing parameters...')
        ds_exp0 = xr.open_dataset(exp_file_lists[0][0])  # First file
        # Extract lead times from exp0
        exp0_leads = [int(x) for x in ds_exp0.lead.values.tolist()
                      ] if 'lead' in ds_exp0.coords else []
    if not fcst_length:
        # Deduce forecast length (maximum lead time in days)
        max_lead_hours = max(exp0_leads)
        fcst_length =  max_lead_hours // 24
        print(f'  Deduced fcst_length: {fcst_length} days (max lead: '
              f'{max_lead_hours} hours)')
    if not fcst_interval:
        # Deduce forecast interval (difference between consecutive leads)
        fcst_interval = exp0_leads[1] - exp0_leads[0]
        print(f'  Deduced fcst_interval: {fcst_interval} hours')
        
    requested_dates = []
    # Parse start and end dates if provided (for YAML-based validation)
    if start_date and end_date and fcst_spacing:
        print('Analyzing YAML file for init dates...')
        try:
            start_dt = datetime.strptime(str(start_date), '%Y%m%d')
            end_dt = datetime.strptime(str(end_date), '%Y%m%d')
            # Generate requested initialization dates
            current_dt = start_dt
            while current_dt <= end_dt:
                requested_dates.append(current_dt.strftime('%Y%m%d'))  
                current_dt += timedelta(days=fcst_spacing)
        except ValueError as e:
            sys.exit(f'ERROR: Invalid date format in YAML file: {e}')
    else:
        # Extract initialization dates from all exp0 files
        print('Analyzing exp0 files for init dates...')
        # Open all datasets and extract just init_date coordinates
        all_init_dates = []
        for f in exp_file_lists[0]:
            ds = xr.open_dataset(f)
            all_init_dates.extend(ds.init_date.values)
            ds.close()
        # Remove duplicates and sort
        unique_dates = sorted(list(set(all_init_dates)))
        requested_dates = [d.astype('datetime64[us]').astype(
            datetime).strftime('%Y%m%d') for d in unique_dates]
    
    if ds_exp0: ds_exp0.close()
    
    print(f'Using timing parameters: fcst_length={fcst_length}d, '
          f'fcst_interval={fcst_interval}h')  

    data = {}
    if process in ['indiv', 'comp']: 
    
        # Initialize output structures
        data = {
            'raw': {},  # Will be indexed by [collection][exp_idx]
            'avg': {},  # Will be indexed by [collection][exp_idx]
            'glo': {},  # Will be indexed by [collection][exp_idx]
        }
        
        # Print requested parameters
        print('\n=== Requested Parameters ===')
        print('Variables by collection:')
        for collection in collections:
            print(f'  {collection}: {fvars[collection]}')
        print(f'Levels: {requested_levels}')
        print(f'Stats to be Plotted: {plot_stats}')
        print(f'Season: {params["season"]}')
        print(f'Year: {params["year"]}')
        print(f'Plot DPI: {plot_dpi}')
        dates_listing = ', '.join(requested_dates[:5] + (
            ['...'] if len(requested_dates) > 5 else []))
        print(f'Requested Dates ({len(requested_dates)}): [{dates_listing}]')
        print('============================\n')
        
        # Initialize data structure for all collections
        for coll in collections:
            if process == 'comp': data['raw'][coll] = {}  # Only for comp
            data['avg'][coll] = {}
            data['glo'][coll] = {}
        
        # Process part filtering by vars
        if part is not None:
            if part == 0: # only 2d collections
                collections_process = [coll for coll in collections 
                                       if not is_3d[coll]]
                print('Processing part 0: 2D variables')
            if part > 0:
                collections_process = ['de3d']
                if len(fvars['de3d']) >= part:
                    fvars['de3d'] = [fvars['de3d'][part-1]]
                    print(f'Processing part {part}: 3D variable '
                          f'{fvars["de3d"]}')
                else:
                    print(f'Part {part} exceeds available 3D variables, '
                          f'skipping')
                    collections_process = []
        else: 
            collections_process = collections
        
        # Process each experiment file list
        for exp_idx, file_list in enumerate(exp_file_lists):
            print(f'\n=== Experiment {exp_idx}: {fcst_names[exp_idx]}(F) / '
                  f'{ana_names[exp_idx]}(A) / {clim_names[exp_idx]}(C) ===')
            
            # Handle single vs multiple files
            if len(file_list) == 1:
                basename = os.path.basename(file_list[0])
                ds, excluded_dates_set, exclusion_count = (
                    merge_experiment_files(file_list, f'exp{exp_idx}'))
            else:
                ds, excluded_dates_set, exclusion_count = (
                    merge_experiment_files(file_list, f'exp{exp_idx}'))
                basename = os.path.basename(file_list[0])
            
            # Let exp0 define the baseline dates by subtracting its exclusions
            if exp_idx == 0 and excluded_dates_set:
                print(f'Found exclusions in exp0: {sorted(excluded_dates_set)}')
                original_count = len(requested_dates)
                requested_dates = [date for date in requested_dates 
                                   if date not in excluded_dates_set]
                if len(requested_dates) < original_count:
                    print(f'Found exclusions in exp0: '
                          f'{sorted(excluded_dates_set)}')
                    print(f'Applied exclusions: {original_count} → '
                          f'{len(requested_dates)} dates')
                else:
                    print(f'Found exclusions in exp0: '
                          f'{sorted(excluded_dates_set)} '
                          f'(already reflected in requested dates)')
                
            # Extract coordinates
            available_levels = [int(x) for x in ds.lev.values.tolist()]
            available_leads = ([int(x) for x in ds.lead.values.tolist()] 
                               if 'lead' in ds.coords else [])
            lats = ds.lat
            lons = ds.lon
            n_lats = len(lats)
            n_lons = len(lons)
            
            # Filter dataset to requested levels
            if len(requested_levels) < len(available_levels):
                # Find indices of requested levels while preserving order
                level_indices = [available_levels.index(level) 
                                 for level in requested_levels]
                ds = ds.isel(lev=level_indices)
                print(f'Filtered dataset from {len(available_levels)} to '
                      f'{len(requested_levels)} requested levels')

            # Get initialization dates
            init_dates = ds.init_date.values
            available_date_nms = [d.astype('datetime64[us]').astype(
                datetime).strftime('%Y%m%d') for d in init_dates]
            
            # Date validation: all requested dates must be present
            missing_dates = set(requested_dates) - set(available_date_nms)
            if missing_dates:
                missing_strs = [str(d) for d in sorted(missing_dates)]
                ds.close()
                sys.exit(f'ERROR: exp{exp_idx} is missing required dates:\n'
                         f'  Missing dates: {missing_strs[:10]}'
                         f'{"..." if len(missing_strs) > 10 else ""}'
                         f'  ({len(missing_dates)} total)\n'
                         f'  Because of averaging, for syscmp, all requested '
                         f'dates (from YAML or exp0) must be present in each '
                         f'experiment.')
            
            # Date validation: no extra dates allowed (because of averaging)
            extra_dates = set(available_date_nms) - set(requested_dates)
            if extra_dates:
                extra_strs = [str(d) for d in sorted(extra_dates)]
                ds.close()
                sys.exit(f'ERROR: exp{exp_idx} contains extra dates:\n'
                         f'  Extra dates: {extra_strs[:10]}'
                         f'{"..." if len(extra_strs) > 10 else ""}'
                         f'  ({len(extra_dates)} total)\n'
                         f'  Because of averaging, for syscmp, all requested '
                         f'dates (from YAML or exp0) must be present in each '
                         f'each experiment.')
            print(f'Date validation: Perfect match - '
                  f'{len(available_date_nms)} dates')
            
            # Order dates within combined dataset
            date_indices = [available_date_nms.index(date) 
                            for date in requested_dates]
            ds = ds.isel(init_date=date_indices)
            
            # Leads validation: all requested must be present
            expected_leads = list(range(0, fcst_length*24 + 1, fcst_interval))
            missing_leads = []
            for lead in expected_leads:
                if lead not in available_leads:
                    missing_leads.append(lead)
            if missing_leads:
                sys.exit(f'ERROR: Missing expected lead times in {basename}: '
                         f'{missing_leads}\nAvailable leads: {available_leads}'
                         '\nExpected leads (based on fcst_length='
                         f'{fcst_length}d, fcst_interval={fcst_interval}h): '
                         f'{expected_leads}')
            else:
                lead_indices = [available_leads.index(exp_lead) 
                                for exp_lead in expected_leads]
                ds = ds.isel(lead=lead_indices)
            
            # Validation: check for requested variables, levels, and stats
            # Collect all variables that exist in the file
            available_vars = {coll: [] for coll in collections}
            available_stats = set()
            # Create mapping of all variables to their collections
            var_to_collection = {}
            for collection, var_list in fvars.items():
                for var in var_list:
                    var_to_collection[var] = collection
            # Scan variables to categorize them
            for var_name in ds.variables:
                # Skip coordinates
                if var_name in ds.coords:
                    continue
                # Extract variable and stat name
                parts = var_name.split('_')
                if len(parts) < 2:
                    continue
                var = parts[0] # Variable name is first part
                # Find what collection it belongs to
                if var not in var_to_collection:
                    continue  # Skip variables not in collections
                collection = var_to_collection[var]
                # Determine if it is raw, avg, or glo
                if var_name.endswith('_avg'):
                    # Strip _avg to get base stat name
                    stat = '_'.join(parts[1:-1])  # Join middle parts
                    available_stats.add(stat)
                elif var_name.endswith('_glo'):
                    # Strip _glo to get base stat name
                    stat = '_'.join(parts[1:-1])  # Join middle parts
                    available_stats.add(stat)
                else:
                    stat = '_'.join(parts[1:])  # Join all parts after var name
                    available_stats.add(stat)
                # Add to available variables if not already there
                if var not in available_vars[collection]:
                    available_vars[collection].append(var)
            
            # Check if all requested variables are available
            missing_vars = []
            for collection in collections:
                for var in fvars[collection]:
                    if var not in available_vars[collection]:
                        missing_vars.append(
                            f'{var} (collection: {collection})')
            
            # Check if all requested levels are available
            missing_levels = []
            for level in requested_levels:
                if level not in available_levels:
                    missing_levels.append(level)
            
            # Check if all plot statistics are available
            missing_stats = []
            for stat in plot_stats:
                if stat not in available_stats:
                    missing_stats.append(stat)
            
            # If anything is missing, exit with error
            if missing_vars or missing_levels or missing_stats:
                error_msg = (f'ERROR: Missing required elements in '
                             f'{basename}:\n')
                if missing_vars:
                    error_msg += f'  Missing variables: {missing_vars}\n'
                    error_msg += '  Available variables by collection:\n'
                    for coll in collections:
                        error_msg += f'    {coll}: {available_vars[coll]}\n'
                if missing_levels:
                    error_msg += f'  Missing levels: {missing_levels}\n'
                    error_msg += f'  Available levels: {available_levels}\n'
                if missing_stats:
                    error_msg += f'  Missing statistics: {missing_stats}\n'
                    error_msg += (f'  Available statistics: '
                                  f'{sorted(available_stats)}\n')
                sys.exit(error_msg)
            
            # Initialize data structures for this experiment
            for coll in collections:
                if process == 'comp': data['raw'][coll][exp_idx] = {}
                data['avg'][coll][exp_idx] = {}
                data['glo'][coll][exp_idx] = {}
            
            # Now load and restructure the data for each collection
            for coll in collections_process:
                n_vars = len(fvars[coll])
                n_stats = len(plot_stats)
                n_init_dates = len(requested_dates)
                n_leads = len(expected_leads)
                
                # Check if 3D collection by examining the collection name
                n_levels = len(requested_levels) if is_3d[coll] else None
                
                # Process
                if is_3d[coll]:
                    # 3D data ([init_date], lead, stat, var, lev, [lat, lon])
                    if process == 'comp': 
                        raw_array = np.zeros(
                            (n_init_dates, n_leads, n_stats, n_vars, n_levels, 
                             n_lats, n_lons))
                    avg_array = np.zeros(
                        (n_leads, n_stats, n_vars, n_levels, n_lats, n_lons))
                    glo_array = np.zeros(
                        (n_leads, n_stats, n_vars, n_levels))
                else:
                    # 2D data ([init_date], lead, stat, var, [lat, lon])
                    if process == 'comp': 
                        raw_array = np.zeros(
                            (n_init_dates, n_leads, n_stats, n_vars, n_lats, 
                             n_lons))
                    avg_array = np.zeros(
                        (n_leads, n_stats, n_vars, n_lats, n_lons))
                    glo_array = np.zeros(
                        (n_leads, n_stats, n_vars))
                
                # Fill arrays with data
                for var_idx, var in enumerate(fvars[coll]):
                    for stat_idx, stat in enumerate(plot_stats):
                        if process == 'comp': 
                            # Raw statistic
                            raw_var_name = f'{var}_{stat}'
                            if raw_var_name in ds:
                                raw_data = ds[raw_var_name].values
                                if is_3d[coll]:
                                    # shape: (init_date, lead, lev, lat, lon)
                                    raw_array[:, :, stat_idx, var_idx, :
                                              ] = raw_data[:]
                                else:
                                    # shape: (init_date, lead, lat, lon)
                                    raw_array[:, :, stat_idx, var_idx, :
                                              ] = raw_data[:]
                        # Averaged statistic
                        avg_var_name = f'{var}_{stat}_avg'
                        if avg_var_name in ds:
                            avg_data = ds[avg_var_name].values
                            if is_3d[coll]:
                                # shape: (lead, lev, lat, lon)
                                avg_array[:, stat_idx, var_idx, :
                                          ] = avg_data[:]
                            else:
                                # shape: (lead, lat, lon)
                                avg_array[:, stat_idx, var_idx
                                          ] = avg_data[:]
                        # Global statistic
                        glo_var_name = f'{var}_{stat}_glo'
                        if glo_var_name in ds:
                            glo_data = ds[glo_var_name].values
                            if is_3d[coll]:
                                # shape: (lead, lev)
                                glo_array[:, stat_idx, var_idx, :
                                          ] = glo_data[:]
                            else:
                                # shape: (lead)
                                glo_array[:, stat_idx, var_idx
                                          ] = glo_data[:]
                
                # Store arrays in data structure
                if process == 'comp': data['raw'][coll][exp_idx] = raw_array
                data['avg'][coll][exp_idx] = avg_array
                data['glo'][coll][exp_idx] = glo_array
            
            print('Status: All requested variables, statistics, levels, and '
                  'dates found and loaded')
            print(f'Data: {len(requested_dates)} init dates, '
                  f'{len(available_leads)} lead times')
            
            # Show array shapes for verification
            print('Array shapes:')
            for coll in collections_process:
                if process == 'comp': 
                    raw_shape = data['raw'][coll][exp_idx].shape
                avg_shape = data['avg'][coll][exp_idx].shape
                glo_shape = data['glo'][coll][exp_idx].shape
                if is_3d[coll]:
                    print(f'{coll}: glo {glo_shape} [nleads, nstats, nvars, '
                          f'nlevs]\n'
                          f'      avg {avg_shape} [nleads, nstats, nvars, '
                          f'nlevs, nlats, nlons]')
                    if process == 'comp': 
                        print(f'      raw {raw_shape} [nfcsts, nleads, '
                              f'nstats, nvars, nlevs, nlats, nlons]')
                else: 
                    print(f'{coll}: glo {glo_shape} [nleads, nstats, nvars]\n'
                          f'      avg {avg_shape} [nleads, nstats, nvars, '
                          f'nlats, nlons]')
                    if process == 'comp': 
                        print(f'      raw {raw_shape} [nfcsts, nleads, '
                              f'nstats, nvars, nlats, nlons]')

            # Close the dataset
            ds.close()
    
    # Save all metadata in output structure
    data['date_nms'] = requested_dates
    data['leads'] = expected_leads
    # Apply forecast name overrides if specified in YAML
    for exp_idx in range(len(fcst_names)):
        original_idx = original_exp_indices[exp_idx]
        override_key = f'fcst_exp{original_idx}'
        if override_key in params and params[override_key] is not None:
            override_name = params[override_key]
            # Validate alphanumeric only
            if not override_name.isalnum():
                sys.exit(f'ERROR: Override forecast name "{override_name}" '
                         f'for {override_key} must be alphanumeric only')
            original_name = fcst_names[exp_idx]
            fcst_names[exp_idx] = params[override_key]
            print(f'Override: exp{exp_idx} forecast name "{original_name}" '
                  f'→ {params[override_key]}')
    data['fcst_names'] = fcst_names
    data['ana_names'] = ana_names
    data['clim_names'] = clim_names
    data['fcst_length'] = fcst_length
    data['fcst_interval'] = fcst_interval
    data['fvars'] = fvars
    data['levels'] = requested_levels
    data['lats'] = lats
    data['lons'] = lons
    data['collections'] = collections_process  # Use processed collections
    data['is_3d'] = is_3d
    data['plot_stats'] = plot_stats
    data['season'] = params['season']
    data['year'] = params['year']
    data['plot_dpi'] = plot_dpi
    data['out_suffix'] = out_suffix
    data['syscmp_colormap'] = params.get('syscmp_colormap', 'custom_spectral')
    
    return data

def round_down_max(arr):
    '''
    Return the max absolute value rounded down to the nearest 10, with a 
    minimum threshold of 10 (smaller values use specific "nice" values).
    '''
    
    with np.errstate(invalid='ignore'):
        max_abs = np.nanmax(np.abs(arr))
    if 0 < max_abs <= 0.1:
        return 0.1
    elif 0.1 < max_abs <= 1:
        return 1
    elif 1 < max_abs <= 5:
        return 5
    elif 5 < max_abs <= 10:
        return 10
    elif max_abs > 10:
        return int(max_abs // 10 * 10)
    else:
        return 0  # For all-zero or all-NaN input

def nice_levels(data_min, data_max, n_levels, n_ticks):
    '''
    Return contour levels with nice tick label values based on data range.
    '''
    
    # Get raw step size and order or magnitude
    data_range = data_max - data_min
    raw_step = data_range / (n_ticks - 1)
    mag = 10 ** np.floor(np.log10(raw_step))
    norm_step = raw_step / mag

    # Choose a nice normalized step size
    if norm_step <= 1:
        nice_step = 1
    elif norm_step <= 2:
        nice_step = 2
    elif norm_step <= 2.5:
        nice_step = 2.5
    elif norm_step <= 5:
        nice_step = 5
    else:
        nice_step = 10
    step = nice_step * mag

    # Compute the lower and upper bounds and levels
    lower = np.floor(data_min / step) * step
    upper = np.ceil(data_max / step) * step
    levels = np.linspace(lower, upper, n_levels)
    return levels

def setup_plot_metadata(coll, v, lev, zonal, lead, plot_type):
    '''
    Setup plot metadata including naming components and figure with gridspec.
    Parameters:
    - coll: collection name
    - v: variable index  
    - lev: level value
    - zonal: zonal plot type (0 for level, others for zonal)
    - lead: lead time
    - plot_type: 'indiv' or 'comp' to determine file naming and grid layout
    Returns:
    - pre: filename prefix
    - ending: plot title ending text
    - gs: gridspec object
    - fig: figure object
    '''
    
    # Distinguish between indiv and comp plots
    if plot_type == 'indiv':
        fig = plt.figure(figsize=(16, 5))
        ncols = 4
        suffix = 'all'
    else:  # comp
        fig = plt.figure(figsize=(12, 5))
        ncols = 3
        suffix = 'syscmp'
    
    # Distinguish between level and zonal plots
    if zonal == 0:  # level
        pre = f'/stats_{title[coll][v]}_{suffix}_GLO_{lev}_{season}'
        if is_3d[coll]:  # 3d vars
            ending = f'{long[coll][v]}  Level: {lev} mb  Hour: {lead}'
        else:  # 2d vars
            if coll[:2] == 'de':
                ending = f'{long[coll][v]}  Level: 1000 mb  Hour: {lead}'
            elif coll[:2] == 'sl':
                ending = (f'{long[coll][v]}  Level: {lev_levs[coll][v]}m  '
                          f'Hour: {lead}')
            elif coll[:2] == 'ae':
                ending = (f'{long[coll][v]}  Level: surface  '
                          f'Hour: {lead}')
        gs = gridspec.GridSpec(5, ncols, figure=fig, hspace=0.0, 
                               height_ratios=[1, 0.05, 0.12, 1, 0.05])
    else:  # zonal
        pre = f'/stats_{title[coll][v]}_{suffix}_GLO_z_{season}'
        ending = f'{long[coll][v]}  Hour: {lead}'
        if zonal == 10: 
            pre = pre.replace('_z_', '_zlog10_')
        elif zonal == 1: 
            pre = pre.replace('_z_', '_zlog1_')
        gs = gridspec.GridSpec(5, ncols, figure=fig, hspace=0.375, 
                               height_ratios=[1, 0.067, 0.0, 1, 0.067])
    
    return pre, ending, gs, fig

def generate_masks(base_raw, comp_raw, v, sig_levs, dim):
    '''
    Generate significance mask(s) for comp plots from model/comp raw data, 
    variables index (v), significance level(s) as list (i.e., [0.95]), and 
    variable dimension (2d or 3d).
    '''
    
    # Initialize masks based on number of stats
    masks = [None] * nstats
    # Create mask for each stat
    for i in range(nstats):
        # Extract model data
        if dim == 3:
            model_data = base_raw[:,i,v,:,:,:]
            comp_data = comp_raw[:,i,v,:,:,:]
        else:  # dim == 2
            model_data = base_raw[:,i,v,:,:]
            comp_data = comp_raw[:,i,v,:,:]
        if dim == 3:
            nlevs = comp_data.shape[1]
            sig_masks = [np.zeros((nlevs, nlats, nlons), dtype=bool) 
                           for _ in range(len(sig_levs))]
        else:  # dim == 2
            sig_masks = [np.zeros((nlats, nlons), dtype=bool) 
                           for _ in range(len(sig_levs))]
        # Calculate differences
        mean_diff = np.mean(comp_data - model_data, axis=0)
        # Calculate variance of the differences
        var_diff = stats.tvar(comp_data - model_data, axis=0)
        # Calculate t-statistic
        numerator = mean_diff * np.sqrt(nfcsts - 1)
        denominator = np.sqrt(var_diff)
        t_values = np.divide(numerator, denominator, out=np.full_like(
            numerator, np.nan), where=denominator!=0)
        # Create mask for each significance level
        for s, sig in enumerate(sig_levs):
            # Calculate t-critical value (two-sided)
            t_crit = stats.t.ppf((1 + sig) / 2, nfcsts - 1)
            # Create significance mask (where |t| >= t_crit)
            sig_masks[s] = np.abs(t_values) >= t_crit
        masks[i] = sig_masks
    return masks

def create_filled_colorbar(cs, fig, cax, bounds, vmax, ticks_vis, 
                           is_contour=False):
    '''
    Create colorbar for filled plots.
    Parameters:
    - cs: contour or contourf object
    - fig: figure object
    - cax: colorbar subplot axis
    - bounds: contour level divisions
    - vmax: largest bound
    - ticks_vis: list of tick label values to display
    - is_contour: whether plot is contour (versus default contourf)
    Returns colorbar object
    '''
    
    # Create colorbar -- different for contour and contourf plots
    if is_contour:  # contour (lines only)
        norm = BoundaryNorm(boundaries=bounds, ncolors=cs.cmap.N)
        sm = ScalarMappable(norm=norm, cmap=cs.cmap)
        sm.set_array(np.ones((1, 1)))
        cbar = fig.colorbar(sm, cax=cax, orientation='horizontal', 
                           boundaries=bounds, drawedges=True)
    else:  # contourf (filled)
        cbar = fig.colorbar(cs, cax=cax, orientation='horizontal', 
                            drawedges=True)
    
    # Fix floating point precision for tick label values near zero
    for i in range(len(ticks_vis)):
        if abs(ticks_vis[i]) < 1e-10:
            ticks_vis[i] = 0.0
            
    # Format tick label number of digits after decimal based on vmax
    ticklabels = []
    for t in range(len(ticks_vis)):
        if t % 2 == 0:
            val = ticks_vis[int(t)]
            if vmax < 1:
                val_str = f'{val:.2f}'.replace('-0.', '-.').replace('0.', '.')
            elif vmax < 10: 
                val_str = f'{val:.1f}'
            else:
                val_str = f'{val:.0f}'
            ticklabels.append(val_str)
        else:
            ticklabels.append('')
            
    # Format colorbar ticks and tick labels
    cbar.ax.tick_params(size=2, bottom=True, labelbottom=True, labelsize=8)
    cbar.set_ticks(ticks_vis)
    cbar.set_ticklabels(ticklabels)
    cbar.ax.xaxis.set_tick_params(pad=2)
    return cbar

def create_empty_colorbar(fig, cax):
    '''
    Create white (empty) colorbar with only center 0 tick for empty plots.
    Parameters:
    - fig: figure object
    - cax: colorbar subplot axis
    Returns colorbar object
    ''' 
    norm = Normalize(vmin=-1, vmax=1)
    white_cmap = ListedColormap(['white'])
    sm = ScalarMappable(norm=norm, cmap=white_cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cax, orientation='horizontal', 
                       drawedges=True, ticks=[0])
    cbar.ax.tick_params(size=2, bottom=True, labelbottom=True, labelsize=8)
    cbar.set_ticklabels(['0'])
    cbar.ax.xaxis.set_tick_params(pad=2)
    return cbar

def setup_level_subplot(ax, data, masks=None):
    '''
    Assemble input components and format coastlines and ticks for an 
    individual subplot for level plots.
    Parameters:
    - ax: subplot axis
    - data: original data (without cyclic points)
    - masks: significance mask(s) for comp plots
    Returns x, y, and z ("data") arrays and mask(s) updated with cyclic points
    '''
    
    # Add cyclic points to data, lons, and mask(s) and make x/y arrays
    data, lons_cyclic = add_cyclic_point(data, coord=lons)
    if masks:
        masks_cyclic = [None] * len(masks)
        for s, sig in enumerate(masks):
            masks_cyclic[s], _ = add_cyclic_point(sig, coord=lons)
        masks = masks_cyclic
    x = lons_cyclic
    y = lats
    
    # Add coastlines and ticks / tick labels for both x- and y- axes
    ax.coastlines(linewidth=0.8, color='black')
    ax.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
    ax.set_xticklabels(['0', '60E', '120E', '180', '120W', '60W', '0'], 
                       fontsize=8)
    ax.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())
    ax.set_yticklabels(['90S', '60S', '30S', '0', '30N', '60N', '90N'], 
                       fontsize=8)
    
    return x, y, data, masks

def setup_zonal_subplot(ax, zonal, masks=None):
    '''
    Assemble input components and format ticks and y-axis for an individual 
    subplot for zonal plots.
    Parameters:
    - ax: subplot axis
    - zonal: top level (100, 10, or 1 where 10 or 1 imply log y-axis)
    - masks: significance mask(s) for comp plots
    Returns x and y arrays
    '''
    
    # Make x/y arrays
    x = lats
    y = levs
    
    # Set x-axis ticks / tick labels
    ax.set_xticks(np.arange(-90, 91, 30))
    ax.set_xticklabels(['90S', '60S', '30S', '0', '30N', '60N', '90N'], 
                       fontsize=8)
    
    # Format y-axis (inverted and regular or log) and set ticks / tick labels
    ax.invert_yaxis()
    if zonal == 100: 
        ax.set_ylim(1000, 100)
        ax.set_yticks(np.arange(1000, 99, -100))
        ax.set_yticklabels(['1000', '900', '800', '700', '600', '500', '400', 
                            '300', '200', '100'], fontsize=8)
    else:
        ax.set_yscale('log')
        if zonal == 10:
            ax.set_ylim(1000, 10)
            log_ticks = [10, 20, 30, 50, 70, 100, 200, 300, 500, 700, 1000]
            ax.set_yticks(log_ticks)
            ax.set_yticklabels([str(tick) for tick in log_ticks], fontsize=8) 
        if zonal == 1:
            ax.set_ylim(1000, 1)
            log_ticks = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
            ax.set_yticks(log_ticks)
            ax.set_yticklabels([str(tick) for tick in log_ticks], fontsize=8)
            
    return x, y

def plot_indiv(m, model, l, lead, v, var, z, lev, zonal, coll, cmax, cmin, 
               FCmax, MEmax, Rmax):
    '''
    Create a single individual plot for a given model (m, model),
    lead (l, lead), variable (v, var), and level (z, lev).
    Additional parameters:
    - zonal: 0 for level plots or top level (100, 10, or 1 where 10 or 1 
             imply log y-axis) for zonal plots
    - coll: collection variable is from
    - cmin/cmax: limits for contour line-only subplots
    - FCmax: max for Forecast-Climatology subplot
    - MEmax: max for Mean Error subplot
    - Rmax: max for RMS subplots
    Returns pre (filename prefix)
    '''
    
    # Extract data arrays
    base_avg = data['avg'][coll][m][l]
    base_glo = data['glo'][coll][m][l]
    
    # Setup plot metadata
    u = vars_unit_map.get(var.upper())
    pre, ending, gs, fig = setup_plot_metadata(coll, v, lev, zonal, lead, 
                                               'indiv')

    # Assemble plot data for each subplot
    if zonal == 0:  # level
        def slicer(i):
            '''Returns level slices of model data (raw, mean)'''
            if is_3d[coll]:  # 3d
                return [base_avg[i][v,z,:,:], base_glo[i][v,z]]
            else:  # 2d
                return [base_avg[i][v,:,:], base_glo[i][v]]
        # 0:F, 1:F-C, 2:ME, 3:ACORR 4:RMS, 5:RMS_bar, 6:RMS_amp, 7:RMS_phz
        z0, z1, z2, z3, z4, z5, z6, z7 = (slicer(i) for i in range(8))
        # Subplot components: title (with mean), z data array, colormap
        plot_data = [
            (f'Forecast: {z0[1]:.2f} {u}',                       z0[0], o),
            (f'Forecast-Climatology: {z1[1]:.2f} {u}',           z1[0], c), 
            (f'Mean Error (Forecast-Analysis): {z2[1]:.2f} {u}', z2[0], c), 
            (f'Anomaly Correlation: {z3[1]:.2f}',                z3[0], b),
            (f'Root Mean Square Error (F-A): {z4[1]:.2f}',       z4[0], r),
            (f'Root Bias Error (F-A): {z5[1]:.2f}',              z5[0], r),
            (f'Root Amplitude Error (F-A): {z6[1]:.2f}',         z6[0], r),
            (f'Root Phase Error (F-A): {z7[1]:.2f}',             z7[0], r)]

    else:  # zonal
        def slicer(i):
            '''Returns zonal slices of 3d model data (raw)'''
            return [np.nanmean(base_avg[i][v,:,:,:], axis=-1)]
        # 0:F, 1:F-C, 2:ME, 3:ACORR 4:RMS, 5:RMS_bar, 6:RMS_amp, 7:RMS_phz
        z0, z1, z2, z3, z4, z5, z6, z7 = (slicer(i) for i in range(8))
        # Subplot components: title, z data array, colormap
        plot_data = [
            (f'Forecast ({u})',                       z0[0], o),
            (f'Forecast-Climatology ({u})',           z1[0], c), 
            (f'Mean Error (Forecast-Analysis) ({u})', z2[0], c), 
            ('Anomaly Correlation',                   z3[0], b),
            ('Root Mean Square Error (F-A)',          z4[0], r),
            ('Root Bias Error (F-A)',                 z5[0], r),
            ('Root Amplitude Error (F-A)',            z6[0], r),
            ('Root Phase Error (F-A)',                z7[0], r)]
                
    # Create each subplot, looping through stats to be plotted
    for i, (title, zdata, cmap) in enumerate(plot_data):
        # Setup subplot axis and data to be plotted
        prow = (i // 4) * 3  # 0 for top row, 3 for bottom
        col = i % 4
        if zonal == 0:  # level
            ax = fig.add_subplot(gs[prow, col], projection=ccrs.PlateCarree())
            x, y, zdata, masks = setup_level_subplot(ax, zdata)
        else:  # zonal
            ax = fig.add_subplot(gs[prow, col])
            x, y = setup_zonal_subplot(ax, zonal)
        # Create colorbar axis
        cax = fig.add_subplot(gs[prow + 1, col])
    
        # Plot the data
        fill = False
        if i == 0:  # contour lines-only
            fill = True
            num_levels = 11
            vmax = cmax
            vmin = cmin
            bounds = nice_levels(vmin, vmax, num_levels, (num_levels + 1)/2)
            ticks_vis = bounds
            cs = ax.contour(x, y, zdata, levels=bounds, cmap=cmap, 
                            linewidths=0.8)
            # Format contour labels
            fmt = {}
            for n, level in enumerate(cs.levels):
                if n % 2 == 0:  # Every other level
                    fmt[level] = f'{level:.0f}'
                else:
                    fmt[level] = ''
            ax.clabel(cs, cs.levels[::2], inline=True, fmt=fmt, fontsize=6)
        else:  # contourf
            if i in [1, 2]:  # F-C and ME (diverging data)
                if np.nanmax(abs(zdata)) > 0:
                    fill = True
                    vmax = {1: FCmax, 2: MEmax}.get(i)
                    vmin = -vmax
                    offset = (vmax - vmin) / 20 / 2
                    bounds = np.linspace(vmin-offset, vmax+offset, 22)
                    ticks_vis = ((bounds[:-1] + bounds[1:]) / 2)
                    cs = ax.contourf(x, y, zdata, levels=bounds, cmap=cmap, 
                                     extend='both')
            elif i==3:  # ACORR
                fill = True
                zdata[zdata > 1] = 1
                vmax = 1
                bounds = np.linspace(0, vmax, 11)
                ticks_vis = bounds
                cs = ax.contourf(x, y, zdata, levels=bounds, cmap=cmap, 
                                 extend='min')
            else:  # RMS
                if np.nanmax(abs(z4[0])) > 0:
                    fill = True
                    vmax = Rmax
                    bounds = np.linspace(0, vmax, 11)
                    ticks_vis = bounds
                    cs = ax.contourf(x, y, zdata, levels=bounds, cmap=cmap, 
                                     extend='max')
        if fill:  # Add colorbar
            create_filled_colorbar(cs, fig, cax, bounds, vmax, ticks_vis, 
                                   is_contour=(i == 0))
        else:  # Add an empty colorbar if no non-zero data
            create_empty_colorbar(fig, cax)
        
        # Set title and subplot boundaries
        ax.set_title(title, fontsize=10)
        if zonal == 0: ax.set_global()
    
    # Add main title
    top_title = (f'{model.replace("_", " (")}-ver)  Forecasts Statistics '
                 f'({nfcsts})  {seas_yr}\n{ending}')
    plt.suptitle(top_title, fontsize=12, y=0.98)
    
    # Save plot
    if zonal == 0:
        plt.subplots_adjust(top=0.90)
    else:
        plt.subplots_adjust(top=0.857)
    plotnm = f'{pre}.10{l:02d}.png'
    print(plotnm)
    plt.savefig(f'{plotsdir[m]}{plotnm}', dpi=dpi, bbox_inches='tight')
    return pre

def plot_comp(m, model, l, lead, v, var, z, lev, zonal, coll, MEmax, Amax, 
              Rmax, masks):
    
    '''
    Create a single individual plot for a given model (m, model),
    lead (l, lead), variable (v, var), and level (z, lev).
    Additional parameters:
    - zonal: 0 for level plots or top level (100, 10, or 1 where 10 or 1 
             imply log y-axis) for zonal plots
    - coll: collection variable is from
    - MEmax: max for Mean Error subplot
    - Amax: max for ACORR subplot
    - Rmax: max for RMS subplots
    - Masks: significance mask(s)
    Returns pre (filename prefix)
    '''
    
    # Extract data arrays
    base_avg = data['avg'][coll][m][l]
    base_glo = data['glo'][coll][m][l]
    comp_avg = data['avg'][coll][0][l]
    comp_glo = data['glo'][coll][0][l]
    
    # Setup plot metadata  
    u = vars_unit_map.get(var.upper())
    pre, ending, gs, fig = setup_plot_metadata(coll, v, lev, zonal, lead, 
                                               'comp')
    
    # Assemble plot data for each subplot
    if zonal == 0:  # level
        def diff_slicer(i):
            '''Returns level slices of difference data (raw, mean, masks)'''
            if is_3d[coll]:  # 3d
                return [base_avg[i][v,z,:,:] - comp_avg[i][v,z,:,:], 
                        base_glo[i][v,z] - comp_glo[i][v,z], masks[i]]
            else:  # 2d
                return [base_avg[i][v,:,:] - comp_avg[i][v,:,:], 
                        base_glo[i][v] - comp_glo[i][v], masks[i]]
        # 0:ACORR, 1:ME, 2:RMS, 3:RMS_bar 4:RMS_amp, 5:RMS_phz
        z0, z1, z2, z3, z4, z5 = (diff_slicer(i) for i in range(6))
        # Subplot components: title (with mean), z data array, colormap, masks
        plot_data = [
            (f'Mean Error (Forecast-Analysis): {z0[1]:.2f} {u}', 
             z0[0], c, z0[2]), 
            (f'Anomaly Correlation: {z1[1]:.2f}',          z1[0], c, z1[2]),
            (f'Root Mean Square Error (F-A): {z2[1]:.2f}', z2[0], c, z2[2]),
            (f'Root Bias Error (F-A): {z3[1]:.2f}',        z3[0], c, z3[2]),
            (f'Root Amplitude Error (F-A): {z4[1]:.2f}',   z4[0], c, z4[2]),
            (f'Root Phase Error (F-A): {z5[1]:.2f}',       z5[0], c, z5[2])]
    else:  # zonal
        def diff_slicer(i):
            '''Returns zonal slices of 3d difference data (raw, masks)'''
            return [np.nanmean(base_avg[i][v,:,:,:] - comp_avg[i][v,:,:,:], 
                               axis=-1), np.nanmean(masks[i], axis=-1)]
        # 0:ACORR, 1:ME, 2:RMS, 3:RMS_bar 4:RMS_amp, 5:RMS_phz
        z0, z1, z2, z3, z4, z5 = (diff_slicer(i) for i in range(6))
        # Subplot components: title, z data array, colormap, masks
        plot_data = [
            (f'Mean Error (Forecast-Analysis) ({u})', z0[0], c, z0[1]), 
            ('Anomaly Correlation',                   z1[0], c, z1[1]),
            ('Root Mean Square Error (F-A)',          z2[0], c, z2[1]),
            ('Root Bias Error (F-A)',                 z3[0], c, z3[1]),
            ('Root Amplitude Error (F-A)',            z4[0], c, z4[1]),
            ('Root Phase Error (F-A)',                z5[0], c, z5[1])]
    # Create each subplot, looping through stats to be plotted
    for i, (title, zdata, cmap, masks) in enumerate(plot_data):
        # Setup subplot axis and data to be plotted
        prow = (i // 3) * 3  # 0 for top row, 3 for bottom
        col = i % 3
        if zonal == 0:  # level
            ax = fig.add_subplot(gs[prow, col], projection=ccrs.PlateCarree())
            x, y, zdata, masks = setup_level_subplot(ax, zdata, masks)
        else:  # zonal
            ax = fig.add_subplot(gs[prow, col])
            x, y = setup_zonal_subplot(ax, zonal, masks)
        # Create colorbar axis
        cax = fig.add_subplot(gs[prow + 1, col])

        # Plot the data
        fill = False  
        if i==0:  # ME
            if np.nanmax(abs(zdata)) > 0:  
                fill = True
                vmax = MEmax
        elif i==1:  # ACORR
            fill = True
            vmax = 0.5
            if vmax > 1: vmax = 1
        else:  # RMS
            if np.nanmax(abs(z2[0])) > 0:
                fill = True
                vmax = Rmax
        if fill:  # Only plot if non-zero data
            # Add contourf
            vmin = -vmax
            offset = (vmax - vmin) / 20 / 2
            bounds = np.linspace(vmin-offset, vmax+offset, 22)
            ticks_vis = ((bounds[:-1] + bounds[1:]) / 2)
            cs = ax.contourf(x, y, zdata, levels=bounds, cmap=cmap, 
                             extend='both')
            # Add significance contours
            for s, sig in enumerate(masks):
                ax.contour(x, y, sig.astype(int), levels=[0.5], 
                           colors='k', linestyles=styles[s], linewidths=0.2, 
                           alpha=0.5)
            # Add colorbar
            create_filled_colorbar(cs, fig, cax, bounds, vmax, ticks_vis)
        else:  # Add an empty colorbar if no non-zero data
            create_empty_colorbar(fig, cax)
                
        # Set title and subplot boundaries
        ax.set_title(title, fontsize=10)
        if zonal == 0: ax.set_global()
    
    # Add main title
    top_title = (f'{model.replace("_", " (")}-ver) - '
                 f'{models[0].replace("_", " (")}-ver)  Forecasts Statistics '
                 f'({nfcsts})  {seas_yr}\n{ending} (contours: >90% '
                 f'confidence)')
    plt.suptitle(top_title, fontsize=12, y=0.98)
    
    # Save plot
    if zonal == 0:  # level
        plt.subplots_adjust(top=0.90)
    else:  # zonal
        plt.subplots_adjust(top=0.857)
    plotnm = f'{pre}.10{l:02d}.png'
    print(plotnm)
    plt.savefig(f'{plotsdir[m-1]}{plotnm}', dpi=dpi, bbox_inches='tight')
    return pre

def extract_number(filename):
    '''Extract numeric suffix from filename like image_0042.gif'''
    match = re.search(r'(\d+)(?=\.gif$)', filename)
    return int(match.group()) if match else -1

def rename_animate(m, pre):
    '''
    Correct all filename extensions (from png to gif) and create animated gifs.
    Parameters:
    - m: model index
    - pre: filename prefix
    '''
    
    # Rename all .png files to .gif
    renamed_count = 0
    if 'syscmp' in pre: m = m-1 #comp
    for filename in os.listdir(plotsdir[m]):
        if filename.endswith('.png') and pre[1:] in filename:
            new_filename = f'{filename[:-4]}.gif'
            os.rename(os.path.join(plotsdir[m], filename), 
                      os.path.join(plotsdir[m], new_filename))
            renamed_count += 1
    print(f'{renamed_count} files renamed from .png to .gif')
    
    # Collect all lead time plots for filename prefix and create/save animation
    gif_files = [f for f in os.listdir(plotsdir[m]) 
             if f.endswith('.gif') and pre[1:] in f and f[-8:-4].isdigit()]
    gif_files.sort(key=extract_number)
    frames = [Image.open(os.path.join(plotsdir[m], f)).convert('RGB') 
              for f in gif_files]
    output_path = os.path.join(plotsdir[m], f'{pre[1:]}.gif')
    frames[0].save(output_path, save_all=True, 
                   append_images=frames[1:], duration=500, loop=1)
    print(f'made animation: {pre[1:]}.gif')

def get_limits_indiv(base, index_str, use_mean=False, axis=-1):
    '''
    Get appropriate limits for contour, F-C, Mean Error, and RMS subplots. 
    Parameters:
    - base: data array for model
    - index_str: string of indices to slice basefor appropriate variable
    - use_mean: defaults to False (for level plots); make True for zonal plots
    - axis: axis over which means are taken; defaults to -1 for level
    Returns: cmin/cmax (for contour line-only), FCmax, (for Fcst-Clim), 
             MEmax (for Mean Error), and Rmax (for RMS)
    '''
    
    # Establish slicing dims from index_str
    parts = [part.strip() for part in index_str.split(',')]
    dims = tuple(slice(None) if part == ':' else int(part) for part in parts)
    zdata = base[0][dims]  
    # Take mean over levels before calculating limits
    if use_mean:
        cmax, cmin = np.nanmax(np.nanmean(zdata, axis=axis)
                               ), np.nanmin(np.nanmean(zdata, axis=axis))
        FCmax, MEmax, Rmax = [round_down_max(np.nanmean(base[idx][dims], 
                                                        axis=axis)) 
                              for idx in [1, 2, 4]]
    # Calculate limits directly
    else:
        cmax, cmin = np.nanmax(zdata), np.nanmin(zdata)
        FCmax, MEmax, Rmax = [round_down_max(base[idx][dims]) 
                              for idx in [1, 2, 4]]
    return cmax, cmin, FCmax, MEmax, Rmax

def get_limits_comp(base, comp, index_str, use_mean=False, axis=-1):
    '''
    Get appropriate max limits for Mean Error, ACORR, and RMS subplots. 
    Parameters:
    - base and comp: data arrays for models
    - index_str: string of indices to slice base/comp for appropriate variable
    - use_mean: defaults to False (for level plots); make True for zonal plots
    - axis: axis over which means are taken; defaults to -1 for level
    Returns: MEmax (for Mean Error), Amax (for ACORR), and Rmax (for RMS)
    '''
    
    # Establish slicing dims from index_str
    parts = [part.strip() for part in index_str.split(',')]
    dims = tuple(slice(None) if part == ':' else int(part) for part in parts)
    if use_mean:  # Take mean over levels before calculating maxes
        MEmax, Amax, Rmax = [round_down_max(np.nanmean(base[idx][dims], 
                                                       axis=axis) 
                                            - np.nanmean(comp[idx][dims], 
                                                         axis=axis)) 
                             for idx in [2, 3, 4]]
    else: # Calculate maxes directly
        MEmax, Amax, Rmax = [round_down_max(base[idx][dims] - comp[idx][dims]) 
                             for idx in [2, 3, 4]]
    return MEmax, Amax, Rmax

def create_3d_plots(plot_type, m, model, leads, v, var, coll):
    '''
    Create zonal and level plots for a given plot_type (indiv or comp), 
    model (m, model), 3d variable (v, var), and collection (coll).
    '''
    
    plot_func = globals()[f'plot_{plot_type}']  # plot_indiv or plot_comp
    llimits = {}
    # Loop through leads
    for n, lead in enumerate(leads):
        if plot_type == 'indiv':
            if n == 0:  # Get limits once for zonal plots
                limits = get_limits_indiv(data['avg'][coll][m][-1, :], 
                                          f'{v},:,:,:', use_mean=True)
            # Establish arguments for plot_indiv() for zonal plots
            args = lambda lev: [m, model, n, lead, v, var, 0, 0, lev, coll, 
                                *limits]
        else:  # comp
            if n == 0:  # Get limits once for zonal plots
                limits = get_limits_comp(data['avg'][coll][m][-1, :], 
                                         data['avg'][coll][0][-1, :], 
                                         f'{v},:,:,:', use_mean=True)
            # Generate significance mask(s) for this lead
            masks = generate_masks(data['raw'][coll][m][:, n, :], 
                                   data['raw'][coll][0][:, n, :], 
                                   v, sig_levs, 3)
            # Establish arguments for plot_comp() for zonal plots
            args = lambda lev: [m, model, n, lead, v, var, 0, 0, lev, coll, 
                                *limits, masks]
        # Make zonal plots (regular and log) and create animations
        for lev in [100, 10, 1]:
            if lev == 100 or min(levs) <= lev:
                # Create plot
                pre = plot_func(*args(lev))
                plt.close('all')
                # Rename and animate plots if final lead
                if n == len(leads) - 1: rename_animate(m, pre)
        # Make level plots and create animations, looping through levels
        for l, lev in enumerate(levs):
            if plot_type == 'indiv':
                if n == 0: # Get limits for this level once
                    llimits[l] = get_limits_indiv(data['avg'][coll][m][-1, :], 
                                                  f'{v},{l},:,:', 
                                                  use_mean=True)
                # Establish arguments for plot_indiv() for this lead/level
                args = [m, model, n, lead, v, var, l, lev, 0, coll, 
                        *llimits[l]]
            else:  # comp
                if n == 0: # Get limits for this level once
                    llimits[l] = get_limits_comp(data['avg'][coll][m][-1, :], 
                                                 data['avg'][coll][0][-1, :], 
                                                 f'{v},{l},:,:')
                # Extract significance mask(s) for this level (created above)
                level_masks = [[array[l,:,:] for array in mask_list] 
                               for mask_list in masks]
                # Establish arguments for plot_comp() for this lead/level
                args = [m, model, n, lead, v, var, l, lev, 0, coll, 
                        *llimits[l], level_masks]
            # Create plot
            pre = plot_func(*args)
            plt.close('all')
            # Rename and animate plots if final lead
            if n == len(leads) - 1: rename_animate(m, pre)

def create_2d_plots(plot_type, m, model, leads, v, var, coll):
    '''
    Create level plots for a given plot_type (indiv or comp), model (m, model),
    2d variable (v, var), and collection (coll).
    '''
    
    plot_func = globals()[f'plot_{plot_type}']  # plot_indiv() or plot_comp()
    lev_nms = {'de2d': 1000,'sl2d': 2000, 'ae2d': 1000}
    # Make level plots and create animations, looping through leads
    for n, lead in enumerate(leads):
        if plot_type == 'indiv':
            if n == 0:  # Get limits once
                limits = get_limits_indiv(data['avg'][coll][m][-1], f'{v},:,:')
            # Establish arguments for plot_indiv()
            args = [m, model, n, lead, v, var, 0, lev_nms[coll], 0, coll, 
                    *limits]
        else:  # comp
            if n == 0:  # Get limits once
                limits = get_limits_comp(data['avg'][coll][m][-1, :], 
                                         data['avg'][coll][0][-1, :], 
                                         f'{v},:,:')
            # Generate significance mask(s) for this lead
            masks = generate_masks(data['raw'][coll][m][:, n, :], 
                                   data['raw'][coll][0][:, n, :], 
                                   v, sig_levs, 2)
            # Establish arguments for plot_comp()
            args = [m, model, n, lead, v, var, 0, lev_nms[coll], 0, coll, 
                    *limits, masks]
        # Create plot
        pre = plot_func(*args)
        plt.close('all')
    # Rename and animate plots
    rename_animate(m, pre)

# ================== MAIN SCRIPT: SETUP ==================

# Suppress warning for mean of empty slice
warnings.filterwarnings('ignore', message='.*Mean of empty slice.*', 
                        category=RuntimeWarning)

# Check for required cartopy coastline data
check_coastline_data()

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--config', default='plots.yaml', 
                    help='Configuration file (default: plots.yaml)')
parser.add_argument('--process', required=True,choices=['indiv', 'comp'], 
                    help='indiv or comp')
parser.add_argument('--part', required=False, help='split up plots by var')
parser.add_argument('--exp', required=False, help='index of experiment')
args = parser.parse_args()
config = args.config
exp = int(args.exp) if args.exp is not None else None
process = args.process
part = int(args.part) if args.part is not None else None

# Load and validate data
data = load_stats_data(config, exp, process, part)

# Collect Date/time info
date_nms = data['date_nms']
nfcsts = len(date_nms)
leads = data['leads']
nleads = len(leads)
fcst_length = data['fcst_length'] # days
fcst_interval = data['fcst_interval'] # hours

# Collect plot input info
nexps = len(data['fcst_names'])
fvars = data['fvars']
collections = data['collections']
is_3d = data['is_3d']
nvars = {coll: len(fvars[coll]) for coll in collections}
levs = data['levels']
nlevs = len(levs)
lats = data['lats']
nlats = len(lats)
lons = data['lons']
nlons = len(lons)
nstats = len(data['plot_stats'])

# Collect plot label info
x_vals = [x / 24 for x in leads]
xloc = x_vals[-1] + (x_vals[-1] * 0.05)
season = data['season']
year = data['year']
seas_yr = f'{season} {year}'
models = []
for m in range(nexps):
    models.append(f'{data["fcst_names"][m]}_{data["ana_names"][m]}')

# Collect variable metadata
(title, long, unit, lev_levs) = [{} for _ in range(4)]
for coll in collections:
    title[coll] = [vars_title_map.get(var.upper()) for var in fvars[coll]]
    long[coll] = [vars_long_map.get(var.upper()) for var in fvars[coll]]
    if coll[:2] == 'sl': 
        lev_levs[coll] = [re.search(r'\d+', s).group() for s in fvars[coll]]

# Setup dynamic colormap choice
colormap_choice = data.get('syscmp_colormap', 'custom_spectral')
if colormap_choice == 'bwr':
    c_cmap = plt.cm.bwr(np.linspace(0, 1, 21))
elif colormap_choice == 'RdBu_r':
    c_cmap = plt.cm.RdBu_r(np.linspace(0, 1, 21))
else:  # default
    c_cmap = [  # Custom spectral-like colormap
        (0.40, 0.00, 0.60),  # 0 vivid deep purple
        (0.30, 0.05, 0.78),  # 1 purple
        (0.17, 0.15, 0.95),  # 2 bright purple-blue
        (0.05, 0.40, 1.00),  # 3 bright blue
        (0.05, 0.65, 1.00),  # 4 cyan-blue
        (0.10, 0.80, 1.00),  # 5 cyan
        (0.30, 0.90, 1.00),  # 6 light cyan
        (0.60, 0.95, 1.00),  # 7 very light cyan
        (0.85, 0.98, 1.00),  # 8 near white cyan
        (0.95, 0.99, 1.00),  # 9 almost white cyan
        (1.00, 1.00, 1.00),  # 10 white
        (1.00, 1.00, 0.85),  # 11 pale yellow
        (1.00, 0.95, 0.60),  # 12 light yellow
        (1.00, 0.85, 0.30),  # 13 golden yellow
        (1.00, 0.70, 0.10),  # 14 bright orange
        (1.00, 0.55, 0.00),  # 15 orange
        (1.00, 0.40, 0.00),  # 16 red-orange
        (0.95, 0.25, 0.00),  # 17 strong red
        (0.80, 0.15, 0.00),  # 18 deep red
        (0.65, 0.05, 0.00),  # 19 very deep red
        (0.45, 0.00, 0.00),  # 20 darkest red (bold maroon)
    ]

# Define colormaps
c = mcolors.ListedColormap(c_cmap)       # full colormap
r = mcolors.ListedColormap(c_cmap[10:])  # red half of colormap
b = mcolors.ListedColormap(c_cmap[:11])  # blue half of colormap
o = mcolors.ListedColormap(c_cmap[1::2]) # every other element

# Collect plot saving info and make plots directory
dpi = data['plot_dpi']
output_dir = os.path.join(os.getcwd(), f'output/plots_{data["out_suffix"]}')
plotsdir = []
if process == 'indiv':
    for m in range(nexps):
        dir_nm = Path(f'{output_dir}/{models[m].replace("_", "-")}')
        dir_nm.mkdir(parents=True, exist_ok=True)
        plotsdir.append(f'{dir_nm}/')
        print(f'Created plots directory: {dir_nm}')
elif process == 'comp':
    for m in range(nexps)[1:]:
        dir_nm = Path(f'{output_dir}/{models[0].replace("_", "-")}.'
                      f'{models[m].replace("_", "-")}')
        dir_nm.mkdir(parents=True, exist_ok=True)
        plotsdir.append(f'{dir_nm}/')
        print(f'Created plots directory: {dir_nm}')

# ================== MAIN SCRIPT: PLOTTING ==================

# Make individual plots
if process == 'indiv':
    for m in range(nexps):
        for coll in collections:
            if is_3d[coll]:  # 3d vars
                for v, var in enumerate(fvars[coll]):
                    print(f'\nMaking plots for {models[m]} {var} (3D):')
                    create_3d_plots('indiv', m, models[m], leads, v, var, coll)
            else:  #2d vars
                for v, var in enumerate(fvars[coll]):
                    print(f'\nMaking plots for {models[m]} {var} (2D):')
                    create_2d_plots('indiv', m, models[m], leads, v, var, coll)
 
# Make comparison plots
if process == 'comp':
    for m in range(nexps)[1:]:
        for coll in collections:
            if is_3d[coll]: # 3d vars
                for v, var in enumerate(fvars[coll]):
                    print(f'\nMaking comp plots for {models[m]} vs '
                          f'{models[0]} {var} (3D):')
                    create_3d_plots('comp', m, models[m], leads, v, var, coll) 

            else: # 2d vars
                for v, var in enumerate(fvars[coll]):
                    print(f'\nMaking comp plots for {models[m]} vs '
                          f'{models[0]} {var} (2D):')
                    create_2d_plots('comp', m, models[m], leads, v, var, coll)
        
print('\nAll finished! :)')
