# coupled_diagnostics (GEOS_Util)

**Audience:** coding agents and developers working on the GEOS_Util diagnostics for coupled ocean-atmosphere runs (`coupled_diagnostics/`).
**Describes:** the MAPL3 line, branch `release/MAPL-v3`.
**Verified against:** `GEOS_Util` @ `0fbacb5` (2026-11-06).
**Placement:** as in the GEOSgcm fixture (`components.yaml` @ `f50622d`): key `GEOS_Util`, checked out at `src/Shared/@GMAO_Shared/@GEOS_Util`; this directory is `coupled_diagnostics/`.
Other fixtures (for example GEOSadas, GEOSldas) may place this repository
elsewhere; paths inside this repository do not change.

This repository: [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md). Parent repository GMAO_Shared: `../../docs/ARCHITECTURE.md`.

## 1. Purpose

Python (plus a few GrADS `.ctl`, Fortran, and csh files) post-processing for coupled-model output: ocean, sea-ice and surface-flux diagnostics, plotted against observational/reanalysis verification data sets. It holds two generations of tooling: the older `g5lib` + `analysis` + `verification` set (Python 2 era), and the newer `geospy` package (xarray, YAML configured).

## 2. Build and install

- `CMakeLists.txt` builds nothing. It globs all immediate subdirectories (`SUBDIRS`, `CONFIGURE_DEPENDS`; currently `analysis`, `geospy`, `verification`, `g5lib`), so any new subdirectory is installed automatically, and does one `install(DIRECTORY ... DESTINATION coupled_diagnostics USE_SOURCE_PERMISSIONS)`, so the trees are copied verbatim to `<install>/coupled_diagnostics/`. The parent `GEOS_Util/CMakeLists.txt` lists `coupled_diagnostics` as a subdirectory.
- Not installed to `lib/Python`; no Python package metadata, no tests.
- Present but not compiled: `g5lib/src/fortran/{g2g.f90,varimax.f90,varimax2.f,Makefile}` and `g5lib/src/reroute_runoff/reroute.f90` (they are copied as source only).
- Dependencies are Python modules (numpy, scipy, netCDF4, xarray, yaml, cftime, matplotlib); no MAPL or GMAO_Shared library link.

## 3. Contents

| Path | Role |
|---|---|
| `geospy/` | Newer package (`Readme.md`). Config `ocnconf.yaml` (`expid`, `data_path`, `plot_path`, `griddir`, optional `cmpexp`). |
| `geospy/mkplots.py` | Entry point: loads experiments (`geosdset.load_exps`) and runs the default plot modules (sst, sst_tp, sss, surf_stress, zonal_stress_tp, surf_current, precip, ...) or a list from the config. |
| `geospy/mkexp.py` | Entry point: generates an `ocnconf.yaml` for an experiment ID (defaults under `$HOME/geos5`). |
| `geospy/{sst,sss,ssh,sea_lev,temp,salt,amoc,precip,surf_stress,surf_current,...}.py` | One plot module per quantity; each is also runnable alone with a config path. |
| `geospy/{geosdset,hist_parser,utils,plots,template}.py` | Dataset loading, HISTORY parsing, helpers. |
| `geospy/verification/{GPCP,OISSTv2,QSCAT,woa13,woa18}` | Verification-data loaders for `geospy`. |
| `g5lib/` | Older library: `Dset`/`Field`/`Grid`/`Domain` classes (`dset.py`, `field.py`, `grid.py`, `domain.py`, `g5dset.py`, `gridtile.py`), plotting (`plots.py`, `plotters.py`, `cmaps.py`), `pca.py`, `utils.py`. |
| `g5lib/confocn.py` | Per-experiment configuration template; copied as `__init__.py` into the experiment's ocean directory. |
| `g5lib/plotocn.j`, `g5lib/plotocn` | SLURM csh job template (`@PLOT_T`, `@GEOSDIR`, loads a Python 2.7 module) and csh list calling `@anadir/clim/*.py @expid`. |
| `g5lib/src/` | Utilities: `interpolate.py`, `interp_kpar.py`, `show_colormaps.py`, `regrid_bcs/regrid_bcs.py`, `reroute_runoff/` (runoff re-routing, route masks), `fortran/` (g2g, varimax). |
| `analysis/clim/` | ~35 climatology scripts (sst, sss, temp, salt, amoc, stress, precip, seaice, mld, heat transport, flux terms, ...). |
| `analysis/tseries/` | Time-series scripts (nino3, sst_gm, temp_gm, ssh_gm, seaice, hov_tp, ...). |
| `verification/` | ~23 observation/reanalysis directories (levitus, woa13, merra, merra2, ceres2, ecmwf_int, gpcp, OAFlux, reynolds, HadISST, ...), each a small Python package (`ctl.py`, `*.ctl`, loader scripts) used by `analysis/`. |

