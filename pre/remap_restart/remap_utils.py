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

# define some constants for bcs

NewStructureBCTag = ('NL3', 'NL4', 'NL5', 'v06', 'v07', 'v08', 'v09') 
BCBase={}
BCBase['discover_ops']     = "/discover/nobackup/projects/gmao/share/gmao_ops/fvInput/g5gcm/bcs"
BCBase['discover_legacy']  = "/discover/nobackup/projects/gmao/bcs_shared/legacy_bcs"
BCBase['discover_couple'] = "/discover/nobackup/projects/gmao/ssd/aogcm/atmosphere_bcs"
BCBase['discover_ns']  = "/discover/nobackup/projects/gmao/bcs_shared/fvInput/ExtData/esm/tiles"

BCSTag = {}
TagsRank = {}
tag_initialized = False

def init_tags():
   # copy and paste from rigrid.pl
   # minor change. Add "D" to the number for each group
   # BCS Tag: Fortuna-1_4
   global tag_initialized
   if tag_initialized : return
#   F14  = ( 'F14',              'Fortuna-1_4',            'Fortuna-1_4_p1' )
#   D214 = ( 'D214',              'GEOSdas-2_1_4',          'GEOSdas-2_1_4-m1',
#            'GEOSdas-2_1_4-m2', 'GEOSdas-2_1_4-m3',       'GEOSdas-2_1_4-m4' )
#   D540 = ( 'D540',              'GEOSadas-5_4_0',         'GEOSadas-5_4_0_p1',
#            'GEOSadas-5_4_0_p2',  'GEOSadas-5_4_0_p3',    'GEOSadas-5_4_0_p4',
#            'GEOSadas-5_4_1',     'GEOSadas-5_4_1_p1',    'GEOSadas-5_4_2',
#            'GEOSadas-5_4_3',     'GEOSadas-5_4_4',       'GEOSadas-5_5_0',
#            'GEOSadas-5_5_1',     'GEOSadas-5_5_2',       'GEOSadas-5_5_3' )

  # BCS Tag: Fortuna-2_0
  #---------------------
#   F20  = ( 'F20',                    'Fortuna-2_0')

  # BCS Tag: Fortuna-2_1
  #---------------------
#   F21  = ( 'F21',                  'Fortuna-2_1',         'Fortuna-2_1_p1',
#            'Fortuna-2_1_p2',       'Fortuna-2_1_p3',      'Fortuna-2_2',
#            'Fortuna-2_2_p1',       'Fortuna-2_2_p2',      'Fortuna-2_3',
#            'Fortuna-2_3_p1',       'Fortuna-2_4',         'Fortuna-2_4_p1',
#            'Fortuna-2_4_p2',       'Fortuna-2_5',         'Fortuna-2_5_BETA0',
#            'Fortuna-2_5_p1',       'Fortuna-2_5_p2',      'Fortuna-2_5_p3',
#            'Fortuna-2_5_p4',       'Fortuna-2_5_p5',      'Fortuna-2_5_p6',
#            'Fortuna-2_5_pp2' )
#   D561 = ( 'D561',                  'GEOSadas-5_6_1',      'GEOSadas-5_6_1_p1',
#            'GEOSadas-5_6_1_p2',    'GEOSadas-5_6_1_p3',   'GEOSadas-5_6_1_p4',
#            'GEOSadas-5_6_2',       'GEOSadas-5_6_2_p1',   'GEOSadas-5_6_2_p2',
#            'GEOSadas-5_6_2_p3',    'GEOSadas-5_6_2_p4',   'GEOSadas-5_6_2_p5',
#            'GEOSadas-5_6_2_p6',    'GEOSadas-5_7_1',      'GEOSadas-5_7_1_p1',
#            'GEOSadas-5_7_1_p2',    'GEOSadas-5_7_2',      'GEOSadas-5_7_2_p1',
#            'GEOSadas-5_7_2_p2',    'GEOSadas-5_7_2_p2_m1','GEOSadas-5_7_2_p3',
#            'GEOSadas-5_7_2_p3_m1', 'GEOSadas-5_7_2_p3_m2','GEOSadas-5_7_2_p4',
#            'GEOSadas-5_7_2_p5',    'GEOSadas-5_7_2_p5_m1','GEOSadas-5_7_3',
#            'GEOSadas-5_7_3_p1',    'GEOSadas-5_7_3_p2',   'GEOSadas-5_7_3_p2' )

 # BCS Tag: Ganymed-1_0
 #---------------------
