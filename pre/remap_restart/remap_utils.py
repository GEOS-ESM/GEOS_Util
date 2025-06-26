#!/usr/bin/env python3
#
# remap_restarts package:
#   remap_utils.py contains utility functions and definitions
#
import os
import subprocess
import ruamel.yaml
from collections import OrderedDict
import shutil
import questionary
import glob
import shlex
import netCDF4 as nc

# shared global variables

#During cmake step, the string will be changed according to the system

GEOS_SITE       = "@GEOS_SITE@"

# top-level directory for BCs (machine-dependent)

choices_bc_base  =[ "NCCS/Discover : /discover/nobackup/projects/gmao/bcs_shared/fvInput/ExtData/esm/tiles",
                    "NAS           : /nobackup/gmao_SIteam/ModelData/bcs_shared/fvInput/ExtData/esm/tiles",
                    "Custom "                                                                                 ]

# define "choices", "message" strings, and "validate" lists that are used multiple times
#   (and related definitions, even if they are used just once).

choices_bc_ops     = ['NL3', 'ICA', 'GM4', 'Other']

choices_bc_other   = ['v06','v11','v12']

choices_bc_cmd     = ['NL3', 'ICA', 'GM4', 'v06', 'v11','v12']

choices_omodel     = ['data', 'MOM5', 'MOM6']

choices_catchmodel = ['catch', 'catchcnclm40', 'catchcnclm45']

choices_ogrid_data = ['360x180   (Reynolds)','1440x720  (MERRA-2)','2880x1440 (OSTIA)','CS  (same as atmosphere OSTIA cubed-sphere grid)']

choices_ogrid_cpld = ['72x36', '360x200', '540x458', '720x410', '1440x1080']

choices_ogrid_cmd  = ['360x180', '1440x720', '2880x1440', 'CS'] + choices_ogrid_cpld

# the following needs more cleanup; e.g., first define list of SGxxx names and parameters (i.e., STRETCH_GRID),
#   then assemble message_stretch and choices_stretch using this definition

message_stretch =  f'''\n
 Select parameters of stretched cubed-sphere grid for new restarts:

 Name   Stretch_Factor  Focus_Lat  Focus_Lon
 -----  --------------  ---------  ---------
 SG001      2.5            39.5       -98.35
 SG002      3.0            39.5       -98.35
 \n\n'''

STRETCH_GRID = {}
STRETCH_GRID['SG001'] = ['2.50', '39.50', '-98.35']
STRETCH_GRID['SG002'] = ['3.00', '39.50', '-98.35']

choices_stretch    = [False, 'SG001', 'SG002']

choices_res_SG001  = ['C270', 'C540', 'C1080', 'C2160']

choices_res_SG002  = ['C1536']

message_datetime    = "Enter restart date/time:  (Must be 10 digits: yyyymmddhh"

message_out_dir     = "Enter output directory for new restarts:\n"

message_expid       = "Enter experiment ID for new restarts:  (Added as prefix to new restart file names; can leave blank.)\n"

message_bc_base_in  = "BCs base directory for input restarts: \n"
message_bc_base_new = "BCs base directory for new restarts: \n"

message_bc_ops     = f'''\n
 BCs version      | ADAS tags            | GCM tags typically used with BCs version
 -----------------|----------------------|-----------------------------------------
 GM4: Ganymed-4_0 | 5_12_2 ... 5_16_5    | Ganymed-4_0      ... Heracles-5_4_p3
 ICA: Icarus      | 5_17_0 ... 5_24_0_p1 | Icarus, Jason    ... 10.18
 NL3: Icarus-NLv3 | 5_25_1 ... present   | Icarus_NL, 10.19 ... present
 ----------------------------------------------------------------------------------
 Other: Additional choices used in model or DAS development.
           \n\n '''

message_bc_ops_in  = ("Select boundary conditions (BCs) version of input restarts:\n" + message_bc_ops)
message_bc_ops_new = ("Select boundary conditions (BCs) version for new restarts:\n"  + message_bc_ops)

message_bc_other   = f'''\n

          v06:     NL3 + JPL veg height + PEATMAP + MODIS snow alb\n
          v11:     NL3 + JPL veg height + PEATMAP + MODIS snow alb v2\n
          v12:     NL3 + JPL veg height + PEATMAP + MODIS snow alb v2 + Argentina peatland fix \n\n'''\

