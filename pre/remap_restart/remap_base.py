#!/usr/bin/env python3
#
# remap_restarts package:
#  remap_base.py does [???]
#
import os
import ruamel.yaml
import shutil
import subprocess
from remap_utils import *

class remap_base(object):
  def __init__(self, **configs):
     for key, value in configs.items():
        if (key == 'params_file'):
          print( "use Config yaml file: " + value)
          self.config = get_config_from_file(value)
          out_dir    = self.config['output']['shared']['out_dir']
          if not os.path.exists(out_dir) : os.makedirs(out_dir)
          f = os.path.basename(value)
          dest = out_dir+'/'+f
          try:
            shutil.copy(value, dest)
          except shutil.SameFileError:
            pass
        if (key == 'config_obj'):
          print( "use Config obj")
          self.config = value
          out_dir    = self.config['output']['shared']['out_dir']
          if not os.path.exists(out_dir) : os.makedirs(out_dir)
        break
  def remove_merra2(self):
    if self.config['input']['shared']['MERRA-2']:
      print(" remove temporary folder that contains MERRA-2 archived files ... \n")
      subprocess.call(['/bin/rm', '-rf', self.config['input']['shared']['rst_dir']])

  def copy_without_remap(self, restarts_in, compared_file_in, compared_file_out, suffix):
     config = self.config
     in_agrid        = config['input']['shared']['agrid']
     out_agrid       = config['output']['shared']['agrid']
     out_levels      = config['output']['air']['nlevel']
     in_bc_version   = config['input']['shared']['bc_version']
     out_bc_version  = config['output']['shared']['bc_version']
     in_stretch      = config['input']['shared']['stretch']
     out_stretch     = config['output']['shared']['stretch']

     if (in_agrid == out_agrid and in_stretch  == out_stretch):

       for rst in restarts_in :
         if 'fvcore_internal' in rst:
           fvrst     = nc.Dataset(rst)
           in_levels = fvrst.dimensions['lev'].size
           if in_levels != int(out_levels): return False

       cmd = 'diff -q ' + compared_file_in + ' ' + compared_file_out
       print('\n' + cmd)
       diff  = subprocess.call(shlex.split(cmd))
       # diff = 0 means no difference
       if diff != 0: return False

       expid = config['output']['shared']['expid']
       if (expid) :
         expid = expid + '.'
       else:
         expid = ''
       out_dir    = config['output']['shared']['out_dir']

       print('\nCopy restart files from  orignal restart files without remapping. \n')
       for rst in restarts_in :
         f = expid + os.path.basename(rst).split('_rst')[0].split('.')[-1]+'_rst.'+suffix
         cmd = '/bin/cp ' + rst + ' ' + out_dir+'/'+f
         print('\n'+cmd)
         subprocess.call(shlex.split(cmd))

       return True

     return False