#   G10 =  ( 'G10',                  'Ganymed-1_0',          'Ganymed-1_0_BETA',
#            'Ganymed-1_0_BETA1',    'Ganymed-1_0_BETA2',    'Ganymed-1_0_BETA3',
#            'Ganymed-1_0_BETA4' )
#
#   D580 = ( 'D580',                  'GEOSadas-5_8_0',       'GEOSadas-5_9_0',
#            'GEOSadas-5_9_1' )
#
#  # BCS Tags: Ganymed-1_0_M and Ganymed-1_0_D
#  #------------------------------------------
#   G10p = ( 'G10p',                 'Ganymed-1_0_p1',       'Ganymed-1_0_p2',
#            'Ganymed-1_0_p3',       'Ganymed-1_0_p4',       'Ganymed-1_0_p5',
#            'Ganymed-1_0_p6' )
#
#   D591p= ( 'D591p',                 'GEOSadas-5_9_1_p1',    'GEOSadas-5_9_1_p2',
#            'GEOSadas-5_9_1_p3',    'GEOSadas-5_9_1_p4',    'GEOSadas-5_9_1_p5',
#            'GEOSadas-5_9_1_p6',    'GEOSadas-5_9_1_p7',    'GEOSadas-5_9_1_p8',
#            'GEOSadas-5_9_1_p9' )
#
#  # BCS Tags: Ganymed-1_0_M and Ganymed-1_0_D w/ new landice rst
#  #------------------------------------------------------------------------
#   G20  = ( 'G20',                  'Ganymed-2_0',          'Ganymed-2_1',
#            'Ganymed-2_1_p1',       'Ganymed-2_1_p2',       'Ganymed-2_1_p3',
#            'Ganymed-2_1_p4',       'Ganymed-2_1_p5',       'Ganymed-2_1_p6' )
#   D5A0 = ( 'D5A0',                  'GEOSadas-5_10_0',      'GEOSadas-5_10_0_p1' )
#
#
# BCS Tags: Ganymed-1_0_Reynolds and Ganymed-1_0_Ostia
#-----------------------------------------------------
#   G30  = ( 'G30',                  'Ganymed-3_0',         'Ganymed-3_0_p1' )
#   D5B0 = ( '5B0',                  'GEOSadas-5_10_0_p2',  'GEOSadas-5_11_0' )
#
#  # BCS Tags: Ganymed-4_0_Reynolds, Ganymed-4_0_MERRA-2, and Ganymed-4_0_Ostia
#  #---------------------------------------------------------------------------
   G40  = ( 'G40',                  'Ganymed-4_0',         'Ganymed-4_0_p1',
            'Ganymed-4_1',          'Heracles-1_0',        'Heracles-1_1',
            'Heracles-2_0',         'Heracles-2_1',        'Heracles-3_0',
            'Heracles-4_0',         'Heracles-5_4_p3' )
#   D512 = ( '512',                  'GEOSadas-5_12_2',     'GEOSadas-5_12_4',
#            'GEOSadas-5_12_4_p1',   'GEOSadas-5_12_4_p2',  'GEOSadas-5_12_4_p3',
#            'GEOSadas-5_12_5',      'GEOSadas-5_13_0_p1',  'GEOSadas-5_13_0_p2',
#            'GEOSadas-5_13_1',      'GEOSadas-5_16_5' )
#
#  # BCS Tags: Icarus (New Land Parameters, New Topography)
#  #---------------------------------------------------------------------------
   ICA  = ( 'ICA',                  'Icarus',              'Jason' )
   NLv3  = ( 'NLv3',                  'NLV3')
