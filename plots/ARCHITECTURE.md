# plots: GrADS/csh plotting and verification package

**Audience:** coding agents and developers working on the GEOS_Util GrADS plotting package (`plots/`).
**Describes:** the MAPL3 line, branch `release/MAPL-v3`.
**Verified against:** `GEOS_Util` @ `0fbacb5` (2026-11-06).
**Placement:** as in the GEOSgcm fixture (`components.yaml` @ `f50622d`): key `GEOS_Util`, checked out at `src/Shared/@GMAO_Shared/@GEOS_Util`; this directory is `plots/`.
Other fixtures (for example GEOSadas, GEOSldas) may place this repository
elsewhere; paths inside this repository do not change.

## 1. Purpose

`plots/` is the legacy GEOS plotting package: csh drivers that run GrADS
(`.gs`) scripts over model history output and compare it with observational
verification datasets (ERBE, SRB, CERES and others). It produces seasonal
maps, zonal means, time series, forecast statistics and Taylor diagrams, and
copies results to a web server. It is a tool directory, not a gridded
component.

## 2. Build and install

From `plots/CMakeLists.txt`:

- `zonal_${CMAKE_SYSTEM_NAME}.x` from `zonal.f` (links `MAPL`).
- `regrid2_${CMAKE_SYSTEM_NAME}.x` from `grads_util/regrid2.f` (no library).
- Installed unchanged to `<prefix>/plots`: `quickplot`, `landscape.script`,
  `portrait.script`, `moveplot`, `movestat`, `get_exports`, `chckhist.new`,
  `chckhist.old`, `chckrc`, `zonal` (csh wrapper for the executable).
- `quickstat` and `configure` go through `configure_file(... @ONLY)` and the
  configured copy is installed to `<prefix>/plots`.
- Every subdirectory of `plots/` (found by a `CONFIGURE_DEPENDS` glob) is
  installed whole under `<prefix>/plots`, keeping source permissions.
- `install(CODE ...)` runs `<prefix>/plots/configure` in `<prefix>/plots` at
  install time, last.

What `configure` (csh) does:
1. Detects the host (`pleiades`, `discover`, else "desktop") and sets
   `TOPODIR`, `VERIFICATION`, OpenGrADS location (`GRADS`, `GXYAT`) and
   ImageMagick on `PATH` from hard-coded site paths.
2. Sets `GEOSUTIL` (to `@CMAKE_INSTALL_PREFIX@`), `GASCRP`
   (`$GEOSUTIL/plots/grads_util`), `GAUDFT`, `GAUDXT`; creates
   `grads_util/udft_<arch>.tools` from `udft.template` (sed of `GEOSUTIL`, `ARCH`)
   if missing.
3. Symlinks `../VERIFICATION_RCS/VERIFICATION.<dataset>.rc` into each
   per-quantity directory that uses that dataset (SRB, ERBE, CERES_EBAF and
   others), by `ln -sf`.
   (Read through the dataset-linking loop only; the rest of the file was not read.)

Present but neither built nor installed individually: nothing outside the glob;
`formulas`, `.tmpl`, `.stk`/`.stack` files are installed with their directories.

## 3. Contents

| Item | Role |
|---|---|
| `quickplot` (tcsh) | Entry point. `-source DIR -season S [-cmpexp DIR] [-lat/lon box] [-begdate/-enddate] [-plots LIST] [-plotsdir]`; reads `plot.rc` per quantity and drives GrADS |
| `quickstat` | Entry point for statistics plots (configured copy); needs `GEOSUTIL`; runs `$GEOSUTIL/plots/configure` itself and substitutes `@GEOSBIN`/`@GEOSSRC` in the files it generates (`quickstat`) |
| `moveplot`, `movestat` | Copy plots/stats to a web server (`~/.WEBID`, `~/.WEBSERVER`, gif) |
| `landscape.script`, `portrait.script` | Drivers for the quickplot plot lists; `-list`, `-plots`, `-v` options. Header gives list-making recipe |
| `get_exports`, `chckrc`, `chckhist.new/old` | Match HISTORY.rc exports/collections against plottable quantities; check plot `.rc` files |
| `configure` | Install-time environment/symlink setup (section 2) |
| `zonal.f`, `zonal` | Zonal-mean fortran program and its wrapper |
| `grads_util/` | Shared GrADS library (`.gs` functions, `regrid2.f`, `udft.template`, `writegrads.gs`) |
| `VERIFICATION_RCS/` | `VERIFICATION.<dataset>.rc` files linked by `configure` |
| Per-quantity directories | Pattern: one directory per plotted quantity holding `plot.rc` (and `.gs`/helper scripts, dataset `.rc` symlinks). Examples: `cldtt`, `cldhi/md/lo`, `lwp`, `tpw`, `precip`/`precipcn`/`precipls`, `olr`/`olrc`/`olrcf`, `osr*`, `nettoa*`, `lwg*`/`swg*` (up/dwn/net, clear-sky `c`, `cf`), `taux`, `tauy`, `T2M`, `UU10M`, `sst`, `tskin`, `albedo`, `eflux`, `hflux`, `uflux`, `emp` |
| `fcst/` | Forecast-statistics plots (`pltcor*.gs`, `pltrms*.gs`, `*.stack`, `setup_statd`, `gif_stats`) |
| `zcmp`, `zcmp1`, `hcmp`, `lcmp` | Zonal/horizontal/line comparison plots |
| `tseries`, `taylor`, `diurnal` | Time series, Taylor diagrams (`taylor_*.gs`), diurnal cycle (python and `run_diurnal`) |
| `res/` | Residual circulation / EP-flux (`makeres`, `run_residual`, `.gs`, python) |
| `aerosol`, `moist`, `turb`, `gwd`, `rad`, `phys`, `cloud`, `formulas` | Topical plot groups and formula definitions |

## 4. Who uses it

- `src/Applications/@GEOSgcm_App/gcm_quickplot.csh`: runs `$GEOSUTIL/plots/quickplot` (line 28).
- `gcm_moveplot.j`: runs `$GEOSUTIL/plots/moveplot` (lines 62, 73).
- `gcm_quickstat.j`: `cd $GEOSUTIL/plots` (line 41).
- `post/gcmplot.script` (lines 393, 396) and `post/gcmpost_CPLFCSTfull.script`/`..part.script` (around lines 1113-1131): call `landscape.script` and `portrait.script` (`-list`, `-plots`).
- `post/ec2grd.csh`, `post/ec_prs2fv`, `post/ec_prs2eta`: call `plots/configure` and `plots/grads_util/writegrads.gs`.
- `post/ecmwf2geos.pl` puts a hard-coded `.../GEOSadas/.../plots/grads_util` on its Perl `use lib` path.

## 5. Known traps

- `configure` embeds site paths (`/nobackup/gmao_SIteam`, `/discover/nobackup/...`, `/ford1/...`); the "desktop" branch comments say the package is only partly enabled there.
- Installed `<prefix>/plots` is modified at install time (`udft_<arch>.tools`, symlinks); the source tree holds the unlinked state.
- `quickplot` and `quickstat` abort unless `GEOSUTIL` is set.

## 6. Observations (noted, not fixed)

- The `install(DIRECTORY)` glob also picks up any new subdirectory automatically.
- `chckhist.new` and `chckhist.old` are both installed; no caller was searched for.
- File counts: 251 `.gs`; 127 `.rc` (125 regular files, 2 symlinks: `UU10M/VERIFICATION.GSSTF.rc`, `SPEED/VERIFICATION.COADS.rc`).
