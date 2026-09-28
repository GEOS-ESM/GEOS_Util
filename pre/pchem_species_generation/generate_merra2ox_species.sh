#!/bin/bash
# generate_merra2ox_species.bash
#
# Creates a pchem species file using MERRA-2 OX and CMIP others.
# Follows the workflow described in merra2_ox_readme.
#
# Requirements: CDO 1.9.0, NCO (ncatted)

set -e

# ---------------------------------------------------------------------------
# Arguments:
#   $1  END_YEAR_MONTH   YYYYMM through which to extend the CMIP file
#   $2  ZONAL_MEANS_DIR  directory containing the MERRA-2 monthly zonal-mean files
#   $3  CMIP_DIR         directory containing the CMIP input species file
#   $4  LEV_SOURCE       netCDF file whose lev variable (float64) is copied into the output
#
# $2, $3, and $4 fall back to hardcoded defaults if not supplied.
#
# END_YEAR_MONTH must be in YYYYMM format, e.g. 202512 (default) or 202612.
# It can also be set via the END_YYYYMM environment variable; the command-line
# argument takes precedence.
# ---------------------------------------------------------------------------
_arg="${1:-${END_YYYYMM:-202512}}"
if [[ ! "${_arg}" =~ ^[0-9]{6}$ ]]; then
    echo "ERROR: END_YEAR_MONTH must be in YYYYMM format (e.g. 202512), got '${_arg}'" >&2
    exit 1
fi
END_YEAR="${_arg:0:4}"
END_MON="${_arg:4:2}"
END_YYYYMM="${END_YEAR}${END_MON}"
# Last day of the end month (used by cdo seldate)
END_DAY="$(cal "${END_MON}" "${END_YEAR}" | awk 'NF{last=$NF} END{print last}')"
END_DATE="${END_YEAR}-${END_MON}-${END_DAY}"

# Number of years from 1979 through END_YEAR (inclusive)
CLIM_YEARS=$(( END_YEAR - 1979 + 1 ))

echo "=== Generating output through ${END_YYYYMM} (${END_DATE}) ==="

# ---------------------------------------------------------------------------
# Configurable paths
# ---------------------------------------------------------------------------
CMIP_DIR="${3:-/discover/nobackup/projects/gmao/bcs_shared/fvInput/ExtData/esm/tiles/v12/PCHEM}"
MERRA2_DIR="$(mktemp -d)"
WORK_DIR="$(mktemp -d)"

_cleanup_tmpdir() {
    rm -rf "${MERRA2_DIR}" "${WORK_DIR}"
}
trap _cleanup_tmpdir EXIT

ZONAL_MEANS_DIR="${2:-/discover/nobackup/projects/gmao/SIteam/pchem_species_inputs/monthly_zonal}"   # Directory containing the raw MERRA-2 monthly zonal-mean files

CMIP_INPUT="${CMIP_DIR}/pchem.species.CMIP-5.1870-2097.z_91x72.nc4"

# File whose lev variable (float64) is copied verbatim into the output.
LEV_SOURCE="${4:-${LEV_SOURCE:-${CMIP_DIR}/pchem.species.CMIP-5.MERRA2OX.197902-201706.z_91x72.nc4}}"

# Intermediate / output file names  (all derived from END_YYYYMM)
CMIP_CARVED="${WORK_DIR}/pchem.species.CMIP-5.197902-${END_YYYYMM}.z_91x72.nc4"
CMIP_REFTIME="${WORK_DIR}/pchem.species.CMIP-5.197902-${END_YYYYMM}.z_91x72.referenced_to_1979_02.nc4"
CMIP_NEWLEV="${WORK_DIR}/pchem.species.CMIP-5.197902-${END_YYYYMM}.z_91x72.referenced_to_197902.newlevels.nc4"
CMIP_TEMP="${WORK_DIR}/temp.nc4"

MERRA2_MERGED="${MERRA2_DIR}/MERRA-2.inst3_3d_asm_Nv.monthly.197902-${END_YYYYMM}.0001x0091x0072.OX.nc4"
MERRA2_NEWLEV="${MERRA2_DIR}/MERRA-2.inst3_3d_asm_Nv.monthly.197902-${END_YYYYMM}.0001x0091x0072.OX.newlevels.nc4"

OUTPUT="pchem.species.CMIP-5.MERRA2OX.197902-${END_YYYYMM}.z_91x72.nc4"

MYZAXIS="myzaxis"