#   D517 = ( '517', 'GEOSadas-5_17_0',      'GEOSadas-5_17_1',     'GEOSadas-5_18_0',
#            'GEOSadas-5_18_1',      'GEOSadas-5_18_2',     'GEOSadas-5_18_3',
#            'GEOSadas-5_18_3_p1',   'GEOSadas-5_19_0',     'GEOSadas-5_20_0',
#            'GEOSadas-5_20_0_p1',   'GEOSadas-5_20_0_p2',  'GEOSadas-5_21_0',
#            'GEOSadas-5_21_2',      'GEOSadas-5_21_3_p1',  'GEOSadas-5_22_0',
#            'GEOSadas-5_22_0_p1',   'GEOSadas-5_22_0_p2',  'GEOSadas-5_23_0',
#            'GEOSadas-5_23_0_p1',   'GEOSadas-5_24_0',     'GEOSadas-5_24_0_p1' )
#   GITOL = ( 'GITOL', '10.3',  '10.4',  '10.5',
#             '10.6',  '10.7',  '10.8',
#             '10.9',  '10.10', '10.11',
#             '10.12', '10.13', '10.14',
#             '10.15', '10.16', '10.17',
#             '10.18'  )

  # BCS Tags: Icarus-NLv3 (New Land Parameters)
  #---------------------------------------------------------------------------
#   INL  = ( 'INL', 'Icarus-NL', 'Icarus-NLv3', 'Jason-NL' )
#   GITNL = ( 'GITNL', '10.19', '10.20', '10.21', '10.22', '10.23' )
#   D525  = ( '525', 'GEOSadas-5_25_1', 'GEOSadas-5_25_1_p5', 'GEOSadas-5_25_p7',
#                    'GEOSadas-5_27_1', 'GEOSadas-5_29_3',    'GEOSadas-5_29_4' )

#   for tag in F14:   BCSTag[tag]= "Fortuna-1_4"
#   for tag in F20:   BCSTag[tag]= "Fortuna-2_0"
#   for tag in F21:   BCSTag[tag]= "Fortuna-2_1"
#   for tag in G10:   BCSTag[tag]= "Ganymed-1_0"
#   for tag in G10p:  BCSTag[tag]= "Ganymed-1_0_M"
#   for tag in G20:   BCSTag[tag]= "Ganymed-1_0_M"
#   for tag in G30:   BCSTag[tag]= "Ganymed-1_0_Reynolds"
   for tag in G40:   BCSTag[tag]= "Ganymed-4_0_Reynolds"
   for tag in ICA:   BCSTag[tag]= "Icarus_Reynolds"
   for tag in NLv3:  BCSTag[tag]= "Icarus-NLv3_Reynolds"
#   for tag in GITOL: BCSTag[tag]= "Icarus_Reynolds"
#   for tag in INL:   BCSTag[tag]= "Icarus-NLv3_Reynolds"
#   for tag in GITNL: BCSTag[tag]= "Icarus-NLv3_Reynolds"
#   for tag in NewStructureBCTag: BCSTag[tag]= tag
#

