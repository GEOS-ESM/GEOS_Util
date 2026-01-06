#!/bin/bash

source /discover/nobackup/projects/gmao/obsdev/eyang2/GEOSadas-5.42.11/GEOSadas/install-SLES15/bin/g5_modules.sh

cd /discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens_reg

YAML_FILE="remap_params.yaml"

# Loop for 002 to 032 member
for i in $(seq 1 31)
#for i in $(seq 24 31)
do
    old=mem$(printf "%03d" $i)
    new=mem$(printf "%03d" $((i+1)))
    echo for $new

    # 1) Make directory for each member from 002 to 032
    mkdir $new 

    # 2) Edit remap_params.yaml
    sed -i "s/$old/$new/g" "$YAML_FILE"

    # 3) Execute remap_restarts_ens.py w/ yaml config file
    python3 /discover/nobackup/projects/gmao/obsdev/eyang2/GEOSadas-5.42.11/GEOSadas/install-SLES15/bin/remap_restarts_ens.py config_file -c $YAML_FILE

done