# ---------------------------------------------------------------------------
# Step 0 – write the myzaxis file if it doesn't already exist
# ---------------------------------------------------------------------------
_myzaxis_created=0
if [[ ! -f "${MYZAXIS}" ]]; then
    echo "Writing ${MYZAXIS}..."
    cat > "${MYZAXIS}" <<'EOF'
zaxistype = pressure
size      = 72
name      = lev
longname  = "pressure at layer midpoints"
units     = layer
levels    = 1.5  2.635  4.015  5.68  7.764999  10.45  13.96  18.54  24.49  32.175  42.04  54.63  70.595  90.725  115.995  147.565  186.79  235.26  294.83  367.65  456.17  563.18  691.83  845.635  1028.49  1246.015  1505.025  1812.435  2176.1  2604.91  3108.89  3699.27  4390.965  5201.59  6149.565  7255.785  8543.899  10051.44  11825  13911.5  16366.15  19254.1  22651.35  26647.9  31279.15  35625  39375  43125  46875  50625  54375  58125  61875  65625  69375  73125.02  76250  78750  81250.02  83750.02  85750.02  87250.01  88750  90249.98  91749.98  93250.01  94750  96249.98  97374.98  98124.99  98875  99625
EOF
    _myzaxis_created=1
fi

# ---------------------------------------------------------------------------
# Step 1 – Carve CMIP file to 1979-02 through 2025-12
# ---------------------------------------------------------------------------
echo "=== Step 1: Carving CMIP file to 197902-${END_YYYYMM} ==="
cdo -O seldate,1979-02-01,"${END_DATE}" \
    "${CMIP_INPUT}" \
    "${CMIP_CARVED}"

# ---------------------------------------------------------------------------
# Step 2 – Reset the reference date so times are indexed from 1979-02
# ---------------------------------------------------------------------------
echo "=== Step 2: Setting reference date on CMIP file ==="
cdo -O setreftime,1979-02-19,08:00:00 \
    "${CMIP_CARVED}" \
    "${CMIP_REFTIME}"

