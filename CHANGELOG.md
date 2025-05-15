# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Updates for MAPL3]

### Changed

- Modified interfaces for variables gFTL container to be V2.  Changes include
  - `%key()` becomes `%first()`
  - `%value()` becomes `%second()`
  - `begin()` and `end()` become `ftn_begin()` and `ftn_end()` respectively.
  - `iter%next()` goes to top of loop instead of bottom.
  - any other `iter%next()` for a `cycle` statement should be deleted.

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

### Deprecated

## [2.1.8] - 2025-05-15

### Changed

- remap_restarts package: bug fix and minor change to accommodate GEOSldas requirements (#137)

## [2.1.7] - 2025-04-23

### Changed

- Remapping seaicetherom_import_rst and saltwater_import_rst if they are in the restart directory

### Fixed

- Fixed issue with `movestat` which only allowed single-month seasons

### Removed

- Removed detection of OS at NCCS as it is all SLES15 now

## [2.1.6] - 2025-01-23

### Fixed

- Patch to fix EXPIDs containing underscores

## [2.1.5] - 2024-12-05

### Changed

- Updates for TEM_Diag to include ALL Times

## [2.1.4] - 2024-12-05

### Changed

- Update GitHub Actions

### Fixed

- Correct bug in `remap_restarts.py` where `N2O` was added as `N20`

## [2.1.3] - 2024-10-08

### Added

- Added remapping for GEOS-IT restarts
- Added new res C1120
- NOTE: If running on SLES15 remap tests will not be zero diff for GOCART RST but are zero diff for all other

### Changed

- Update ESMF CMake target to `ESMF::ESMF`

### Fixed

- Plots package bug fixes for EXPID names containing periods and TEM diagnostics

## [2.1.2] - 2024-07-30

### Changed

- Added MASKFILE for time-discontinuous data in TEM diagnostics

## [2.1.1] - 2024-07-30

### Added

- MOM6 C90 ogrid option to `remap_utils.py`

### Fixed

- Fix quote-v-comma issue in `time_ave.rc` that ESMF 8.6.1 was triggered by.

## [2.1.0] - 2024-06-10

### Added

- Added new BCS version v12
- Updates for TEM diagnostics

### Removed

- Removed mask from `read_reynolds.F90`

## [2.0.8] - 2024-03-29

### Fixed

- Fixed threshold ice concentration (boundary condition), so it is bounded in [0, 1] for atmospheric forecasting with anomaly persistence.
- Fix SLES15 detection in `remap_utils.py` to look for `TRUE` rather than the absence of `TRUE`. This will allow a fix in `ESMA_cmake`
  for correcting other scripting

## [2.0.7] - 2024-02-21

### Changed

- Update of transport plots.

### Fixed

- Fixed `q gxout` bug affecting the stats montage plots.

## [2.0.6] - 2024-02-21

### Added

- Do not remap groups of restarts when it is not necessary, make copies instead.
- Addition of SST and FRACI forecast (ocean) boundary conditions generation capability in `pre/prepare_ocnExtData`
- Added EASE grid option for remapping of land restarts in remap_restarts.py package (facilitates use of package in GEOSldas setup script)
- Added support for SLES15, NAS site and log for remap_lake_landice_saltwater in remap_restarts.py package
- Added "land_only" option for remapping of restarts

### Changed

- Update CMakeLists.txt so it is ready for sparse checkout
- Update CI to v2 orb
- Move to use `cp` and `tar` at NAS rather than the deprecated `mcp` and `mtar`

## [2.0.5] - 2023-12-11

### Fixed

- Fix issue in `remap_bin2nc.py` for remapping MERRA2 restarts to levels other than 72

## [2.0.4] - 2023-11-17

### Added

- Add CI step to make PR to MAPL3 on push to `main`

### Changed

- Add/update command_line options: more items such as label and altbcs were added to `remap_params.tpl`
- Updated paths to the legacy bcs data by pointing to the new "bcs_shared" directory in the GMAO project space.
- Support for new boundary conditions package output layout

### Removed

- Use of haswell nodes on NCCS machines for `cube_BCs.pl`

## [2.0.3] - 2023-08-24

### Changed

- Update CI to use Baselibs default from CircleCI orb

### Fixed

- Eliminate accidental post-processing of *.nc4-partial files
- fixed the cmpz plots for rms and anomaly correlation

## [2.0.2] - 2023-06-28


### Fixed

- Updates to fix dates for comparison plots. Updates for plot levels.

## [2.0.1] - 2023-06-22

### Changed

- Update CI to use Baselibs 7.13.0

### Fixed

- Get number of land tiles from input catch restart file if input bcs path is not available (as in GEOSldas).
- Speed up remap_restarts.py package by adding more processes to catch tiles for fine resolutions.

## [2.0.0] - 2023-05-17

### Fixed

- Fixed issue with `remap_upper.py` where nc4 files were being linked instead of binary files which FV routines require
- Speedup remap_restarts.py package by adding more processes to catch tiles for fine resolutions.

### Changed

- Moved to pass in stretched grid factors to `interp_restarts.x` rather than using a namelist file
- Updates paths to the legacy bcs data by pointing to the new "bcs_shared" directory in the GMAO project space.
- Support for new boundary conditions package output layout


## [1.1.1] - 2023-03-29

### Fixed

- Fixed bad indentation in remap_restarts.py

## [1.1.0] - 2023-03-10

- Plot updates for MOIST variables.
- Add stretched grid to regrid and remap_restarts

### Fixed

- Plot updates to fix QBO labeling.

## [1.0.2] - 2023-03-07

### Added

- Plot updates for MOIST variables.

### Changed

- 3CH and Quickplot Updates: 3CH reads Grads Template file rather than list of actual files used. Quickplot updates allows count.gs utility to skip UNDEF periods.
- Moved `regrid.pl` and the Python `remap_*` scripts from `post/` to `pre/`

### Fixed

- Plot updates to fix QBO labeling.

## [1.0.1] - 2023-01-20

### Fixed

- Fixed a Readme file in coupled diagnostics/geospy to point to GEOS_Util repo instead of GEOS_Shared.

## [1.0.0] - 2023-01-20

### Added

- Initial release of GEOS_Util based on GEOS_Util code from GMAO_Shared v1.6.5