message_bc_other_in  = ("Select BCs version of input restarts:\n" + message_bc_other)
message_bc_other_new = ("Select BCs version for new restarts:\n"  + message_bc_other)

message_agrid_list = f'''
 C12   C180    C1120
 C24   C360    C1440
 C48   C720    C2880
 C90   C1000   C5760      \n'''

message_agrid_in   = ("Enter atmospheric grid of input restarts:\n" + message_agrid_list)

message_agrid_new  = ("Enter atmospheric grid for new restarts:\n"  + message_agrid_list)

validate_agrid     = ['C12','C24','C48','C90','C180','C360','C720','C1000','C1120','C1440','C2880','C5760']

message_ogrid_in   = "Select data ocean grid/resolution of input restarts:\n"

message_ogrid_new   = "Select data ocean grid/resolution of output restarts:\n"

message_qos        = "SLURM or PBS quality-of-service (qos)?  (If resolution is c1440 or higher, enter 'allnccs' for NCCS or 'normal' for NAS.)\n"

message_account    = "Select/enter SLURM or PBS account:\n"

message_partition  = "Enter SLURM or PBS partition: (If desired, can leave blank)\n"


job_directive = {"SLURM": """#!/bin/csh -f
#SBATCH --account={account}
#SBATCH --ntasks={NPE}
#SBATCH --job-name={job_name}
#SBATCH --output={log_name}
#SBATCH --qos={QOS}
#SBATCH --time={TIME}
#SBATCH --constraint={CONSTRAINT}
{PARTITION}
""",
"PBS": """#!/bin/csh -f
#PBS -l walltime={TIME}
#PBS -l select={NNODE}:ncpus=40:mpiprocs=40:model={CONSTRAINT}
#PBS -N {job_name}
#PBS -q {QOS}
#PBS -W group_list={account}
#PBS -o {log_name}
#PBS -j oe
{PARTITION}
"""
}

# --------------------------------------------------------------------------------

def init_merra2(x):
  if not x.get('input:shared:MERRA-2') : return False

  yyyymm = int(x.get('input:shared:yyyymmddhh')[0:6])
  if yyyymm < 197901 :
     exit("Error. MERRA-2 data < 1979 not available\n")
  elif (yyyymm < 199201):
     expid = "d5124_m2_jan79"
  elif (yyyymm < 200106):
     expid = "d5124_m2_jan91"
  elif (yyyymm < 201101):
     expid = "d5124_m2_jan00"
  elif (yyyymm < 202106):
     expid = "d5124_m2_jan10"
  # There was a rewind in MERRA2 from Jun 2021 to Sept 2021
  elif (yyyymm < 202110):
     expid = "d5124_m2_jun21"
  else:
     expid = "d5124_m2_jan10"
  x['input:shared:expid']        = expid
  x['input:shared:omodel']       = 'data'
  x['input:shared:agrid']        = 'C180'
  x['input:shared:ogrid']        = '1440x720'
  x['input:shared:omodel']       = 'data'
  x['input:shared:bc_version']   = 'GM4'
  x['input:shared:bc_base']     = '/discover/nobackup/projects/gmao/bcs_shared/fvInput/ExtData/esm/tiles'
  x['input:surface:catch_model'] = 'catch'
  x['input:shared:stretch']      = False
  x['input:shared:rst_dir']      = x['output:shared:out_dir'] + '/merra2_tmp_'+x['input:shared:yyyymmddhh']+'/'
  x['input:air:nlevel']          = 72

  return False

def init_geosit(x):
  if not x.get('input:shared:GEOS-IT') : return False

  yyyymm = int(x.get('input:shared:yyyymmddhh')[0:6])

  if yyyymm < 199701:
      exit("Error. GEOS-IT data < 1997 not available\n")
  elif 199612 <= yyyymm <= 200712:
      expid = "d5294_geosit_jan98"
  elif 200801 <= yyyymm < 201801:
      expid = "d5294_geosit_jan08"
  elif yyyymm >= 201801:
      expid = "d5294_geosit_jan18"  # For any date starting from 201801 and beyond
  else:
      exit("Error. GEOS-IT data not available for this date\n")

  x['input:shared:expid']        = expid
  x['input:shared:omodel']       = 'data'
  x['input:shared:agrid']        = 'C180'
  x['input:shared:ogrid']        = 'CS'
  x['input:shared:omodel']       = 'data'
  x['input:shared:bc_version']   = 'NL3'
  x['input:shared:bc_base']     = '/discover/nobackup/projects/gmao/bcs_shared/fvInput/ExtData/esm/tiles'
  x['input:surface:catch_model'] = 'catch'
  x['input:shared:stretch']      = False
  x['input:shared:rst_dir']      = x['output:shared:out_dir'] + '/geosit_tmp_'+x['input:shared:yyyymmddhh']+'/'
  x['input:air:nlevel']          = 72

  return False


