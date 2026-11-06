# GEOS_Util architecture

**Audience:** coding agents and developers working on the GEOS_Util repository.
**Describes:** the MAPL3 line, branch `release/MAPL-v3`.
**Verified against:** `GEOS_Util` @ `0fbacb5` (2026-11-06).
**Placement:** as in the GEOSgcm fixture (`components.yaml` @ `f50622d`): key `GEOS_Util`, checked out at `src/Shared/@GMAO_Shared/@GEOS_Util`.
Other fixtures (for example GEOSadas, GEOSldas) may place this repository
elsewhere; paths inside this repository do not change.

> **Build status on this line:** not built, not ported. On
> `release/MAPL-v3`, `../CMakeLists.txt` (GMAO_Shared) builds only `GMAO_mpeu`,
> `GMAO_hermes` (light) and `GEOS_Shared`, under the comment "not yet ported to
> MAPL3"; `GEOS_Util` appears only in a commented-out list. The code in this
> repository is the MAPL2 code, kept for a later port. The code differs from
> the MAPL2 line in two ways only: (1) the MAPL constants import (`use
> MAPL_Constants` instead of `use MAPL_ConstantsMod`, and `MAPL_UNDEF` from
> `MAPL_Constants` instead of `MAPL_BaseMod`) in `post/*.F*` and
> `plots/zonal.f`; (2) in `post/rs_hinterp.F`, gFTL iteration over `vars` uses
> `ftn_begin()`/`ftn_end()`/`iter%first()` instead of
> `begin()`/`end()`/`iter%key()`. The claims in these documents are otherwise
> the MAPL2-line claims, and describe the sources as they are, not a built
> result.
> `GMAO_gfio` is named only in commented-out blocks of `../CMakeLists.txt`,
> and `GMAO_transf` only in its commented-out list; neither is built on this line. `post` links `GMAO_gfio_r4`, so `post` could not be built here as is.

## Placement
Nested repository of GMAO_Shared. On this line the parent's documents are not written yet; the MAPL2-line versions are on its `develop` branch. Parent: `../../docs/ARCHITECTURE.md`,
`../../AGENTS.md`; the GEOSgcm fixture lists it in its
repository table (`../../../../../docs/ARCHITECTURE.md`).
GEOS_Util is a set of tools, not gridded components.

## Directory map
| Directory | Role | Document |
|---|---|---|
| `pre/` | Restart remapping (`remap_restarts.py`), SST/sea-ice boundary data, pchem generation | [pre](../pre/ARCHITECTURE.md) |
| `post/` | History post-processing scripts, time means, statistics, restart/IC converters | [post](../post/ARCHITECTURE.md) |
| `plots/` | Legacy GrADS plotting package, configured at install time | [plots](../plots/ARCHITECTURE.md) |
| `plots_v2/` | Python forecast statistics and scorecards (`stats_v2/`) | [plots_v2](../plots_v2/ARCHITECTURE.md) |
| `coupled_diagnostics/` | Python ocean/sea-ice diagnostics (two generations) | [coupled_diagnostics](../coupled_diagnostics/ARCHITECTURE.md) |

## Build structure
This describes the build files as written (not reached on this line).
`CMakeLists.txt` sets `alldirs` to `pre plots post coupled_diagnostics` and
calls `esma_add_subdirectories`. `plots_v2` is absent from the list.

| Directory | Compiles | Only installs |
|---|---|---|
| `pre/` | Libraries and executables in `NSIDC-OSTIA_SST-ICE_blend` and `prepare_ocnExtData` | `remap_restart` (globbed scripts, `remap_utils.py` configured); `pchem_species_generation` not installed |
| `post/` | Libraries `post`, `post_nompi`, `tem_lib` and 26 `.x` programs | Scripts and `.rc` files to `post/` and `bin/`; `3CH.j` configured |
| `plots/` | `zonal_<system>.x`, `regrid2_<system>.x` | Scripts and every subdirectory under `<prefix>/plots`; `configure` runs at install time |
| `coupled_diagnostics/` | Nothing | All subdirectories under `<prefix>/coupled_diagnostics` |

### Dependencies on other repositories
(Not reached on this line.)

| Directory | Links |
|---|---|
| `post/` | `MAPL`, `GEOS_Shared`, GMAO_hermes (`../../GMAO_hermes/ARCHITECTURE.md` in the fixture), GMAO_gfio (`../../GMAO_gfio/ARCHITECTURE.md` in the fixture) (`GMAO_gfio_r4`; `_r8` for `convert_aerosols.x`), `ESMF::ESMF` for `stats.x` |
| `pre/` | `MAPL`, `NetCDF::NetCDF_Fortran`; optional f2py modules |
| `plots/` | `MAPL` (`zonal`) |
| `coupled_diagnostics/` | Python modules only; no library link |

