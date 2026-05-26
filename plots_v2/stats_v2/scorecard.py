#!/usr/bin/env python3
'''
Creates scorecard image, pulling stats data from SQL database which requires 
PG pass in home directory for access. See parse_args() method for usage notes.
'''


import argparse
import itertools
import os
import psycopg2
import sys
import datetime as dt
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.stats import t

##############################################################################
# Configuration (moved from config.py)
##############################################################################

# Note: usage requires a pgpass
HOST = 'edb1'
USER = 'gmao_web'
DB = {'fc_ops':'gmao_stats', 'fc_exp':'semper'}

##############################################################################
# Database Connection Class (moved from connection.py)
##############################################################################

class Connection(object):
    '''PostGreSQL connection'''
    
    def __init__(self, host=HOST, db=None):
        # only 2 db available presently
        if db not in DB:
            print('Database name provided not in list of known profiles.')
            print(db)
            sys.exit(2)
        self.db = db
        try:
            self.con = psycopg2.connect(
                host=host, database=DB[self.db],
                user=USER
            )
        except psycopg2.OperationalError as e:
            try:
                # try default user if run from CLI
                self.con = psycopg2.connect(
                    host=host, database=DB[self.db],
                    user='gmao_user'
                )
                return
            except psycopg2.OperationalError as e:
                print(self.db)
                print(DB[self.db])
                print('Failed to connect to database.\n{0}'.format(e))
                sys.exit(2)
            print(self.db)
            print(DB[self.db])
            print('Failed to connect to database.\n{0}'.format(e))
            sys.exit(2)

    def get(self, expver=None, num=None, **kwargs):
        '''Generic database querying of forecast stats.'''
        if expver is None:
            return []
        query = ('select date, value from ' + self.db 
                 + '.v_view where expver=%s ')
        args = [expver]
        for key,value in kwargs.items():
            query += ' and '
            if isinstance(value, list):
                query += key + ' in %s'
                args += [tuple([v for v in value])]
            else:
                query += key + '=%s'
                args += [value]
        cursor = self.con.cursor()
        if num:
            cursor.execute(query + ' limit ' + str(int(num)) + ';',
                           tuple(args))
        else:
            cursor.execute(query + ';', tuple(args))
        rows = cursor.fetchall()
        cursor.close()
        return rows

##############################################################################
# Utility Functions
##############################################################################

# Define variable fields and display names/mapping

std_fields = ['h', 'p', 'q', 't', 'u', 'v']
sfc_fields = ['t2m', 'q2m', 'd2m', 'u10m', 'v10m']
aer_fields = ['aod', 'logaod', 'pm25']

std_var_display = {'h': 'Geopotential\nHeight', 'p': 'SLP',
                   'q': 'Specific\nHumidity', 't': 'Temperature',
                   'u': 'U-Wind', 'v': 'V-Wind'}
sfc_var_display = {'t2m': 'T2m', 'q2m': 'Q2m', 'd2m': 'Dewpoint 2m', 
                   'u10m': 'U10m', 'v10m': 'V10m'}
aer_var_display = {'aod': 'total AOD', 'logaod': 'log(AOD+0.01)', 
                   'pm25': 'PM2.5'}

sfc_to_std = {'t2m': 't', 'q2m': 'q', 'd2m': 'q', 'u10m': 'u', 'v10m': 'v'}

# Define verify fallbacks

ver_fallback_map = {'self': 'gmao',  'gmao':  'self', 
                    'era5': 'ecmwf', 'ecmwf': 'era5'}

def find_experiment_database(expver, verify):
    """
    Find which database contains the experiment, handling verify fallbacks.
    Args:
        expver: Experiment version to find
        verify: Verification dataset to try first
    Returns:
        tuple (db_name, expver, verify_that_worked) if found or None
    """
    
    # List of verify values to try
    verify_options = [verify]
    if verify in ver_fallback_map:
        verify_options.append(ver_fallback_map[verify])
    
    # Try each database (ops first, then exp)
    for db_name in sorted(DB.keys(), reverse=True):
        try:
            # Create connection to this database
            connection = Connection(db=db_name)
            # Try each verify option
            for ver in verify_options:
                # Check if this combination exists
                exists_query = f'''
                    select exists (
                        select *
                        from {db_name}.v_view
                        where expver = %s and verify = %s limit 1
                    )
                '''
                cursor = connection.con.cursor()
                cursor.execute(exists_query, (expver, ver))
                row = cursor.fetchone()
                cursor.close()
                if row and row[0]:  # If experiment exists
                    if ver != verify: # Using fallback
                        print(f'Successfully located {expver} in {db_name} '
                              f'database with fallback verify {ver} '
                              f'(requested {verify}).')
                    else: # Using requested verify
                        print(f'Successfully located {expver} in {db_name} '
                              f'database with verify {ver}.')
                    return (db_name, expver, ver)
            # Exp not found with either requested or fall back in db   
            print(f'Experiment {expver} with verify {verify_options[0]} or '
                  f'{verify_options[1]} not found in database {db_name}.')
            
        except Exception as e:
            print(f'ERROR checking database {db_name}: {e}')
    
    # Exp not found with either requested or fall back
    print(f'ERROR: Experiment {expver} with verify {verify_options[0]} or '
          f'{verify_options[1]} not found in any database.')
    return None

def get_with_fallback(connection, expver, verify, **kwargs):
    '''
    Query the database with fallback verify if requested returns no results.
    Args:
        connection: Connection object
        expver: Experiment version
        verify: Requested verify value
        **kwargs: Other query parameters
    Returns:
        Query results from either requested verify or fallback
    '''

    # If no results from requested verify, try fallback if available
    results = connection.get(expver, verify=verify, **kwargs)
    if not results and verify in ver_fallback_map:
        fallback_ver = ver_fallback_map.get(verify)
        fallback_res = connection.get(expver, verify=fallback_ver, **kwargs)
        if fallback_res:
            print(f'Info: Used fallback verify "{fallback_ver}" instead of '
                  f'"{verify}" for {expver}')
            # Return results if using fallback
            return fallback_res
    # Return results (empty or not)
    return results

