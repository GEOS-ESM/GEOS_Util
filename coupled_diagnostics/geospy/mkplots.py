#!/usr/bin/env python3

'''
This module runs different plotting modules. Can be used as script.
'''
import sys
import geosdset

def main(exp_conf):
    
    # Load metadata for experiments to plot
    exps=geosdset.load_exps(exp_conf)

    # Load ocean 2d data
    ocn2d=geosdset.load_collection(exps, 'geosgcm_ocn2d')

    # Plot SST
    import sst
    sst.mkplots(exps, ocn2d)

    # Plot SSS
    import sss
    sss.mkplots(exps, ocn2d)

    # Load ocean 3d data
    try:
        ocn3d=geosdset.load_collection(exps,'geosgcm_ocn3d')
    except OSError:
        ocn3d=geosdset.load_collection(exps,'prog_z',type='MOM')

    # Plot T profiles
    import temp_mapl
    temp_mapl.mkplots(exps, ocn3d)

    # Plot S profiles
    import salt_mapl
    salt_mapl.mkplots(exps, ocn3d)

    # Add more plots....
    
if __name__ == "__main__":
    main(sys.argv[1])
