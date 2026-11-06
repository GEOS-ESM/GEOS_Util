# plots_v2/ architecture

**Audience:** coding agents and developers working on the GEOS_Util forecast-statistics scripts (`plots_v2/`).
**Describes:** the MAPL2 line, branch `main`.
**Verified against:** `GEOS_Util` @ `5b87f93` (2026-11-06).
**Placement:** as in the GEOSgcm fixture (`components.yaml` @ `0f2e0fb`): key `GEOS_Util`, checked out at `src/Shared/@GMAO_Shared/@GEOS_Util`; this directory is `plots_v2/`.
Other fixtures (for example GEOSadas, GEOSldas) may place this repository
elsewhere; paths inside this repository do not change.

## Purpose

`plots_v2/` holds one subdirectory, `stats_v2/`: Python and csh scripts that compute forecast verification statistics (forecast vs. analysis and vs. climatology), plot them, and draw scorecards. The CHANGELOG describes it as "scripts to process forecast stats and create stats plots and scorecards" (`../CHANGELOG.md` lines 128, 140). Whether it replaces `plots/` or `post/` tools is not stated in the sources read; *Inferred:* the `_v2` names suggest a successor, no evidence found.

## Build and install

- No `CMakeLists.txt` in `plots_v2/` or `stats_v2/`.
- The top `GEOS_Util/CMakeLists.txt` sets `alldirs` to `pre plots post coupled_diagnostics` (lines 1-6) and calls `esma_add_subdirectories`. `plots_v2` is not listed, so **nothing here is built or installed** by the fixture build.
- Scripts are used in place from the source tree (`$GEOSUTIL/plots_v2/stats_v2/...`) or copied to a working directory.

## Contents (`stats_v2/`)

| File | Role |
|---|---|
| `stats.run` (1157 lines, csh) | Driver. Takes a YAML file (default `stats.yaml`), validates model names, makes `output/stats_<fcst>_<ana>_<clim>_<dates>_<timestamp>/{logs,jobs,tmp}`, copies the YAML, finds `stats.py`, and submits batch jobs (104 `sbatch`/`SBATCH` matches). |
| `stats.py` (5589 lines) | Batch forecast processor. Reads forecast, analysis and climatology files; computes regional statistics (for corcmp) and global statistics (for syscmp). Uses xarray, xESMF, metpy, scipy, pandas. |
| `plots.run` (567 lines, csh) | Driver for plotting. Takes a YAML file (default `plots.yaml`), looks for the plot scripts in the CWD, then `$GEOSUTIL/plots_v2/stats_v2/`. |
| `plots_corcmp.py` | corcmp plots from regional stats: die-off curves, zonal means (single and comparison), montages. matplotlib. |
| `plots_syscmp.py` | plotsys (single) and syscmp (comparison) plots from global stats, static and animated. matplotlib, cartopy. |
| `scorecard.py` | Scorecard image. Reads statistics from a PostgreSQL database (psycopg2), not from the stats files. |
| `stats_ops_tmpl.yaml`, `stats_dev_tmpl.yaml` | Config templates for `stats.run` (operational FP and development/replay experiments). |
| `plots_tmpl.yaml` | Config template for `plots.run`: stats file paths for `exp0`..`exp9`, plot types (`corcmp`, `syscmp`, `both`), levels. |
| `stats_readme.pdf` | User documentation (about 8.9 MB); not read here. |

Usage: copy a template to `stats.yaml`/`plots.yaml`, edit, run `stats.run [file.yaml]`, then `plots.run [file.yaml]`. `scorecard.py` documents its own usage in `parse_args()`.

Inputs: NetCDF forecast, analysis and climatology files located by templates with tags such as `{init_YYYYMMDD}`, `{valid_HH,shift=-90m}`, `{expid}`. Variables: 3D (H, Q, T, U, V), surface, column, cloud and aerosol fields; regions such as GLO, NHE, TRO, SHE.

## Who uses it

- No user found in the GEOSgcm fixture outside this directory. Within GEOS_Util, `plots_v2` appears only in `stats.run` and `plots.run`, and `stats_v2` also in `CHANGELOG.md`; elsewhere only GMAO_Shared's `GMAO_etc/ARCHITECTURE.md` mentions these scripts (a documentation line listing `rst_date` calls).
- `plots.run` expects `$GEOSUTIL` to find its scripts when not run from the directory that holds them (`plots.run`, "Locate plots_corcmp.py").

## Known traps

- Site-specific: `module load python/GEOSpyD` and `/usr/share/lmod/lmod/init/csh` in both `.run` files; `/discover/nobackup/projects/gmao/...` input paths in the YAML templates (`stats_ops_tmpl.yaml`, `stats_dev_tmpl.yaml`); Slurm batch submission.
- `scorecard.py` hard-codes database host `edb1`, user `gmao_web`, databases `gmao_stats` and `semper`, and needs a `pgpass` file in the home directory.
- The `.run` files parse YAML with `grep`/`sed`/`awk`, so the YAML key layout in the templates must be kept.

## Observations (noted, not fixed)

- Not in the CMake build, so it is not tested or installed with GEOS_Util.
- `stats_readme.pdf` is a large binary in the source tree.
- Python dependencies (xesmf, metpy, cartopy, adjustText, psycopg2) come from the GEOSpyD module, not from the repository.
