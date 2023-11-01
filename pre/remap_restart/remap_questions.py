#!/usr/bin/env python3
#
# source install/bin/g5_modules
#
# Newer GEOS code should load a module with GEOSpyD Python3 if not run:
#   module load python/GEOSpyD/Min4.10.3_py3.9
#

import os
import subprocess
import shlex
import ruamel.yaml
import shutil
import questionary
import glob
from remap_utils import *

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

def echo_level(x):
  if x["output:air:nlevel"] != str(x.get("input:air:nlevel")) :
      print("NOTE: Different # atm levels in input and new restarts.  Cannot remap agcm_import_rst (a.k.a. IAU) file.")
      x['output:air:agcm_import_rst'] = False
      return False
  return True

def echo_bcs(x,opt):
  if opt == "IN":
    in_bcsdir = get_bcsdir(x, 'IN')
    agrid = x.get('input:shared:agrid')
    ogrid = x.get('input:shared:ogrid')
    model = x.get('input:shared:omodel')
    stretch = x.get('input:shared:stretch')
    land_dir = get_landdir(in_bcsdir, agrid, ogrid, model, stretch)    
    x['input:shared:bcs_dir']  = in_bcsdir
    print("\n BC of land for input restart: " + land_dir )
  if opt == "OUT":
    out_bcsdir =  get_bcsdir(x, 'OUT')
    agrid = x.get('output:shared:agrid')
    ogrid = x.get('output:shared:ogrid')
    model = x.get('output:shared:omodel')
    stretch = x.get('output:shared:stretch')
    land_dir = get_landdir(out_bcsdir, agrid, ogrid, model, stretch)    
    x['output:shared:bcs_dir'] = out_bcsdir
    print("\n BC of land for output restart: " + land_dir)
  return False

def default_partition(x):
   if x['slurm:qos'] == 'debug':
      x['slurm:partition'] = 'compute'
      return False
   return True

def validate_merra2_time(text):
   if len(text) == 10 :
      hh = text[8:]
      if hh in ['03','09','15','21']:
         return True
      else:
         return False 
   else:
     return False

