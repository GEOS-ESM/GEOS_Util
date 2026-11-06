# GEOS_Util

**Audience:** coding agents and developers working on the GEOS_Util repository.
**Describes:** the MAPL2 line, branch `main`.
**Verified against:** `GEOS_Util` @ `5b87f93` (2026-11-06).
**Placement:** as in the GEOSgcm fixture (`components.yaml` @ `0f2e0fb`): key `GEOS_Util`, checked out at `src/Shared/@GMAO_Shared/@GEOS_Util`.
Other fixtures (for example GEOSadas, GEOSldas) may place this repository
elsewhere; paths inside this repository do not change.

## What this repository is
Pre-processing, post-processing, plotting and diagnostics tools for GEOS runs
(Fortran programs, csh/perl/shell scripts, GrADS, Python). It holds no gridded
components. The install prefix is reached by job scripts as `$GEOSUTIL`: the
templates in `src/Applications/@GEOSgcm_App` (`gcm_run.j`, `gcm_post.j`, ...) carry
`setenv GEOSUTIL @GEOSSRC`, and `gcm_setup` sets `GEOSSRC` from `GEOSDIR`
(the installation directory) and substitutes it.

## Place in the GEOSgcm fixture
Nested repository of GMAO_Shared: `../AGENTS.md` and
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
- `CMakeLists.txt` sets `alldirs` to `pre plots post coupled_diagnostics` and
  calls `esma_add_subdirectories`. `plots_v2` is not listed: not built, not installed.
- Some directories compile programs (`post`, `plots`, `pre`); others only
  install source trees (`coupled_diagnostics`, most of `plots`).
- Tests: no test directory or test target at the top level. `pre/remap_restart/tests`
  holds a Python test file and case yamls, installed with the scripts.