def validate_data_availability(exp, cntrl, args_exp, args_cntrl, ver_exp, 
                               ver_cntrl, dates, domains, stats, skip_surface, 
                               skip_aerosol):
    '''Validate all data availability'''
    
    # Define datasets to check
    datasets = [(exp, args_exp, ver_exp, 'experiment'), 
                (cntrl, args_cntrl, ver_cntrl, 'control')]
    
    # 1. Validate main data using across full date range using H@500
    print('Validating date availibity using H@500...')
    for date in dates:
        for connection, exp_name, verify, dataset_type in datasets:
            data = get_with_fallback(
                connection, exp_name, verify, variable='h', level=500,
                domain_name=domains[0], statistic=stats[0], date=date)
            if not data:
                print(f'ERROR: Missing H@500 data for {dataset_type} '
                      f'{exp_name} with verify {verify} on date {date}')
                sys.exit(2)
    
    # 2. Check pressure level availability for std variables (first date only)
    print('Checking pressure level availability for standard variables '
          '(first date only)...')
    avail_levs = {}
    first_date = dates[0]
    for var in std_fields:
        # Check both datasets for each level
        if var == 'p': 
            base_levels = [1000] 
        else: 
            base_levels = [850, 700, 500, 250, 100, 70, 10]
        exp_levels = []
        cntrl_levels = []
        for level in base_levels:
            exp_data = get_with_fallback(
                datasets[0][0], datasets[0][1], datasets[0][2], variable=var, 
                level=level, domain_name=domains[0], statistic=stats[0], 
                date=first_date)
            if exp_data: exp_levels.append(level)
            cntrl_data = get_with_fallback(
                datasets[1][0], datasets[1][1], datasets[1][2], variable=var, 
                level=level, domain_name=domains[0], statistic=stats[0], 
                date=first_date)
            if cntrl_data: cntrl_levels.append(level)
        
        # Find available levels as intersection and report missing levels
        avail_levs[var] = sorted(list(set(exp_levels) & set(cntrl_levels)))
        missing_exp = [level for level in base_levels 
                       if level not in exp_levels]
        missing_cntrl = [level for level in base_levels 
                         if level not in cntrl_levels]
        if missing_exp:
            print(f'Dataset {args_exp} with verify {ver_exp} is missing: '
                  f'{missing_exp}')
        if missing_cntrl:
            print(f'Dataset {args_cntrl} with verify {ver_cntrl} is missing: '
                  f'{missing_cntrl}')
        if missing_exp or missing_cntrl:
            print(f'Only these levels will be plotted for 3d {var}: '
                  f'{avail_levs[var]}')
        
        # Exit if variable has no available levels
        if not avail_levs[var]:
            print(f'ERROR: Variable {var} has no available levels among '
                  f'{base_levels}')
            sys.exit(2)
    
    # 3. Check surface and aerosol variables availability (first date only)  
    def check_lev0_var_availability(var_list, var_type_name):
        '''Check availability of level=0 variables using first date only'''
        available_vars = []
        for var in var_list:
            # Check both datasets
            dataset_has_var = []
            missing_in = []
            for connection, exp_name, verify, dataset_type in datasets:
                data = get_with_fallback(
                    connection, exp_name, verify, variable=var, level=0,
                    domain_name=domains[0], statistic=stats[0], 
                    date=first_date)
                if data:
                    dataset_has_var.append(True)
                else:
                    dataset_has_var.append(False)
                    missing_in.append(
                        f'{dataset_type} {exp_name} with verify {verify}')
            # Report availibility
            if all(dataset_has_var):
                available_vars.append(var)
                print(f'{var_type_name} variable {var} is available in both '
                      f'datasets')
            else:
                print(f'{var_type_name} variable {var} is missing in '
                      f'{" and ".join(missing_in)}')
        return available_vars
    
    # Check surface and aerosol variables
    avail_sfc_vars = []
    avail_aer_vars = []
    if not skip_surface:
        print('Checking surface variable availability (first date only)...')
        avail_sfc_vars = check_lev0_var_availability(sfc_fields, 'Surface')
    if not skip_aerosol:
        print('Checking aerosol variable availability (first date only)...')
        avail_aer_vars = check_lev0_var_availability(aer_fields, 'Aerosol')
    
    # Return lists of available surface and aerosol variables and levels
    return avail_sfc_vars, avail_aer_vars, avail_levs

def create_scorecard(card, args_exp, args_cntrl, ver_exp, ver_cntrl, bdate, 
                     edate, bdate_code, edate_code, n_fcst, land_only):
    '''Top method for creating the actual scorecard image'''
    
    # Make regional scorecard images and save as individual png files
    if not land_only:
        print('Generating Northern Hemisphere scorecard...')
        make_card('n.hem', card)
        print('Generating Southern Hemisphere scorecard...')
        make_card('s.hem', card)
        print('Generating Tropics scorecard...')
        make_card('tropics', card)
    else:
        print('Generating Northern Hemisphere Land scorecard...')
        make_card('n.hem_l', card)
        print('Generating Southern Hemisphere Land scorecard...')
        make_card('s.hem_l', card)
        print('Generating Tropics Land scorecard...')
        make_card('trop_l', card)
    
    # Create main image with regional scorecards and save as png
    create_main_layout(args_exp, args_cntrl, ver_exp, ver_cntrl, bdate, edate, 
                       bdate_code, edate_code, n_fcst, land_only)

    # Cleanup: remove the regional scorecard png files
    if not land_only:
        for file in ['n.hem','s.hem','tropics']:
            os.remove(f'{file}_card_cli_temp.png')
    else:
        for file in ['n.hem_l','s.hem_l','trop_l']:
            os.remove(f'{file}_card_cli_temp.png')