def ask_questions():

   # See remap_utils.py for definitions of "choices", "message" strings, and "validate" lists
   # that are used multiple times.

   questions = [
        {
            "type": "confirm",
            "name": "input:shared:MERRA-2",
            "message": "Remap archived MERRA-2 restarts?\n",
            "default": False,
        },
        {
            "type": "path",
            "name": "input:shared:rst_dir",
            "message": "Enter input directory with restart files to be remapped:\n",
            "when": lambda x: not x['input:shared:MERRA-2'],
        },
        {
            "type": "text",
            "name": "input:shared:yyyymmddhh",
            "message": "Enter restart date/time:  (Must be 10 digits: yyyymmddhh.)\n",
            "validate": lambda text: len(text)==10 ,
            "when": lambda x: not x['input:shared:MERRA-2'] and not fvcore_info(x),
        },
        {
            "type": "text",
            "name": "input:shared:yyyymmddhh",
            "message": "Enter restart date:  (Must be 10 digits: yyyymmddhh; hour=03,09,15,21z.)\n",
            "validate": lambda text: validate_merra2_time(text) ,
            "when": lambda x: x['input:shared:MERRA-2'],
        },
        {
            "type": "path",
            "name": "output:shared:out_dir",
            "message": "Enter output directory for new restarts:\n"
        },

        # dummy (invisible) question to run function that initializes MERRA-2 config
        {
            "type": "path",
            "name": "output:shared:out_dir",
            "message": "init merra2\n",
            # always return false, so question never shows but changes x
            "when": lambda x: init_merra2(x),
        },

        {
            "type": "text",
            "name": "input:shared:agrid",
            "message": message_agrid_in,
            "validate": lambda text : text in validate_agrid,
            # if it is merra-2 or has_fvcore, agrid is deduced
            "when": lambda x: not x['input:shared:MERRA-2'] and not fvcore_info(x),
        },

        {
            "type": "select",
            "name": "input:shared:omodel",
            "message": "Select ocean model of input restarts:\n",
            "choices": choices_omodel,
            "default": "data",
            "when": lambda x: not x['input:shared:MERRA-2']
        },

        {
            "type": "select",
            "name": "input:shared:ogrid",
            "message": "Select data ocean grid/resolution of input restarts:\n",
            "choices": choices_ogrid_data,
            "default": lambda x: data_ocean_default(x.get('input:shared:agrid')),
            "when": lambda x: x.get('input:shared:omodel') == 'data' and not x['input:shared:MERRA-2'],
        },

        # dummy (invisible) question to remove parenthetical comments from selected input:shared:ogrid
        {
            "type": "text",
            "name": "input:shared:ogrid",
            "message": "remove the comment of ogrid",
            # always return false, so question never shows but changes ogrid
            "when": lambda x: remove_ogrid_comment(x, 'IN')
        },

        {
            "type": "select",
            "name": "input:shared:ogrid",
            "message": "Select coupled ocean resolution of input restarts:\n",
            "choices": choices_ogrid_cpld,
            "when": lambda x: x.get('input:shared:omodel') == 'MOM5' or x.get('input:shared:omodel')== 'MOM6'
        },

        {
            "type": "confirm",
            "name": "output:shared:stretch",
            "message": "Remap to a stretched cubed-sphere grid?",
            "default": False,
        },
        {
            "type": "text",
            "name": "output:shared:agrid",
            "message": message_agrid_new,
            "default": 'C360',
            "validate": lambda text : text in validate_agrid,
            "when": lambda x : not x['output:shared:stretch'],
        },

        {
            "type": "select",
            "name": "output:shared:stretch",
            "message": message_stretch, 
            "choices": choices_stretch[1:3],
            "when": lambda x : x['output:shared:stretch'],
        },

        {
            "type": "select",
            "name": "output:shared:agrid",
            "message": "Select resolution of SG001 grid for new restarts: \n",
            "choices": choices_res_SG001, 
            "when": lambda x : x.get('output:shared:stretch') == 'SG001',
        },

        {
            "type": "select",
            "name": "output:shared:agrid",
            "message": "Select resolution of SG002 grid for new restarts: \n",
            "choices": choices_res_SG002, 
            "when": lambda x : x.get('output:shared:stretch') == 'SG002',
        },

        {
            "type": "select",
            "name": "output:shared:omodel",
            "message": "Select ocean model for new restarts:\n",
            "choices": choices_omodel,
            "default": "data",
        },
        {
            "type": "select",
            "name": "output:shared:ogrid",
            "message": "Select data ocean grid/resolution for new restarts:\n",
            "choices": choices_ogrid_data,
            "default": lambda x: data_ocean_default(x.get('output:shared:agrid')),
            "when": lambda x: x['output:shared:omodel'] == 'data',
        },

        # dummy (invisible) question to remove parenthetical comments from selected output:shared:ogrid
        {
            "type": "text",
            "name": "output:shared:ogrid",
            "message": "remove the comment of ogrid",
            # always return false, so questions never shows but changes ogrid
            "when": lambda x: remove_ogrid_comment(x, 'OUT')
        },
        {
            "type": "select",
            "name": "output:shared:ogrid",
            "message": "Select coupled ocean resolution for new restarts:\n",
            "choices": choices_ogrid_cpld,
            "when": lambda x: x['output:shared:omodel'] != 'data',
        },

        {
            "type": "text",
            "name": "output:air:nlevel",
            "message": "Enter number of atmospheric levels for new restarts: (71 72 91 127 132 137 144 181)\n",
            "default": "72",
        },

        # to show the message, we ask output first
        {
            "type": "select",
            "name": "input:shared:bc_version",
            "message": message_bc_ops_in,
            "choices": choices_bc_ops,
            "when": lambda x: not x["input:shared:MERRA-2"],
        },

        {
            "type": "select",
            "name": "input:shared:bc_version",
            "message": message_bc_other_in,
            "choices": choices_bc_other,
            "when": lambda x: x["input:shared:bc_version"] == 'Other',
        },

        {
            "type": "select",
            "name": "output:shared:bc_version",
            "message": message_bc_ops_new,
            "choices": choices_bc_ops,
            "default": "NL3",
            "when": lambda x: x["input:shared:MERRA-2"],
        },

        {
            "type": "select",
            "name": "output:shared:bc_version",
            "message": "Select BCs version for new restarts:\n",
            "choices": choices_bc_ops,
            "default": "NL3",
            "when": lambda x: not x["input:shared:MERRA-2"],
        },

        {
            "type": "select",
            "name": "output:shared:bc_version",
            "message": message_bc_other_new,
            "choices": choices_bc_other,
            "when": lambda x:  x["output:shared:bc_version"] == 'Other' and x["input:shared:bc_version"] not in ['v06','v11'],
        },

        {
            "type": "select",
            "name": "output:shared:bc_version",
            "message": "\nSelect BCs version of input restarts:\n",
            "choices": choices_bc_other,
            "when": lambda x:  x["output:shared:bc_version"] == 'Other' and x["input:shared:bc_version"] in ['v06','v11'],
        },

        {
            "type": "path",
            "name": "input:shared:bcs_dir",
            "message": "Is this BCs version correct for input restarts? If no, enter your own absolute path: \n",
            "when": lambda x: echo_bcs(x, "IN"),
        },
        {
            "type": "path",
            "name": "output:shared:bcs_dir",
            "message": "Is this BCs version correct for new restarts? If no, enter your own absolute path: \n",
            "when": lambda x:  echo_bcs(x, "OUT"),
        },

        {
            "type": "confirm",
            "name": "output:air:remap",
            "message": "Remap upper air restarts?",
            "default": True,
        },

        {
            "type": "confirm",
            "name": "output:air:agcm_import_rst",
            "message": f'''Remap agcm_import_rst (a.k.a. IAU) file needed for REPLAY runs? 
                        (NOTE: Preferred method is to regenerate IAU file, 
                               but IF requested, remapping will be performed.)''',
            "default": False,
            "when": lambda x: echo_level(x),
        },


        {
            "type": "confirm",
            "name": "output:surface:remap",
            "message": "Remap surface restarts?",
            "default": True,
        },

        {
            "type": "confirm",
            "name": "output:analysis:bkg",
            "message": "Remap bkg files?  (Required by ADAS but not mapped onto ADAS grid; run one ADAS cycle to spin up.) ",
            "default": False,
        },

        {
            "type": "confirm",
            "name": "output:analysis:lcv",
            "message": "Write lcv file?  (Required by ADAS.) ",
            "default": False,
        },
        {
            "type": "text",
            "name": "input:surface:wemin",
            "message": "Enter value of WEMIN (min. snow water equivalent parameter) used in simulation that produced input restarts.\n",
            "default": lambda x: wemin_default(x.get('input:shared:bc_version')),
            "when": lambda x: show_wemin_default(x),
        },
        {
            "type": "text",
            "name": "output:surface:wemin",
            "message": "Enter value of WEMIN (min. snow water equivalent parameter) to be used in simulation with new restarts.\n",
            "default": lambda x: wemin_default(x.get('output:shared:bc_version'))
        },
        {
            "type": "text",
            "name": "input:surface:zoom",
            "message": "Enter value of zoom parameter for surface restarts [1-8]?  (Search radius, smaller value means larger radius.)\n",
            "default": lambda x: zoom_default(x)
        },
        {
            "type": "text",
            "name": "output:shared:expid",
            "message": "Enter experiment ID for new restarts:  (Added as prefix to new restart file names; can leave blank.)\n",
            "default": "",
        },
        {
            "type": "confirm",
            "name": "output:shared:label",
            "message": "Add labels for BCs version and atm/ocean resolutions to restart file names?",
            "default": False,
        },

        {
            "type": "text",
            "name": "slurm:qos",
            "message": "SLURM quality-of-service (qos)?  (If on NCCS and atm resolution is c1440 or higher, enter allnccs.) ",
            "default": "debug",
        },

        {
            "type": "text",
            "name": "slurm:account",
            "message": "SLURM account?",
            "default": get_account(),
        },
        {
            "type": "text",
            "name": "slurm:partition",
            "message": "SLURM partition?",
            "default": "compute",
            "when": lambda x : default_partition(x),
        },
   ]
   answers = questionary.prompt(questions)
   answers['input:shared:rst_dir']  = os.path.abspath(answers['input:shared:rst_dir'])
   answers['output:shared:out_dir'] = os.path.abspath(answers['output:shared:out_dir'])

   if answers.get('input:air:nlevel') : del answers['input:air:nlevel']
   if answers["output:surface:remap"] and not answers["input:shared:MERRA-2"]:  
      answers["input:surface:catch_model"] = catch_model(answers)
 
   return answers

if __name__ == "__main__":
   answers = ask_questions()
   cmdl = get_command_line_from_answers(answers)
   config = get_config_from_answers(answers)
   yaml = ruamel.yaml.YAML()
   with open("raw_answers.yaml", "w") as f:
     yaml.dump(config, f)

