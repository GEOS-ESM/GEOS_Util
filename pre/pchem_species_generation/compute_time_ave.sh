#!/usr/bin/env bash

#SBATCH --time=4:00:00
#SBATCH --nodes=2
#SBATCH --job-name=time_ave_2025
#SBATCH --constraint=mil
#SBATCH --account=g0620
#SBATCH --partition=preops
#SBATCH --qos=benchmark
#SBATCH --mail-type=ALL
#SBATCH -o gcm_run.o%j

umask 022
limit stacksize unlimited

set -euo pipefail
# Positional args:
#   $1  START_YEAR
#   $2  START_MONTH
#   $3  END_YEAR
#   $4  END_MONTH
#   $5  MODEL_BUILD_DIR  (path to GEOSgcm install-release)
#   $6  SOURCE_ROOT      (path to raw MERRA-2 daily input files)
#   $7  MONTHLY_OUT_DIR  (directory to write monthly average output files)
model_build="${5:-/discover/swdev/bmauer/models/geosgcm_v11.10.0/GEOSgcm/install-release}"
source $model_build/bin/g5_modules.sh

source_root="${6:-/discover/nobackup/projects/gmao/merra2/data/products/d5124_m2_jan10}"
monthly_out_dir="${7:-monthly_files}"
prefix="MERRA2_400.inst3_3d_asm_Nv"
start_year="${1:-2025}"
start_month="${2:-1}"
end_year="${3:-2025}"
end_month="${4:-12}"

if [[ ! $start_year =~ ^[0-9]{4}$ || ! $end_year =~ ^[0-9]{4}$ ]]; then
  printf 'Error: start_year and end_year must be 4-digit YYYY values.\n' >&2
  exit 1
fi

if [[ ! $start_month =~ ^[0-9]{1,2}$ || ! $end_month =~ ^[0-9]{1,2}$ ]]; then
  printf 'Error: start_month and end_month must be numeric month values.\n' >&2
  exit 1
fi

if (( 10#$start_month < 1 || 10#$start_month > 12 || 10#$end_month < 1 || 10#$end_month > 12 )); then
  printf 'Error: start_month and end_month must be between 1 and 12.\n' >&2
  exit 1
fi

start_total=$((10#$start_year * 12 + 10#$start_month))
end_total=$((10#$end_year * 12 + 10#$end_month))

if (( start_total > end_total )); then
  printf 'Error: START_YEAR/START_MONTH must be earlier than or equal to END_YEAR/END_MONTH.\n' >&2
  exit 1
fi


work_dir="dailies_tmp_$$_$(date +%s)"

cleanup() {
  rm -rf "$work_dir"
}

trap cleanup EXIT

year=$start_year
month=$start_month
while :; do
  rm -rf "$work_dir"
  mkdir -p "$work_dir"

  month_dir=$(printf '%02d' "$month")
  last_day=$(python3 - "$year" "$month_dir" <<'PY'
import calendar
import sys

year = int(sys.argv[1])
month = int(sys.argv[2])
print(calendar.monthrange(year, month)[1])
PY
  )

  day=1
  while (( day <= last_day )); do
    day_dir=$(printf '%02d' "$day")
    source_file="$source_root/Y${year}/M${month_dir}/${prefix}.${year}${month_dir}${day_dir}.nc4"
    dest_file="$work_dir/${prefix}.${year}${month_dir}${day_dir}.nc4"

    if [[ -e $source_file ]]; then
      #ln -sfn "$source_file" "$dest_file"
      $BASEDIR/Linux/bin/ncks -v O3 "$source_file" "$dest_file"
    fi

    day=$((day + 1))
  done

  #YOUR_COMMAND
  cd "$work_dir"
  nymd="${year}${month_dir}"
  mpirun -np 192 $model_build/bin/time_ave.x -hdf `/bin/ls -1 | grep $nymd | grep -v month` -noquad
  cp monthly_ave.${nymd}.nc4 "${monthly_out_dir}/MERRA-2.inst3_3d_asm_Nv.monthly.${nymd}.nc4"
  cd ..
  rm -rf "$work_dir"

  if (( year == end_year && month == end_month )); then
    break
  fi

  if (( month == 12 )); then
    year=$((year + 1))
    month=1
  else
    month=$((month + 1))
  fi
done