def get_symbols(data):
    '''Define symbol based on difference significance testing results'''
    dat_str = ''
    # Strongly significantly better: green up filled triangle
    if data == 3: 
        u_tri  = u'\u25b2'
        dat_str += u_tri
        color = 'g'
    # Significantly better: green up open triangle
    elif data == 2: 
        uo_tri = u'\u25b3'
        dat_str += uo_tri
        color = 'g'
    # Slightly significantly better: green fuzzy rectangle
    elif data == 1: # 
        fuzz   = u'\u2591'
        dat_str += fuzz
        color = 'g'
    # No significant difference: grey rectangle
    elif data == 0:
        block  = u'\u2588'
        dat_str += block
        color = (0.7,0.7,0.7)
    # Slightly significantly worse: red fuzzy rectangle
    elif data == -1:
        fuzz   = u'\u2591'
        dat_str += fuzz
        color = 'r'
    # Significantly worse: red down open triangle
    elif data == -2:
        do_tri = u'\u25bD'
        dat_str += do_tri
        color = 'r'
    # Strongly significantly worse: red down filled triangle
    elif data == -3:
        d_tri  = u'\u25bC'
        dat_str += d_tri
        color = 'r'

    return [dat_str, color]

def make_card(region, data):
    '''Make scorecard for a region'''
    
    # Get region info and data
    data = data[region]
    region_dict = {'n.hem':   'Northern Hemisphere', 
                   's.hem':   'Southern Hemisphere', 
                   'tropics': 'Tropics', 
                   'n.hem_l': 'Northern Hemisphere Land',
                   's.hem_l': 'Southern Hemisphere Land',
                   'trop_l':  'Tropics Land'}
    region_key = region
    region = region_dict[region_key]

    # Extract metadata if available
    metadata = data.get('_meta', {})
    sfc_vars = metadata.get('surface_vars', {})
    # Remove _meta from data if it exists to avoid processing it as a variable
    if '_meta' in data:
        data_without_meta = {k: v for k, v in data.items() if k != '_meta'}
    else:
        data_without_meta = data
    
    # Surface variables display info 
    sfc_to_std = metadata.get('surface_vars', {})
    sfc_vars_to_show = [var for var in sfc_vars if var in data_without_meta]
    
    # Aerosol variables display info
    aer_vars = metadata.get('aerosol_vars', {})
    aer_vars_to_show = [var for var in aer_vars if var in data_without_meta]

    # Create figure and gridspec
    g_cols = 11  # Number of columns
    card = plt.figure(figsize=(6, 10), constrained_layout=False)
    max_possible_rows = 50 # 6 header rows + 8 rows for each of 5 reg vars 
                           # (7 levels plus P or corresponding sfc vars) 
                           # + D2m row + 3 aer var rows
    gs = gridspec.GridSpec(ncols=g_cols, nrows=max_possible_rows, figure=card)
    all_axes = {}

    # Create header axes 
    all_axes['region'] = card.add_subplot(gs[:2, :])
    all_axes['var_head'] = card.add_subplot(gs[2:5, 0:3])
    all_axes['pres_head'] = card.add_subplot(gs[2:5, 3:5])
    all_axes['cor_head'] = card.add_subplot(gs[2:5, 5:8])
    all_axes['rms_head'] = card.add_subplot(gs[2:5, 8:11])
    all_axes['fcst_day'] = card.add_subplot(gs[5:6, :5])
    all_axes['cor_days'] = card.add_subplot(gs[5:6, 5:8])
    all_axes['rms_days'] = card.add_subplot(gs[5:6, 8:11])
    
    # Create axes for standard and surface variables
    current_row = 6  # Start after heads
    var_levels = {}
    for std_var in std_fields:        
        # Get available levels for each standard variable from metadata
        if std_var == 'p':
            # For surface pressure, always use 1000
            var_levels[std_var] = [1000]
        elif (metadata and 'avail_levs' in metadata 
              and std_var in metadata['avail_levs']):
            # For 3d, use available levels from metadata
            var_levels[std_var] = sorted(metadata['avail_levs'][std_var])
        n_levels = len(var_levels[std_var])
        
        # Find related surface var(s) if available and get total group height
        related_sfc_vars = [sfc_var for sfc_var in sfc_vars_to_show 
                            if sfc_to_std.get(sfc_var) == std_var]
        n_related_sfc = len(related_sfc_vars)
        var_height = n_levels + n_related_sfc
        
        # Create standard variable name column and level, COR, and RMS axes
        all_axes[f'{std_var}_name'] = card.add_subplot(
            gs[current_row:current_row+n_levels, 0:3])
        for i, level in enumerate(var_levels[std_var]):
            level_row = current_row + i
            all_axes[f'{std_var}_level_{level}'] = card.add_subplot(
                gs[level_row:level_row+1, 3:5])
            all_axes[f'{std_var}_cor_{level}'] = card.add_subplot(
                gs[level_row:level_row+1, 5:8])
            all_axes[f'{std_var}_rms_{level}'] = card.add_subplot(
                gs[level_row:level_row+1, 8:11])            
        
        # Create separate cells for related surface var(s)
        row_offset = n_levels
        for j, sfc_var in enumerate(related_sfc_vars):
            sfc_row = current_row + row_offset + j
            # Create variable name column and level, COR, and RMS axes
            all_axes[f'{sfc_var}_name'] = card.add_subplot(
                gs[sfc_row:sfc_row+1, 0:3])
            all_axes[f'{sfc_var}_level'] = card.add_subplot(
                gs[sfc_row:sfc_row+1, 3:5])
            all_axes[f'{sfc_var}_cor'] = card.add_subplot(
                gs[sfc_row:sfc_row+1, 5:8])
            all_axes[f'{sfc_var}_rms'] = card.add_subplot(
                gs[sfc_row:sfc_row+1, 8:11])
        current_row += var_height
        
    # Create axes for aerosol variables
    for aer_var in aer_vars_to_show:
        # Create variable name column level, COR, and RMS axes
        all_axes[f'{aer_var}_name'] = card.add_subplot(
            gs[current_row:current_row+1, 0:3])
        all_axes[f'{aer_var}_level'] = card.add_subplot(
            gs[current_row:current_row+1, 3:5])
        all_axes[f'{aer_var}_cor'] = card.add_subplot(
            gs[current_row:current_row+1, 5:8])
        all_axes[f'{aer_var}_rms'] = card.add_subplot(
            gs[current_row:current_row+1, 8:11])
        current_row += 1
    
    # Set region title
    all_axes['region'].text(
        0.5, 0.5, region, horizontalalignment='center', 
        verticalalignment='center', transform=all_axes['region'].transAxes, 
        fontweight='bold', fontsize=12)
    
    # Set headers
    all_axes['var_head'].text(
        0.5, 0.5, 'Variable', horizontalalignment='center', 
        verticalalignment='center', transform=all_axes['var_head'].transAxes,
        fontweight='bold', fontsize=10)
    all_axes['pres_head'].text(
        0.5, 0.5, 'Pressure\nLevel', horizontalalignment='center', 
        verticalalignment='center', transform=all_axes['pres_head'].transAxes, 
        fontweight='bold', fontsize=10)
    all_axes['cor_head'].text(
        0.5, 0.5, 'COR', horizontalalignment='center', 
        verticalalignment='center', transform=all_axes['cor_head'].transAxes, 
        fontweight='bold', fontsize=10)
    all_axes['rms_head'].text(
        0.5, 0.5, 'RMS', horizontalalignment='center', 
        verticalalignment='center', transform=all_axes['rms_head'].transAxes,
        fontweight='bold', fontsize=10)
    all_axes['fcst_day'].text(
        0.5, 0.5, 'Forecast Day', horizontalalignment='center', 
        verticalalignment='center', transform=all_axes['fcst_day'].transAxes,
        fontweight='normal', fontsize=10)
    
    # Add forecast day numbers
    all_axes['cor_days'].text(
        0, 0.5, '  1  2  3  4  5', horizontalalignment='left', 
        verticalalignment='center', transform=all_axes['cor_days'].transAxes,
        fontweight='bold', fontsize=10)
    all_axes['rms_days'].text(
        0, 0.5, '  1  2  3  4  5', horizontalalignment='left', 
        verticalalignment='center', transform=all_axes['rms_days'].transAxes,
        fontweight='bold', fontsize=10)    

    # Set standard variable names and levels
    for std_var in std_fields:
        if std_var in data_without_meta:
            # Set variable name
            all_axes[f'{std_var}_name'].text(
                0.5, 0.5, std_var_display.get(std_var, std_var), 
                horizontalalignment='center', verticalalignment='center', 
                transform=all_axes[f'{std_var}_name'].transAxes,
                fontweight='normal', fontsize=10)
            # Set level labels
            for level in var_levels[std_var]:
                all_axes[f'{std_var}_level_{level}'].text(
                    0.5, 0.5, str(level), horizontalalignment='center', 
                    verticalalignment='center', 
                    transform=all_axes[f'{std_var}_level_{level}'].transAxes, 
                    fontweight='normal', fontsize=10)    
    
    # Set surface and aerosol variable names and levels
    for var_list, display_dict in [(sfc_vars_to_show, sfc_var_display), 
                                   (aer_vars_to_show, aer_var_display)]:
        for var in var_list:
            # Set the variable name
            all_axes[f'{var}_name'].text(
                0.5, 0.5, display_dict.get(var, var), 
                horizontalalignment='center', verticalalignment='center', 
                transform=all_axes[f'{var}_name'].transAxes, 
                fontweight='normal', fontsize=10)
            # Show dash as the level
            all_axes[f'{var}_level'].text(
                0.5, 0.5, '-', horizontalalignment='center', 
                verticalalignment='center', 
                transform=all_axes[f'{var}_level'].transAxes,
                fontweight='normal', fontsize=10)
    
    # Set header background colors
    all_axes['region'].set_facecolor((0.5, 0.5, 0.5))     # dark grey
    all_axes['var_head'].set_facecolor((0.8, 0.8, 0.8))   # light grey
    all_axes['pres_head'].set_facecolor((0.8, 0.8, 0.8))  # light grey
    all_axes['cor_head'].set_facecolor((0.8, 0.8, 0.8))   # light grey
    all_axes['rms_head'].set_facecolor((0.8, 0.8, 0.8))   # light grey
    
    # Set level background colors for standard variables
    for std_var in std_fields:
        if std_var in data_without_meta:
            # Set colors for each level
            for i, level in enumerate(sorted(var_levels[std_var], 
                                             reverse=True)):
                if level == 1000: # SLP (1000) gets highest alpha (darkest)
                    color_intensity = 0.7
                else:
                    # Above surface, start at alpha=0.6 and decrease
                    color_intensity = max(0.6 - i * 0.1, 0.0)
                all_axes[f'{std_var}_level_{level}'].set_facecolor(
                    (61.0/255, 97.0/255, 212.0/255, color_intensity))    

    # Set surface and aerosol level background colors (darkest; same as SLP)
    for var in sfc_vars_to_show + aer_vars_to_show:
        all_axes[f'{var}_level'].set_facecolor(
            (61.0/255, 97.0/255, 212.0/255, 0.7))
    
    # Display symbols for standard variables
    for std_var in std_fields:
        if std_var in data_without_meta:
            for level in sorted(var_levels[std_var]):
                for test in ['cor', 'rms']:
                    if test in data_without_meta[std_var][level]:
                        dataset = data_without_meta[std_var][level][test]
                        for i, d in enumerate(dataset):
                            if len(d) > 1:  # Make sure tuple has data
                                d = d[1]
                                result = get_symbols(d)
                                sym = result[0]
                                color = result[1]
                                ax = all_axes[f'{std_var}_{test}_{level}']
                                ax.text(
                                    0.1+0.08*i, 0.5, sym, color=color, 
                                    horizontalalignment='center',
                                    verticalalignment='center', 
                                    transform=ax.transAxes, 
                                    fontweight='normal', fontsize=10)    

    # Display symbols for surface and aerosol variables
    for var in sfc_vars_to_show + aer_vars_to_show:
        for test in ['cor', 'rms']:
            if (0 in data_without_meta[var] 
                and test in data_without_meta[var][0]):
                dataset = data_without_meta[var][0][test]
                for i, d in enumerate(dataset):
                    if len(d) > 1:  # Make sure tuple has data
                        d = d[1]
                        result = get_symbols(d)
                        sym = result[0]
                        color = result[1]
                        ax = all_axes[f'{var}_{test}']
                        ax.text(
                            0.1+0.08*i, 0.5, sym, color=color, 
                            horizontalalignment='center',
                            verticalalignment='center', 
                            transform=ax.transAxes, fontweight='normal', 
                            fontsize=10)
    
    # Remove ticks/whitespace and save
    card.subplots_adjust(wspace=0, hspace=0)
    for ax in all_axes.values():
        ax.tick_params(axis='both', left=False, labelleft=False, bottom=False,
                       labelbottom=False)
    card.savefig(f'{region_key}_card_cli_temp.png', dpi=500)