No GEOS_Util CMake target links GMAO_transf (`../../GMAO_transf/ARCHITECTURE.md` in the fixture)
(grep of the `CMakeLists.txt` files); `post/` carries its own copies of some
utility modules (see traps). Other library documents:
GMAO_etc (`../../GMAO_etc/ARCHITECTURE.md` in the fixture), GMAO_mpeu (`../../GMAO_mpeu/ARCHITECTURE.md` in the fixture).

## Which job script calls which tool
All paths in `src/Applications` unless stated.
| Caller | Tool | Directory |
|---|---|---|
| `@GEOSgcm_App/gcm_run.j` | `$GEOSUTIL/post/gcmpost.script -source $EXPDIR -movefiles` | `post/` |
| `gcm_run.j` | `$GEOSBIN/remap_restarts.py command_line` | `pre/` |
| `gcm_run.j`, `gcm_run_benchmark.j` | `binarytile.x`, `rs_numtiles.x` from `$GEOSBIN` | `post/` |
| `gcm_post_part_CPLFCST.j` | `gcmpost_CPLFCSTpart.script` | `post/` (not installed) |
| `gcm_forecast.setup`, `gcm_forecast.tmpl` | `$GEOSUTIL/post/tick`; `$GEOSUTIL/bin/stats.x -rc $GEOSUTIL/post/stats.rc` | `post/` |
| `gcm_setup`, `stratchem_setup`, `gmichem_setup`, `geoschemchem_setup` | copy `post.rc`, `plot.rc` into `$EXPDIR` | `post/` |
| same setup scripts | copy `plotocn.j` and `confocn.py` from `coupled_diagnostics/g5lib` | `coupled_diagnostics/` |
| `gcm_quickplot.csh`, `gcm_moveplot.j`, `gcm_quickstat.j` | `$GEOSUTIL/plots/quickplot`, `moveplot`, `quickstat` | `plots/` |
| `post/gcmplot.script`, CPLFCST post scripts | `landscape.script`, `portrait.script` | `plots/` |
| `post/ec2grd.csh`, `ec_prs2fv`, `ec_prs2eta` | `plots/configure`, `grads_util/writegrads.gs` | `plots/` |

No caller found in the fixture for `plots_v2`, the `pre/` ocean-data and
SST/ice tools, or `pchem_species_generation` (*Unverified:* use by GEOSadas or by hand).

## Cross-directory and cross-repository traps
- Two `tick` programs: `post/tick` (perl, installed to `post/`) and the GMAO_etc
  one installed to `bin/` (GMAO_etc (`../../GMAO_etc/ARCHITECTURE.md` in the fixture)). Callers use both
  `$GEOSUTIL/post/tick` and `$GEOSBIN/tick`. See [post](../post/ARCHITECTURE.md).
- `post/` has `dynamics_lattice_module.F`, `mpi_util.F`, `mymalloc.F`, `timer.F`,
  also present in GMAO_transf as separate sources in separate libraries
  (GMAO_transf (`../../GMAO_transf/ARCHITECTURE.md` in the fixture)). `pre/prepare_ocnExtData` has its own `hermes_m_tick.f90`
  next to GMAO_hermes (GMAO_hermes (`../../GMAO_hermes/ARCHITECTURE.md` in the fixture)).
- `gcmpost.script` calls `time_ave_nompi.x`, which no CMake target builds.
- `plots_v2` scripts expect `$GEOSUTIL` but are not installed
  ([plots_v2](../plots_v2/ARCHITECTURE.md)).
- `plots/` is modified at install time by `configure`; `remap_utils.py` and `3CH.j`
  exist in source with unexpanded `@` placeholders and only the configured copy
  is usable ([pre](../pre/ARCHITECTURE.md), [plots](../plots/ARCHITECTURE.md)).
- `coupled_diagnostics` `plotocn.j` and `confocn.py` hold `@` placeholders
  that the setup scripts substitute ([coupled_diagnostics](../coupled_diagnostics/ARCHITECTURE.md)).
- Hard-coded site paths (`/discover/nobackup/...`, `/nobackup/gmao_SIteam`, `/archive/u...`)
  occur in all five directories.
- Two overlapping SST/sea-ice toolchains in `pre/` and two generations of coupled
  diagnostics; `.x` names such as `sst_sic_EIGTHdeg.x` and `sst_sic_eight.x` overlap.
- Source trees carry sources that are installed but not built (for example
  `coupled_diagnostics/g5lib/src/fortran`).

## Children
- [`pre/`](../pre/ARCHITECTURE.md)
- [`post/`](../post/ARCHITECTURE.md)
- [`plots/`](../plots/ARCHITECTURE.md)
- [`plots_v2/`](../plots_v2/ARCHITECTURE.md)
- [`coupled_diagnostics/`](../coupled_diagnostics/ARCHITECTURE.md)

## Parent
GMAO_Shared: `../../docs/ARCHITECTURE.md`,
`../../AGENTS.md`.
