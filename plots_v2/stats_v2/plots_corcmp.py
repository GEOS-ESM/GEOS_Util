#!/usr/bin/env python3
'''
Creates corcmp plots (dieoff curve and individual/comparison zonal mean) and 
montages for regional statistics data.
'''

# ================== IMPORTS ==================

import argparse
import glob
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
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from adjustText import adjust_text
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
from scipy import stats
from typing import Any, Dict

# ================== PLOT CONFIGURATION ==================

# Plot colors for each model (in level plots)
colors = ['black',   # black
          '#0072B2', # blue
          '#E69F00', # orange
          '#009E73', # bluish green
          '#CC79A7', # reddish purple
          '#F0E442', # yellow
          '#D55E00', # vermillion
          '#56B4E9', # sky blue
          '#8B0000', # dark red
          '#228B22'] # forest green

# Variables metadata
vars_title_map = {'H': 'hght', 'U': 'uwnd', 'V': 'vwnd', 'T': 'tmpu', 
                  'Q': 'sphu', 'P': 'slp', 'PS': 'sfcp', 'Q2M': 'sphu', 
                  'T2M': 'tmpu', 'U10M': 'uwnd', 'V10M': 'vwnd', 'D2M': 'dwpt',
                  'AOD': 'aod', 'LOGAOD': 'lnaod', 'PM25': 'pm25'}
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

# 3d variables min/max magnitude for zonal RMS plots
vars_range_map = {'H': 4, 'U': 0.4, 'V': 0.4, 'T': 0.2, 'Q': 0.1}  

# Regions metadata
region_short_map = {'GLO': 'global',  'NHE': 'n.hem',   'TRO': 'tropics',
                    'SHE': 's.hem',   'NWQ': 'nw.quad', 'NEQ': 'ne.quad',
                    'SWQ': 'sw.quad', 'SEQ': 'se.quad', 'NAM': 'america',
                    'EUR': 'europe',  'NPO': 'npolar',  'SPO': 'spolar',
                    'XPO': 'xpolar',  'CUS': 'conus',   'LND': 'glob_l',
                    'NHL': 'n.hem_l', 'TRL': 'trop_l',  'SHL': 's.hem_l'}
region_long_map = {
    'GLO': 'Global',
    'NHE': 'N.Hem. ExtraTropics (Lats: 20,80)',
    'TRO': 'Tropics (Lats: -20,20)',
    'SHE': 'S.Hem. ExtraTropics (Lats: -20,-80)',
    'NWQ': 'N.W. Quadrant (Lons:-180,0  Lats: 0, 90)',
    'NEQ': 'N.E. Quadrant (Lons: 0,180  Lats: 0, 90)',
    'SWQ': 'S.W. Quadrant (Lons:-180,0  Lats: 0,-90)',
    'SEQ': 'S.E. Quadrant (Lons: 0,180  Lats: 0,-90)',
    'NAM': 'North America (Lons:-140,-60  Lats: 20,60)',
    'EUR': 'Europe (Lons:-10,30  Lats: 30,60)',
    'NPO': 'N.Polar (Lats: 60,90)',
    'SPO': 'S.Polar (Lats:-90,-60)',
    'XPO': 'X.Polar (Lats: -60,60)',
    'CUS': 'Continental United States',
    'LND': 'Global Land-only',
    'NHL': 'N.Hem. ExtraTropics (Lats: 20,80) Land-only',
    'TRL': 'Tropics (Lats: -20,20) Land-only',
    'SHL': 'S.Hem. ExtraTropics (Lats: -20,-80) Land-only'
}

# ================== UTILITY FUNCTIONS ==================