def create_main_layout(exp, cont, ver_exp, ver_cntrl, start, end, bdate_code, 
                       edate_code, n_fcst, land_only):
    '''Create main layout for the full scorecard image using matplotlib'''
    
    def normalize_verify_display(verify):
        ''''Convert verify values to standardized display format'''
        verify_map = {'gmao': 'SELF', 'ecmwf': 'ERA5'}
        # Use the mapped value if in map, uppercase if not
        return verify_map.get(verify.lower(), verify.upper())

    ver_exp_d = normalize_verify_display(ver_exp)
    ver_cntrl_d = normalize_verify_display(ver_cntrl)
    
    land_suffix = '_land' if land_only else ''
    f_name = (f'scorecard_{exp}_ver{ver_exp_d}_{cont}_ver{ver_cntrl_d}_'
              f'{bdate_code}_{edate_code}{land_suffix}.png')

    x_t  = 0.02   # x-location for title
    x_l1 = 0.36   # x-location for legend, 1st column
    x_l2 = 0.68   # x-location for legend, 2nd column
    x_ld = 0.02   # horizontal delta between legend symbol and text
    ts_l = 10     # legend text size
    y_l  = 0.970  # y-location of top legend item
    y_ld = 0.025  # vertical delta between legend items
    
    # Create matplotlib figure for text elements (title, description, legend)
    fig = plt.figure(figsize = (12,10))
    
    # Title/description
    fig.suptitle(f'{exp} ({ver_exp_d}-ver) Scorecard', x = x_t, y = 0.965,
                 fontsize=12, fontweight='bold', ha = 'left', va='bottom')
    description = (f'\nComparison of scores for {cont} ({ver_cntrl_d}-ver) and'
                   f'\n{exp} ({ver_exp_d}-ver) experiments for the'
                   f'\nperiod of {start} to {end}'
                   f'\n({n_fcst} forecasts)')
    plt.figtext(x_t, 0.97, description, ha='left', va='top', fontsize = 11)
 
    # Legend (symbols followed by text)
    plt.figtext(x_l1, y_l, 'Legend', fontweight = 'bold', fontsize = 11)
    plt.figtext(x_l1, y_l-y_ld, u'\u25b2', fontsize = ts_l, color = 'g')
    plt.figtext(x_l1+x_ld, y_l-y_ld, 
                'strongly significantly better (99.99% confidence)', 
                fontsize = ts_l)
    plt.figtext(x_l1, y_l-2*y_ld, u'\u25b3', fontsize = ts_l, color = 'g')
    plt.figtext(x_l1+x_ld, y_l-2*y_ld, 
                'significantly better (99% confidence)', fontsize = ts_l)
    plt.figtext(x_l1, y_l-3*y_ld, u'\u2591', fontsize = ts_l, color = 'g')
    plt.figtext(x_l1+x_ld, y_l-3*y_ld, 
                'slightly significantly better (95% confidence)', 
                fontsize = ts_l)
    plt.figtext(x_l2, y_l, u'\u2588', fontsize = ts_l, color = (0.7,0.7,0.7))
    plt.figtext(x_l2+x_ld, y_l, 'no significant difference', fontsize = ts_l)
    plt.figtext(x_l2, y_l-y_ld, u'\u2591', fontsize = ts_l, color = 'r')
    plt.figtext(x_l2+x_ld, y_l-y_ld, 
                'slightly significantly worse (95% confidence)', 
                fontsize = ts_l)
    plt.figtext(x_l2, y_l-2*y_ld, u'\u25bD', fontsize = ts_l, color = 'r')
    plt.figtext(x_l2+x_ld, y_l-2*y_ld, 'significantly worse (99% confidence)', 
                fontsize = ts_l)
    plt.figtext(x_l2, y_l-3*y_ld, u'\u25bC', fontsize = ts_l, color = 'r')
    plt.figtext(x_l2+x_ld, y_l-3*y_ld, 
                'strongly significantly worse (99.99% confidence)', 
                fontsize = ts_l)

    # Save and close matplotlib figure (base image with text elements)
    fig.savefig(f_name, dpi=500)
    plt.close(fig)
    
    # Add regional scorecard images using PIL
    add_regional_images(land_only, f_name)

    return

