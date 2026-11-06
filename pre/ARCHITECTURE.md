# pre/ (GEOS_Util pre-processing tools)

**Audience:** coding agents and developers working on the GEOS_Util pre-processing tools (`pre/`).
**Describes:** the MAPL2 line, branch `main`.
**Verified against:** `GEOS_Util` @ `5b87f93` (2026-11-06).
**Placement:** as in the GEOSgcm fixture (`components.yaml` @ `0f2e0fb`): key `GEOS_Util`, checked out at `src/Shared/@GMAO_Shared/@GEOS_Util`; this directory is `pre/`.
Other fixtures (for example GEOSadas, GEOSldas) may place this repository
elsewhere; paths inside this repository do not change.

## 1. Purpose
Tools that prepare model inputs: remapping restart files to a new
resolution or boundary-condition version, generating SST/sea-ice (ocean
external data) files, and generating a MERRA-2 ozone pchem file. They are
tools, not gridded components. Library dependencies are described in
`../../GMAO_hermes/ARCHITECTURE.md` and the other GMAO_Shared documents
(`../../docs/ARCHITECTURE.md`).

## 2. Build and install
`pre/CMakeLists.txt` calls `esma_add_subdirectories` on three directories:
`NSIDC-OSTIA_SST-ICE_blend`, `prepare_ocnExtData`, `remap_restart`.
`pchem_species_generation/` has no `CMakeLists.txt`: nothing there is built
or installed.

- `NSIDC-OSTIA_SST-ICE_blend`: a library from `bin2bin, check, fill_Land,
  hflip, interp_to_eight_deg, read_input(_quart), read_Ostia(_quart),
  read_Reynolds` (depends on MAPL, `NetCDF::NetCDF_Fortran`). Executables
  linked to it: `regrid_forcing.x`, `regrid_forcing_esmf.x`,
  `sst_sic_EIGTHdeg.x`, `sst_sic_QUARTdeg.x`, `lake_sst_sic_EIGTHdeg.x`,
  `reynolds_QUART.x`. With `USE_F2PY` and F2PY3 found, an f2py module
  `read_ops_bcs` from `read_bin.f90` (to `bin`). All `*.csh` and `*.pl`
  files are globbed and installed to `bin`.
  Present, neither built nor installed: `fill_NPOLE`, `get_nsidc_icec`,
  `read_nsidc_icec`, `convert_nsidc_grid` (F90), `plot_bcs.py`, `README_lake`,
  `input_stuff.txt`, `caspian_ice_fix.pdf`.
- `prepare_ocnExtData`: a library from `sst_ice_helpers.F90`,
  `hermes_m_tick.f90` (MAPL, NetCDF). Executables: `sst_sic_eight.x`,
  `cal_daily_clim.x`, `extract_daily_sst_ice.x`, `gen_forecast_bcs.x`.
  Optional f2py module `read_sst_ice_bcs` (`read_sst_ice_bin.f90`). Installed
  Python to `bin`: `plot_binary_sst_ice.py`, `plot_sst_ice.py`,
  `ocnExtData_utils.py`, `write_kPAR.py`. Not installed:
  `gen_wts_regrid_ostia_geos.py`, `plot_diff_ostia_native_regridded_binned.py`,
  `input_template`, `notebooks/`.
- `remap_restart`: no targets. Globs `remap*`, `bin2nc_merra2*`, `tests/*.*`
  and installs them as programs to `bin`. `remap_utils.py` goes through
  `configure_file` (`@ONLY`) first (it carries `@GEOS_SITE@`) and the
  configured copy is installed.

## 3. Contents

### remap_restart/ (Python package, driver `remap_restarts.py`)
| File | Role |
|---|---|
| `remap_restarts.py` | Main entry point; subcommands include `command_line` |
| `remap_questions.py`, `remap_command_line.py`, `remap_params.tpl` | Interactive questions / command-line options / parameter template |
| `remap_base.py`, `remap_utils.py` | Shared base class and helpers (site configured) |
| `remap_upper.py` | Atmosphere: writes a csh script running `interp_restarts.x` (or `interp_restarts_bin.x`) via `esma_mpirun` |
| `remap_catchANDcn.py` | Land: runs `mk_catchANDcnRestarts.x` |
| `remap_other_restarts.py` | Lake, landice, salt: `mk_LakeLandiceSaltRestarts.x`, `SaltIntSplitter.x` |
| `remap_analysis.py` | Analysis files: `dyn2dyn.x`, `mkdrstdate.x` |
| `remap_bin2nc.py`, `bin2nc_merra2_*.yaml` | Convert MERRA-2 binary restarts to netCDF, one yaml per restart type |
| `tests/` | `test_remap_restarts.py`, `test_remap_cases.yaml`, case yamls (`c24Toc12`, `c180Toc360`, ...) |

