#!/usr/bin/env python3

import xarray as xr
import xesmf as xe

import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import sys

ostia_path = "/discover/nobackup/sakella/projects/bcs_pert/data/data_OSTIA"
geos_path  = "/discover/nobackup/sakella/projects/bcs_pert/tests"

date_str = sys.argv[1]#'20230101'
ds_ostia = xr.open_dataset(ostia_path + "/" + date_str + "-UKMO-L4HRfnd-GLOB-v01-fv02-OSTIA.nc").squeeze()
ds_geos  = xr.open_dataset(geos_path  + "/" + "sst_fraci_" + date_str + ".nc4").squeeze()

regridder = xe.Regridder(ds_ostia, ds_geos, 'conservative', weights='wts_cons_ostia_to_geos_eight.nc')
ds_ostia_on_geos_grid = regridder(ds_ostia, keep_attrs=True)
#

fig = plt.figure(figsize=(16,4))

ax1 = plt.subplot(121, projection=ccrs.PlateCarree( central_longitude=0))
ax1.coastlines()
ax1.add_feature(cfeature.LAND,  facecolor='white', zorder=100)
ax1.add_feature(cfeature.LAKES, edgecolor='gray',  zorder=50)
im1 = ax1.pcolormesh(ds_geos['lon'], ds_geos['lat'], ds_ostia_on_geos_grid.analysed_sst-ds_geos.SST,  transform=ccrs.PlateCarree(), cmap=plt.cm.bwr, vmin=-0.25, vmax=0.25)
gl = ax1.gridlines(crs=ccrs.PlateCarree(), linewidth=1, color='0.85', alpha=0.5, linestyle='-', draw_labels=True)
gl.top_labels = False
cbar=fig.colorbar(im1, extend='both', shrink=0.5, ax=ax1, pad=0.1)
cbar.set_label(r'diff SST')
ax1.set_title(r'%s'%(date_str))

ax2 = plt.subplot(122, projection=ccrs.PlateCarree())
ax2.coastlines()
ax2.add_feature(cfeature.LAND,  facecolor='white', zorder=100)
ax2.add_feature(cfeature.LAKES, edgecolor='gray',  zorder=50)
im2 = ax2.pcolormesh(ds_geos['lon'], ds_geos['lat'], ds_ostia_on_geos_grid.sea_ice_fraction-ds_geos.FRACI,  transform=ccrs.PlateCarree(), cmap=plt.cm.bwr, vmin=-0.1, vmax=0.1)
gl = ax2.gridlines(crs=ccrs.PlateCarree(), linewidth=1, color='0.85', alpha=0.5, linestyle='-', draw_labels=True)
gl.top_labels = False
cbar=fig.colorbar(im2, extend='both', shrink=0.5, ax=ax2, pad=0.1)
cbar.set_label(r'diff FRACI')
ax2.set_title(r'%s'%(date_str))

fName_fig = 'consr_binned_sst_ice_diff_' + date_str + '.png'
plt.savefig(fName_fig, dpi=100)
