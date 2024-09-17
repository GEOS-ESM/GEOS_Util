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
  def remove_geosit(self):
    if self.config['input']['shared']['GEOS-IT']:
      print(" remove temporary folder that contains GEOS-IT archived files ... \n")
      subprocess.call(['/bin/rm', '-rf', self.config['input']['shared']['rst_dir']])

  def copy_without_remap(self, restarts_in, compared_file_in, compared_file_out, suffix, catch=False):
#
#    Determine if remapping is needed for a group of restart files, or if the input restart files 
#    can just simply be copied to the output dir, based on the following dependency table:
#
#    restarts     | agrid/stretch | #levels | topo files | tile file | bcs version
#    ----------------------------------------------------------------------------
#    upper air    |       X       |    X    |     X      |           |
#    catch/vegdyn |       X       |         |            |     X     |     X
#    landice      |       X       |         |            |     X     |
#
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

       # for catchment, even tile files are the same, if bc is different, it still need remap
       if (catch) :
          if in_bc_version != out_bc_version : return False

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

  def copy_geosit(self):
    if not self.config['input']['shared']['GEOS-IT']:
        return 
     
    expid = self.config['input']['shared']['expid']
    yyyymmddhh_ = str(self.config['input']['shared']['yyyymmddhh'])
    yyyy_ = yyyymmddhh_[0:4]
    mm_   = yyyymmddhh_[4:6]
    day_  = yyyymmddhh_[6:8]  # Extract the day from yyyymmddhh_
          
    time_suffix = '_21z' 
    time_suffix_nc4 = '_2100z' 
        
    geos_it_rst_dir = '/discover/nobackup/projects/gmao/geos-it/dao_ops/archive/' + expid + '/rs/Y' + yyyy_ + '/M' + mm_ + '/'
    rst_dir = self.config['input']['shared']['rst_dir'] + '/'
    os.makedirs(rst_dir, exist_ok=True)
             
    print('Stage GEOS-IT restarts \n from \n    ' + geos_it_rst_dir + '\n to\n    ' + rst_dir + '\n')

    # Only use the specific day from yyyymmddhh_
    filename = f'{expid}.rst.{yyyy_}{mm_}{day_}{time_suffix}.tar'
    src_file = os.path.join(geos_it_rst_dir, filename)
    dest_file = os.path.join(rst_dir, filename)
    if os.path.exists(dest_file):
       print('tar file is copied and untar, no need to copy')
       return
    if os.path.exists(src_file):
        print(f"Copying file {src_file} to {dest_file}")
        shutil.copy(src_file, dest_file)

        # Untar the .tar file using the tar command
        if os.path.exists(dest_file):
            print(f"Untarring {dest_file} to {rst_dir}")
            try:
                subprocess.run(['tar', '-xf', dest_file, '-C', rst_dir], check=True)
                print(f"Untarred {dest_file} successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error untarring {dest_file}: {e}")

        # Optionally remove the tar file after extraction
        #os.remove(dest_file)
    else:
                print(f"Tar file {src_file} does not exist.")

    # Now handle the additional .nc4 file
    nc4_filename = f'{expid}.agcm_import_rst.{yyyy_}{mm_}{day_}{time_suffix_nc4}.nc4'
    src_nc4_file = os.path.join(geos_it_rst_dir, nc4_filename)
    dest_nc4_file = os.path.join(rst_dir, nc4_filename)

    # Copy the .nc4 file if it exists
    if os.path.exists(src_nc4_file):
        print(f"Copying .nc4 file {src_nc4_file} to {dest_nc4_file}")
        shutil.copy(src_nc4_file, dest_nc4_file)
    else:
        print(f" agcm_import_rst file {src_nc4_file} does not exist.")