#   for tag in D214:  BCSTag[tag]= "Fortuna-1_4"
#   for tag in D540:  BCSTag[tag]= "Fortuna-1_4"
#   for tag in D561:  BCSTag[tag]= "Fortuna-2_1"
#   for tag in D580:  BCSTag[tag]= "Ganymed-1_0"
#   for tag in D591p: BCSTag[tag]= "Ganymed-1_0_M"
#   for tag in D5A0:  BCSTag[tag]= "Ganymed-1_0_M"
#   for tag in D5B0:  BCSTag[tag]= "Ganymed-1_0_Reynolds"
#   for tag in D512:  BCSTag[tag]= "Ganymed-4_0_Reynolds"
#   for tag in D517:  BCSTag[tag]= "Icarus_Reynolds"
#   for tag in D525:  BCSTag[tag]= "Icarus-NLv3_Reynolds"
#
   TagsRank['Ganymed-4_0_Reynolds'] = 12
   TagsRank['Ganymed-4_0_Ostia']    = 13
   TagsRank['Ganymed-4_0_MERRA-2']  = 14
   TagsRank['Icarus_Reynolds']      = 15
   TagsRank['Icarus_MERRA-2']       = 16
   TagsRank['Icarus_Ostia']         = 17
   TagsRank['Icarus-NLv3_Reynolds'] = 18
   TagsRank['Icarus-NLv3_MERRA-2']  = 19
   TagsRank['Icarus-NLv3_Ostia']    = 20
   for tag in NewStructureBCTag: TagsRank[tag] = 21
   tag_initialized = True

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
  x['input:shared:expid'] = expid
  x['input:shared:model'] = 'data'
  x['input:shared:agrid'] = 'C180'
  x['input:shared:ogrid'] = '1440x720'
  x['input:shared:tag']   = 'Ganymed-4_0'
  x['input:surface:catch_model']   = 'catch'
  x['input:shared:rst_dir'] = x['output:shared:out_dir'] + '/merra2_tmp_'+x['input:shared:yyyymmddhh']+'/'

  return False

def fvcore_name(x):
  ymdh = x['input:shared:yyyymmddhh']
  time = ymdh[0:8] + '_'+ymdh[8:10]
  rst_dir = x.get('input:shared:rst_dir')
  if not rst_dir : return False

  x['input:shared:rst_dir'] = rst_dir.strip() # remove extra space

  files = glob.glob(rst_dir+'/*fvcore_*')

  if len (files) == 0 : return False

  if len(files) == 1: 
    fname = files[0]

  if len(files) > 1 :
    files = glob.glob(rst_dir+'/*fvcore_*'+time+'*')
    fname = files[0]
  fvrst = os.path.dirname(os.path.realpath(__file__)) + '/fvrst.x -h '
  cmd = fvrst + fname
  #print(cmd +'\n')
  p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
  (output, err) = p.communicate()
  p_status = p.wait()
  ss = output.decode().split()
  lat = int(ss[0])
  lon = int(ss[1])
  if (lon != lat*6) :
      sys.exit('This is not a cubed-sphere grid fvcore restart. Please contact SI team')
  ymdh  = x.get('input:shared:yyyymmddhh')
  ymdh_ = str(ss[3]) + str(ss[4])[0:2]
  if (ymdh_ != ymdh) :
      print("Warning: The date in fvcore is " + ymdh_ )
  x['input:shared:agrid'] = "C"+ss[0] # save for air parameter
  print("The input fvcore restart has air grid: " + "C" + ss[0] + '\n')
  expid = os.path.basename(fname).split('fvcore')[0]
  expid = expid[0:-1]
  x['input:shared:expid'] = expid 
  return fname

def data_ocean_default(resolution):
   # the default string should match the choice in remapl_question.py
   default_ = 'CS  (same as atmosphere OSTIA cubed-sphere grid)' 
   if resolution in ['C12','C24', 'C48'] : default_ = '360x180   (Reynolds)'
   return default_

def get_bcs_basename(bcs):
  if not bcs: return ""
  k = bcs.find('/geometry')
  if k != -1 :
     bcs = bcs[0:k]
  while bcs[-1] == '/': bcs = bcs[0:-1] # remove extra '/'
  return os.path.basename(bcs)