def load_stats_data(yaml_file: str, process: str, part: int
                    ) -> Dict[str, Any]:
    '''
    Load statistics data from files specified in the YAML configuration.
    Validates that all requested init dates, leads, variables, levels, regions,
    and statistics exist for each experiment file.
    Parameters (come directly from script arguments):
    - yaml_file: YAML config file (full path)
    - process: 'plot' (level/zonal plots) or 'mont' (stats/regions montages)
    - part: integer selecting region from requested list (0 for first)
    Returns a dictionary containing statistics data and configuration:
        - 'raw': Nested dict [coll][exp][region] of raw statistics arrays
        - 'avg': Nested dict [coll][exp][region] of avg statistics arrays
        - 'date_nms': List of initialization dates as strings ('%Y%m%d')
        - 'leads': List of lead time hours
        - 'fcst_names': List of forecast model names
        - 'ana_names':  List of analysis model names
        - 'clim_names': List of climatology model names
        - 'fcst_length': Forecast length in days
        - 'fcst_interval': Forecast interval in hours
        - 'fvars': Dict of variable lists by collection
        - 'levels': List of pressure levels
        - 'regions': List of region names
        - 'collections': List of non-empty collection names
        - 'is_3d': Dict mapping collections to dim (3d or not) 
        - 'plot_stats': List of statistics to be plotted
        - 'season': Season string
        - 'year': Year integer
        - 'plot_dpi': Plot DPI setting
        - 'out_suffix': suffix for plots directory name
        - 'plot_RMS_decomp': Boolean for RMS decomposition
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
    required_params = ['regions', 'season', 'year']
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
    exp_file_lists = []
    exp_idx = 0
    while f'cor_exp{exp_idx}' in params:
        file_spec = params[f'cor_exp{exp_idx}']
        file_list = parse_file_specification(file_spec)
        file_list = sorted(set(file_list))
        missing_files = []
        for file_path in file_list:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        if missing_files:
            sys.exit(f'ERROR: Files not found for cor_exp{exp_idx}:\n' + 
                     '\n'.join(f'  {f}' for f in missing_files))
        exp_file_lists.append(file_list)
        exp_idx += 1
    # Check for required specifications
    if len(exp_file_lists) < 2:
        sys.exit('ERROR: At least exp0 and exp1 must be specified in config')
    if len(exp_file_lists) > 9:
        sys.exit('ERROR: Only 10 experiments (up to exp9) are supported for '
                 'plotting')
    
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
    
    # Initialize exclusion tracking
    experiment_excluded_dates = []  # Sets of excluded dates per experiment
    experiment_exclusion_counts = []  # File counts per experiment
    experiment_valid_dates = []  # Valid dates after initial merging/filtering

    # Set defaults for optional parameters
    plot_dpi = params.get('plot_dpi', 300)
    out_suffix = params.get('suffix', '')
    plot_RMS_decomp = params.get('plot_RMS_decomp', True)
    
    # Define statistics to plot based on RMS decomposition setting
    if plot_RMS_decomp:
        plot_stats = [
            'acorr', 'rms', 'rms_ran', 'rms_bar', 'rms_amp', 'rms_phz']  
    else:
        plot_stats = ['acorr', 'rms']  

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
                 '3d_vars_default, 2d_vars_default, 2d_vars_slices, or '
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
                    
    # Get requested regions and levels
    requested_regions = params.get('regions', [])
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
        '''Merge multiple files for a single experiment'''
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
                    
        if len(datasets) > 1:  # Multiple files
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
            
            # Separate non-avg variables by presence of init_date dimension
            first_ds = datasets[0]
            vars_with_init_date = []
            vars_without_init_date = []
            
            for var_name in first_ds.data_vars:
                if var_name.endswith('_avg'):
                    continue  # Skip _avg variables entirely
                elif 'init_date' in first_ds[var_name].dims:
                    vars_with_init_date.append(var_name)
                else:
                    vars_without_init_date.append(var_name)
            
            # Merge variables with init_date dimension (regular concatenation)
            ds_with_init = xr.concat([ds[vars_with_init_date] 
                                      for ds in datasets], 
                                    dim='init_date').sortby('init_date')
            
            # For non-avg variables without init_date, take from first dataset
            ds_without_init = first_ds[vars_without_init_date]
            
            # Combine everything back together
            merged_ds = xr.merge([ds_with_init, ds_without_init])
            
            # Close individual datasets
            for ds in datasets:
                ds.close()
                
        else: # Single file case - skip merge operations
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
            # Files should be as: stats_regional_FCST_ANA_CLIM_[dates]_[suffix]
            if len(parts) < 6 or parts[0] != 'stats' or parts[1] != 'regional':
                sys.exit(f'ERROR: File format not recognized: {basename}\n'
                         f'Expected: '
                         f'stats_regional_FCST_ANA_CLIM_[dates]_[suffix]')
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
    
    # Extract timing parameters for compatibility checking
    exp_lens = []
    exp_ints = []
    exp_spcs = []
    for i, file_list in enumerate(exp_file_lists):
        basename = os.path.basename(file_list[0])
        len_match = re.search(r'len(\d+)', basename)
        int_match = re.search(r'int(\d+)', basename)
        spc_match = re.search(r'spc(\d+)', basename)
        exp_lens.append(int(len_match.group(1)) if len_match else None)
        exp_ints.append(int(int_match.group(1)) if int_match else None)
        # Default to spc1d if no spacing found (single-forecast files)
        exp_spcs.append(int(spc_match.group(1)) if spc_match else 1)
        
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
        ds_exp0 = xr.open_dataset(exp_file_lists[0][0]) # First file
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
        all_init_dates = []
        for f in exp_file_lists[0]:
            ds = xr.open_dataset(f)
            all_init_dates.extend(ds.init_date.values)
            ds.close()
        # Remove duplicates and sort
        unique_dates = sorted(list(set(all_init_dates)))
        requested_dates = [d.astype('datetime64[us]').astype(
            datetime).strftime('%Y%m%d') for d in unique_dates]
        # Deduce spacing from exp0 for compatibility checks
        if not fcst_spacing:
            fcst_spacing = exp_spcs[0]
    
    if ds_exp0: ds_exp0.close()
    
    print(f'Using timing parameters: fcst_length={fcst_length}d, '
      f'fcst_interval={fcst_interval}h, fcst_spacing={fcst_spacing}d')

    # Check timing parameter compatibility against requested parameters
    timing_issues = []
    for i in range(len(exp_file_lists)):
        if exp_lens[i] < fcst_length:
            timing_issues.append(f'  exp{i}: Shorter forecast length '
                                 f'({exp_lens[i]}d < {fcst_length}d)')
        if exp_ints[i] > fcst_interval:
            timing_issues.append(f'  exp{i}: Coarser forecast interval '
                                 f'({exp_ints[i]}h > {fcst_interval}h)')
        if exp_spcs[i] > fcst_spacing:
            timing_issues.append(f'  exp{i}: Coarser forecast spacing '
                                 f'({exp_spcs[i]}d > {fcst_spacing}d)')
    
    if timing_issues:
        issues = '\n'.join(timing_issues)
        sys.exit(f'ERROR: Incompatible timing parameters found:\n'
                 f'{issues}\nExperiments must have equal or longer length, '
                 f'equal or finer interval, and equal or finer spacing than '
                 f'requested parameters.'
        )
    
    # Check if all parameters match requested values
    all_match = all(
        exp_lens[i] == fcst_length and
        exp_ints[i] == fcst_interval and
        exp_spcs[i] == fcst_spacing
        for i in range(len(exp_file_lists))
    )
    
    if all_match:
        print('Timing validation: All experiments match requested parameters')
    else:
        print('Timing validation: Compatible with requested parameters:')
        for i in range(len(exp_file_lists)):
            if (exp_lens[i] != fcst_length or exp_ints[i] != fcst_interval 
                or exp_spcs[i] != fcst_spacing):
                print(f'  exp{i}: len{exp_lens[i]}d_int{exp_ints[i]}h_spc'
                      f'{exp_spcs[i]}d')
    
    data = {}
    if process == 'plot': 
    
        # Initialize output structures
        data = {
            'raw': {},  # Will be indexed by [collection][exp_idx][region]
            'avg': {},  # Will be indexed by [collection][exp_idx][region]
        }
        
        # Print requested parameters
        print('\n=== Requested Parameters ===')
        print('Variables by collection:')
        for collection in collections:
            print(f'  {collection}: {fvars[collection]}')
        print(f'Levels: {requested_levels}')
        print(f'Regions: {requested_regions}')
        print(f'Stats to be Plotted: {plot_stats}')
        print(f'Season: {params["season"]}')
        print(f'Year: {params["year"]}')
        print(f'Plot DPI: {plot_dpi}')
        print(f'RMS Decomposition: {plot_RMS_decomp}')
        dates_listing = ', '.join(requested_dates[:5] + (
            ['...'] if len(requested_dates) > 5 else []))
        print(f'Requested Dates ({len(requested_dates)}): [{dates_listing}]')
        print('============================\n')
        
        # Initialize data structure for all collections
        for coll in collections:
            data['raw'][coll] = {}
            data['avg'][coll] = {}
        
        # Process part filtering by region
        if part is not None:
            requested_regions = [requested_regions[part]]
            print(f'Processing region part {part}: {requested_regions}')
        
        # Process each experiment file list
        for exp_idx, file_list in enumerate(exp_file_lists):
            print(f'\n=== Experiment {exp_idx}: {fcst_names[exp_idx]}(F) / '
                  f'{ana_names[exp_idx]}(A) / {clim_names[exp_idx]}(C) ===')
            
            # Handle single vs multiple files
            if len(file_list) == 1:
                basename = os.path.basename(file_list[0])
                print(f'Loading {basename}...')
                ds, excluded_dates_set, exclusion_count = (
                    merge_experiment_files(file_list, f'exp{exp_idx}'))
            else:
                ds, excluded_dates_set, exclusion_count = (
                    merge_experiment_files(file_list, f'exp{exp_idx}'))
                basename = os.path.basename(file_list[0])
            
            # Store exclusion data for this experiment
            experiment_excluded_dates.append(excluded_dates_set)
            experiment_exclusion_counts.append(exclusion_count)      
    
            # Extract coordinates
            available_levels = [int(x) for x in ds.lev.values.tolist()]
            available_regions = (ds.region.values.tolist() 
                                 if 'region' in ds.coords else [])
            available_leads = ([int(x) for x in ds.lead.values.tolist()] 
                               if 'lead' in ds.coords else [])
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
            
            # Date validation: check if missing dates are in exclusions
            missing_dates = set(requested_dates) - set(available_date_nms)
            if missing_dates:
                # Check if all missing dates are in experiment's exclusion set
                missing_and_not_excluded = missing_dates - excluded_dates_set
                if missing_and_not_excluded:
                    missing_strs = [str(d) for d in 
                                    sorted(missing_and_not_excluded)]
                    ds.close()
                    sys.exit(f'ERROR: exp{exp_idx} is missing required dates '
                             f'that are not excluded:\n'
                             f'  Missing non-excluded dates: '
                             f'{missing_strs[:10]}'
                             f'{"..." if len(missing_strs) > 10 else ""}\n'
                             f'  Total missing and not excluded: '
                             f'{len(missing_and_not_excluded)}/'
                             f'{len(requested_dates)} dates')
                else:
                    print(f'  Note: {len(missing_dates)} requested dates are '
                          f'missing but in exclusion list')
            
            # Filter dataset to only include requested dates (remove extras)
            available_requested = sorted(list(set(available_date_nms) 
                                              & set(requested_dates)))
            original_date_count = len(available_date_nms)
            date_indices = [available_date_nms.index(date) 
                            for date in available_requested]
            ds = ds.isel(init_date=date_indices)
            print(f'Date validation: {original_date_count} → '
                  f'{len(available_requested)} dates (after removing extras)')
            
            # Track the valid dates for this experiment
            experiment_valid_dates.append(available_requested)
            
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
            
            # Validation: check for requested variables/levels/regions/stats
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
                # Only process raw statistics (skip _avg variables)
                if var_name.endswith('_avg'):
                    continue  # Skip pre-computed averages
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
            
            # Check if all requested regions are available
            missing_regions = []
            for region in requested_regions:
                if region not in available_regions:
                    missing_regions.append(region)
            
            # Check if all plot statistics are available
            missing_stats = []
            for stat in plot_stats:
                if stat not in available_stats:
                    missing_stats.append(stat)
            
            # If anything is missing, exit with error
            if (missing_vars or missing_levels or missing_regions 
                or missing_stats):
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
                if missing_regions:
                    error_msg += f'  Missing regions: {missing_regions}\n'
                    error_msg += f'  Available regions: {available_regions}\n'
                if missing_stats:
                    error_msg += f'  Missing statistics: {missing_stats}\n'
                    error_msg += (f'  Available statistics: '
                                  f'{sorted(available_stats)}\n')
                sys.exit(error_msg)
            
            # Initialize data structures for this experiment
            for coll in collections:
                data['raw'][coll][exp_idx] = {}
                data['avg'][coll][exp_idx] = {}
            
            print('Loading raw data...')
            # Now load and restructure the data for each collection and region
            for coll in collections:
                n_vars = len(fvars[coll])
                n_stats = len(plot_stats)
                n_init_dates = len(available_requested)
                n_leads = len(expected_leads)
                
                # Check if 3D collection by examining the collection name
                n_levels = len(requested_levels) if is_3d[coll] else None
                
                # Process each region
                for region in requested_regions:
                    reg_idx = available_regions.index(region)
                    if is_3d[coll]:
                        # 3D data ([init_date], lead, stat, var, lev)
                        raw_array = np.zeros((n_init_dates, n_leads, n_stats, 
                                              n_vars, n_levels))
                        avg_array = np.zeros((n_leads, n_stats, n_vars, 
                                              n_levels))
                    else:
                        # 2D data ([init_date], lead, stat, var)
                        raw_array = np.zeros((n_init_dates, n_leads, n_stats, 
                                              n_vars))
                        avg_array = np.zeros((n_leads, n_stats, n_vars))
                        
                    # Fill raw array with data
                    for var_idx, var in enumerate(fvars[coll]):
                        for stat_idx, stat in enumerate(plot_stats):
                            # raw_data shape: (init_date, lead, [lev,] region)
                            raw_data = ds[f'{var}_{stat}'].values 
                            if is_3d[coll]:
                                raw_array[:, :, stat_idx, var_idx, :] = raw_data[:, :, :, reg_idx]
                            else:
                                raw_array[:, :, stat_idx, var_idx] = raw_data[:, :, reg_idx]
                    # Store raw_array in data structure
                    data['raw'][coll][exp_idx][region] = raw_array
                    # Store avg_array as placholder (still zeros) 
                    data['avg'][coll][exp_idx][region] = avg_array
            
            print('Status: All requested variables, statistics, levels, '
                  'regions, and dates found and loaded')
            print(f'Data: {len(requested_dates)} init dates, '
                  f'{len(available_leads)} lead times')
            
            # Close the dataset
            ds.close()

        # Calculate union of all exclusions across experiments
        all_excluded_dates = set()
        for excluded_set in experiment_excluded_dates:
            all_excluded_dates.update(excluded_set)
        
        # Check if all experiments have identical valid dates
        if all(set(exp_dates) == set(experiment_valid_dates[0]) 
               for exp_dates in experiment_valid_dates):
        # No filtering of arrays: all experiments have same dates
            if all_excluded_dates:
                # Same dates but have exclusions: update requested_dates
                print(f'Found exclusions across experiments: '
                      f'{sorted(all_excluded_dates)}')
                original_count = len(requested_dates)
                requested_dates = [date for date in requested_dates 
                                   if date not in all_excluded_dates]
                print(f'Applied exclusions: {original_count} → '
                      f'{len(requested_dates)} dates')
        else:
        # Not all have same dates: find common and filter arrays
            print(f'Found exclusions across experiments: '
                  f'{sorted(all_excluded_dates)}')
            # Find intersection of all valid dates, minus global exclusions
            common_dates = set(experiment_valid_dates[0])
            for exp_dates in experiment_valid_dates[1:]:
                common_dates &= set(exp_dates)
            common_dates -= all_excluded_dates
            requested_dates = sorted(list(common_dates))
            print(f'Common dates after filtering: {len(requested_dates)}')

            # Filter raw arrays to common dates
            print('Filtering raw arrays to common dates...')
            for coll in collections:
                for exp_idx in range(len(exp_file_lists)):
                    # Create mapping from common dates to this experiment
                    exp_dates = experiment_valid_dates[exp_idx]
                    date_indices = []
                    for common_date in requested_dates:  
                        date_indices.append(exp_dates.index(common_date))
                    # Replace raw arrays with filtered arrays
                    for region in requested_regions:
                        raw_array = data['raw'][coll][exp_idx][region]
                        filtered_array = raw_array[date_indices, :]
                        data['raw'][coll][exp_idx][region] = filtered_array
        
        print('Computing averages...')
        # Compute and store averages from (filtered) raw arrays
        for coll in collections:
            for exp_idx in range(len(exp_file_lists)):
                for region in requested_regions:
                    raw_array = data['raw'][coll][exp_idx][region]
                    avg_array = np.mean(raw_array, axis=0)
                    data['avg'][coll][exp_idx][region] = avg_array
        
        # Show array shapes for verification
        print('Final array shapes after computing averages:')
        for coll in collections:
            raw_shape = data['raw'][coll][0][requested_regions[0]].shape
            avg_shape = data['avg'][coll][0][requested_regions[0]].shape
            if is_3d[coll]:
                print(f'{coll}: avg {avg_shape} [nleads, nstats, nvars, '
                      f'nlevs]\n'
                      f'      raw {raw_shape} [nfcsts, nleads, nstats, '
                      f'nvars, nlevs]')
            else: 
                print(f'{coll}: avg {avg_shape} [nleads, nstats, nvars]\n'
                      f'      raw {raw_shape} [nfcsts, nleads, nstats, '
                      f'nvars]')
    
    # Save all metadata in output structure
        data['date_nms'] = requested_dates
        data['leads'] = expected_leads
    # Apply forecast name overrides if specified in YAML
    for exp_idx in range(len(fcst_names)):
        override_key = f'fcst_exp{exp_idx}'
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
    data['regions'] = requested_regions
    data['collections'] = collections
    data['is_3d'] = is_3d
    data['plot_stats'] = plot_stats
    data['season'] = params['season']
    data['year'] = params['year']
    data['plot_dpi'] = plot_dpi
    data['out_suffix'] = out_suffix
    data['plot_RMS_decomp'] = plot_RMS_decomp
    data['colormap'] = params.get('corcmp_colormap', 'bwr')
    
    return data

def plot_rectangle(ax, i, x_vals, cil, ciu, color, width):
    '''
    Plot confidence interval rectangle
    Parameters:
    - ax: subplot axis
    - i: leads index
    - x-vals: x-data (leads) values
    - cil, ciu: lower and upper confidence interval values
    - color, width: rectangle border color and width
    '''
    
    rect = Rectangle((x_vals[i]-width/2, cil[i]), width, abs(cil[i]) + ciu[i],
                     fill=False, edgecolor=color, linestyle='-', linewidth=0.8)
    ax.add_patch(rect)
    
def plot_lev(s, reg, coll, v, var, z, lev):
    '''
    Create a level plot for a given stat (s), region (reg), collection (coll),
    variable (v, var), and level (z, lev).
    '''
    
    # Create figure with upper and lower axes and labels
    fig = plt.figure(figsize=(8, 6))   
    axu = fig.add_axes([0.205, 0.417, 0.678, 0.466])
    axl = fig.add_axes([0.205, 0.117, 0.678, 0.300])
    axu.set_ylabel(stat_lbls[s])
    axl.set_ylabel('Difference')
    textsu, textsl = [], []
    
    # For RMS components, also plot total RMS in light grey
    if s > 1:  
        if is_3d[coll]:  # 3d
            rms_vals = data['avg'][coll][0][reg][:, 1, v, z]
        else:  # 2d
            rms_vals = data['avg'][coll][0][reg][:, 1, v]
        axu.plot(x_vals, rms_vals, label = f'{models[0]} RMS_tot', 
                 color='lightgrey', linestyle='-', linewidth=1.5)
        final = rms_vals[-1]
        txt = axu.text(xloc, final, f'{final:.4f}', color='lightgrey', 
                       fontsize=8, ha='left', va='center')
        textsu.append(txt)
    
    # Plot data for each model
    for m, model in enumerate(models):
        
        # Plot dieoff curve with final value text in upper panel
        if is_3d[coll]:  # 3d
            y_vals = data['avg'][coll][m][reg][:, s, v, z]
        else:  # 2d
            y_vals = data['avg'][coll][m][reg][:, s, v]
        axu.plot(x_vals, y_vals, label = f'{model.replace("_", " (")}-ver)', 
                 color=colors[m], linestyle='-', linewidth=1.5)
        final = y_vals[-1]
        txt = axu.text(xloc, final, f'{final:.4f}', color=colors[m], 
                       fontsize=8, ha='left', va='center')
        textsu.append(txt)
        
        # If control, plot 0 line in lower panel
        if m == 0:
            ctl_vals = y_vals
            axl.axhline(y=0, color='k', linestyle='-')
            
        # If non-control, plot model difference from control in lower panel
        else:
            # Plot difference with final value text in lower panel
            y_diff_vals = y_vals - ctl_vals
            axl.plot(x_vals, y_diff_vals, label=model, color=colors[m], 
                     marker='o', markersize=5, linestyle='-', linewidth=1.5)
            final = y_diff_vals[-1]
            txt = axl.text(xloc, final, f'{final:.4f}', color=colors[m], 
                           fontsize=8, ha='left', va='center')
            textsl.append(txt)
            
            # Plot confidence intervals in lower panel
            cil_vals, ciu_vals = [{} for _ in range(2)]
            for conf in conf_levels:
                if is_3d[coll]:  # 3d
                    cil_vals[conf] = cil[conf][coll][m][:, s, v, z]
                    ciu_vals[conf] = ciu[conf][coll][m][:, s, v, z]
                else:  # 2d
                    cil_vals[conf] = cil[conf][coll][m][:, s, v]
                    ciu_vals[conf] = ciu[conf][coll][m][:, s, v]
            base_width = fcst_interval/24.
            for i in range(nleads):
                # For 2 models: rectangles (68%, 90%, 95%) and errorbar (99%)
                if len(models) == 2:
                    rect_colors = ['lawngreen', 'tomato', 'deepskyblue']
                    width_factors = [0.9, 0.7, 0.5]
                    for c, conf in enumerate(conf_levels[:3]):  # 
                        plot_rectangle(axl, i, x_vals, cil_vals[conf], 
                                         ciu_vals[conf],rect_colors[c], 
                                         width_factors[c]*base_width)
                    axl.errorbar(x_vals, np.zeros(len(x_vals)), fmt='none', 
                                 yerr=[abs(cil_vals[conf_levels[3]]), 
                                       abs(ciu_vals[conf_levels[3]])], 
                                 linewidth=0.5, capthick=0.5, ecolor='black', 
                                 capsize=3)
                # For 3 or more models: single rectangle in model's color
                else:
                    plot_rectangle(axl, i, x_vals, cil_vals[conf_levels[2]], 
                                    ciu_vals[conf_levels[2]], colors[m], 
                                    0.9*base_width)
        
    # Plot synoptic confidence intervals (95%) as dashed lines in upper panel
    if is_3d[coll]:  #3d 
        cisynl_vals = cisynl[coll][:, s, v, z]
        cisynu_vals = cisynu[coll][:, s, v, z]
    else:  #2d
        cisynl_vals = cisynl[coll][:, s, v]
        cisynu_vals = cisynu[coll][:, s, v]
    ymin, ymax = axu.get_ylim()  # Save auto limits before adding CI's
    axu.plot(x_vals, cisynl_vals, color=colors[0], linestyle='--', 
             linewidth=1.0)
    axu.plot(x_vals, cisynu_vals, color=colors[0], linestyle='--', 
             linewidth=1.0)
    
    # Format upper panel ticks, grid, and limits
    axu.set_xticks(np.arange(0, fcst_length + 0.1, 0.5))
    axu.tick_params(axis='x', labelbottom=False)
    axu.tick_params(axis='y', labelsize=8, pad=2, length=2)
    axu.spines['bottom'].set_visible(False)
    formatter = mticker.FormatStrFormatter('%.1f')
    axu.xaxis.set_major_formatter(formatter)
    axu.grid(True, which='both', axis='both', color='lightgrey', 
             linestyle='--', linewidth=0.5)
    axu.set_xlim(0, fcst_length)
    if s == 0:  # ACORR: pre-CI automatic min but max 1
        axu.set_ylim(ymin, 1.0)
    else:  # RMS: pre-CI automatic limits
        axu.set_ylim(ymin, ymax)

    # Add title and region/variable/season/year texts
    u = vars_unit_map.get(var.upper())
    region = region_long_map.get(reg)
    if coll[:2] == 'de':
        axu.set_title(f'Forecasts Statistics ({nfcsts}) \n{lev}-mb '
                      f'{long[coll][v]} ({u}) {region}', fontsize=12)
    elif coll[:2] == 'sl' or coll[:2] == 'ae':
        axu.set_title(f'Forecasts Statistics ({nfcsts}) \n'
                      f'{long[coll][v]} ({u}) {region}', fontsize=12) 
    axu.text(-0.2, 1.1, f'{reg}\n{var}', transform=axu.transAxes,
                  fontsize=14, va='center', ha='left')
    axu.text(-0.2, 0.1, seas_yr, transform=axu.transAxes,
                  fontsize=12, va='center', ha='center', rotation = 90)
    
    # Format lower panel ticks, grid, and limits
    axl.set_xticks(np.arange(0, fcst_length + 0.1, 0.5))
    axl.set_xlim(0, fcst_length)
    axl.set_xlabel('Forecast Day', fontsize=10, labelpad=3)
    axl.tick_params(axis='both', labelsize=8, pad=2, length=2)
    axl.grid(True, which='both', axis='both', color='lightgrey', 
             linestyle='--', linewidth=0.5)
    
    # Add main legend (including RMS total line when applicable)
    handles, leg_labels = axu.get_legend_handles_labels()
    if s > 1:
        handles = handles[1:] + handles[:1]
        leg_labels = leg_labels[1:] + leg_labels[:1]
    main_legend = axl.legend(handles, leg_labels, fontsize=8, labelspacing=0.4, 
                             handlelength=2, handletextpad=0.5, 
                             loc='upper center', bbox_to_anchor=(0.5, -0.15), 
                             ncol=4, frameon=False)
    
    # If only 2 models, add CI legend for the lower plot
    if len(models) == 2:
        legend_elements = []
        # Add rectangles for first 3 significance levels (68%, 90%, 95%)
        for i in range(3):
            legend_elements.append(
                Rectangle((0,0), 0.6, 0.4, facecolor=rect_colors[i], 
                          label=f'{int(conf_levels[i]*100)}% CI'))
        # Add error bar for 4th confidence level (99%)
        legend_elements.append(Line2D([0], [0], color='black', linewidth=0.5,
                                    marker='_', markersize=6, 
                                    label=f'{int(conf_levels[3]*100)}% CI'))
        # Add legend (must add artists for both for visibility)
        ci_legend = axl.legend(handles=legend_elements, loc='lower left', 
                               fontsize=6, handlelength=1, handleheight=0.2, 
                               handletextpad=0.3, columnspacing=0.5, 
                               framealpha=0.4)
        ci_legend.get_frame().set_linewidth(0.5)
        ci_legend.get_frame().set_edgecolor('lightgrey')
        axl.add_artist(main_legend)
        axl.add_artist(ci_legend)
    
    # Add final value texts (suupressing warnings about limitations)
    original_stdout = sys.stdout
    sys.stdout = None
    adjust_text(textsu, ax=axu, only_move={'text':'y'}, quiet=True)
    for txt in textsu: txt.set_x(xloc)
    adjust_text(textsl, ax=axl, only_move={'text':'y'}, quiet=True)
    for txt in textsl: txt.set_x(xloc)
    sys.stdout = original_stdout
    
    # Enforce non-scientific notation for y-axis tick labels and save
    for ax in fig.get_axes():
        ax.ticklabel_format(style='plain', axis='y')
    plotnm = (f'stats_{title[coll][v]}_{stat_outnms[s]}_{reg}_'
              f'{lev}_{season}.png')
    print(plotnm)
    plt.savefig(f'{plotsdir}{plotnm}', dpi=dpi)

def plot_zon(m, comp, s, reg, coll, v, var, vmin, vmax):
    '''
    Create a zonal plot for a given model (m), stat (s), region (reg), 
    collection (coll), and variable (v, var).
    Additional parameters:
    - comp: True for comparison plot, False for individual
    - vmin, vmax: min and max for contour scale
    '''
    
    # Create figure
    fig = plt.figure(figsize=(8, 6))   
    ax = fig.add_axes([0.205, 0.117, 0.678, 0.766])
    
    # Determine comparison model (self for individual plot)
    comp_model = 0 if comp else m
    comp_model_nm = models[comp_model]
    
    # Info for title
    u = vars_unit_map.get(var.upper())
    region = region_long_map.get(reg)
    
    # Make comparison plot (color mesh of diffs with significance shading)
    if comp: 
        # Determine contour level bounds and visible ticks
        offset = (vmax - vmin) / 20 / 2
        bounds = np.linspace(vmin-offset, vmax+offset, 22)
        norm = BoundaryNorm(bounds, cmap.N)
        ticks_vis = (bounds[:-1] + bounds[1:]) / 2
        for i in range(len(ticks_vis)): # Fix precision for values near zero
            if abs(ticks_vis[i]) < 1e-10:
                ticks_vis[i] = 0.0 
                
        # Plot differences as color mesh
        z_ctl = data['avg'][coll][0][reg][:, s, v, :]
        z_mod = data['avg'][coll][m][reg][:, s, v, :]
        z_vals = (z_mod - z_ctl)
        im = ax.pcolormesh(x_vals, levs, (z_vals.T), cmap=cmap, norm=norm, 
                           shading='nearest')
        
        # Create colorbar
        cbar_ax = fig.add_axes([0.155, 0.030, 0.778, 0.020])
        cbar = fig.colorbar(im, cax=cbar_ax, aspect = 40, drawedges=True, 
                            orientation='horizontal', extend='both')
        cbar.ax.tick_params(size=2, top=False, bottom=True, labelbottom=True, 
                            labelsize=8)
        
        # Format colorbar tick labels
        ticklabels = []
        for t in range(len(ticks_vis)):
            if t % 2 == 0:  # Label every other tick
                if vmax < 0.1:
                    ticklabels.append(f'{ticks_vis[int(t)]:.3f}')
                else:
                    ticklabels.append(f'{ticks_vis[int(t)]:.2f}')
            else:
                ticklabels.append('')
        cbar.set_ticks(ticks_vis)
        cbar.set_ticklabels(ticklabels)
        cbar.minorticks_off()
        cbar.ax.xaxis.set_tick_params(pad=2)
        
        # Create a mask from CIs for each selected sig level (95%, 99%, 99.99%)
        mask = {}
        for conf in conf_levels[2:]:  
            mask[conf] = (z_vals.T < cil[conf][coll][m][:, s, v, :].T) | (
                z_vals.T > ciu[conf][coll][m][:, s, v, :].T)
        
        # Apply patches to areas corresponding to masks (centered on level)
        e_colors = ['#2a2a2a', '#3a3a3a', 'dimgrey']  # Dark grey to light
        h_styles = ['xxx', '\\\\\\', '...']  # Hatched, diagonal, dotted
        for i in range(nlevs):
            for j in range(nleads):
                # Set rectangle size/location for this level/lead combination
                x_size = fcst_interval/24.
                x_beg = x_vals[j] - (x_size/2.)
                if i == 0:
                    y_beg = levs[i]
                    y_size = y_beg - (levs[i]+levs[i+1])/2
                elif i < (nlevs-1):
                    y_beg = (levs[i]+levs[i-1])/2
                    y_size = y_beg - (levs[i]+levs[i+1])/2
                else:
                    y_beg = (levs[i]+levs[i-1])/2
                    y_size = y_beg - levs[i]
                # Apply patch corresponding to strongest sig level passed
                for c, conf in enumerate(reversed(conf_levels[2:])):
                    if mask[conf][i, j]:
                        rect = plt.Rectangle(
                            (x_beg, y_beg), x_size, -y_size, linewidth=0, 
                            facecolor='none', edgecolor=e_colors[c], 
                            hatch=h_styles[c], alpha=0.7)
                        ax.add_patch(rect)
                        break
        
        # Add title
        ax.set_title(f'{models[m]} - {comp_model_nm} ({nfcsts})\n'
                     f'{stat_nms[s]} Difference [dot: >95%, diag: >99%,'
                     f' hatch: >99.99%]\n{long[coll][v]} ({u}) {region}', 
                     fontsize=12)
    
    # Make individual plot (simple lines contour)
    else: 
        # Add contour lines
        num_levels = 10
        Z = data['avg'][coll][m][reg][:, s, v, :]
        contour_colors = plt.cm.rainbow(np.linspace(0, 1, num_levels))
        contour = ax.contour(x_vals, levs, Z.T, levels=num_levels, 
                             colors=contour_colors)
        
        # Add labels (rotated 90 deg) for every other contour line
        fmt = {}
        for i, level in enumerate(contour.levels):
            if i % 2 == 0:  # Every other level
                if s == 0: fmt[level] = f'{level:.3f}'
                else: fmt[level] = f'{level:.1f}'
            else:
                fmt[level] = ''
        labels = ax.clabel(contour, contour.levels[::2], inline=True, fmt=fmt, 
                           fontsize=10)
        for label in labels:
            label.set_rotation(90)
        
        # Add title
        ax.set_title(f'{models[m]} ({nfcsts}) {stat_lbls[s]}\n'
                     f'{long[coll][v]} ({u}) {region}', fontsize=12)
    
    # Format axes, labels, and ticks
    ax.invert_yaxis()
    ax.set_ylim(1000, 100)
    ax.set_xlabel('Forecast Day', fontsize=10, labelpad=3)
    ax.set_ylabel('Pressure (hPa)', fontsize=10)
    ax.set_xticks(np.arange(0, fcst_length + 0.1, 0.5))
    formatter = mticker.FormatStrFormatter('%.1f')
    ax.xaxis.set_major_formatter(formatter)
    ax.set_xlim(0, fcst_length)
    ax.tick_params(axis='both', labelsize=8, pad=2, length=2)
    
    # Add region/variable/season/year texts
    ax.text(-0.2, 1.0, f'{reg}\n{fvars[coll][v]}', 
            transform=ax.transAxes, fontsize=14, va='top', ha='left')
    ax.text(-0.2, 0.5, seas_yr, transform=ax.transAxes,
                  fontsize=12, va='center', ha='left', rotation = 90)
    
    # Save figure
    mnm = f'{models[m].replace("_", "-")}_{comp_model_nm.replace("_", "-")}'
    plotnm = (f'{mnm}_stats_{title[coll][v]}_{stat_outnms[s]}_'
              f'{reg}_z_{season}.png')
    print(plotnm)
    plt.savefig(f'{plotsdir}{plotnm}', dpi=dpi)
    
    # Create additional log plots if applicable
    log_configs = []
    if min(levs) < 100:  # Log plot with top level 10
        log_configs.append({'suffix': '2', 'ylim': (1000, 10),
            'ticks': [10, 20, 30, 50, 70, 100, 200, 300, 500, 700, 1000]})
    if min(levs) < 10:  # Log plot with top level 1
        log_configs.append({'suffix': '3', 'ylim': (1000, 1),
            'ticks': [1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 200, 300, 500, 
                      700, 1000]})
    for config in log_configs:  # Adjust y-axis limits/ticks and save figure
        ax.set_ylim(*config['ylim'])
        ax.set_yticks(config['ticks'])
        ax.set_yticklabels([f'{tick}' for tick in config['ticks']])
        plotnm = (f'{mnm}_stats{config["suffix"]}_{title[coll][v]}_'
                  f'{stat_outnms[s]}_{reg}_z_{season}.png')
        print(plotnm)
        plt.savefig(f'{plotsdir}{plotnm}', dpi=dpi)

def calc_syn_ci(ctl_data, model_data_all, coll, sig):
    '''
    Calculate synoptic confidence intervals for full experiment list
    Parameters:
    - ctl_data: control data
    - model_data_all: list of non-control model data arrays
    - coll: collection CIs are calculated for
    - sig: significance level CIs are caluclated for (i.e., 0.95)
    Returns lower/upper confidence intervals (centered on control exp values)
    '''
    
    # Initialize confidence interval arrays
    if is_3d[coll]:
        ci_lower, ci_upper = [np.zeros((nleads, nstats, nvars[coll], nlevs)) 
                              for _ in range(2)]
    else:
        ci_lower, ci_upper = [np.zeros((nleads, nstats, nvars[coll])) 
                              for _ in range(2)]
    
    # Create CIs, looping through leads and stats
    for l in range(nleads):
        for s in range(nstats):
            if s == 0:  # ACORR
                # Apply Fisher transform to control
                ctl_clipped = np.clip(ctl_data[:, l, s, :], 
                                      -1 + 5.0E-6, 1 - 5.0E-6)
                ctl_tr = 0.5 * np.log((1 + ctl_clipped) / (1 - ctl_clipped))
                # Calculate control mean in transformed space
                ctl_tr_mean = np.mean(ctl_tr, axis=0)
                # Apply transform to non-control models and calculate variance
                if is_3d[coll]:  # 3d
                    varm_tr = np.zeros((len(models)-1, nvars[coll], nlevs))
                else:  # 2d
                    varm_tr = np.zeros((len(models)-1, nvars[coll]))
                for m in range(nexps-1):
                    model_data = np.asarray(model_data_all[m][:, l, s, :])
                    model_tr = 0.5 * np.log((1 + model_data) / 
                                            (1 - model_data))
                    varm_tr[m] = stats.tvar(model_tr)
                # Calculate control variance and mean of other model variances
                varctl_tr = stats.tvar(ctl_tr)
                var_tr = np.mean(varm_tr, axis=0)
                # Calculate standard error from average of control/other variances
                se_tr = ((varctl_tr + var_tr) / 2 / nfcsts)**(1/2)
                # Calculate t-critical value (two-sided) and CIs
                t_crit = stats.t.ppf((1 + sig) / 2, nfcsts-1)
                dx = se_tr * t_crit
                # Back-transform CIs around control, then subtract control
                ci_lower[l, s] = (
                    ((np.exp(2 * (ctl_tr_mean - dx)) - 1) / 
                     (np.exp(2 * (ctl_tr_mean - dx)) + 1)) - 
                    ((np.exp(2 * ctl_tr_mean) - 1) / 
                     (np.exp(2 * ctl_tr_mean) + 1)))
                ci_upper[l, s] = (
                    ((np.exp(2 * (ctl_tr_mean + dx)) - 1) / 
                     (np.exp(2 * (ctl_tr_mean + dx)) + 1)) - \
                    ((np.exp(2 * ctl_tr_mean) - 1) / 
                     (np.exp(2 * ctl_tr_mean) + 1)))
            else:  # RMS
                # Apply power transform to control
                ctl_tr = (ctl_data[:, l, s, :])**2
                # Calculate control mean in transformed space
                ctl_tr_mean = np.mean(ctl_tr, axis=0)
                # Apply transform to non-control models and calculate variance
                if is_3d[coll]:  #3d
                    varm_tr = np.zeros((len(models)-1, nvars[coll], nlevs))
                else:  #2d
                    varm_tr = np.zeros((len(models)-1, nvars[coll]))
                for m in range(nexps-1):
                    model_data = np.asarray(model_data_all[m][:, l, s, :])
                    model_tr = (model_data)**2
                    varm_tr[m] = stats.tvar(model_tr)
                # Calculate control variance and mean of other model variances
                varctl_tr = stats.tvar(ctl_tr)
                var_tr = (varctl_tr + np.mean(varm_tr, axis=0)) / 2 
                # Calculate standard error from sum of control/other variances
                se_tr = (var_tr / nfcsts)**(1/2)
                # Calculate t-critical value (two-sided) and CIs
                t_crit = stats.t.ppf((1 + sig) / 2, nfcsts - 1)
                dx = se_tr * t_crit
                # Back-transform CIs around control, then subtract control
                ci_lower[l, s] = ((np.maximum(0, ctl_tr_mean - dx))**(1/2) - 
                                  (np.maximum(0, ctl_tr_mean))**(1/2))
                ci_upper[l, s] = ((np.maximum(0, ctl_tr_mean + dx))**(1/2) - 
                                  (np.maximum(0, ctl_tr_mean))**(1/2))
            # Add CIs to control mean in original space
            ctl_mean = np.mean(ctl_data[:, l, s, :], axis=0) 
            ci_lower[l, s] = ci_lower[l, s] + ctl_mean
            ci_upper[l, s] = ci_upper[l, s] + ctl_mean
    return ci_lower, ci_upper

def calc_ci(ctl_data, model_data, coll, sig):
    '''
    Calculate asymmetric confidence intervals for model-control differences
    Parameters:
    - ctl_data, model_data: control and comparison experiment data
    - coll: collection CIs are calculated for
    - sig: significance level CIs are caluclated for (i.e., 0.95)
    Returns lower/upper confidence intervals for differences (centered on zero)
    '''
    
    # Initialize confidence interval arrays
    if is_3d[coll]:
        ci_lower, ci_upper = [np.zeros((nleads, nstats, nvars[coll], nlevs)) 
                              for _ in range(2)]
    else:
        ci_lower, ci_upper = [np.zeros((nleads, nstats, nvars[coll])) 
                              for _ in range(2)]
    
    # Create CIs, looping through leads and stats
    for l in range(nleads):
        for s in range(nstats):
            if s == 0:  # ACORR
                # Apply Fisher transform to control and model
                ctl_clipped   = np.clip(ctl_data[:, l, s, :],
                                        -1 + 5.0E-6, 1 - 5.0E-6)
                model_clipped = np.clip(model_data[:, l, s, :], 
                                        -1 + 5.0E-6, 1 - 5.0E-6)
                ctl_tr   = 0.5 * np.log((1 + ctl_clipped) / 
                                        (1 - ctl_clipped))
                model_tr = 0.5 * np.log((1 + model_clipped) / 
                                        (1 - model_clipped))
                # Calculate differences and control mean in transformed space
                diffs_tr = model_tr - ctl_tr
                ctl_tr_mean = np.mean(ctl_tr, axis=0)
                # Calculate variance and standard error of transformed diffs
                vard_tr = stats.tvar(diffs_tr, axis=0)
                se_tr = (vard_tr / nfcsts)**(1/2)
                # Calculate t-critical value (two-sided) and CIs
                t_crit = stats.t.ppf((1 + sig) / 2, nfcsts - 1)
                dx = se_tr * t_crit
                # Back-transform CIs around control, then subtract control
                ci_lower[l, s] = (
                    ((np.exp(2 * (ctl_tr_mean - dx)) - 1) / 
                     (np.exp(2 * (ctl_tr_mean - dx)) + 1)) - 
                    ((np.exp(2 * ctl_tr_mean) - 1) / 
                     (np.exp(2 * ctl_tr_mean) + 1)))
                ci_upper[l, s] = (
                    ((np.exp(2 * (ctl_tr_mean + dx)) - 1) / 
                     (np.exp(2 * (ctl_tr_mean + dx)) + 1)) - \
                    ((np.exp(2 * ctl_tr_mean) - 1) / 
                     (np.exp(2 * ctl_tr_mean) + 1)))
            else:  # RMS  
                # Apply power transform to control and model
                ctl_tr   = (ctl_data[:, l, s, :])**2 
                model_tr = (model_data[:, l, s, :])**2
                # Calculate differences and control mean in transformed space
                diffs_tr = model_tr - ctl_tr
                ctl_tr_mean = np.mean(ctl_tr, axis=0)
                # Calculate variance and standard error of transformed diffs
                vard_tr = stats.tvar(diffs_tr, axis=0)
                se_tr = (vard_tr / nfcsts)**(1/2)
                # Calculate t-critical value (two-sided) and CIs
                t_crit = stats.t.ppf((1 + sig) / 2, nfcsts - 1)
                dx = se_tr * t_crit
                # Back-transform CIs around control, then subtract control
                ci_lower[l, s] = ((np.maximum(0, ctl_tr_mean - dx))**(1/2) - 
                                  (np.maximum(0, ctl_tr_mean))**(1/2))
                ci_upper[l, s] = ((np.maximum(0, ctl_tr_mean + dx))**(1/2) - 
                                  (np.maximum(0, ctl_tr_mean))**(1/2))
    return ci_lower, ci_upper

def plot_3d_coll(coll):
    '''Create all plots (zonal and level) for a 3d collection (coll).'''
    
    # Create plots for each variable/stat combination
    for v, var in enumerate(fvars[coll]):
        print(f'\nMaking zonal and level plots for {var} (3D) {reg}:')
        # Set scale min/max (equal in magnitude) for RMS plots for variable
        var_range = vars_range_map.get(var.upper())
        vmin, vmax = zip(*[(-0.02, 0.02) if i == 0 # fixed value for ACORR
                           else (-var_range, var_range) 
                           for i in range(nstats)])
        for n in range(nstats):
            # Create level plots
            for l, lev in enumerate(levs):
                plot_lev(n, reg, coll, v, var, l, lev)
                plt.close('all')
            # Create comparison zonal plots 
            for m in range(1, nexps):
                plot_zon(m, True, n, reg, coll, v, var, vmin[n], vmax[n])
                plt.close('all')
            # Create individual zonal plots
            for m in range(nexps):
                plot_zon(m, False, n, reg, coll, v, var, vmin[n], vmax[n])
                plt.close('all')

def plot_2d_coll(coll, lev):
    '''
    Create all plots for a 2d collection.
    Parameters:
    - coll: 2d collection
    - lev: level save name for collection
    '''
    
    # Create level plot for each variable/stat combination
    for v, var in enumerate(fvars[coll]):
        print(f'\nMaking level plots for {var} (2D) {reg}:')
        for n in range(nstats):
            plot_lev(n, reg, coll, v, var, 0, lev)
            plt.close('all')

def create_image_montage(image_files, output_path, tile_shape, padding):
    '''
    Create montage image from input images.
    Parameters:
    - image_files: list of input image files
    - output_path: save path for montage image
    - tile_shape: dimensions for montage image (row, column)
    - padding: level of padding betweenimages
    '''
    
    # Check if all files exist and open
    missing_files = [f for f in image_files if not os.path.exists(f)]
    if missing_files:
        print(
            f'Skipping {os.path.basename(output_path)} due to missing files:')
        for missing in missing_files:
            print(f'  {os.path.basename(missing)}')
        return  # Exit early without creating montage
    images = [Image.open(f) for f in image_files]
    # Create a new blank canvas with size based on tile_shape and padding
    widths, heights = zip(*(img.size for img in images))
    max_w, max_h = max(widths), max(heights)
    rows, cols = tile_shape
    total_w = cols * max_w + (cols - 1) * padding
    total_h = rows * max_h + (rows - 1) * padding
    montage = Image.new('RGB', (total_w, total_h), color=(255, 255, 255))
    # Paste each component immage and save
    for i, img in enumerate(images):
        r = i // cols
        c = i % cols
        x = c * (max_w + padding)
        y = r * (max_h + padding)
        montage.paste(img, (x, y))
    montage.save(output_path)

def make_rmsd_montages(mont_nms, mont_vars, mont_title, mont_reg, mont_levs):
    '''
    Create RMS decomposition montages (2x2: total, bias, amplitude, phase).
    Parameters:
    - mont_nms: stat save names
    - mont_vars: variables to make montages for
    - mont_title: variables titles dictionary
    - mont_reg: region to make montages for
    - mont_levs: levels to make montages for
    '''
    
    mont = {}
    # Create montages for each level/variables combination
    for lev in mont_levs:
        mont[lev] = {}
        for v, var in enumerate(mont_vars):
            mont[lev][var] = []
            # Collect plots (by stat) for montage
            for nm in mont_nms:
                searchnm = (f'stats_{mont_title[v]}_{nm}_{mont_reg}_{lev}_'
                            f'{season}.png')
                mont[lev][var].append(f'{plotsdir}{searchnm}')
            # Define montage save name and create from collected plots
            plotnm = (f'stats_{mont_title[v]}_rmsdcmp_{mont_reg}_{lev}_'
                      f'{season}_montage.png')
            print(plotnm)
            create_image_montage(mont[lev][var], f'{plotsdir}{plotnm}', (2,2),
                                 10)
                
def make_montages(mont_nms, mont_vars, mont_title, stat_mont_regs, 
                  land_mont_regs, regs_mont_regs, z):
    '''
    Create zonal comparison montages for given top level:
        Traditional stats montages (4x5: regions as rows, vars as columns)
        Land-only stats montages (4x5: regions as rows, vars as columns)
        Regions montages (2x3: first 3 regions on top row; last 3 on bottom)
    Parameters:
    - mont_nms: stat save names
    - mont_vars: variables to make montages for
    - mont_title: variables titles dictionary
    - stat_mont_regs: regions to make traditional stats montages for
    - land_mont_regs: regions to make land-only stats montages for
    - regs_mont_regs: regions to make regions montages for
    - z: top level (100, 10, or 1 where 10 or 1 imply log y-axis)
    '''
    
    # Loop through comparison experiments
    for model in models[1:]:
        mnm = f'{model.replace("_", "-")}_{models[0].replace("_", "-")}'
        # Loop through stats
        for nm in mont_nms:
            # Collect plots (by region and var) for traditional stats montages
            stat_files = []
            for region in stat_mont_regs:
                for v in range(len(mont_vars)):
                    searchnm = (f'{mnm}_stats{z}_{mont_title[v]}_{nm}_{region}'
                               f'_z_{season}.gif')
                    stat_files.append(f'{plotsdir}{searchnm}')
            # Define montage save name and create from collected plots
            plotnm = f'{mnm}_{nm}_{season}_montage{z}.png'
            print(plotnm)
            create_image_montage(stat_files, f'{plotsdir}{plotnm}', 
                                 (4, len(mont_vars)), 10)
            # Collect plots (by region and var) for traditional stats montages
            stat_files = []
            for region in land_mont_regs:
                for v in range(len(mont_vars)):
                    searchnm = (f'{mnm}_stats{z}_{mont_title[v]}_{nm}_{region}'
                               f'_z_{season}.gif')
                    stat_files.append(f'{plotsdir}{searchnm}')
            # Define montage save name and create from collected plots
            plotnm = f'{mnm}_{nm}_{season}_montage{z}_land.png'
            print(plotnm)
            create_image_montage(stat_files, f'{plotsdir}{plotnm}', 
                                 (4, len(mont_vars)), 10)
            # Collect plots (by var and region) for regions montages
            for v, var in enumerate(mont_vars):
                regs_files = []
                for region in regs_mont_regs:
                    searchnm = (f'{mnm}_stats{z}_{mont_title[v]}_{nm}_{region}'
                               f'_z_{season}.gif')
                    regs_files.append(f'{plotsdir}{searchnm}')
                # Define montage save name and create from collected plots
                plotnm = f'{mnm}_{mont_title[v]}_{nm}_{season}_montage{z}.png'
                print(plotnm)
                create_image_montage(regs_files, f'{plotsdir}{plotnm}', (2, 3),
                                     10)

def rename(reg):
    '''Correct all filename extensions (from png to gif) for a given region.'''
    print('\nRenaming files from .png to .gif')
    renamed_count = 0
    for filename in os.listdir(plotsdir):
        if filename.endswith('.png') and reg in filename:
            new_filename = f'{filename[:-4]}.gif'
            os.rename(os.path.join(plotsdir, filename), 
                      os.path.join(plotsdir, new_filename))
            renamed_count += 1
    print(f'{renamed_count} files renamed from .png to .gif')
    
# ================== MAIN SCRIPT: SETUP ==================
    
# Suppress warning for precision loss (small variances)
warnings.filterwarnings('ignore', message='.*Precision loss occurred.*', 
                        category=RuntimeWarning)

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--config', default='plots.yaml', 
                    help='Configuration file (default: plots.yaml)')
parser.add_argument('--process', required=True, choices=['plot', 'mont'], 
                    help='plot or mont')
parser.add_argument('--part', required=False, help='split up plots by region')
args = parser.parse_args()
config = args.config
process = args.process
part = int(args.part) if args.part is not None else None

# load and validate data
data = load_stats_data(config, process, part)

# Collect Date/time info
if process == 'plot': 
    date_nms = data['date_nms']
    nfcsts = len(date_nms)
    leads = data['leads']
    nleads = len(leads)
    fcst_length = data['fcst_length']  # days
    fcst_interval = data['fcst_interval']  # hours

# Collect plot input info
nexps = len(data['fcst_names'])
fvars = data['fvars']
collections = data['collections']
is_3d = data['is_3d']
nvars = {coll: len(fvars[coll]) for coll in collections}
levs = data['levels']
nlevs = len(levs)
regions = data['regions']
plot_RMS_decomp = data['plot_RMS_decomp']
nstats = len(data['plot_stats'])

# Collect plot label info
if process == 'plot': 
    x_vals = [x / 24 for x in leads]
    xloc = x_vals[-1] + (x_vals[-1] * 0.05)
season = data['season']
year = data['year']
seas_yr = f'{season} {year}'
models = []
for m in range(nexps):
    models.append(f'{data["fcst_names"][m]}_{data["ana_names"][m]}')
    
# Collect variable metadata
(title, long) = [{} for _ in range(2)]
for coll in collections:
    title[coll] = [vars_title_map.get(var.upper()) for var in fvars[coll]]
    long[coll] = [vars_long_map.get(var.upper()) for var in fvars[coll]]
    
# Define stats names
stat_lbls   = ['Anomaly Correlation', 'Root Mean Square Error', 
               'RMS for RANDOM Errror', 'RMS for BIAS Error', 
               'RMS for AMPLITUDE Error', 'RMS for PHASE Error']
stat_nms    = ['ACORR', 'RMSE', 'RMS RANDOM Error', 'RMS BIAS Error', 
               'RMS AMPLITUDE Error', 'RMS PHASE Error']
stat_outnms = ['corcmp', 'rmscmp', 'rmscmp_RANDOM', 'rmscmp_BIAS', 
               'rmscmp_AMPLITUDE', 'rmscmp_PHASE']

# Setup dynamic colormap choice
colormap_choice = data.get('colormap', 'bwr')
if colormap_choice == 'RdBu_r':
    c_cmap = plt.cm.RdBu_r(np.linspace(0, 1, 21))
elif colormap_choice == 'custom_spectral':
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
else:  # default
    c_cmap = plt.cm.bwr(np.linspace(0, 1, 21))

# Define colormap
cmap = mcolors.ListedColormap(c_cmap)

# Collect plot saving info and make plots directory
dpi = data['plot_dpi']
output_dir = os.path.join(os.getcwd(), f'output/plots_{data["out_suffix"]}')
plotsdir = Path(f'{output_dir}/corcmp')
plotsdir.mkdir(parents=True, exist_ok=True)
plotsdir = f'{plotsdir}/'
print(f'\nCreated plots directory: {plotsdir}')

# Make corcmp.rc file
with open(f'{output_dir}/corcmp.rc', 'w') as f:
    for i in range(nexps):
        f.write(f'DSC{i}: {models[i].replace("_", "-")}\n')
print('Created corcmp.rc')

# ================== MAIN SCRIPT: PLOTTING ==================

if process == 'plot': 
    # Create plots by region
    for reg in regions:
        # Initialize confidence interval dictionaries
        conf_levels = [0.68, 0.90, 0.95, 0.99, 0.9999]
        cil, ciu = [{} for _ in range(2)]
        for conf in conf_levels: 
            cil[conf] = {}
            ciu[conf] = {}
            for coll in collections:
                cil[conf][coll] = {}
                ciu[conf][coll] = {}
        # Calculate difference CIs for each comp exp and confidence level
        for m in range(1, nexps):
            # Loop through confidence levels and collections
            for conf in conf_levels:
                for coll in collections:
                    if len(fvars[coll]) > 0:
                        (cil[conf][coll][m], ciu[conf][coll][m]
                         ) = calc_ci(data['raw'][coll][0][reg], 
                                     data['raw'][coll][m][reg], coll, conf)
        # Calculate synoptic CIs for full experiment list
        cisynl, cisynu = [{} for _ in range(2)]
        for c, coll in enumerate(collections):
            cisynl[coll], cisynu[coll] = calc_syn_ci(
                data['raw'][coll][0][reg],[data['raw'][coll][i][
                    reg] for i in range(1, nexps)], coll, 0.95)
        # Plot each collection
        lev_nms = {'de2d': 1000,'sl2d': 2000, 'ae2d': 1000}
        for coll in collections:
            if is_3d[coll]: plot_3d_coll(coll)
            else: plot_2d_coll(coll, lev_nms[coll])
        # Create RMS decomp montages: per lev_plot/var/reg [2x2]
        if plot_RMS_decomp:
            print('\nMaking rms decomp montages:')
            mont_nms = ['rmscmp', 'rmscmp_BIAS', 'rmscmp_AMPLITUDE', 
                        'rmscmp_PHASE']    
            for coll in collections:
                if is_3d[coll]: 
                    mont_levs = [f'{lev}' for lev in levs]
                else:
                    mont_levs = [f'{lev_nms[coll]}']
                make_rmsd_montages(mont_nms, fvars[coll], title[coll], reg, 
                                   mont_levs)
                plt.close('all')
        # Rename (from png to gif) all plots for this region
        rename(reg)

if process == 'mont':
    # Create zonal montages
    print('\nMaking stats and regional montages:')
    # Traditional stats montages: z per stat/model [4x5]
    # Land-only stats montages: z per stat/model [4x5]
    # Regions montages: per stat/var/model [2x3]
    mont_nms = stat_outnms if plot_RMS_decomp else stat_outnms[:2]
    stat_mont_regs = ['GLO', 'NHE', 'SHE', 'TRO']
    land_mont_regs = ['LND', 'NHL', 'SHL', 'TRL']
    regs_mont_regs = ['SHE', 'TRO', 'NHE', 'SPO', 'XPO', 'NPO']
    suffixes = ['']
    if min(levs) < 100: suffixes.append('2')
    if min(levs) < 10: suffixes.append('3')
    for suffix in suffixes:
        make_montages(mont_nms, fvars['de3d'], title['de3d'], stat_mont_regs, 
                      land_mont_regs, regs_mont_regs, suffix)    
        plt.close('all')
    rename('montage')
           
print('\nAll finished! :)')