def add_regional_images(land_only, f_name):
    '''
    Add regional scorecard images using PIL Image library for the .paste() 
    method needed to overlay regional cards onto the main scorecard.
    '''

    # Open main image and resize
    bg = Image.open(f_name)
    bg = bg.resize((1500, 1200))

    # Define size and positional parameters (in pixels)
    card_w  = 500  # card width
    card_h  = 950  # card height
    start_x = 25  # x-position of left edge of left-most card
    del_x   = 495   # horizontal delta between left edges of cards
    y_pos   = 135   # y-postion of top of cards
    box     = (350, 500, -50, -50)  # left, upper, right_offset, bottom_offset

    # Setup regions
    card_suffix = '_card_cli_temp.png'
    if not land_only:
        # Regular regions
        config_dict = {
            'n.hem': {'x': start_x, 'y': y_pos},
            's.hem': {'x': start_x + del_x, 'y': y_pos},
            'tropics': {'x': start_x + del_x*2, 'y': y_pos}}
    else:
        # Land-only regions
        config_dict = {
            'n.hem_l': {'x': start_x, 'y': y_pos},
            's.hem_l': {'x': start_x + del_x, 'y': y_pos},
            'trop_l': {'x': start_x + del_x*2, 'y': y_pos}}
    
    # Process and paste regional images
    for region in config_dict.keys():
        # Open and crop image
        img = Image.open(f'{region}{card_suffix}')
        w, h = img.size
        img = img.crop((box[0], box[1], w + box[2], h + box[3]))
        # Resize and paste
        img = img.resize((card_w, card_h))
        x, y = config_dict[region]['x'], config_dict[region]['y']
        bg.paste(img, (x, y), img)
	
    # Crop off bottom whitespace of full image
    width, height = bg.size
    cropped_height = height - 200  
    bg = bg.crop((0, 0, width, cropped_height))
    
    # Save and close scorecard
    bg.save(f_name, format='png', dpi=(500,500))
    bg.close()
    print(f'Scorecard saved as {f_name}')
    
    return
    