def we_default(tag):
   default_ = '26'
   if tag =='NLv3' : default_ = '13'
   if tag in NewStructureBCTag  : default_ = '13'
   return default_

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
   subprocess.call(['chmod', '+x',out_dir + '/remap_restarts.CMD'])

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

   in_tagin = ''
   if answers.get("input:shared:tag"):
     in_tagin = " -tagin " + answers["input:shared:tag"]        
   tagout = " -tagout " + answers["output:shared:tag"]       

   ocnmdlin  = ''
   if answers.get("input:shared:model"):
      ocnmdlin  = ' -ocnmdlin ' + answers.get("input:shared:model")
   ocnmdlout = ' -ocnmdlout ' + answers["output:shared:model"]

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

   account = " -account " + answers["slurm:account"]
   qos     = " -qos  " + answers["slurm:qos"]
   constraint  = " -constraint  " + answers["slurm:constraint"]


   cmdl = "remap_restarts.py command_line " + merra2 + \
                                          ymdh  + \
                                          grout + \
                                          levsout  + \
                                          out_newid + \
                                          ocnmdlin + \
                                          ocnmdlout + \
                                          oceanin + \
                                          oceanout + \
                                          in_tagin + \
                                          tagout + \
                                          rst_dir  + \
                                          out_dir  + \
                                          in_bcsdir + \
                                          out_bcsdir + \
                                          catch_model + \
                                          zoom + \
                                          wemin + \
                                          wemout + \
                                          label + \
                                          nobkg + \
                                          nolcv + \
                                          out_rs + \
                                          account + \
                                          qos + \
                                          constraint

         
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

def get_bcTag(tag, ogrid):
  bctag = BCSTag[tag]
  if bctag in NewStructureBCTag : return bctag
  if ogrid[0].upper() == "C":
     bctag=bctag.replace('_Reynolds','_Ostia')
  else:
     xy = ogrid.upper().split('X')
     x = int(xy[0])
     if x == 1440:   bctag=bctag.replace('_Reynolds','_MERRA-2')
     if x == 2880:
        bctag=bctag.replace('_Reynolds','_Ostia')
        bctag=bctag.replace('_M','_D')
  return bctag

def get_grid_subdir(bcdir, agrid, ogrid, model):
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
  init_tags()
  tag   = x.get('input:shared:tag')
  agrid = x.get('input:shared:agrid')
  ogrid = x.get('input:shared:ogrid')
  model = x.get('input:shared:model')
  if opt.upper() == "OUT":
    tag   = x.get('output:shared:tag')
    agrid = x.get('output:shared:agrid')
    ogrid = x.get('output:shared:ogrid')
    model = x.get('output:shared:model')

  bcdir   = ''
  base = 'discover_legacy'
  if model != "data":
     base = 'discover_couple'
  if tag in NewStructureBCTag:
     base = 'discover_ns'
  if x.get('input:shared:MERRA-2') and opt.upper() == "IN":
     base = 'discover_ops'

  bc_base = BCBase[base]

  bctag   = get_bcTag(tag,ogrid)
  tagrank = TagsRank[bctag]

  if (tagrank >= TagsRank['NL3']) :
     bcdir = bc_base+'/'+ bctag+'/geometry/'
  elif (tagrank >= TagsRank['Icarus-NLv3_Reynolds']) :
     bcdir = bc_base+'/Icarus-NLv3/'+bctag+'/'
     if model == 'MOM6' or model == 'MOM5':
        bcdir = bc_base+'/Icarus-NLv3/'+model+'/'
  elif (tagrank >= TagsRank['Icarus_Reynolds']):
     if bc_base == BCBase['discover_ops']:
        bcdir = bc_base+'/Icarus_Updated/'+bctag+'/'
     else:
        bcdir = bc_base+'/Icarus/'+bctag+'/'
     if model == 'MOM6' or model == 'MOM5':
        bcdir = bc_base+'/Icarus/'+model+'/'
  elif(tagrank >= TagsRank["Ganymed-4_0_Reynolds"]):
     bcdir = bc_base + '/Ganymed-4_0/'+bctag+'/'
     if model == 'MOM6' or model == 'MOM5':
        bcdir = bc_base+'/Ganymed/'+model+'/'
  else:
     bcdir = bc_base + '/' + bctag + '/'
     if model == 'MOM6' or model == 'MOM5':
        bcdir = bc_base+'/Ganymed/'+model+'/'

  if not os.path.exists(bcdir):
     exit("Cannot find bc dir " +  bcdir)


  gridStr = get_grid_subdir(bcdir,agrid, ogrid, model)
  bcdir =  bcdir + gridStr

  return bcdir


if __name__ == '__main__' :
   config = yaml_to_config('c24Toc12.yaml')
   print_config(config)
