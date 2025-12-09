#!/bin/bash

DST="/discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens/"

# Loop from 001 to 032
#for i in $(seq -f "%03g" 1 32)
for i in $(seq -f "%03g" 3 32)
do
    echo "=== Processing mem$i ==="
    DST_MEM=${DST}/mem${i} 
    echo $DST_MEM
    # mkdir
    mkdir ${DST_MEM}/orig_resol

    # Run your command after updating the YAML file
    echo "Running command for mem${i}..."
    cd ${DST_MEM}
    mv *gwd_import_rst* *moist_import_rst* *turb_import_rst* *turb_internal_rst* *gocart_import_rst* *saltwater_import_rst* *surf_import_rst* *solar_internal_rst* *irrad_internal_rst* ./orig_resol/

    echo "Done mem${i}"
    echo
done