def generate_scorecard_data(
        db_exp, args_exp, exp, args_cntrl, cntrl, ver_exp, ver_cntrl, 
        bdate, edate, avail_sfc_vars, avail_aer_vars, avail_levs, 
        land_only):
    '''Perform calculations and process data for the scorecards'''
    
    # Domains and stats
    if not land_only: domains = ['n.hem', 's.hem', 'tropics']
    else: domains = ['n.hem_l', 's.hem_l', 'trop_l']
    stats = ['cor', 'rms']
    cor_calculator = AnomCorr()  # Anomaly correlation with Fisher transform
    rms_calculator = RootMeanSquare()  # RMS with squared transform
    
    # Initialize empty card dictionary 
    card = {}
    
    # Add standard variables and available levels
    iter_levels = []
    # Add standard variables
    for field in std_fields:
        if field == 'p':
            # Use 1000 for SLP
            iter_levels.append((field, 1000))
        else:
            # Use available levels
            for level in avail_levs.get(field, []):
                iter_levels.append((field, level))
    
    # Add available surface variables
    available_sfc = {var: True for var in avail_sfc_vars}
    for sfc_var, is_available in available_sfc.items():
        if is_available:
            iter_levels.append((sfc_var, 0))
    
    # Add available aerosol variables  
    available_aer = {var: True for var in avail_aer_vars}
    for aer_var, is_available in available_aer.items():
        if is_available:
            iter_levels.append((aer_var, 0))

    # Set forecast leads
    fcst_leads = list(range(24, 5*24+1, 12)) # 5 days at 12-hour intervals

    # Get date strings
    dates = []
    for i in range((edate - bdate).days+1):
        dates.append(
            int((bdate + dt.timedelta(days=1*i)).strftime('%Y%m%d00')))

    # Data collection, significance testing, and scorecard symbol assignment
    print('Processing data and calculating statistics...')
    for (field, level), domain, stat in list(
            itertools.product(*[iter_levels, domains, stats])):
        # Create statistical calculators
        if stat == 'rms': score = rms_calculator  
        elif stat == 'cor': score = cor_calculator  
        
        # Collect data across all dates for this variable combination
        e_data = []  # Experiment data: list of arrays, one per forecast
        c_data = []  # Control data: list of arrays, one per forecast
        for date in dates:
            
            # Query database for both experiment and control data for this date
            # Each query returns [(lead1, value1), (lead2, value2), ...]
            datasets = [(exp, args_exp, ver_exp, 'experiment'), 
                        (cntrl, args_cntrl, ver_cntrl, 'control')]
            query_results = []
            for connection, exp_name, verify, dataset_type in datasets:
                result = get_with_fallback(
                    connection, exp_name, verify, variable=field,
                    level=level, domain_name=domain, statistic=stat,
                    step=fcst_leads, date=date)
                query_results.append((result, exp_name, verify, dataset_type))
            e, args_exp_check, _, _ = query_results[0]
            c, args_cntrl_check, _, _ = query_results[1]
    
            # Report if data is missing for this date in either dataset
            if not e or not c:
                missing_details = []
                if not e:
                    missing_details.append(
                        f'experiment {args_exp} with verify {ver_exp}')
                if not c:
                    missing_details.append(
                        f'control {args_cntrl} with verify {ver_cntrl}')
                print(f'ERROR: Missing data for date {date} in '
                      f'{" and ".join(missing_details)}')
                print(f'Variable: {field}, level: {level}, domain: {domain}, '
                      f'statistic: {stat}')
                sys.exit(1)
            
            # Extract just the values (removing forecast leads)
            e_data.append([value for lead, value in e])
            c_data.append([value for lead, value in c])
        
        # Test all confidence levels
        for l, lev in enumerate([.9999, .99, .95]):
            
            # Perform statistical significance testing (mask missing values)
            diffs, lower, upper = score.significance(
                np.ma.masked_values(c_data, 1.7e+38),
                np.ma.masked_values(e_data, 1.7e+38), lev)
                
            # Create dictionary structure 
            if domain not in card: 
                card[domain] = {}
            if field not in card[domain]: 
                card[domain][field] = {}
            if level not in card[domain][field]: 
                card[domain][field][level] = {}
            if stat not in card[domain][field][level]: 
                card[domain][field][level][stat] = []
            
            # Create a set of leads already processed for faster lookups
            existing_leads = {a for a, b in card[domain][field][level][stat]}
            lead_to_index = {a: idx for idx, (a, b) 
                             in enumerate(card[domain][field][level][stat])}
            
            # Update significance code if difference outside confidence bounds
            for i, lead in enumerate(fcst_leads):
                if diffs[i] >= upper[i] or diffs[i] <= lower[i]: 
                    # Determine direction based on which bound exceeded
                    if diffs[i] >= upper[i]:
                        # Exceeded upper bound = significantly better
                        significance_code = 3-l  # positive code
                    else:  # diffs[i] <= lower[i]
                        # Exceeded lower bound = significantly worse  
                        significance_code = -3+l  # negative code
                    if lead not in existing_leads:
                        card[domain][field][level][stat].append(
                            (lead, significance_code))
                        existing_leads.add(lead)
                    else:  # Existing lead
                        x = lead_to_index[lead]
                        _, existing_code = card[domain][field][level][stat][x]
                        # Update if new significance is stronger than existing
                        if existing_code == 0 or (
                                abs(significance_code) > abs(existing_code)): 
                            card[domain][field][level][stat][x] = (
                                lead, significance_code)
                else:  # Not outside bounds
                    if lead not in existing_leads:
                        card[domain][field][level][stat].append((lead, 0))
                        existing_leads.add(lead)
                        
    # Save information about variable relationships for visualization
    for domain in card:
        # Create metadata for visualization if it does not exist
        if '_meta' not in card[domain]:
            card[domain]['_meta'] = {}
            
        # Store available sfc variables and their relations to std variables
        sfc_vars_available = {}
        for sfc_var, is_available in available_sfc.items():
            if is_available and sfc_var in card[domain]:
                related_std_var = sfc_to_std.get(sfc_var)
                sfc_vars_available[sfc_var] = related_std_var
        
        # Store available aerosol variables
        aer_vars_available = {}
        for aer_var, is_available in available_aer.items():
            if is_available and aer_var in card[domain]:
                aer_vars_available[aer_var] = True
        
        # Store all availability info
        card[domain]['_meta']['surface_vars'] = sfc_vars_available
        card[domain]['_meta']['aerosol_vars'] = aer_vars_available
        card[domain]['_meta']['avail_levs'] = avail_levs

    # Return: card[domain][field][level][stat] contains list of tuples where
    # first value is forecast lead and second is significance code (-3 to +3)
    for domain in card:
        for field in card[domain]:
            # Skip metadata field
            if field == '_meta':
                continue
            for level in card[domain][field]:
                for stat in card[domain][field][level]:
                    card[domain][field][level][stat] = sorted(
                        card[domain][field][level][stat], 
                        key=lambda tup: tup[0])
    return card