def fvcore_info(x):
  if 'input:shared:agrid' in x.keys():
     return True
  rst_dir = x.get('input:shared:rst_dir')
  if not rst_dir : return False
  x['input:shared:rst_dir'] = rst_dir.strip() # remove extra space

  files = glob.glob(rst_dir+'/*fvcore_internal*')
  if len (files) == 0 : return False

  fname =''
  ymdh  =''

  if len(files) > 1 :
    ymdh = x.get('input:shared:yyyymmddhh')
    if (not ymdh): return False
    time = ymdh[0:8] + '_'+ymdh[8:10]
    files = glob.glob(rst_dir+'/*fvcore_internal*'+time+'*')
    fname = files[0]

  if len(files) == 1:
    fname = files[0]

  fvrst = nc.Dataset(fname)
  lon = fvrst.dimensions['lon'].size
  lat = fvrst.dimensions['lat'].size
  lev = fvrst.dimensions['lev'].size
  x['input:air:nlevel'] = lev
  ymdh = fvrst.variables['time'].units.split('since ')[1].split(":")[0].replace('-','').replace(' ', "")
  if (lat != lon*6) :
      print("(N_lon, N_lat) = ", lon, lat)
      exit('This is not a cubed-sphere grid fvcore restart. Please contact SI team')
  x['input:shared:yyyymmddhh'] = ymdh
  x['input:shared:agrid'] = "C"+str(lon)
  print("The input fvcore restart has atm grid: " + "C" + str(lon) + '\n')
  print("The input fvcore restart has time: " + ymdh + '\n')
  expid = os.path.basename(fname).split('fvcore')[0]
  expid = expid[0:-1]
  x['input:shared:expid'] = expid
  if (expid) : print("The input fvcore restart has experiment ID " + expid + '\n')

  # get stretch parameters from input restart file
  x['input:shared:stretch'] = False
  stretch_factor = fvrst.__dict__.get('STRETCH_FACTOR')
  if (stretch_factor) :
     target_lat = fvrst.__dict__.get('TARGET_LAT')
     target_lon = fvrst.__dict__.get('TARGET_LON')
     sg = [stretch_factor, target_lat, target_lon]
     # verify that stretched cubed-sphere grid is supported by remap_restarts.py
     f_ = [f"{number:.{2}f}" for number in sg]
     print("[stretch_factor, target_lat, target_lon]: ", f_)
     if f_ == STRETCH_GRID['SG001']:
       x['input:shared:stretch'] = 'SG001'
     elif f_ == STRETCH_GRID['SG002'] :
       x['input:shared:stretch'] = 'SG002'
     else:
       exit("This stretched cubed-sphere grid is not supported ")
  return True

def catch_model(x):
  ymdh = x['input:shared:yyyymmddhh']
  time = ymdh[0:8] + '_'+ymdh[8:10]
  rst_dir = x.get('input:shared:rst_dir')
  if not rst_dir : return False

  x['input:shared:rst_dir'] = rst_dir.strip() # remove extra space

  files = glob.glob(rst_dir+'/*catch*')

  if len (files) == 0 : return False
  fname = ''
  fname = os.path.basename(files[0])

  model = 'catch'
  if 'cnclm40' in fname.lower():
    model = 'catchcnclm40'
  if 'cnclm45' in fname.lower():
    model = 'catchcnclm45'
  return model

def data_ocean_default(resolution):
   # the default string should match the choice in remapl_question.py
   default_ = 'CS  (same as atmosphere OSTIA cubed-sphere grid)'
   if resolution in ['C12','C24', 'C48'] : default_ = '360x180   (Reynolds)'
   return default_

