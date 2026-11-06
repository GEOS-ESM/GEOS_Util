# post/ — post-processing, restart and initial-condition tools

**Audience:** coding agents and developers working on the GEOS_Util post-processing, restart and initial-condition tools (`post/`).
**Describes:** the MAPL3 line, branch `release/MAPL-v3`.
**Verified against:** `GEOS_Util` @ `0fbacb5` (2026-11-06).
**Placement:** as in the GEOSgcm fixture (`components.yaml` @ `f50622d`): key `GEOS_Util`, checked out at `src/Shared/@GMAO_Shared/@GEOS_Util`; this directory is `post/`.
Other fixtures (for example GEOSadas, GEOSldas) may place this repository
elsewhere; paths inside this repository do not change.

## 1. Purpose

The largest GEOS_Util directory (about 99 entries, ~75k lines). It holds (a) the
scripts that post-process GCM history output (monthly means, climatologies,
archive and plot job launch), (b) Fortran programs that analyse output (time
means, statistics, TEM diagnostics), and (c) programs that build or convert
restarts and initial conditions (regrid, vertical interpolation, analysis
increments). It is not a gridded component.

## 2. Build and install

`GMAO_gfio` is named only in commented-out blocks of `../CMakeLists.txt`, and `GMAO_transf` only in its commented-out list; neither is built on this line. `post` links `GMAO_gfio_r4`, so `post` could not be built here as is. This section describes the build files as written (not reached on this line).

On this line the parent's documents are not written yet; the MAPL2-line versions are on its `develop` branch.

From `CMakeLists.txt` (parent repository GMAO_Shared; library docs: GMAO_hermes (`../../GMAO_hermes/ARCHITECTURE.md` in the fixture), GMAO_gfio (`../../GMAO_gfio/ARCHITECTURE.md` in the fixture), GMAO_transf (`../../GMAO_transf/ARCHITECTURE.md` in the fixture)):

- Libraries: `${this}` (`dynamics_lattice_module.F mpi_util.F mymalloc.F PWSSSP.F windfix.F timer.F gmap.F alias.F fft.F`; depends on `GEOS_Shared MAPL GMAO_hermes`) and `post_nompi` (`dynamics_lattice_module.F mpi_util.F mymalloc.F timer.F`; depends on `MAPL GMAO_hermes`). Both are compiled with `-Dmpi`. `flat2hdf.x` and `stats.x` link `post_nompi` (which depends on GMAO_hermes).
- Executables from `<name>.F` with `DEFINITIONS mpi`: `makeiau hdf2rs gg2fv eta2prs eta2rst rs_hinterp convert_eta rs2hdf AI_prs2eta ec_prs2fv flat2hdf fvrst gg2eta ec_prs2eta merra2scm rsg3_vinterp era5_prs2eta` (each `.x`). On this line `rs_hinterp.F` iterates the gFTL `vars` container with `ftn_begin()`/`ftn_end()`/`iter%first()` (MAPL2 line: `begin()`/`end()`/`iter%key()`).
- Other executables: `binarytile.x`, `rs_numtiles.x`, `rs_vinterp.x`, `rs_vinterp_scm.x` (`.F90`); `time_ave.x` and `Create_TEM_Diag.x` (share the `tem_lib` OBJECT library built from `TEM.F90`); `stats.x` (`stats.F90`, links `post_nompi`, big-endian flag); `convert_aerosols.x` (links `GMAO_gfio_r8 MAPL_cfio_r8`); `3CH_mpi.x` (`3CH.F90`).
- Link dependencies: most programs link `GMAO_gfio_r4` (`GMAO_gfio_r8` for `convert_aerosols.x`), `MAPL`, and `GMAO_hermes`.
- Installed to `bin/`: `ecmwf2geos.pl`, `g5fcst_stats.pl`, `ncep2geos.pl`, `ec2grd.csh`, plus the executables above.
- Installed to `post/` (programs): `gcmpost.script tick get_streams get_archive getdates gcmclim.script check_clim run_gcmclim.script`; (files): `plot.rc post.rc stats.rc statsNx.rc time_ave.rc 3CH.rc`; `3CH.j` is configured (`@BINARY_INSTALL_DIR@`) and installed there. `stats.rc time_ave.rc statsNx.rc` are also installed to `etc/`.
- Present but neither built nor installed: `regridding/` (only `cub2latlon.py`; no `add_subdirectory` found in this `CMakeLists.txt`), `gcmplot.script`, `gcmpost_CPLFCSTfull/part.script`, `plot_CPLFCST.rc`, `stats.script`, `fire.F`, `interp.F`, `ec_eta2fv.F`, `ncep_prs2fv.F`, `gfio_get.F`, `swapendian*`, `checkdate.F`, `fix_undef.F90`, `netcdf.inc`, `unused_dummy.H`, small csh helpers (`stats`, `monthly`, `scpget`, `cmprst`, `convert_hist`, ...).

## 3. Contents

Post-processing chain (read from `gcmpost.script`):

1. `gcmpost.script -source $EXPDIR [-movefiles]` parses `HISTORY.rc` via `get_streams`/`get_archive`, moves files from `holding/<stream>` into `YYYYMM` directories, and uses `getdates` and `tick` for date arithmetic.
2. When a month is complete it builds `gcm_post.<collection>.j<date>` from `$SOURCE/post/gcm_post.j` with `sed` and submits it (`qsub`/`sbatch`). That job's means come from `$GEOSUTIL/bin/time_ave.x` with `time_ave.rc` (linked from `$GEOSUTIL/post`); in the "Performing time average" branch, `time_ave_nompi.x` is run when NCPUS is NULL or 1 or `RUN_CMD` is unset, and `$RUN_CMD $NCPUS time_ave.x` otherwise.
3. Archive (`gcm_archive.j`) and plot (`plot.rc`, via `$SOURCE/plot`) jobs are spawned from the same script; `post.rc` (`POST_SEASONS` etc.) and `plot.rc` (`PLOT_STATUS`, `PLOT_SEASONS`, `CLIM_STATUS`) are the controls.
4. `gcmclim.script` and `run_gcmclim.script` make monthly/seasonal/annual and diurnal climatologies from the monthly files; `check_clim` checks them.

