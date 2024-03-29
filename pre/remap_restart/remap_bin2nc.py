#!/usr/bin/env python3
#
# remap_restarts package:
#   remap_bin2nc.py converts binary MERRA-2 restarts to nc4
#
# As of Sep 2023, MERRA-2 restarts are the only binary restarts that may need to be
# remapped.  The set of yaml config files "bin2nc_merra2_*.yaml" include hard-wired
# variables names, long names, and tile/grid dimensions specific to MERRA-2 restarts.

from yaml import safe_load, load, dump
from netCDF4 import Dataset
import numpy as np
from scipy.io import FortranFile

def writeCVars(coordVars,dimensions):

   for v in coordVars:
       if v=='time':
          coordVars[v][:]=0
       elif (v=='lat') | (v=='lon') | (v=='lev') | (v=='edge'):
          dsize=dimensions[v]
          coords=np.arange(1,dsize+1)
          coordVars[v][:]=coords

def writeVar(v, vars, dimensions, bintype, binf):
   var=vars[v['short_name']]
   dims = v['dimension']
   # is tile?
   if 'tile' in dims:
      if ('subtile' in dims) & (len(dims)==2):
         rec=binf.read_reals(dtype=bintype)
         tilesize=dimensions.get('tile')
         for i in range(dimensions.get('subtile')):
             var[i,:]=rec[i*tilesize:(i+1)*tilesize]
      elif (len(dims)==2) & ( ('unknown_dim1' in dims) | ('unknown_dim2' in dims) ):
         if 'unknown_dim1' in dims:
            dsize=dimensions.get('unknown_dim1')
         if 'unknown_dim2' in dims:
            dsize=dimensions.get('unknown_dim2')
         for i in range(dsize):
            rec = binf.read_reals(dtype=bintype)
            var[i,:]=rec
      elif (len(dims)==3) & ('unknown_dim1' in dims) & ('unknown_dim2' in dims):
         for j in range(dimensions.get('unknown_dim2')):
            for i in range(dimensions.get('unknown_dim1')):
               rec = binf.read_reals(dtype=bintype)
               var[j,i,:]=rec
      elif (len(dims)==1):
         rec = binf.read_reals(dtype=bintype)
         var[:]=rec

   # is gridded
   elif 'lat' in dims:
      if 'lev' in dims:
         for i in range(dimensions.get('lev')):
            rec = binf.read_reals(dtype=bintype)
            var[i,:,:]=rec
      elif 'edge' in dims:
         for i in range(dimensions.get('edge')):
            rec = binf.read_reals(dtype=bintype)
            var[i,:,:]=rec
      else:
         rec = binf.read_reals(dtype=bintype)
         var[:,:]=rec
   # is just lev
   else:
      if 'edge' in dims:
         rec = binf.read_reals(dtype=bintype)
         var[:]=rec

def defineDimVars(fid,dims):
   coordVars = {}
   for d in dims:
       if d=="lon":
          newVar=fid.createVariable(d,'f8',d)
          setattr(newVar,'units','degrees_east')
          setattr(newVar,'long_name','Longitude')
          coordVars.update([(d,newVar)])
       if d=="lat":
          newVar=fid.createVariable(d,'f8',d)
          setattr(newVar,'units','degrees_north')
          setattr(newVar,'long_name','Latitude')
          coordVars.update([(d,newVar)])
       if d=="lev":
          newVar=fid.createVariable(d,'f8',d)
          setattr(newVar,'units','layer')
          setattr(newVar,'long_name','sigma_at_layer_midpoints')
          setattr(newVar,'standard_name','atmosphere_hybrid_sigma_pressure_coordinate')
          setattr(newVar,'coordinate','eta')
          setattr(newVar,'positive','down')
          setattr(newVar,'formulaTerms','ap: ak b: bk ps: ps p0: p00')
          coordVars.update([(d,newVar)])
       if d=="edge":
          newVar=fid.createVariable(d,'f8',d)
          setattr(newVar,'units','level')
          setattr(newVar,'long_name','sigma_at_layer edge')
          setattr(newVar,'standard_name','atmosphere_hybrid_sigma_pressure_coordinate')
          setattr(newVar,'coordinate','eta')
          setattr(newVar,'positive','down')
          setattr(newVar,'formulaTerms','ap: ak b: bk ps: ps p0: p00')
          coordVars.update([(d,newVar)])
       if d=="time":
          newVar=fid.createVariable(d,'f8',d)
          setattr(newVar,'units','minutes since ')
          setattr(newVar,'long_name','time')
          coordVars.update([(d,newVar)])

   return coordVars

def bin2nc(binfile, ncfile, yamlfile, isDouble=False, hasHeader=False, debug=False):
  
  bintype=np.float32
  if (isDouble):
     bintype=np.float64
  
  
  f=open(yamlfile,'r')
  
  data=safe_load(f)
  
  dimensions = data["dimensions"]
  variables = data["variables"]
  
  if debug:
     print(dump(variables))
     print(dump(dimensions))
  
  ncfid = Dataset(ncfile,mode='w',format='NETCDF4')
  
  dimids = {}
  for d in dimensions:
      dsize = dimensions.get(d)
      newDim = ncfid.createDimension(d,dsize)
      dimids.update([(d,newDim)])
  
  cVars = defineDimVars(ncfid,dimids)
      
  vars = {}
  for v in variables:
      sname = v['short_name']
      lname = v['long_name']
      units = v['units']
      dims = v['dimension']
      newVar = ncfid.createVariable(sname,'f4',dims)
      setattr(newVar,'long_name',lname)
      setattr(newVar,'units',units)
      vars.update([(sname,newVar)])
  
  writeCVars(cVars,dimensions)
  
  binf =FortranFile(binfile,'r')
  if hasHeader:
     if debug:
        print("reading header")
     rec = binf.read_ints(dtype=np.int32)
     if debug:
        print(rec)
     rec = binf.read_ints(dtype=np.int32)  
     if debug:
        print(rec)
  
  for v in variables:
     writeVar(v,vars,dimensions,bintype, binf)
  
  ncfid.close()

if __name__ == "__main__":

   bin2nc('fvcore_internal_rst',   'fvcore_internal_rst.nc4',    'bin2nc_merra2_fv.yaml', isDouble=True, hasHeader=True)
   bin2nc('moist_internal_rst',    'moist_internal_rst.nc4',     'bin2nc_merra2_moist.yaml')
   bin2nc('pchem_internal_rst',    'pchem_internal_rst.nc4',     'bin2nc_merra2_pchem.yaml')
   bin2nc('agcm_import_rst',        'agcm_import_rst.nc4',       'bin2nc_merra2_agcm.yaml')
   bin2nc('gocart_internal_rst',   'gocart_internal_rst.nc4',    'bin2nc_merra2_gocart.yaml')
   bin2nc('lake_internal_rst',     'lake_internal_rst.nc4',      'bin2nc_merra2_lake.yaml')
   bin2nc('landice_internal_rst',  'landice_internal_rst.nc4',   'bin2nc_merra2_landice.yaml')
   bin2nc('saltwater_internal_rst','saltwater_internal_rst.nc4', 'bin2nc_merra2_saltwater.yaml')
   bin2nc('catch_internal_rst',    'catch_internal_rst.nc4',     'bin2nc_merra2_catch.yaml')