def get_label(config):
  label = ''
  if config['output']['shared']['label']:
     agrid     = config['output']['shared']['agrid']
     ogrid     = config['output']['shared']['ogrid']
     omodel    = config['output']['shared']['omodel']
     stretch   = config['output']['shared']['stretch']
     EASE_grid = config['output']['surface'].get('EASE_grid', None)

     out_resolution = get_resolutions(agrid=agrid, ogrid=ogrid, omodel=omodel, stretch=stretch, grid=EASE_grid)

     agrid     = config['input']['shared']['agrid']
     ogrid     = config['input']['shared']['ogrid']
     omodel    = config['input']['shared']['omodel']
     stretch   = config['input']['shared']['stretch']
     EASE_grid = config['input']['surface'].get('EASE_grid', None)

     in_resolution = get_resolutions(agrid=agrid, ogrid=ogrid, omodel=omodel, stretch=stretch, grid=EASE_grid)

     in_bcv         =  config['input']['shared']['bc_version']
     out_bcv        =  config['output']['shared']['bc_version']
     label = '.' + in_bcv  + '.' + in_resolution + \
             '.' + out_bcv + '.' + out_resolution
  return label

# NOTE: "wemin" is a configurable parameter that can be set to anything, independent
#       of the bcs version.  The default set here is simply the "wemin" value that is
#       typically used with the bcs version.  The user needs to confirm the default
#       value or overwrite it with the "wemin" value used in the simulation that is
#       associated with the given set of restarts.
def wemin_default(bc_version):
   default_ = '13'
   if bc_version =='GM4' or bc_version == 'ICA' : default_ = '26'
   return default_

def show_wemin_default(x):
   if x['input:shared:MERRA-2']:
       x['input:surface:wemin'] = '26'
       return False
   elif x['input:shared:GEOS-IT']:
       x['input:surface:wemin'] = '13'
       return False
   else:
       # If neither MERRA2 or GEOS-IT is selected option will be shown on screen
       return True

def zoom_default(x):
   zoom_ = '8'
   cxx = x.get('input:shared:agrid')
   if cxx :
      lat = int(cxx[1:])
      zoom = lat /90.0
      zoom_ = str(int(zoom))
      if zoom < 1 : zoom_ = '1'
      if zoom > 8 : zoom_ = '8'
   if x.get('input:shared:MERRA-2') or x.get('input:shared:GEOS-IT'):
      zoom_ = '2'
   return zoom_

def get_account():
   cmd = 'id -gn'
   p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
   (accounts, err) = p.communicate()
   p_status = p.wait()
   accounts = accounts.decode().split()
   return accounts[0]

def config_to_yaml(config, yaml_file, noprompt = False):
   if os.path.exists(yaml_file) and not noprompt :
      overwrite = questionary.confirm("Do you want to overwrite " + yaml_file + "?" , default=False).ask()
      if not overwrite :
         while True:
           new_name = questionary.text("What's the backup name?  ", default=yaml_file +'.1').ask()
           if os.path.exists(new_name):
              print('\n'+ new_name + ' exists, please enter a new one. \n')
           else:
              shutil.move(yaml_file, new_name)
              break
   yaml = ruamel.yaml.YAML()
   out_dir = os.path.dirname(yaml_file)
   if not os.path.exists(out_dir) : os.mkdir(out_dir)
   with open(yaml_file, "w") as f:
      yaml.dump(config, f)

def yaml_to_config(yaml_file):
   yaml = ruamel.yaml.YAML()
   stream =''
   with  open(yaml_file, 'r') as f:
     stream = f.read()
   config = yaml.load(stream)
   return config

def write_cmd( out_dir, cmdl) :

   out_dir = os.path.realpath(out_dir)
   if not os.path.exists(out_dir) : os.makedirs(out_dir)
   bin_path = os.path.dirname(os.path.realpath(__file__))
   cmdl = bin_path+'/'+ cmdl
   with open(out_dir + '/remap_restarts.CMD', 'w') as f:
     f.write(cmdl)
   # Don't run remap_ressatrs.CMD directly. It may overwrite itself
   #subprocess.call(['chmod', '+x',out_dir + '/remap_restarts.CMD'])

def print_config( config, indent = 0 ):
   for k, v in config.items():
     if isinstance(v, dict):
        print("   " * indent, f"{k}:")
        print_config(v, indent+1)
     else:
        print("   " * indent, f"{k}: {v}")