# ---------------------------------------------------------------------------
# Step 3 – Extract O3 from each MERRA-2 file and rename it to OX
# ---------------------------------------------------------------------------
echo "=== Step 3: Extracting OX from MERRA-2 files ==="
mkdir -p "${MERRA2_DIR}"
shopt -s nullglob
_zonal_files=( "${ZONAL_MEANS_DIR}"/MERRA-2.inst3_3d_asm_Nv.monthly.*.nc4 )
shopt -u nullglob
if [[ ${#_zonal_files[@]} -eq 0 ]]; then
    echo "ERROR: No MERRA-2 monthly files found in ZONAL_MEANS_DIR='${ZONAL_MEANS_DIR}'" >&2
    exit 1
fi
for orig in "${_zonal_files[@]}"; do
    base="$(basename "${orig}")"
    # Skip files that already have OX in the name (re-run safety)
    [[ "${base}" == *OX* ]] && continue
    new="${MERRA2_DIR}/${base%.nc4}.OX.oldlev.nc4"
    newnew="${MERRA2_DIR}/${base%.nc4}.OX.nc4"
    echo "  Processing ${orig} -> ${new}"
    cdo -O -L chname,O3,OX -selname,O3 "${orig}" "${new}"
    cdo -O setzaxis,"${MYZAXIS}" "${new}" "${newnew}"
done

# ---------------------------------------------------------------------------
# Step 4 – Merge all MERRA-2 OX files into a single time series
# ---------------------------------------------------------------------------
echo "=== Step 4: Merging MERRA-2 OX files ==="
# Collect only the per-month OX files (exclude merged/newlevels files)
mapfile -t monthly_ox_files < <(ls "${MERRA2_DIR}"/MERRA-2.inst3_3d_asm_Nv.monthly.*.OX.nc4 2>/dev/null \
    | grep -v 'newlevels' | grep -v '197902-')
cdo -O mergetime "${monthly_ox_files[@]}" \
    "${MERRA2_MERGED}"

# ---------------------------------------------------------------------------
# Step 5 – Standardise vertical levels on MERRA-2 OX file
# ---------------------------------------------------------------------------
echo "=== Step 5: Setting zaxis on MERRA-2 OX file ==="
cdo -O setzaxis,"${MYZAXIS}" \
    "${MERRA2_MERGED}" \
    "${MERRA2_NEWLEV}"
[[ "${_myzaxis_created}" -eq 1 ]] && rm -f "${MYZAXIS}"

# ---------------------------------------------------------------------------
# Step 6 – Replace OX in CMIP with MERRA-2 OX (Python, handles dimension mismatch)
# ---------------------------------------------------------------------------
echo "=== Step 6: Replacing OX in CMIP with MERRA-2 OX ==="
python3 - "${CMIP_REFTIME}" "${MERRA2_NEWLEV}" "${OUTPUT}" <<'PYEOF'
import sys
import shutil
import numpy as np
import netCDF4 as nc

cmip_path, merra2_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

shutil.copy2(cmip_path, out_path)

with nc.Dataset(merra2_path, 'r') as m2ds, nc.Dataset(out_path, 'r+') as outds:
    # Build a dict: (year, month) -> index in CMIP time axis
    cmip_times = nc.num2date(outds['time'][:], outds['time'].units,
                             getattr(outds['time'], 'calendar', 'standard'))
    cmip_idx = {(t.year, t.month): i for i, t in enumerate(cmip_times)}

    m2_times = nc.num2date(m2ds['time'][:], m2ds['time'].units,
                           getattr(m2ds['time'], 'calendar', 'standard'))

    ox_m2 = m2ds['OX']  # shape: (time, lev, lat, lon) with lon=1
    replaced = 0
    for mi, t in enumerate(m2_times):
        key = (t.year, t.month)
        if key not in cmip_idx:
            print(f"  WARNING: MERRA-2 time {t} not found in CMIP, skipping")
            continue
        ci = cmip_idx[key]
        # Squeeze out the lon dimension (lon=1)
        data = ox_m2[mi, :, :, 0]  # shape: (lev, lat)
        outds['OX'][ci, :, :] = data
        replaced += 1

    print(f"  Replaced OX for {replaced} time steps.")

    # Fix lat metadata: standard_name, lowercase long_name, degrees_north units
    lat_var = outds['lat']
    lat_var.standard_name = 'latitude'
    lat_var.long_name = 'latitude'
    lat_var.units = 'degrees_north'

    # Fix time: ensure standard_name present
    outds['time'].standard_name = 'time'
PYEOF

# ---------------------------------------------------------------------------
# Step 7 – Edit global metadata and restore lev from original CMIP file
# ---------------------------------------------------------------------------
echo "=== Step 7: Editing global metadata and restoring lev from LEV_SOURCE ==="
# Copy lev (as float64, bit-for-bit) from LEV_SOURCE into the output file.
# The rest of the file is rebuilt unchanged around it.
python3 - "${OUTPUT}" "${LEV_SOURCE}" <<'PYEOF'
import sys, os, shutil
import numpy as np
import netCDF4 as nc

out_path, lev_source_path = sys.argv[1], sys.argv[2]
tmp_path = out_path + ".levfix.tmp.nc4"

with nc.Dataset(out_path, 'r') as src, \
     nc.Dataset(lev_source_path, 'r') as lev_src, \
     nc.Dataset(tmp_path, 'w', format=src.file_format) as dst:

    # Copy dimensions
    for name, dim in src.dimensions.items():
        dst.createDimension(name, None if dim.isunlimited() else len(dim))

    # Copy variables, substituting lev from original CMIP
    for name, var in src.variables.items():
        if name == 'lev':
            orig_lev = lev_src['lev']
            # Always write lev as float64, values copied bit-for-bit from LEV_SOURCE
            new_var = dst.createVariable('lev', 'f8', orig_lev.dimensions)
            # Copy original attributes exactly
            for attr in orig_lev.ncattrs():
                new_var.setncattr(attr, orig_lev.getncattr(attr))
            new_var[:] = np.array(orig_lev[:], dtype=np.float64)
        else:
            new_var = dst.createVariable(name, var.dtype, var.dimensions,
                                         fill_value=var._FillValue if '_FillValue' in var.ncattrs() else False)
            # Copy all attributes except _FillValue (already set)
            for attr in var.ncattrs():
                if attr != '_FillValue':
                    new_var.setncattr(attr, var.getncattr(attr))
            new_var[:] = var[:]

    # Copy global attributes
    dst.setncatts({attr: src.getncattr(attr) for attr in src.ncattrs()})

os.replace(tmp_path, out_path)
print("  lev copied from LEV_SOURCE as float64.")
PYEOF

ncatted -O \
    -a begClimYear,global,m,i,1979 \
    -a endClimYear,global,m,i,"${END_YEAR}" \
    -a climYears,global,m,i,"${CLIM_YEARS}" \
    "${OUTPUT}"

echo ""
echo "Done. Output: ${OUTPUT}"