##############################################################################
# Stats Classes
##############################################################################

class Significance:
    
    def critval(self, lev, dof):
        '''
        Calculate critical t-value given confidence level and degs of freedom.
        '''
        if lev > 1:
            raise Exception('Confidence level must be between zero and one.')
        return t.ppf((1 + lev) / 2, dof)

    def significance(self, control, experiment, lev):
        '''
        Generic statistical significance calculation using transform pattern.
        Uses the difference and transform/transform_back methods defined in 
        derived classes (AnomCorr and RootMeanSquare).
        Returns:
            diff_mean: Mean difference per forecast lead
            lower: Lower confidence bounds per forecast lead  
            upper: Upper confidence bounds per forecast lead
        '''
        
        # Calculate raw difference mean
        diff_mean = np.mean(experiment - control, 0)
        
        # Calculate differences and sample variance in transformed space
        diff_transformed = self.transform(experiment) - self.transform(control)
        diff_variance = np.var(diff_transformed, 0, ddof=1)
        sample_size = diff_transformed.shape[0]  # Number of forecasts
        t_crit = self.critval(lev, sample_size - 1)  # Same for all fcst leads
        
        # Calculate critical t-values and confidence intervals
        std_error = np.sqrt(diff_variance / sample_size)
        margin_of_error = t_crit * std_error
        
        # Calculate bounds with control as baseline and transform back
        baseline = np.mean(self.transform(control), 0)
        lower = (self.transform_back(baseline - margin_of_error) - 
                 self.transform_back(baseline))
        upper = (self.transform_back(baseline + margin_of_error) - 
                 self.transform_back(baseline))
        
        # Flip RMS results so positive = experiment better (lower RMS)
        if isinstance(self, RootMeanSquare):
            diff_mean, lower, upper = -diff_mean, -upper, -lower
        
        return diff_mean, lower, upper

class AnomCorr(Significance):

    def transform(self, value):
        '''
        Apply Fisher z-transformation to anomaly correlation values
        (range -1 to +1), facilitating proper averaging and calculating of 
        asymmetric confidence intervals.
        Formula: z = 0.5 * ln((1 + r) / (1 - r))
        '''
        clipped = np.clip(value, -1 + 5.0e-6, 1 - 5.0e-6)
        return 0.5 * np.log((1.0 + clipped) / (1.0 - clipped))

    def transform_back(self, value):
        '''
        Apply inverse Fisher z-transformation to convert back after statistical 
        calculations have been performed in z-space.
        Formula: r = (exp(2z) - 1) / (exp(2z) + 1)
        '''
        return (np.exp(2 * value) - 1) / (np.exp(2 * value) + 1)

