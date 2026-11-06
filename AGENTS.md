# GEOS_Util

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

## What this repository is
Pre-processing, post-processing, plotting and diagnostics tools for GEOS runs
(Fortran programs, csh/perl/shell scripts, GrADS, Python). It holds no gridded
components. The install prefix is reached by job scripts as `$GEOSUTIL`: the
templates in `src/Applications/@GEOSgcm_App` (`gcm_run.j`, `gcm_post.j`, ...) carry
`setenv GEOSUTIL @GEOSSRC`, and `gcm_setup` sets `GEOSSRC` from `GEOSDIR`
(the installation directory) and substitutes it.

## Place in the GEOSgcm fixture
Nested repository of GMAO_Shared. On this line the parent's documents are not written yet; the MAPL2-line versions are on its `develop` branch. Parent: `../AGENTS.md` and
`../docs/ARCHITECTURE.md`. Fixture:
`../../../../AGENTS.md` and
`../../../../docs/ARCHITECTURE.md`.

## Documents
| Document | Content |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Directory map, build structure, which job script calls which tool, cross-directory traps |
| [`docs/decisions.md`](docs/decisions.md) | Visible structural decisions |
| [`pre/ARCHITECTURE.md`](pre/ARCHITECTURE.md) | Restart remapping, ocean external data, pchem generation |
| [`post/ARCHITECTURE.md`](post/ARCHITECTURE.md) | History post-processing, time means, statistics, restart/IC converters |
| [`plots/ARCHITECTURE.md`](plots/ARCHITECTURE.md) | GrADS plotting package (legacy) |
| [`plots_v2/ARCHITECTURE.md`](plots_v2/ARCHITECTURE.md) | Python forecast statistics and scorecards (not built) |
| [`coupled_diagnostics/ARCHITECTURE.md`](coupled_diagnostics/ARCHITECTURE.md) | Python ocean/sea-ice diagnostics |

## Rules for agents
- Note bugs and oddities; do not fix them unless asked.
- Keep the documents current when you change the code they describe.
- The directory documents are directory-level: purpose, build, callers. Read
  the source for per-script or per-routine detail.
- Check `docs/ARCHITECTURE.md` (cross-directory traps) before editing: names
  such as `tick` and the `dynamics_lattice_module` family exist in more than
  one repository.

## Build and test
This describes the build files as written; the repository is not reached by the build on this line.
- `CMakeLists.txt` sets `alldirs` to `pre plots post coupled_diagnostics` and
  calls `esma_add_subdirectories`. `plots_v2` is not listed: not built, not installed.
- Some directories compile programs (`post`, `plots`, `pre`); others only
  install source trees (`coupled_diagnostics`, most of `plots`).
- Tests: no test directory or test target at the top level. `pre/remap_restart/tests`
  holds a Python test file and case yamls, installed with the scripts.
