#!/usr/bin/env python3

'''
Plots SSS.
'''

import sys, importlib
import numpy as np
import matplotlib.pyplot as pl
import cmocean
import cartopy.crs as ccrs
import xesmf
import geosdset, plots, utils

plotname='SSS'
defaults={'name': 'SS', 
          'colname': 'geosgcm_ocn2dT', 
          'coltype': 'GEOSTripolar'}

def mkclim(exp,dset):
    '''
    Computes climatology for given experiment.
    '''
    vardata=exp['plots'].get(plotname,defaults)
    varname=vardata['name']

    ds=dset[[varname]].sel(time=slice(*exp['dates']))
    ds=ds.groupby('time.season').mean('time')
    ds['weight']=dset['mask']*dset['area']
    return ds
    
def plot_clim(plotter, exp, clim):
    '''
    Makes climaology plots.
    '''
    vardata=exp['plots'].get(plotname,defaults)
    varname=vardata['name']

    pl.figure(1); pl.clf() 
    var=clim[varname].sel(season='DJF')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]} SSS, DJF')
    pl.savefig(f'{exp["plot_path"]}/sss_djf.png')
    
    pl.figure(2); pl.clf()
    var=clim[varname].sel(season='JJA')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]} SSS, JJA')
    pl.savefig(f'{exp["plot_path"]}/sss_jja.png')

    pl.figure(3); pl.clf()
    var=clim[varname].mean('season')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]} SSS, Annual Mean')
    pl.savefig(f'{exp["plot_path"]}/sss_am.png')

def plot_diff(plotter, exp, cmpexp, clim, cmpclim):
    '''
    Plots climatology difference between two experiments.
    '''
    vardata=exp['plots'].get(plotname,defaults)
    varname1=vardata['name']

    vardata=cmpexp['plots'].get(plotname,defaults)
    varname2=vardata['name']

    rr=xesmf.Regridder(cmpclim[varname2],clim[varname1],'bilinear',periodic=True)
    dif=clim[varname1]-rr(cmpclim[varname2])

    pl.figure(1); pl.clf() 
    var=dif.sel(season='DJF')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]}-{cmpexp["expid"]} SSS, DJF')
    pl.savefig(f'{exp["plot_path"]}/sss-{cmpexp["expid"]}_djf.png')
    
    pl.figure(2); pl.clf()
    var=dif.sel(season='JJA')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]}-{cmpexp["expid"]} SSS, JJA')
    pl.savefig(f'{exp["plot_path"]}/sss-{cmpexp["expid"]}_jja.png')

    pl.figure(3); pl.clf()
    var=dif.mean('season')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]}-{cmpexp["expid"]} SSS, Annual Mean')
    pl.savefig(f'{exp["plot_path"]}/sss-{cmpexp["expid"]}_am.png')

    #rr.clean_weight_file()

def plot_diffobs(plotter, exp, clim, obsclim, obsname):
    '''
    Plots climatology difference against observations
    '''
    vardata=exp['plots'].get(plotname,defaults)
    varname=vardata['name']

    rr=xesmf.Regridder(obsclim,clim[varname],'bilinear',periodic=True)
    # Just doing clim[varname]-rr(obsclim) does not work, because x,y coords have duplicate values
    dif=clim[varname]
    dif.values-=rr(obsclim).values

    pl.figure(1); pl.clf() 
    var=dif.sel(season='DJF')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]}-{obsname} SSS, DJF')
    pl.savefig(f'{exp["plot_path"]}/sss-{obsname}_djf.png')
    pl.savefig(f'{exp["plot_path"]}/sss-obs_djf.png')
    
    pl.figure(2); pl.clf()
    var=dif.sel(season='JJA')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]}-{obsname} SSS, JJA')
    pl.savefig(f'{exp["plot_path"]}/sss-{obsname}_jja.png')
    pl.savefig(f'{exp["plot_path"]}/sss-obs_jja.png')

    pl.figure(3); pl.clf()
    var=dif.mean('season')
    ax=plotter.contour(var, stat=utils.print_stat(var,('x','y'),clim['weight']))
    ax.set_title(f'{exp["expid"]}-{obsname} SSS, Annual Mean')
    pl.savefig(f'{exp["plot_path"]}/sss-{obsname}_am.png')
    pl.savefig(f'{exp["plot_path"]}/sss-obs_am.png')

    #rr.clean_weight_file()

def mkplots(exps, dsets):
    # Calculate climatologies for experiments to comapre
    clims=[]
    for exp,dset in zip(exps,dsets):
        clims.append(mkclim(exp,dset))

    # Plot parameters
    cbar_kwargs={'orientation': 'horizontal',
                 'shrink': 0.8,
                 'label': 'PSU'}
    
    fill_opts={'cmap': cmocean.cm.haline, 
              'levels': np.arange(32.0,38.1,0.4),
               'cbar_kwargs': cbar_kwargs,
               'x': 'lon',
               'y': 'lat'
    }

    contour_opts={'levels': np.arange(32.0,38.1,0.8),
                  'colors': 'black',
                  'x': 'lon',
                  'y': 'lat'
    }

    projection=ccrs.PlateCarree(central_longitude=210.)
    plotmap=plots.PlotMap(projection=projection, fill_opts=fill_opts, 
                          contour_opts=contour_opts)

    # Plots
    plot_clim(plotmap, exps[0], clims[0]) 

    plotmap.fill_opts['levels']=np.arange(-5.,5.1,0.5)
    plotmap.fill_opts['cmap']=cmocean.cm.diff
    plotmap.contour_opts['levels']=np.arange(-5.,5.1,1.0)

    for exp,clim in zip(exps[1:],clims[1:]):
        plot_diff(plotmap, exps[0], exp, clims[0], clim)
        
    obs={'woa18': 's_an'} # Names of observational data set and variable in this data set.
    for obsname,obsvarname in obs.items():
        ds=importlib.import_module('verification.'+obsname).ds_s
        da=ds[obsvarname].sel(depth=slice(0.,10.)).mean('depth')
        obsclim=da.groupby('time.season').mean('time')
        plot_diffobs(plotmap, exps[0], clims[0], obsclim, obsname)

def main(exps):
    dsets=geosdset.load_data(exps, plotname, defaults)
    mkplots(exps,dsets)
    geosdset.close(dsets)            

if __name__=='__main__':
    exps=geosdset.load_exps(sys.argv[1])
    main(exps)
