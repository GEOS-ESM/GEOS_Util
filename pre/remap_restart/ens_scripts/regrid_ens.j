#!/bin/bash
#SBATCH --account=s0818
#SBATCH --qos=obsdev
#SBATCH --job-name=ens_regrid
#SBATCH --output=ens_regrid.log.o%j.txt
#SBATCH -t 03:00:00
#SBATCH --no-requeue

cd /discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens_reg
bash /discover/nobackup/projects/gmao/obsdev/eyang2/PBLH/Exp/pblhl/atmens_reg/regrid_ens.sh