### prepare_ocnExtData/ (ocean external data; see its `README.md`)
| File | Role |
|---|---|
| `proc_SST_FRACI_eight.F90` -> `sst_sic_eight.x` | Build 1/8-degree SST/ice files |
| `daily_clim_SST_FRACI_eight.F90`, `extract_day_SST_FRACI_eight.F90`, `forecast_SST_FRACI_eight.F90` | Daily climatology, single-day extraction, forecast BCs |
| `write_kPAR.py` | Climatological k-PAR file |
| `gen_wts_regrid_ostia_geos.py`, `ocnExtData_utils.py` | Regrid weights, helpers |
| `plot_*.py`, `notebooks/` | Plotting |

### NSIDC-OSTIA_SST-ICE_blend/ (OSTIA + Reynolds SST, NSIDC ice)
| File | Role |
|---|---|
| `SST_ICE_bcs.csh`, `SST_ICE_bcs.pl`, `BLEND-OSTIA-REYNOLDS.pl` | Top-level blending drivers (history: 2013, OSTIA + Reynolds lakes, NSIDC ice) |
| `make_ostia_quart.csh`, `make_ostia_eigth.csh`, `proc_singleDay.csh`, `gen_input.csh`, `cube_BCs.pl` | Per-resolution drivers, input generation, cube-sphere BCs |
| `proc_SST_FRACI*.F90`, `lake_data_EIGTHdeg.F90` | Programs behind the `*.x` names above |
| `regrid_forcing*.F90` | Regrid forcing (plain and ESMF) |
| `read_*.F90`, `bin2bin`, `hflip`, `fill_Land`, `check` | Readers and helpers (library) |

### pchem_species_generation/ (shell + Python; see its `README.md`)
`run_pipeline.sh` orchestrates a MERRA-2 ozone pchem file for 1979-02 to a
user end date: `compute_time_ave.sh` (SLURM time-averaging),
`zonal_mean_subsample_o3.py`, `generate_merra2ox_species.sh`.

## 4. Who uses it
- `remap_restarts.py command_line ...` is called by
  `src/Applications/@GEOSgcm_App/gcm_run.j` (`$GEOSBIN/remap_restarts.py`,
  with `-grout C${AGCM_IM}`, `-bcvin`, `-bcvout`); also in
  `gcm_run.j-new_rst_approach`. No other caller found in the fixture.
- `remap_upper.py` generates calls to `interp_restarts.x` and
  `interp_restarts_bin.x`, built in `@FVdycoreCubed_GridComp`
  (`interp_restarts.F90`, `interp_restarts_bin.F90`, its `CMakeLists.txt`).
  The other programs the `remap_*.py` scripts run from `$bin` are built
  elsewhere: `mk_catchANDcnRestarts.x`, `mk_LakeLandiceSaltRestarts.x`,
  `SaltIntSplitter.x` in GEOSgcm_GridComp
  (`GEOSsurface_GridComp/Utils/mk_restarts/CMakeLists.txt`, `exe_srcs`);
  `dyn2dyn.x` in GMAO_hermes (`../../GMAO_hermes/CMakeLists.txt`, target
  `dyn2dyn.x`; [document](../../GMAO_hermes/ARCHITECTURE.md)); `mkdrstdate.x`
  in GMAO_etc (`../../GMAO_etc/CMakeLists.txt`, target `mkdrstdate.x`).
- `prepare_ocnExtData` and `NSIDC-OSTIA_SST-ICE_blend` executables and scripts:
  no caller found in the GEOSgcm fixture (`src` grep for `SST_ICE_bcs`,
  `sst_sic`, `regrid_forcing`, `make_ostia`, `cube_BCs`, `gen_forecast_bcs`,
  `cal_daily_clim` outside `pre/` found only `UMD_utils` Python with an
  unrelated `get_sst_sic` function). *Unverified:* use by GEOSadas or by hand.
- `pchem_species_generation/`: no user found in the fixture.

## 5. Known traps
- Two related blending/SST-ice toolchains coexist: `NSIDC-OSTIA_SST-ICE_blend`
  (1/4 and 1/8 degree, csh/perl-driven, 2013 origin) and
  `prepare_ocnExtData` (1/8 degree, Python-assisted). Both build executables
  with overlapping roles (`sst_sic_EIGTHdeg.x` vs `sst_sic_eight.x`).
- `remap_utils.py` in the source tree contains the unexpanded `@GEOS_SITE@`;
  only the installed copy is configured.
- Hard-coded site paths: `SST_ICE_bcs.csh` (`/discover/nobackup/...`,
  `ESMADIR`), the `gcm_run.j` call (`/discover/nobackup/projects/gmao/bcs_shared/...`).
- The `remap_restart` glob install includes `tests/*.*`, so test files land in `bin`.

## 6. Observations (noted, not fixed)
- `pchem_species_generation/` is not in `alldirs`, so it is never installed.
- `fill_NPOLE`, `get_nsidc_icec`, `read_nsidc_icec`, `convert_nsidc_grid` are
  not in the library or executable lists.
- `SST_ICE_bcs.csh` begins `#/bin/csh` (no `!`).
