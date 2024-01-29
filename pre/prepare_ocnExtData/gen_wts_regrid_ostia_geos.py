#!/usr/bin/env python

import xarray as xr
import xesmf as xe

ostia_path = "/discover/nobackup/sakella/projects/bcs_pert/data/data_OSTIA"
geos_path  = "/discover/nobackup/sakella/projects/bcs_pert/tests"

ds_ostia = xr.open_dataset(ostia_path + "/" + "20230101-UKMO-L4HRfnd-GLOB-v01-fv02-OSTIA.nc").squeeze()
ds_geos  = xr.open_dataset(geos_path  + "/" + "sst_fraci_20230101.nc4").squeeze()

print("Generating weights...")
regridder = xe.Regridder(ds_ostia, ds_geos, "conservative", periodic=True)
print("Done.")

regridder.filename = 'wts_cons_ostia_to_geos_eight.nc'
regridder.to_netcdf()
print("Saved weights for reuse to: ", regridder.filename)

# use generated weights
# regridder = xe.Regridder(ds_ostia, ds_geos, 'conservative', weights='wts_cons_ostia_to_geos_eight.nc')
#ds_ostia_on_geos_grid = regridder(ds_ostia, keep_attrs=True)
