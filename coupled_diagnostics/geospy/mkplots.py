#!/usr/bin/env python3

'''
This module runs different plotting modules. Can be used as script.
'''
import sys, importlib
import geosdset

def main(exp_conf):
    
    # Load metadata for experiments to plot
    exps=geosdset.load_exps(exp_conf)

    plot_default=['sst', 'sst_tp', 'sss', 'surf_stress', 
                  'zonal_stress_tp', 'surf_current', 'precip', 
                  'ssh','temp', 'salt', 'amoc']
    plotsets=exps[0]['plots'].get('plotsets', plot_default)
    
    for module in plotsets:
        print(f'\nPlotting {module}\n'.upper())
        importlib.import_module(module).main(exps)

if __name__ == "__main__":
    main(sys.argv[1])