def get_command_line_from_answers(answers):

   merra2  = " -merra2 " if answers.get("input:shared:MERRA-2", False) else ""
   geosit  = " -geosit " if answers.get("input:shared:GEOS-IT", False) else ""
   ymdh    = " -ymdh    " + answers["input:shared:yyyymmddhh"]
   rst_dir = " -rst_dir " + answers["input:shared:rst_dir"]

   grout     = ' -grout '   + answers["output:shared:agrid"]
   levsout   = ' -levsout ' + answers["output:air:nlevel"]

   out_dir   = ' -out_dir ' + answers["output:shared:out_dir"]
   newid     = answers["output:shared:expid"]

   out_newid=''
   if newid.strip():
     out_newid = " -newid " + newid

   bcvin = ''
   if answers.get("input:shared:bc_version"):
     bcvin = " -bcvin " + answers["input:shared:bc_version"]
   bcvout = " -bcvout " + answers["output:shared:bc_version"]

   ocnmdlin  = '-ocnmdlin data'
   if answers.get("input:shared:omodel"):
      ocnmdlin  = ' -ocnmdlin ' + answers.get("input:shared:omodel")

   ocnmdlout = ' -ocnmdlout data'
   if answers.get("output:shared:omodel"):
      ocnmdlout = ' -ocnmdlout ' + answers["output:shared:omodel"]

   oceanin=''
   ogrid = answers.get("input:shared:ogrid")
   if ogrid :
      if ogrid[0] == 'C':
         ogrid = "CS"
      oceanin  = ' -oceanin ' + ogrid

   ogrid = answers.get("output:shared:ogrid")
   if ogrid[0] == 'C':
      ogrid = "CS"
   oceanout = ' -oceanout ' + ogrid

   nobkg  = '' if answers["output:analysis:bkg"] else " -nobkg "
   nolcv  = '' if answers["output:analysis:lcv"] else " -nolcv "

   label  = ' -lbl ' if answers["output:shared:label"] else ""

   in_bc_base  = ' -in_bc_base '  + answers.get("input:shared:bc_base")
   out_bc_base = ' -out_bc_base ' + answers.get("output:shared:bc_base")

   out_stretch = ''
   if answers["output:shared:stretch"]:
     out_stretch = ' -out_stretch ' + answers["output:shared:stretch"]
   in_stretch  = ''
   if answers["input:shared:stretch"]:
     in_stretch  = ' -in_stretch ' + answers["input:shared:stretch"]

   zoom   = " -zoom "      + answers["input:surface:zoom"]
   wemin  = " -in_wemin "  + answers["input:surface:wemin"]
   wemout = " -out_wemin " + answers["output:surface:wemin"]
   catch_model =''
   if answers.get("input:surface:catch_model"):
      catch_model = " -catch_model " + answers["input:surface:catch_model"]

   out_rs = " -rs "
   rs = 3
   if answers['output:air:remap'] and not answers['output:surface:remap_catch']:
       rs = 1
   if answers['output:surface:remap_catch'] and not answers['output:air:remap']:
       rs = 2
   out_rs = out_rs + str(rs)

   noagcm_import_rst  = '' if answers["output:air:agcm_import_rst"] else " -noagcm_import_rst "

   account = " -account " + answers["slurm_pbs:account"]
   qos     = " -qos  " + answers["slurm_pbs:qos"]
   partition = ''
   if answers["slurm_pbs:partition"] != '':
      partition  = " -partition  " + answers["slurm_pbs:partition"]

   cmdl = "remap_restarts.py command_line " + merra2 + \
                                          geosit + \
                                          ymdh  + \
                                          grout + \
                                          levsout  + \
                                          out_newid + \
                                          ocnmdlin + \
                                          ocnmdlout + \
                                          oceanin + \
                                          oceanout + \
                                          bcvin + \
                                          bcvout + \
                                          rst_dir  + \
                                          out_dir  + \
                                          in_bc_base + \
                                          out_bc_base + \
                                          out_stretch + \
                                          in_stretch + \
                                          catch_model + \
                                          zoom + \
                                          wemin + \
                                          wemout + \
                                          label + \
                                          nobkg + \
                                          noagcm_import_rst + \
                                          nolcv + \
                                          out_rs + \
                                          account + \
                                          qos + \
                                          partition


   return cmdl

def flatten_nested(nested_dict, result=None, prefix=''):
  if result is None:
    result = dict()
  for k, v in nested_dict.items():
    new_k = ':'.join((prefix, k)) if prefix else k
    if not (isinstance(v, dict) or isinstance(v, OrderedDict)):
      result.update({new_k: v})
    else:
      flatten_nested(v, result, new_k)
  return result

def get_config_from_file(file):
  yaml = ruamel.yaml.YAML()
  stream = ''
  with  open(file, 'r') as f:
    stream = f.read()
  config = yaml.load(stream)
  return config

