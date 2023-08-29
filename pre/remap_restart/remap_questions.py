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

def echo_bcs(x,opt):
  if opt == "IN":
    x['input:shared:bcs_dir']  = get_bcsdir(x, 'IN')
    print("\nBc path for the input restart: " + x['input:shared:bcs_dir'])
  if opt == "OUT":
    x['output:shared:bcs_dir'] = get_bcsdir(x, 'OUT')
    print("\nBc path for the output restart: " + x['output:shared:bcs_dir'])
    print("\nUsers can change the paths in the generated remap_params.yaml file later on")
  return False

def ask_questions():

   questions = [
        {
            "type": "confirm",
            "name": "input:shared:MERRA-2",
            "message": "Would you like to remap archived MERRA-2 restarts?",
            "default": False,
        },
        {
            "type": "path",
            "name": "input:shared:rst_dir",
            "message": "Enter the input directory containing restart files to be remapped:",
            "when": lambda x: not x['input:shared:MERRA-2'],
        },
        {
            "type": "text",
            "name": "input:shared:yyyymmddhh",
            "message": "From what restart date/time would you like to remap? (must be 10 digits: yyyymmddhh)",
            "validate": lambda text: len(text)==10 ,
            "when": lambda x: not x['input:shared:MERRA-2'],
        },
        {
            "type": "text",
            "name": "input:shared:yyyymmddhh",
            "message": "From what restart date would you like to remap? (must be 8 digits: yyyymmdd, hour=21z)",
            "validate": lambda text: len(text)==8 ,
            "when": lambda x: x['input:shared:MERRA-2'],
        },
        {
            "type": "path",
            "name": "output:shared:out_dir",
            "message": "Enter the output directory for new restarts:\n"
        },
        {
            "type": "path",
            "name": "output:shared:out_dir",
            "message": "init merra2 \n",
            # always return false, no show but change x
            "when": lambda x: init_merra2(x),
        },

        {
            "type": "text",
            "name": "input:shared:agrid",
            "message": f'''Enter input atmospheric grid:
    C12   C180  C1000  C270
    C24   C360  C1440  C540
    C48   C500  C2880  C1080
    C90   C720  C5760  C2160  C1536\n''',
            "validate": lambda text : text in ['C12','C180','C1000','C270','C24','C360','C1440','C540','C48','C500','C2880','C1080','C90','C720','C5760','C2160','C1536'],
            # if it is merra-2 or has_fvcore, agrid is deduced
            "when": lambda x: not x['input:shared:MERRA-2'] and not fvcore_name(x),
        },

        {
            "type": "select",
            "name": "input:shared:model",
            "message": "Select ocean model that matches input restarts:",
            "choices": ["data", "MOM5", "MOM6"],
            "default": "data",
            "when": lambda x: not x['input:shared:MERRA-2']
        },

        {
            "type": "select",
            "name": "input:shared:ogrid",
            "message": "Select data ocean grid that matches input restarts:",
            "choices": ['360x180   (Reynolds)','1440x720  (MERRA-2)','2880x1440 (OSTIA)','CS  (same as atmosphere OSTIA cubed-sphere grid)'],
            "default": lambda x: data_ocean_default(x.get('input:shared:agrid')),
            "when": lambda x: x.get('input:shared:model') == 'data' and not x['input:shared:MERRA-2'],
        },

        {
            "type": "text",
            # remove the comments
            "name": "input:shared:ogrid",
            "message": "remove the comment of ogrid",
            # always return false, so it never shows
            "when": lambda x: remove_ogrid_comment(x, 'IN')
        },

        {
            "type": "select",
            "name": "input:shared:ogrid",
            "message": "Select coupled (MOM5, MOM6) ocean grid that matches input restarts:",
            "choices": ['72x36','360x200','720x410','1440x1080'],
            "when": lambda x: x.get('input:shared:model') == 'MOM5' or x.get('input:shared:model')== 'MOM6'
        },

        {
            "type": "text",
            "name": "output:shared:agrid",
            "message": f'''Enter new atmospheric grid:
    C12   C180  C1000  C270
    C24   C360  C1440  C540
    C48   C500  C2880  C1080
    C90   C720  C5760  C2160  C1536\n''',
            "default": 'C360',
            "validate": lambda text : text in ['C12','C180','C1000','C270','C24','C360','C1440','C540','C48','C500','C2880','C1080','C90','C720','C5760','C2160','C1536'],
        },

        {
            "type": "select",
            "name": "output:shared:model",
            "message": "Select ocean model for new restarts:",
            "choices": ["data", "MOM5", "MOM6"],
            "default": "data",
        },
        {
            "type": "select",
            "name": "output:shared:ogrid",
            "message": "Select data ocean grid for new restarts:",
            "choices": ['360x180   (Reynolds)','1440x720  (MERRA-2)','2880x1440 (OSTIA)','CS  (same as atmosphere OSTIA cubed-sphere grid)'],
            "default": lambda x: data_ocean_default(x.get('output:shared:agrid')),
            "when": lambda x: x['output:shared:model'] == 'data',
        },
        {
            "type": "text",
            # remove the comments
            "name": "output:shared:ogrid",
            "message": "remove the comment of ogrid",
            # always return false, so it never shows
            "when": lambda x: remove_ogrid_comment(x, 'OUT')
        },
        {
            "type": "select",
            "name": "output:shared:ogrid",
            "message": "Select couple ocean grid for new restarts:",
            "choices": ['72x36','360x200','720x410','1440x1080'],
            "when": lambda x: x['output:shared:model'] != 'data',
        },

        {
            "type": "text",
            "name": "output:air:nlevel",
            "message": "Enter new atmospheric levels: (71 72 91 127 132 137 144 181)",
            "default": "72",
        },

        # to show the message, we ask output first
        {
            "type": "select",
            "name": "output:shared:bc_version",
            "message": f'''Enter BC version for new restarts:
    BC version                 ADAS tags                   GCM tags
    ----------              ---------------          ------------------
    GM4: Ganymed-4_0    5_12_2 ... 5_16_5         Ganymed-4_0      ... Heracles-5_4_p3
    ICA: Icarus         5_17_0 ... 5_24_0_p1      Icarus, Jason    ...  10.18   
    NL3: Icarus-NLv3    5_25_1 ... present        Icarus_NL, 10.19 ... present

    Development:            Notes
                        -------------------
        v06:     NL3 + JPL veg height + PEATMAP + MODIS snow alb
              \n ''',
            "choices": ['NL3', 'ICA','GM4','Development'],
            "default": "NL3",
        },

        {
            "type": "select",
            "name": "output:shared:bc_version",
            "message": "Enter BC version for new restarts; this option is in testing stage:",
            "choices": ['v06'],
            "when": lambda x:  x["output:shared:bc_version"] == 'Development',
        },

        {
            "type": "select",
            "name": "input:shared:bc_version",
            "message": "Enter BC version that matches input restarts:", 
            "choices": ['NL3', 'ICA','GM4','Development'],
            "when": lambda x: not x["input:shared:MERRA-2"],
        },

        {
            "type": "select",
            "name": "input:shared:bc_version",
            "message": "Enter BC version for new restarts; this option is in testing stage:",
            "choices": ['v06'],
            "when": lambda x: not x["input:shared:MERRA-2"] and x["input:shared:bc_version"] == 'Development',
        },

        {
            "type": "path",
            "name": "input:shared:bcs_dir",
            "message": "Is this BCS matching input restarts? If no, enter your own absolute path: \n",
            "when": lambda x: echo_bcs(x, "IN"),
        },
        {
            "type": "path",
            "name": "output:shared:bcs_dir",
            "message": "Is this BCS for new restarts? If no, enter your own absolute path: \n",
            "when": lambda x:  echo_bcs(x, "OUT"),
        },

        {
            "type": "confirm",
            "name": "output:air:remap",
            "message": "Would you like to remap upper air?",
            "default": True,
        },

        {
            "type": "confirm",
            "name": "output:surface:remap",
            "message": "Would you like to remap surface?",
            "default": True,
        },

        {
            "type": "confirm",
            "name": "output:analysis:bkg",
            "message": "Remap bkg files?",
            "default": False,
        },
        {
            "type": "confirm",
            "name": "output:analysis:lcv",
            "message": "Write lcv?",
            "default": False,
        },
        {
            "type": "text",
            "name": "input:surface:wemin",
            "message": "What is value of wemin (minimum snow water equivalent parameter) for surface inputs?",
            "default": lambda x: wemin_default(x.get('input:shared:bc_version'))
        },
        {
            "type": "text",
            "name": "output:surface:wemin",
            "message": "What is value of wemin (minimum snow water equivalent parameter) for new surface restarts?",
            "default": lambda x: wemin_default(x.get('output:shared:bc_version'))
        },
        {
            "type": "text",
            "name": "input:surface:zoom",
            "message": "What is value of zoom (parameter of radius search, smaller value means larger radius) for surface inputs [1-8]?",
            "default": lambda x: zoom_default(x)
        },
        {
            "type": "text",
            "name": "output:shared:expid",
            "message": "Enter new restarts expid:",
            "default": "",
        },
        {
            "type": "confirm",
            "name": "output:shared:label",
            "message": "Would you like to add labels (bc_versions,resolutions) to restarts' names?",
            "default": False,
        },

        {
            "type": "text",
            "name": "slurm:qos",
            "message": "qos? If the resolution is c1440 or higher, enter allnccs ",
            "default": "debug",
        },

        {
            "type": "text",
            "name": "slurm:account",
            "message": "account?",
            "default": get_account(),
        },
        {
            "type": "select",
            "name": "slurm:constraint",
            "message": "constraint?",
            "choices": ['sky', 'cas'],
        },
   ]
   answers = questionary.prompt(questions)
   if answers['input:shared:MERRA-2'] :
      answers['input:shared:yyyymmddhh'] = answers['input:shared:yyyymmddhh']+ '21'
   answers['input:shared:rst_dir']  = os.path.abspath(answers['input:shared:rst_dir'])
   answers['output:shared:out_dir'] = os.path.abspath(answers['output:shared:out_dir'])

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

