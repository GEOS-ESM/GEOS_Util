# MERRA-2 OX pchem Species Pipeline

This repository contains scripts to produce a photochemical species (`pchem`) file
in which the CMIP-5 climatological ozone (OX) is replaced with MERRA-2 ozone from
1979-02 through a user-specified end date. The resulting file is suitable for use
as boundary condition input to GEOS atmospheric models.

---

## Overview

The pipeline takes MERRA-2 three-dimensional instantaneous assimilation fields
(`inst3_3d_asm_Nv`), computes monthly time averages, reduces them to zonal means
on a coarser latitude grid, and splices the ozone variable into a CMIP-5 species
file. All steps are orchestrated by a single meta-script, `run_pipeline.sh`.

### Data flow

```
MERRA-2 daily inst3_3d_asm_Nv files  (MERRA2_DAILY_SOURCE)
        │
        ▼  compute_time_ave.sh  (SLURM job, only if needed)
Monthly time-averaged files           (MONTHLY_OUT_DIR → MONTHLY_NEW_DIR)
        │
        ▼  zonal_mean_subsample_o3.py  (only if needed)
Monthly zonal mean files              (ZONAL_OUT_DIR → ZONAL_NEW_DIR)
        │
        ▼  generate_merra2ox_species.sh  (CDO + Python)
pchem.species.CMIP-5.MERRA2OX.197902-{END_YYYYMM}.z_91x72.nc4
```

---

## Repository contents

| File | Description |
|------|-------------|
| `run_pipeline.sh` | **Main entry point.** Orchestrates the full pipeline. Edit the configuration block at the top before running. |
| `compute_time_ave.sh` | SLURM batch script. Extracts O3 from daily MERRA-2 files and computes monthly time averages using `time_ave.x`. Called by the pipeline only when monthly averages are missing. |
| `zonal_mean_subsample_o3.py` | Python script. Computes the zonal mean of O3 from a monthly average file, converts units from kg kg⁻¹ to mol mol⁻¹, and subsamples the latitude grid from 361 to 91 points (0.5° → 2°). Called by the pipeline only when zonal mean files are missing. |
| `generate_merra2ox_species.sh` | Assembles the final pchem species file. Uses CDO to prepare the MERRA-2 and CMIP data, then a Python inline script to splice MERRA-2 OX into the CMIP file. |
| `run_zonal_mean.sh` | Standalone batch wrapper around `zonal_mean_subsample_o3.py`. Not called by the pipeline; retained for manual use. |

---

## Dependencies

The following tools must be available in your environment before running:

| Tool | Required by |
|------|-------------|
| `bash` ≥ 4.0 | All scripts |
| `python3` with `numpy`, `netCDF4` | `zonal_mean_subsample_o3.py`, `generate_merra2ox_species.sh` |
| CDO ≥ 1.9.0 | `generate_merra2ox_species.sh` |
| NCO (`ncatted`, `ncks`) | `generate_merra2ox_species.sh` |
| GEOS `g5_modules.sh`, `time_ave.x` | `compute_time_ave.sh` |
| SLURM (`sbatch`, `squeue`, `sacct`) | `run_pipeline.sh` (SLURM step only) |

On NASA Discover, loading the GEOS GCM modules via `g5_modules.sh` (path set in
`MODEL_BUILD_DIR`) will satisfy most of the above requirements.

---

## Quick start

1. **Clone / copy** this repository to your working directory on Discover.

