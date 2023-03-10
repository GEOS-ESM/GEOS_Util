#!/usr/bin/env python3

import os, argparse, yaml

if __name__=='__main__':

    homdir_default=f'{os.environ["HOME"]}/geos5'
    datadir_default=homdir_default
    plotdir_default=f'{datadir_default}/plots_ocn'

    parser=argparse.ArgumentParser()
    parser.add_argument('expid', help='experiment ID')
    parser.add_argument('--homdir', 
                        default=homdir_default,
                        help='path to configs (gcm_run.j etc)')
    parser.add_argument('--datadir', 
                        default=datadir_default,
                        help='path to data output')
    parser.add_argument('--plotdir', 
                        default=plotdir_default,
                        help='path to plots output')
    args=parser.parse_args()

    conf=f'''# Auto generated by mkexp.py
expid:     {args.expid}

# You can list experimants to compare following the pattern below
#cmpexp:
#    - path_to_config_file1
#    - path_to_config_file2

data_path: {args.datadir}
plot_path: {args.plotdir}

# You can specify dates interval to be used for analysis
# following the pattern below
#dates: ['yyyy-mm-dd','yyyy-mm-dd']
'''
    with open(f'{args.homdir}/{args.expid}/ocnconf.yaml','w') as of:
        print(conf, file=of)

