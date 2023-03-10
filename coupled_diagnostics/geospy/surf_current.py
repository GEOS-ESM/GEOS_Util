#!/usr/bin/env python3

'''
Plots surface currents
'''
import sys
import numpy as np
import matplotlib.pyplot as pl
import cartopy.crs as ccrs
import cmocean
import geosdset, plots

plotname='Surf_current'
defaults={'name': ['US','VS'], 
          'colname': 'geosgcm_ocn2dT', 
          'coltype': 'GEOSTripolar'}

def mkclim(exp,dset):
    '''
    Computes climatology for given experiment.
    '''
    vardata=exp['plots'].get(plotname,defaults)
    varname=vardata['name']

    ds=dset[varname].sel(time=slice(*exp['dates']))
    ds=ds.groupby('time.season').mean('time')
    ds['weight']=dset['mask']*dset['area']
    return ds

def plot_clim(plotter, exp, clim):
    '''
    Makes climaology plots.
    '''
    pl.figure(1); pl.clf() 
    ds=clim.sel(season='DJF')
    ax=plotter.streamplot(ds, x='lon', y='lat', u='US', v='VS')
    ax.set_title(f'{exp["expid"]} Usurf, DJF')
    pl.savefig(f'{exp["plot_path"]}/Usurf_djf.png')
    
    pl.figure(2); pl.clf() 
    ds=clim.sel(season='JJA')
    ax=plotter.streamplot(ds, x='lon', y='lat', u='US', v='VS')
    ax.set_title(f'{exp["expid"]} Usurf, JJA')
    pl.savefig(f'{exp["plot_path"]}/Usurf_jja.png')

def mkplots(exps,dsets):
    clim=mkclim(exps[0],dsets[0])

    # Plot parameters
    cbar_kwargs={'orientation': 'horizontal',
                 'shrink': 0.8,
                 'label': '$m/s$'}
    
    fill_opts={'cmap': cmocean.cm.speed, 
               'levels': (0.01,0.02,0.04,0.06,0.08,0.1,0.2,0.4,0.8,1.5),
               'cbar_kwargs': cbar_kwargs,
               'x': 'lon',
               'y': 'lat'
    }

    stream_opts={'density': (4,2), 
                 'color': 'black'
    }

    projection=ccrs.PlateCarree(central_longitude=210.)
    plotmap=plots.PlotMap(projection=projection, fill_opts=fill_opts,
                          stream_opts=stream_opts)

    # Plots
    plot_clim(plotmap, exps[0], clim)

def main(exps):
    dsets=geosdset.load_data(exps, plotname, defaults)
    mkplots(exps,dsets)
    geosdset.close(dsets)

if __name__=='__main__':
    exps=geosdset.load_exps(sys.argv[1])
    main(exps)