2. **Edit the configuration block** at the top of `run_pipeline.sh` (see
   [Configuration](#configuration) below).

3. **Run the pipeline:**
   ```bash
   bash run_pipeline.sh
   ```

The script logs timestamped progress to stdout. If a SLURM job is submitted it
will poll every 60 seconds and continue automatically when the job finishes.

---

## Configuration

Open `run_pipeline.sh` and set the following variables at the top of the file.

### End date (required)

```bash
END_YEAR=2025
END_MONTH=12
```

The pipeline always starts at **1979-02** (the beginning of the CMIP file). Set
`END_YEAR` and `END_MONTH` to the last month you want MERRA-2 ozone to cover.

---

### Archive directories (required)

These are **read-only** directories. The pipeline never writes into them.

```bash
MONTHLY_ARCHIVE_DIR="/path/to/monthly_archive"
ZONAL_ARCHIVE_DIR="/path/to/zonal_archive"
```

| Variable | Expected file naming pattern |
|----------|------------------------------|
| `MONTHLY_ARCHIVE_DIR` | `MERRA-2.inst3_3d_asm_Nv.monthly.YYYYMM.nc4` |
| `ZONAL_ARCHIVE_DIR` | `MERRA-2.inst3_3d_asm_Nv.monthly.YYYYMM.0001x0091x0072.nc4` |

The pipeline checks these directories first before deciding whether any work
needs to be done. Months whose zonal means are already present are skipped
entirely. Months whose monthly averages are present but whose zonal means are
missing have their zonal means generated directly without going through SLURM.
Only months with neither file trigger the SLURM time-averaging step.

---

### Input data paths (required)

```bash
MODEL_BUILD_DIR="/discover/swdev/bmauer/models/geosgcm_v11.10.0/GEOSgcm/install-release"
MERRA2_DAILY_SOURCE="/discover/nobackup/projects/gmao/merra2/data/products/d5124_m2_jan10"
CMIP_DIR="/path/to/cmip_dir"
LEV_SOURCE="/path/to/file_with_desired_levels.nc4"
```

| Variable | What it points to |
|----------|-------------------|
| `MODEL_BUILD_DIR` | GEOSgcm `install-release` directory. Must contain `bin/g5_modules.sh` and `bin/time_ave.x`. |
| `MERRA2_DAILY_SOURCE` | Root of the raw MERRA-2 daily files, organised as `Y{YYYY}/M{MM}/MERRA2_400.inst3_3d_asm_Nv.YYYYMMDD.nc4`. Only needed if SLURM time-averaging is triggered. |
| `CMIP_DIR` | Directory containing `pchem.species.CMIP-5.1870-2097.z_91x72.nc4`. |
| `LEV_SOURCE` | Path to a NetCDF file whose `lev` variable (float64) is copied verbatim into the output file. |

---

### Output directories (optional — defaults shown)

These directories are created automatically. The working directories
(`MONTHLY_OUT_DIR`, `ZONAL_OUT_DIR`) are deleted at the end of the pipeline run.
The new-files directories (`MONTHLY_NEW_DIR`, `ZONAL_NEW_DIR`) are kept and
contain any files generated during this run.

```bash
MONTHLY_OUT_DIR="${SCRIPT_DIR}/monthly_files"      # working dir, deleted at end
ZONAL_OUT_DIR="${SCRIPT_DIR}/monthly_zonal"        # working dir, deleted at end
MONTHLY_NEW_DIR="${SCRIPT_DIR}/monthly_files_new"  # kept — newly generated monthly averages
ZONAL_NEW_DIR="${SCRIPT_DIR}/monthly_zonal_new"    # kept — newly generated zonal means
```

---

## Pipeline steps in detail

### Step 1 — Audit

The pipeline loops over every month from 1979-02 through `END_YEAR/END_MONTH`
and classifies each month into one of three buckets:

- **Zonal mean present** (in `ZONAL_ARCHIVE_DIR` or `ZONAL_OUT_DIR`) — nothing to do.
- **Monthly average present, zonal mean missing** — queued for zonal mean generation.
- **Neither present** — queued for SLURM time-averaging.

### Step 2 — SLURM time-averaging (skipped if not needed)

If any months have no monthly average, a single SLURM job is submitted via
`compute_time_ave.sh` covering the full span of missing months (from the earliest
to the latest missing month). The pipeline polls `squeue` every 60 seconds until
the job completes, then checks the exit code via `sacct`. On failure the pipeline
aborts with an error message. The SLURM months are then added to the zonal mean
generation queue.

The SLURM job writes monthly average files to `MONTHLY_OUT_DIR` using the naming
pattern `MERRA-2.inst3_3d_asm_Nv.monthly.YYYYMM.nc4`.

### Step 3 — Zonal mean generation (skipped if not needed)

For each month in the zonal mean queue, `zonal_mean_subsample_o3.py` is called
directly. It reads the monthly average, averages over all longitudes, converts O3
from kg kg⁻¹ to mol mol⁻¹, subsamples the latitude axis from 361 to 91 points
(every 4th point, yielding 2° spacing from −90° to +90°), and writes a NetCDF4
file with dimensions `(time=1, lev=72, lat=91, lon=1)` to `ZONAL_OUT_DIR`.

### Step 3b — Symlink archive zonal means

To give `generate_merra2ox_species.sh` a single directory to work from,
archive zonal means (from `ZONAL_ARCHIVE_DIR`) are symlinked into `ZONAL_OUT_DIR`
for any month not already represented there. After this step `ZONAL_OUT_DIR`
contains real files for newly generated months and symlinks for archive months.

### Step 4 — Assemble pchem species file

`generate_merra2ox_species.sh` is called with `END_YYYYMM`, `ZONAL_OUT_DIR`,
and `CMIP_DIR`. It performs the following sub-steps using CDO and Python:

1. Carves the CMIP-5 species file to 1979-02 through `END_YYYYMM`.
2. Resets the CMIP time reference to 1979-02-19 08:00:00.
3. Extracts O3 from each zonal mean file, renames it to OX, and re-assigns
   the vertical axis using a 72-level pressure axis descriptor.
4. Merges all monthly OX files into a single time series.
5. Standardises the vertical levels on the merged file.
6. Uses an inline Python script to replace the OX variable in the CMIP file
   with MERRA-2 OX, matched by (year, month). Fixes coordinate metadata.
7. Copies the `lev` variable (as float64, bit-for-bit) from `LEV_SOURCE` into
       the output file, along with its attributes. Then sets global attributes
       `begClimYear`, `endClimYear`, and `climYears`.

Intermediate files are written to two temporary directories created with
`mktemp -d` and are automatically deleted when the script exits.

**Output file** (written to the directory where `run_pipeline.sh` is run):
```
pchem.species.CMIP-5.MERRA2OX.197902-{END_YYYYMM}.z_91x72.nc4
```

### Step 5 — Move generated files and clean up

Any newly generated monthly averages (real files, not symlinks) are moved from
`MONTHLY_OUT_DIR` to `MONTHLY_NEW_DIR`. Newly generated zonal means are moved
from `ZONAL_OUT_DIR` to `ZONAL_NEW_DIR`. The two working directories, now
containing only symlinks or empty, are deleted.

Files already present in the archive directories are never moved or modified.

---

## Running individual scripts manually

Each sub-script can be run independently outside the pipeline.

### `compute_time_ave.sh`

```bash
sbatch compute_time_ave.sh \
    START_YEAR START_MONTH END_YEAR END_MONTH \
    MODEL_BUILD_DIR SOURCE_ROOT MONTHLY_OUT_DIR
```

Example:
```bash
sbatch compute_time_ave.sh 2025 1 2025 12 \
    /path/to/GEOSgcm/install-release \
    /path/to/merra2/daily \
    ./monthly_files
```

All arguments have hardcoded defaults and are optional when running standalone.

### `zonal_mean_subsample_o3.py`

```bash
python3 zonal_mean_subsample_o3.py <input_file> <output_file>
```

Example:
```bash
python3 zonal_mean_subsample_o3.py \
    monthly_files/MERRA-2.inst3_3d_asm_Nv.monthly.202501.nc4 \
    monthly_zonal/MERRA-2.inst3_3d_asm_Nv.monthly.202501.0001x0091x0072.nc4
```

### `generate_merra2ox_species.sh`

```bash
bash generate_merra2ox_species.sh END_YYYYMM ZONAL_MEANS_DIR CMIP_DIR LEV_SOURCE
```

Example:
```bash
bash generate_merra2ox_species.sh 202512 ./monthly_zonal /path/to/cmip /path/to/file_with_desired_levels.nc4
```

All arguments fall back to hardcoded defaults if omitted.

### `run_zonal_mean.sh`

Standalone batch wrapper around `zonal_mean_subsample_o3.py`. Edit
`START_YEAR`, `START_MONTH`, `END_YEAR`, `END_MONTH` at the top of the file,
then run:

```bash
bash run_zonal_mean.sh START_YEAR START_MONTH END_YEAR END_MONTH
```

This script is not called by the pipeline but is retained for manual use.

---

## Output

The final output file is written to the directory from which `run_pipeline.sh`
is executed:

```
pchem.species.CMIP-5.MERRA2OX.197902-{END_YYYYMM}.z_91x72.nc4
```

For example, with `END_YEAR=2025` and `END_MONTH=12`:

```
pchem.species.CMIP-5.MERRA2OX.197902-202512.z_91x72.nc4
```

This file has the same structure as the original CMIP-5 species file but with
the OX variable replaced by MERRA-2 ozone for all months from 1979-02 onward.
Global attributes `begClimYear`, `endClimYear`, and `climYears` are updated to
reflect the new data coverage.
