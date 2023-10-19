#!/usr/bin/env python3
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
#
# define "choices", "message" strings, and "validate" lists that are used multiple times
#   (and related definitions, even if they are used just once).

choices_bc_ops     = ['NL3', 'ICA', 'GM4', 'Other']

choices_bc_other   = ['v06']

choices_bc_cmd     = ['NL3', 'ICA', 'GM4', 'v06']

choices_omodel     = ['data', 'MOM5', 'MOM6']

choices_catchmodel = ['catch', 'catchcnclm40', 'catchcnclm45']

choices_ogrid_data = ['360x180   (Reynolds)','1440x720  (MERRA-2)','2880x1440 (OSTIA)','CS  (same as atmosphere OSTIA cubed-sphere grid)']

choices_ogrid_cpld = ['72x36', '360x200', '720x410', '1440x1080']

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

          v06:     NL3 + JPL veg height + PEATMAP + MODIS snow alb\n\n'''

message_bc_other_in  = ("Select BCs version of input restarts:\n" + message_bc_other)
message_bc_other_new = ("Select BCs version for new restarts:\n"  + message_bc_other)

message_agrid_list = f'''
 C12   C180    C1440
 C24   C360    C2880
 C48   C720    C5760 
 C90   C1000         \n'''

message_agrid_in   = ("Enter atmospheric grid of input restarts:\n" + message_agrid_list)

message_agrid_new  = ("Enter atmospheric grid for new restarts:\n"  + message_agrid_list)

validate_agrid     = ['C12','C24','C48','C90','C180','C360','C720','C1000','C1440','C2880','C5760']

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
  x['input:shared:bc_version']   = 'GM4'
  x['input:surface:catch_model'] = 'catch'
  x['input:shared:stretch']      = False
  x['input:shared:rst_dir']      = x['output:shared:out_dir'] + '/merra2_tmp_'+x['input:shared:yyyymmddhh']+'/'
  x['input:air:nlevel'] = 72

  return False

def fvcore_info(x):
  if 'input:shared:agrid' in x.keys():
     return True
  rst_dir = x.get('input:shared:rst_dir')
  if not rst_dir : return False
  x['input:shared:rst_dir'] = rst_dir.strip() # remove extra space

  files = glob.glob(rst_dir+'/*fvcore_*')
  if len (files) == 0 : return False

  fname =''
  ymdh  =''

  if len(files) > 1 :
    ymdh = x.get('input:shared:yyyymmddhh')
    if (not ymdh): return False
    time = ymdh[0:8] + '_'+ymdh[8:10]
    files = glob.glob(rst_dir+'/*fvcore_*'+time+'*')
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
      print("(N_lon,N_lat) = ", lon, lat)
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
  fname= ''
  if len(files) == 1:
    fname = os.path.basename(files[0])

  if len(files) > 1 :
    files = glob.glob(rst_dir+'/*fvcore_*'+time+'*')
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

def get_bcs_basename(bcs):
  if not bcs: return ""
  while bcs[-1] == '/': bcs = bcs[0:-1] # remove extra '/'
  return os.path.basename(bcs)

def get_label(config):
  label = ''
  if config['output']['shared']['label']:
     in_resolution  = get_bcs_basename(config['input']['shared']['bcs_dir'])
     out_resolution = get_bcs_basename(config['output']['shared']['bcs_dir'])
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
   if not x['input:shared:MERRA-2']:
      return True
   else:
      x['input:surface:wemin'] = '26'
      return False

def zoom_default(x):
   zoom_ = '8'
   cxx = x.get('input:shared:agrid')
   if cxx :
      lat = int(cxx[1:])
      zoom = lat /90.0
      zoom_ = str(int(zoom))
      if zoom < 1 : zoom_ = '1'
      if zoom > 8 : zoom_ = '8'
   if x['input:shared:MERRA-2'] :
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

   merra2  = " -merra2 " if answers["input:shared:MERRA-2"] else ""    
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
    
   in_bcsdir  = ''
   default_bc = get_bcsdir(answers, "IN")
   if not os.path.samefile(default_bc, answers.get("input:shared:bcs_dir").strip()) :
     in_bcsdir = ' -in_bcsdir ' + answers.get("input:shared:bcs_dir")

   out_bcsdir  = ''
   default_bc = get_bcsdir(answers, "OUT")
   if not os.path.samefile(default_bc, answers.get("output:shared:bcs_dir").strip()) :
     out_bcsdir = ' -out_bcsdir ' + answers.get("output:shared:bcs_dir")

   out_stretch = ''
   if answers["output:shared:stretch"]:   
     out_stretch = ' -out_stretch ' + answers["output:shared:stretch"]
   in_stretch = ''
   if answers["input:shared:stretch"]:   
     in_stretch = ' -in_stretch ' + answers["input:shared:stretch"]

   zoom = " -zoom " + answers["input:surface:zoom"]
   wemin  = " -in_wemin "  + answers["input:surface:wemin"]
   wemout = " -out_wemin " + answers["output:surface:wemin"]
   catch_model =''
   if answers.get("input:surface:catch_model"):
      catch_model = " -catch_model " + answers["input:surface:catch_model"]

   out_rs = " -rs " 
   rs = 3
   if answers['output:air:remap'] and not answers['output:surface:remap']:
       rs = 1
   if answers['output:surface:remap'] and not answers['output:air:remap']:
       rs = 2
   out_rs = out_rs + str(rs)

   noagcm_import_rst  = '' if answers["output:air:agcm_import_rst"] else " -noagcm_import_rst "

   account = " -account " + answers["slurm:account"]
   qos     = " -qos  " + answers["slurm:qos"]
   partition  = " -partition  " + answers["slurm:partition"]


   cmdl = "remap_restarts.py command_line " + merra2 + \
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
                                          in_bcsdir + \
                                          out_bcsdir + \
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

def get_config_from_answers(answers):
   config  = {}
   config['input'] = {}
   config['input']['shared'] = {}
   config['input']['surface'] = {}
   config['output'] = {}
   config['output']['shared'] = {}
   config['output']['air'] = {}
   config['output']['surface'] = {}
   config['output']['analysis'] = {}
   config['slurm'] = {}
   for key, value in answers.items():
     keys = key.split(":")
     if len(keys) == 2:
       config[keys[0]][keys[1]] = value
     if len(keys) == 3:
       config[keys[0]][keys[1]][keys[2]] = value

   return config

def get_grid_subdir(bcdir, agrid, ogrid, model, stretch):
   def get_name_with_grid( grid, names, a_o):
     if not grid :
       return names
     namex = []
     if (grid[0].upper() == 'C'):
       n = int(grid[1:])
       s1 ='{:04d}x6C'.format(n)
       j=n*6
       s2 =str(n)
       s3 =str(j)
       # first try
       for aoname in names:
         name = ''
         if(a_o == 'a'):
           name = aoname.split('_')[0]
         else:
           name = aoname.split('_')[-1]
         if (name.find(s1) != -1 or (name.find(s2) != -1 and name.find(s3) != -1 )):
            namex.append(aoname)
     else:
       xy = grid.upper().split('X')
       s2 = xy[0]
       s3 = xy[1]
       for aoname in names:
         name = ''
         if(a_o == 'a'):
           name = aoname.split('_')[0]
         else:
           name = aoname.split('_')[-1]
         if (name.find(s2) != -1 and name.find(s3) != -1): namex.append(aoname)
     return namex
   #v3.5
   #dirnames = [ f.name for f in os.scandir(bcdir) if f.is_dir()]
   #v2.7
   dirnames = [f for f in os.listdir(bcdir) if os.path.isdir(os.path.join(bcdir,f))]
   if stretch:
      dirnames = [dname for dname in dirnames if stretch in dname]
   anames = get_name_with_grid(agrid, dirnames, 'a')
   gridID = get_name_with_grid(ogrid, anames, 'o')
   if len(gridID) == 0 :
     exit("cannot find the grid subdirctory of agrid: " +agrid+ " and ogrid " + ogrid + " under "+ bcdir)
   g = ''
   gridID.sort(key=len)
   g = gridID[0]

   # For new structure BC
   for g_ in gridID :
     if model == 'MOM5':
        if 'M5' in g_ : g = g_
     if model == 'MOM6':
        if 'M6' in g_ : g = g_

   if len(gridID) >= 2 :
      print("\n Warning! Find many GridIDs in " + bcdir)
      print(" GridIDs found: ", gridID)
      #WY note, found many string in the directory
      print(" This GridID is chosen: " + g)
   return g

def get_bcsdir(x, opt):
  bc_version   = x.get('input:shared:bc_version')
  agrid = x.get('input:shared:agrid')
  ogrid = x.get('input:shared:ogrid')
  model = x.get('input:shared:omodel')
  stretch = x.get('input:shared:stretch')
  if opt.upper() == "OUT":
    bc_version   = x.get('output:shared:bc_version')
    agrid = x.get('output:shared:agrid')
    ogrid = x.get('output:shared:ogrid')
    model = x.get('output:shared:omodel')
    stretch = x.get('output:shared:stretch')

  bc_base = "/discover/nobackup/projects/gmao/bcs_shared/fvInput/ExtData/esm/tiles"
  bcdir = bc_base+'/'+ bc_version+'/geometry/'
  if not os.path.exists(bcdir):
     exit("Cannot find bc dir " +  bcdir)

  gridStr = get_grid_subdir(bcdir,agrid, ogrid, model,stretch)
  bcdir =  bcdir + gridStr

  return bcdir


if __name__ == '__main__' :
   config = yaml_to_config('c24Toc12.yaml')
   print_config(config)
