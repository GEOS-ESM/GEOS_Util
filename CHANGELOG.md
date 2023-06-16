# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

- Updates paths to the legacy bcs data by pointing to the new "bcs_shared" directory in the GMAO project space.
- Support for new boundary conditions package output layout

### Fixed

- Get number of land tiles from input catch restart file if input bcs path is not available (as in GEOSldas).
- Speed up remap_restarts.py package by adding more processes to catch tiles for fine resolutions.

### Removed

### Deprecated

## [1.2.0] - 2023-04-25

### Fixed

- Fixed issue with `remap_upper.py` where nc4 files were being linked instead of binary files which FV routines require

### Changed

- Moved to pass in stretched grid factors to `interp_restarts.x` rather than using a namelist file

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