class RootMeanSquare(Significance):

    def transform(self, value):
        '''
        Apply squared transformation to RMS difference values to handle 
        variance-like properties, facilitating proper averaging and calculating 
        of asymmetric confidence intervals.
        Formula: RMS² (squared RMS values)
        '''
        return value ** 2

    def transform_back(self, value):
        '''
        Apply inverse squared transformation (square root) to convert back 
        after statistical calculations have been performed in squared space.
        Formula: √(RMS²) = RMS
        '''
        return np.sqrt(np.maximum(0, value))
    
##############################################################################
# Main Function
##############################################################################

def parse_args(args=None):
    '''command-line argument parser'''
    parser = argparse.ArgumentParser()

    parser.add_argument('--exp', help='experiment name')
    parser.add_argument('--cntrl', help='control name')
    parser.add_argument('--bdate', help='beginning date; YYYYMMDD')
    parser.add_argument('--edate', help='ending date; YYYYMMDD')
    parser.add_argument('--ver_exp', 
                        help=('experiment verification dataset (i.e., self or '
                              'era5): note that gmao is interpreted as self '
                              'and ecmwf as era5; default is self'), 
                        default='self')
    parser.add_argument('--ver_cntrl', 
                        help=('control verification dataset (i.e., self or '
                              'era5): note that gmao is interpreted as self '
                              'and ecmwf as era5; default is self'), 
                        default='self')
    parser.add_argument('--land', help='make land-only version', 
                        action='store_true')
    parser.add_argument(
        '--skip_surface', action='store_true',
        help='skip surface variables (t2m, q2m, d2m, u10m, v10m)')
    parser.add_argument(
        '--skip_aerosol', action='store_true', 
        help='skip aerosol variables (aod, logaod, pm25)')
    parser.add_argument('--exp_display', 
                        help='override experiment name for display/filename')
    parser.add_argument('--cntrl_display', 
                        help='override control name for display/filename')
    parser.add_argument('--ver_exp_display', 
                        help=('override experiment verification name for '
                              'display/filename'))
    parser.add_argument('--ver_cntrl_display', 
                        help=('override control verification name for '
                              'display/filename'))

    if not args:
        parser.print_usage(sys.stderr)
        sys.exit(1)
    try:
        args = parser.parse_args(args)
    except:
        if len(args) <= 1:
            parser.print_usage(sys.stderr)
            sys.exit(1)
        else:
            parser.print_usage(sys.stderr)
            sys.exit(2)
    return args

def main(arguments=[]):
    '''Main function to find/access databases and create scorecard image'''
    # Parse arguments
    args = parse_args(arguments)
        
    # Test db connection and find corresponding db for experiment and control
    result_exp = find_experiment_database(args.exp, args.ver_exp)
    if result_exp is None:
        sys.exit(2)
    db_exp, exp_name, ver_exp = result_exp
    result_cntrl = find_experiment_database(args.cntrl, args.ver_cntrl)
    if result_cntrl is None:
        sys.exit(2)
    db_cntrl, cntrl_name, ver_cntrl = result_cntrl
    print(f'Using databases: {db_exp} for experiment, {db_cntrl} for control')

    # create db connections
    exp = Connection(db=db_exp)
    cntrl = Connection(db=db_cntrl)

    # get dates/times
    bdate_code, edate_code = args.bdate, args.edate
    bdate = dt.date(int(bdate_code[:4]), int(bdate_code[4:6]), 
                    int(bdate_code[6:8]))
    edate = dt.date(int(edate_code[:4]), int(edate_code[4:6]), 
                    int(edate_code[6:8]))
    dates = []
    for i in range((edate - bdate).days+1):
        dates.append(
            int((bdate + dt.timedelta(days=1*i)).strftime('%Y%m%d00')))
    
    # Define other parameters
    n_fcst = len(dates)
    if args.land:
        domains = ['n.hem_l', 's.hem_l', 'trop_l']
    else: 
        domains = ['n.hem', 's.hem', 'tropics']
    stats = ['cor', 'rms']
    
    # Validate data availability
    avail_sfc_vars, avail_aer_vars, avail_levs = validate_data_availability(
        exp, cntrl, exp_name, cntrl_name, ver_exp, ver_cntrl, dates, domains, 
        stats, args.skip_surface, args.skip_aerosol)
    
    # Generate scorecard data
    card = generate_scorecard_data(
        db_exp, exp_name, exp, cntrl_name, cntrl, ver_exp, ver_cntrl, 
        bdate, edate, avail_sfc_vars, avail_aer_vars, avail_levs, args.land)
    
    # Update display names if arguments were provided
    exp_display       = (args.exp_display if args.exp_display 
                         else exp_name)
    cntrl_display     = (args.cntrl_display if args.cntrl_display 
                         else cntrl_name)
    ver_exp_display   = (args.ver_exp_display if args.ver_exp_display 
                         else ver_exp)
    ver_cntrl_display = (args.ver_cntrl_display if args.ver_cntrl_display 
                         else ver_cntrl)

    # Create scorecard
    bdate = bdate.strftime('%B %d, %Y').replace(' 0', ' ')
    edate = edate.strftime('%B %d, %Y').replace(' 0', ' ')
    create_scorecard(card, exp_display, cntrl_display, ver_exp_display, 
                     ver_cntrl_display, bdate, edate, bdate_code, edate_code, 
                     n_fcst, args.land)
    print('Scorecard generation complete.')
        
    return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