def get_config_from_answers(answers, config_tpl = False):
   config  = {}
   if config_tpl:
     remap_tpl = os.path.dirname(os.path.realpath(__file__)) + '/remap_params.tpl'
     config = get_config_from_file(remap_tpl)
   else:
     config['input'] = {}
     config['input']['air'] = {}
     config['input']['shared'] = {}
     config['input']['surface'] = {}
     config['output'] = {}
     config['output']['shared'] = {}
     config['output']['air'] = {}
     config['output']['surface'] = {}
     config['output']['analysis'] = {}
     config['slurm_pbs'] = {}

   for key, value in answers.items():
     keys = key.split(":")
     if len(keys) == 2:
       config[keys[0]][keys[1]] = value
     if len(keys) == 3:
       config[keys[0]][keys[1]][keys[2]] = value

   bc_version = config['output']['shared'].get('bc_version')
   config['output']['surface']['split_saltwater'] = True
   if 'Ganymed' in bc_version :
     config['output']['surface']['split_saltwater'] = False

   return config

def get_resolutions(agrid=None, ogrid=None, omodel=None, stretch=None, grid=None):
   if grid is not None : return grid
   aname = ''
   oname = ''
   if (agrid[0].upper() == 'C'):
      n = int(agrid[1:])
      aname ='CF{:04d}x6C'.format(n)

   if (ogrid[0].upper() == 'C'):
      oname = aname
   else:
      xy = ogrid.upper().split('X')
      s0 = int(xy[0])
      s1 = int(xy[1])
      if omodel == 'data':
         oname = 'DE{:04d}xPE{:04d}'.format(s0,s1)
      if omodel == 'MOM5':
         oname = 'M5TP{:04d}x{:04d}'.format(s0,s1)
      if omodel == 'MOM6':
         oname = 'M6TP{:04d}x{:04d}'.format(s0,s1)
   if stretch:
      aname = aname + '-' + stretch

   resolutions = aname +'_' + oname

   return resolutions

def get_default_bc_base():
   cmd = 'uname -n'
   p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
   (node, err) = p.communicate()
   p_status = p.wait()
   node = node.decode().split()
   node0 = node[0]
   discover = ['dirac', 'borg','warp', 'discover']
   for node in discover:
      if node in node0:
         return choices_bc_base[0]
   return choices_bc_base[1]

def get_topodir(bc_base, bc_version, agrid=None, ogrid=None, omodel=None, stretch=None):
  gridStr = get_resolutions(agrid=agrid, ogrid=ogrid, omodel=omodel,stretch=stretch)
  agrid_name = gridStr.split('_')[0]
  bc_topo = ''
  if 'GM4' == bc_version:
     bc_topo = bc_base + '/' + bc_version + '/TOPO/TOPO_' + agrid_name
  else:
     bc_topo = bc_base + '/' + bc_version + '/TOPO/TOPO_' + agrid_name + '/smoothed'

  return bc_topo

def get_landdir(bc_base, bc_version, agrid=None, ogrid=None, omodel=None, stretch=None, grid=None):
  gridStr = get_resolutions(agrid=agrid, ogrid=ogrid, omodel=omodel,stretch=stretch, grid=grid)
  bc_land = bc_base+'/'+ bc_version+'/land/'+gridStr
  return bc_land

def get_geomdir(bc_base, bc_version, agrid=None, ogrid=None, omodel=None, stretch=None, grid=None):
  bc_geom =  get_landdir(bc_base, bc_version, agrid=agrid, ogrid=ogrid, omodel=omodel, stretch=stretch, grid=grid). replace('/land/', '/geometry/')
  return bc_geom

def remove_ogrid_comment(x, opt):
  ogrid = ''
  if opt == "IN":
    ogrid = x.get('input:shared:ogrid')
  else:
    ogrid = x.get('output:shared:ogrid')
  if not ogrid: return False

  ogrid = ogrid.split()[0]
  if opt == "IN":
    if ogrid == 'CS':
       ogrid = x['input:shared:agrid']
    x['input:shared:ogrid'] = ogrid
  else:
    if ogrid == 'CS':
       ogrid = x['output:shared:agrid']
    x['output:shared:ogrid'] = ogrid

  return False

if __name__ == '__main__' :
   config = yaml_to_config('c24Toc12.yaml')
   print_config(config)
