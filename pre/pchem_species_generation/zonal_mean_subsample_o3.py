#!/usr/bin/env python3
"""
Compute the zonal mean of O3 from a global NetCDF file and reduce the
latitude grid from 361 (0.5-degree) to 91 points via subsampling (every 4th point).

O3 is converted from mass mixing ratio (kg kg-1) to mole fraction (mol mol-1)
by multiplying by the ratio of the molecular weight of dry air to that of O3.

Output format matches MERRA-2.inst3_3d_asm_Nv.monthly.*.0001x0091x0072.nc4:
  dimensions: (time=1, lev=72, lat=91, lon=1)
  lat: degrees_north, -90 to 90 at 2-degree spacing
  lon: degrees_east, [-180.]

Usage:
    python3 zonal_mean_subsample.py <input_file> <output_file>

Example:
    python3 zonal_mean_subsample.py monthly_ave.201701.nc4 zonal_mean_O3.nc4
"""

import sys
import numpy as np
import netCDF4 as nc

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
if len(sys.argv) != 3:
    print("Usage: python3 zonal_mean_subsample.py <input_file> <output_file>")
    sys.exit(1)

INPUT_FILE  = sys.argv[1]
OUTPUT_FILE = sys.argv[2]
VARNAME     = "O3"

# ---------------------------------------------------------------------------
# Read input
# ---------------------------------------------------------------------------
ds_in = nc.Dataset(INPUT_FILE, "r")

if VARNAME not in ds_in.variables:
    print(f"Error: variable '{VARNAME}' not found in {INPUT_FILE}")
    print(f"Available variables: {list(ds_in.variables.keys())}")
    ds_in.close()
    sys.exit(1)

lat_in  = ds_in.variables["lat"][:]   # (361,)
time_in = ds_in.variables["time"][:]  # (1,)
var_in  = ds_in.variables[VARNAME][:] # (1, 72, 361, 576) masked array

lev_out   = ds_in.variables["lev"][:]
lev_attrs = {a: getattr(ds_in.variables["lev"], a) for a in ds_in.variables["lev"].ncattrs()}

# ---------------------------------------------------------------------------
# Step 1 — Zonal mean (average over all longitudes)
# ---------------------------------------------------------------------------
# Replace fill values with NaN so they don't bias the mean, then average.
var_zm = np.nanmean(np.ma.filled(var_in, np.nan), axis=-1)  # (1, 72, 361)

# Convert O3 from mass mixing ratio (kg kg-1) to mole fraction (mol mol-1).
# The conversion is:  [mol mol-1] = [kg kg-1] * (MW_dryair / MW_O3)
# where MW_dryair = 28.965 g mol-1 and MW_O3 = 47.998 g mol-1.
MW_DRYAIR = 28.965  # g mol-1, mean molecular weight of dry air
MW_O3     = 47.998  # g mol-1, molecular weight of ozone (O3 = 3 * 15.999)
var_zm = var_zm * (MW_DRYAIR / MW_O3)

# ---------------------------------------------------------------------------
# Step 2 — Latitude subsample: 361 → 91
#
#   Take every 4th point from the 361-point 0.5° grid.
#   Indices 0, 4, 8, ..., 360 correspond to -90, -88, -86, ..., +88, +90
#   giving exactly 91 points at 2° spacing.
# ---------------------------------------------------------------------------
indices = np.arange(0, 361, 4)              # 91 indices
var_out = var_zm[:, :, indices, np.newaxis]  # (1, 72, 91, 1)

# Latitude coordinate: -90 to +90 at 2-degree spacing, in degrees_north
lat_out = np.arange(-90., 91., 2., dtype=np.float64)  # 91 points

# Longitude coordinate: single point at -180 degrees_east
lon_out = np.array([-180.], dtype=np.float64)

# ---------------------------------------------------------------------------
# Step 3 — Write output NetCDF
# ---------------------------------------------------------------------------
ds_out = nc.Dataset(OUTPUT_FILE, "w", format="NETCDF4")

# Dimensions
ds_out.createDimension("time", 1)
ds_out.createDimension("lev",  72)
ds_out.createDimension("lat",  91)
ds_out.createDimension("lon",  1)

# Coordinate: time
v = ds_out.createVariable("time", time_in.dtype, ("time",))
for attr in ds_in.variables["time"].ncattrs():
    setattr(v, attr, getattr(ds_in.variables["time"], attr))
v[:] = time_in

# Coordinate: lev — values and attributes taken from reference file
v = ds_out.createVariable("lev", lev_out.dtype, ("lev",))
for attr, val in lev_attrs.items():
    setattr(v, attr, val)
v[:] = lev_out

# Coordinate: lat — degrees_north, -90 to +90 at 2-degree spacing
v = ds_out.createVariable("lat", lat_out.dtype, ("lat",))
v.long_name = "latitude"
v.units = "degrees_north"
v[:] = lat_out

# Coordinate: lon — single point at -180 degrees_east
v = ds_out.createVariable("lon", lon_out.dtype, ("lon",))
v.long_name = "longitude"
v.units = "degrees_east"
v[:] = lon_out

# Data variable
fill_val = ds_in.variables[VARNAME]._FillValue
v = ds_out.createVariable(VARNAME, var_out.dtype, ("time", "lev", "lat", "lon"),
                           fill_value=fill_val)
for attr in ds_in.variables[VARNAME].ncattrs():
    if attr == "_FillValue":
        continue   # already set via fill_value argument
    setattr(v, attr, getattr(ds_in.variables[VARNAME], attr))
# Override units to reflect the mol mol-1 conversion applied above
v.units = "mol mol-1"
v[:] = var_out

# Global attributes
for attr in ds_in.ncattrs():
    setattr(ds_out, attr, getattr(ds_in, attr))
ds_out.History = ds_in.History + "; Zonal mean + lat subsample (361->91, every 4th point) of O3 (converted kg kg-1 -> mol mol-1) by zonal_mean_subsample.py"

ds_in.close()
ds_out.close()

print(f"Done. Output written to {OUTPUT_FILE}")
print(f"  O3 shape: {var_out.shape}  (time, lev, lat, lon)")
print(f"  Lat range: {lat_out[0]:.1f} to {lat_out[-1]:.1f} degrees_north  ({len(lat_out)} points)")
print(f"  Lon: {lon_out[0]:.1f} degrees_east  (1 point)")
