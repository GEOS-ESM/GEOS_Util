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

NewStructureBCTag = ('NL3', 'NL4', 'NL5', 'v06', 'v07', 'v08', 'v09') 
BCBase={}
BCBase['discover_ops']     = "/discover/nobackup/projects/gmao/share/gmao_ops/fvInput/g5gcm/bcs"
BCBase['discover_legacy']  = "/discover/nobackup/projects/gmao/bcs_shared/legacy_bcs"
BCBase['discover_couple'] = "/discover/nobackup/projects/gmao/ssd/aogcm/atmosphere_bcs"
BCBase['discover_ns']  = "/discover/nobackup/projects/gmao/bcs_shared/fvInput/ExtData/esm/tiles"

def fvcore_name(x):
  ymdh = x['input:shared:yyyymmddhh']
  time = ymdh[0:8] + '_'+ymdh[8:10]
  rst_dir = x.get('input:shared:rst_dir')
  if not rst_dir : return False

  files = glob.glob(rst_dir+'/*fvcore_*')
  if len(files) == 1: 
    fname = files[0]
    print('\nFound ' + fname)
    return fname

  if len(files) > 1 :
    files = glob.glob(rst_dir+'/*fvcore_*'+time+'*')
    fname = files[0]
    print('\nFound ' + fname)
    return fname

  return False

def tmp_merra2_dir(x):
   tmp_merra2 = x['output:shared:out_dir']+ '/merra2_tmp_'+x['input:shared:yyyymmddhh']+'/'
   return tmp_merra2

def data_ocean_default(resolution):
   # the default string should match the choice in remapl_question.py
   default_ = 'CS  (same as atmosphere OSTIA cubed-sphere grid)' 
   if resolution in ['C12','C24', 'C48'] : default_ = '360x180   (Reynolds)'
   return default_

def get_bcs_basename(bcs):
  k = bcs.find('/geometry')
  if k != -1 :
     bcs = bcs[0:k]
  while bcs[-1] == '/': bcs = bcs[0:-1] # remove extra '/'
  return os.path.basename(bcs)

def we_default(tag):
   default_ = '26'
   if tag in ['INL','GITNL', '525'] : default_ = '13'
   if tag in NewStructureBCTag      : default_ = '13'
   return default_

def zoom_default(x):
   zoom_ = '8'
   fvcore = fvcore_name(x)
   if fvcore :
      fvrst = os.path.dirname(os.path.realpath(__file__)) + '/fvrst.x -h '
      cmd = fvrst + fvcore
      print(cmd +'\n')
      p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
      (output, err) = p.communicate()
      p_status = p.wait()
      ss = output.decode().split()
      x['input:shared:agrid'] = "C"+ss[0] # save for air parameter
      lat = int(ss[0])
      lon = int(ss[1])
      if (lon != lat*6) :
         sys.exit('This is not a cubed-sphere grid fvcore restart. Please contact SI team')
      ymdh  = x.get('input:shared:yyyymmddhh')
      ymdh_ = str(ss[3]) + str(ss[4])[0:2]
      if (ymdh_ != ymdh) :
         print("Warning: The date in fvcore is different from the date you input\n")
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

def config_to_yaml(config, yaml_file):
   if os.path.exists(yaml_file) :
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

def merra2_expid(config):
   if not config['MERRA-2']:
      return config
   yyyymm = int(config.get('yyyymmddhh')[0:6])
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
   config['expid'] = expid

   return config

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
   if answers.get("input:shared:ogrid"):
      oceanin  = ' -oceanin ' + answers["input:shared:ogrid"]
   oceanout = ' -oceanout ' + answers["output:shared:ogrid"]
   
   nobkg  = '' if answers["output:analysis:bkg"] else " -nobkg "
   nolcv  = '' if answers["output:analysis:lcv"] else " -nolcv "
  
   label  = ' -lbl ' if answers["output:shared:label"] else ""
    
   in_altbcs = ''
   out_altbcs = ''
   if answers.get("input:shared:altbcs", "").strip() :
      in_altbcs = " -in_altbcs " + answers["input:shared:altbcs"]
   if answers.get("output:shared:altbcs", "").strip() :
      out_altbcs = " -out_altbcs " + answers["output:shared:altbcs"]

   zoom = " -zoom " + answers["input:surface:zoom"]
   wemin  = " -wemin "  + answers["input:surface:wemin"]
   wemout = " -wemout " + answers["output:surface:wemin"]
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
                                          in_altbcs + \
                                          out_altbcs + \
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


if __name__ == '__main__' :
   config = yaml_to_config('c24Toc12.yaml')
   print_config(config)