## 4. Who uses it

- All four setup scripts in `src/Applications/@GEOSgcm_App` copy `${GEOSDEF}/coupled_diagnostics/g5lib/plotocn.j` into the ocean temp directory and `g5lib/confocn.py` as `__init__.py`: `gcm_setup` (2380-2381), `gmichem_setup` (2575-2576), `stratchem_setup` (2380-2381), `geoschemchem_setup` (2396-2397). Each then moves `plotocn.j` to `$EXPDIR/plot` when `$OGCM == TRUE` and `$OCNMODEL != MIT` (`gcm_setup` line 2526; same pattern in the others).
- `GEOSDEF` is `dirname` of the directory `gcm_setup` runs from (`set GEOSDEF = \`dirname $BINDIR\``, `gcm_setup` line 62), i.e. the installation prefix, so the tools are reached at `<install>/coupled_diagnostics`.
- Placeholders substituted by the setup scripts' `sed` (`gcm_setup` lines ~2104-2204): in `plotocn.j`, `@PLOT_T`, `@GEOSDIR`, `@EXPID`, `@HOMDIR`, `@EXPDIR`; in `confocn.py`, `@EXPID`, `@EXPDIR`, `@EXPDSC`, `@COUPLEDIR` (it also contains `@OGCM_IM/JM`, `@AGCM_IM/JM`; I did not locate their substitution). At run time `plotocn.j` itself seds `@expid` and `@anadir` into `g5lib/plotocn`.
- No other caller of `geospy` in the GEOSgcm fixture. `geospy/Readme.md` documents running it by hand on discover/NAS after `module load python/GEOSpyD`: generate `ocnconf.yaml` with `mkexp.py` (the file header says "Auto generated by mkexp.py"), edit it, then run `mkplots.py <config>` for the full set or one module (e.g. `ssh.py <config>`) for a single plot set. *Unverified:* use of `g5lib` or `geospy` outside GEOSgcm.
- `analysis/` scripts import `g5lib` and `verification` packages; `plotocn.j` sets `G5LIBDIR`, `ANADIR`, `VERIFICATION` under `@GEOSDIR/coupled_diagnostics`.

## 5. Known traps

- Two parallel generations: `analysis/clim/sst.py` (old, `g5lib`) and `geospy/sst.py` (new). A `geospy/verification/` package coexists with the top-level `verification/`.
- `plotocn.j` and `plotocn` contain `@`-placeholders substituted by setup scripts; they are not runnable as installed. `plotocn` also names `@anadir/clim/*.py` scripts (e.g. `stress.py`).
- Hard-coded site paths: `geospy/ocnconf.yaml` (`/home/yvikhlia/...`, `/discover/nobackup/...`), `plotocn.j` (discover/borg hostname tests, Python 2.7 module name), and several `analysis/clim/*.py` and `analysis/tseries/plot_extent_ts.py` contain `/discover`, `/home` or `/gpfsm` paths.

## 6. Observations (noted, not fixed)

- `g5lib` uses Python 2 style imports (`from grid import Grid`, implicit relative), while `plotocn.j` loads a Python 2.7 module; `geospy` uses Python 3 (`#!/usr/bin/env python3`).
- The `geospy/Readme.md` clone command (`git clone -b git@github.com:GEOS-ESM/GMAO_Util.git`) names a repository `GMAO_Util` and has no branch argument.
- `ToDo.md` and `CHANGELOG` in `geospy/` track the newer package separately from the repository CHANGELOG.
- Fortran and `reroute` sources under `g5lib/src` are installed but not built by CMake (a local `Makefile` exists for `fortran/`).