| Role | Entries |
|---|---|
| Driver scripts | `gcmpost.script` (entry point), `gcmpost_CPLFCSTfull/part.script` (coupled forecast variants), `gcmclim.script`, `run_gcmclim.script`, `gcmplot.script` (QUICKPLOT launcher), `stats.script` |
| Script helpers | `tick`, `getdates`, `get_streams`, `get_archive`, `check_clim`, `monthly`, `scpget` |
| Time means / climatology | `time_ave.F` (`time_ave.rc`: quadratics, aliases), `TEM.F90`, `Create_TEM_Diag.F` |
| Statistics | `stats.F90` (`stats.rc`, `statsNx.rc`; forecast vs analysis), `g5fcst_stats.pl`, `3CH.F90` (+`3CH.j`, `3CH.rc`) |
| Restart tools | `rs_hinterp.F`, `rs_vinterp.F90`, `rs_vinterp_scm.F90`, `rsg3_vinterp.F`, `rs_numtiles.F90`, `binarytile.F90`, `fvrst.F`, `rs2hdf.F`, `hdf2rs.F`, `eta2rst.F`, `makeiau.F` (analysis increments) |
| IC from other analyses | `ecmwf2geos.pl`, `ncep2geos.pl`, `ec_prs2eta.F`, `era5_prs2eta.F`, `AI_prs2eta.F`, `ec_prs2fv.F`, `gg2eta.F`, `gg2fv.F`, `merra2scm.F`, `convert_eta.F`, `convert_aerosols.F` |
| Format/vertical conversion | `eta2prs.F`, `flat2hdf.F`, `swapendian*`, `fix_undef.F90` |
| Shared library code | `dynamics_lattice_module.F`, `mpi_util.F`, `mymalloc.F`, `timer.F`, `gmap.F`, `alias.F`, `fft.F`, `PWSSSP.F`, `windfix.F` |
| Subdirectory | `regridding/cub2latlon.py` |

## 4. Who uses it

- `gcm_run.j` runs `$GEOSUTIL/post/gcmpost.script -source $EXPDIR -movefiles` (`@GEOSgcm_App/gcm_run.j:1329`); `gcm_post_part_CPLFCST.j:50` runs `gcmpost_CPLFCSTpart.script`; the `@CPLFCST_Etc` scripts grep `gcmpost_CPLFCSTfull.script` for `MASDIR`.
- `gcm_setup` and its family (`stratchem_setup`, `geoschemchem_setup`, `gmichem_setup`) copy `post.rc` into `$EXPDIR/post` and `plot.rc` into `$EXPDIR/plot`.
- `$GEOSUTIL/post/tick` is used in `gcm_forecast.setup` (lines 73, 77) and `gcm_forecast.tmpl` (152, 871, 890).
- `gcm_forecast.tmpl:876-882` runs `$GEOSUTIL/bin/stats.x ... -rc $GEOSUTIL/post/stats.rc`.
- `gcm_run_benchmark.j` and the `gcm_run*` templates run `binarytile.x` and `rs_numtiles.x` from `$GEOSBIN`.
- Library users: ~27 files here use GFIO and `use m_set_eta` (GMAO_hermes) in 13 files. Restart/IC converters, `makeiau`, `hdf2rs`, etc.: no user found in the GEOSgcm fixture (*Unverified:* used by GEOSadas or manually).

## 5. Known traps

- `dynamics_lattice_module.F`, `mpi_util.F`, `mymalloc.F`, `timer.F` duplicate file names in GMAO_transf; the two copies are separate sources in separate libraries.
- `post/tick` (perl) vs a `tick` installed by GMAO_etc: this one is installed to `post/`, while `GMAO_etc/CMakeLists.txt` (`perlscripts`, `DESTINATION bin`) installs its own `tick` to `bin/`. Callers use both `$GEOSUTIL/post/tick` and `$GEOSBIN/tick`.
- `gcmpost_CPLFCSTfull.script` contains a hard-coded `setenv MASDIR /archive/u...` that other scripts grep. Scripts also contain site paths (`/discover/nobackup/...` in `stats.script`) and `discover`-specific batch commands.
- Source files carry `BYTERECLEN`/`EXTENDED_SOURCE`/`FREAL8` per-file flags; wrong flags change record lengths.
- `3CH.j` is configured at build time; edit `3CH.j` in the source, not the generated copy.

## 6. Observations (noted, not fixed)

- `gcmpost.script` runs `time_ave_nompi.x` in the NCPUS NULL/1 or no-`RUN_CMD` branch of its time-average step, but its executable check (`set execs = "time_ave"`) tests only `time_ave.x`. No `time_ave_nompi.x` target exists in `post/CMakeLists.txt` (`post_nompi` is a library) or elsewhere in GEOS_Util CMake files.
- `regridding/` is not referenced by this `CMakeLists.txt`.
- Setup scripts copy `post.rc` and `plot.rc` by installed path.
- Many `.F` sources listed above (`fire.F`, `interp.F`, `ec_eta2fv.F`) are not built; whether they are obsolete is unclear.
