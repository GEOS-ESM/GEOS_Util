# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

### Deprecated

## [1.1.0] - 2023-03-10

- Plot updates for MOIST variables.
- Add stretched grid to regrid and remap_restarts

### Changed

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
