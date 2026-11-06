# GEOS_Util decisions

**Audience:** coding agents and developers working on the GEOS_Util repository.
**Describes:** the MAPL3 line, branch `release/MAPL-v3`.
**Verified against:** `GEOS_Util` @ `0fbacb5` (2026-11-06).
**Placement:** as in the GEOSgcm fixture (`components.yaml` @ `f50622d`): key `GEOS_Util`, checked out at `src/Shared/@GMAO_Shared/@GEOS_Util`.
Other fixtures (for example GEOSadas, GEOSldas) may place this repository
elsewhere; paths inside this repository do not change.

Visible structural decisions. Evidence from the source; reasons are inferred.

### Tools installed as source trees rather than built
- Pattern: `coupled_diagnostics/CMakeLists.txt` builds nothing and installs every subdirectory; `pre/remap_restart` and most of `plots/` are installed by glob (`coupled_diagnostics/CMakeLists.txt`, `plots/CMakeLists.txt`, `pre/remap_restart/CMakeLists.txt`). [Verified]
- Likely reason: scripts need no compilation and a glob lets new files appear without editing CMake. [Inferred]
- Question for maintainers: should installed-by-glob test files (`remap_restart/tests`) land in `bin`?

### plots configured at install time
- Pattern: `install(CODE ...)` runs `<prefix>/plots/configure`, which sets `GEOSUTIL`, GrADS paths and symlinks verification files (`plots/CMakeLists.txt`, `plots/configure`). [Verified]
- Likely reason: paths depend on the install prefix and host, known only at install. [Inferred]
- Question for maintainers: is the host detection (`pleiades`, `discover`, desktop) still the intended mechanism?

### plots_v2 kept outside the build
- Pattern: `plots_v2` is absent from `alldirs` and has no `CMakeLists.txt` (`CMakeLists.txt`). [Verified]
- Likely reason: scripts are used in place from the source tree or copied by hand. [Inferred]
- Question for maintainers: is `plots_v2` meant to be installed, and does it supersede `plots/`?

### Two generations of coupled diagnostics
- Pattern: `g5lib` + `analysis` + `verification` (Python 2 style) coexist with `geospy` (Python 3) (`coupled_diagnostics/*`). [Verified]
- Likely reason: `geospy` is a newer rewrite not yet wired into setup scripts, which copy only `g5lib/plotocn.j`. [Inferred]
- Question for maintainers: which generation is current?

### Own copies of utility modules in post
- Pattern: `post` builds its own `dynamics_lattice_module.F`, `mpi_util.F`, `mymalloc.F`, `timer.F` into `post` and `post_nompi` (`post/CMakeLists.txt`); the same names exist in GMAO_transf. [Verified]
- Likely reason: historical copy to avoid a dependency on GMAO_transf. [Inferred]
- Question for maintainers: are the two copies meant to stay separate?
