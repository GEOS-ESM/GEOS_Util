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
