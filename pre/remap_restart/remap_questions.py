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
            "message": "Enter the directory containing restart files to be remapped:",
            "when": lambda x: not x['input:shared:MERRA-2'],
        },
        {
            "type": "text",
            "name": "input:shared:yyyymmddhh",
            "message": "From what restart date/time would you like to remap? (must be 10 digits: yyyymmddhh)",
            "validate": lambda text: len(text)==10 ,
        },

        {
            "type": "path",
            "name": "output:shared:out_dir",
            "message": "Enter the directory for new restarts:\n"
        },

        {
            "type": "text",
            "name": "input:shared:agrid",
            "message": "Enter input atmospheric grid: \n C12   C180  C1000  C270\n C24   C360  C1440  C540\n C48   C500  C2880  C1080\n C90   C720  C5760  C2160\n ",
            "default": 'C360',
            # if it is merra-2 or has_fvcore, agrid is deduced
            "when": lambda x: not x['input:shared:MERRA-2'] and not fvcore_name(x),
        },

        {
            "type": "select",
            "name": "input:shared:model",
            "message": "Select ocean model for input restarts:",
            "choices": ["data", "MOM5", "MOM6"],
            "default": "data",
            "when": lambda x: not x['input:shared:MERRA-2']
        },

        {
            "type": "select",
            "name": "input:shared:ogrid",
            "message": "Select Data Ocean Grid for input restarts:",
            "choices": ['360x180   (Reynolds)','1440x720  (MERRA-2)','2880x1440 (OSTIA)','CS  (same as atmosphere OSTIA cubed-sphere grid)'],
            "default": lambda x: data_ocean_default(x.get('input:shared:agrid')),
            "when": lambda x: x.get('input:shared:model') == 'data' and not x['input:shared:MERRA-2'],
        },

        {
            "type": "select",
            "name": "input:shared:ogrid",
            "message": "Select Coupled (MOM5, MOM6) Ocean Grid for input restarts:",
            "choices": ['72x36','360x200','720x410','1440x1080'],
            "when": lambda x: x.get('input:shared:model') == 'MOM5' or x.get('input:shared:model')== 'MOM6'
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
            "message": "Select Data Ocean Grid for new restarts:",
            "choices": ['360x180   (Reynolds)','1440x720  (MERRA-2)','2880x1440 (OSTIA)','CS  (same as atmosphere OSTIA cubed-sphere grid)'],
            "default": lambda x: data_ocean_default(x.get('output:shared:agrid')),
            "when": lambda x: x['output:shared:model'] == 'data',
        },
        {
            "type": "select",
            "name": "output:shared:ogrid",
            "message": "Select Couple Ocean Grid for new restarts:",
            "choices": ['72x36','360x200','720x410','1440x1080'],
            "when": lambda x: x['output:shared:model'] != 'data',
        },


        {
            "type": "text",
            "name": "output:shared:agrid",
            "message": "Enter new atmospheric grid: \n C12   C180  C1000  C270\n C24   C360  C1440  C540\n C48   C500  C2880  C1080\n C90   C720  C5760  C2160\n ",
            "default": 'C360',
        },

        {
            "type": "text",
            "name": "output:air:nlevel",
            "message": "Enter new atmospheric levels: (71 72 91 127 132 137 144 181)",
            "default": "72",
        },



        {
            "type": "text",
            "name": "input:shared:tag",
            "message": "Enter GCM or DAS tag for input restarts: \n \
\n \
Sample GCM tags for legacy BCs:\n \
--------------- \n \
G40   : Ganymed-4_0  .........  Heracles-5_4_p3 \n \
ICA   : Icarus  ..............  Jason \n \
GITOL : 10.3  ................  10.18 \n \
INL   : Icarus-NL  ...........  Jason-NL \n \
GITNL : 10.19  ...............  10.23 \n \
\n \
Sample DAS tags for legacy BCs:\n \
--------------- \n \
5B0  : GEOSadas-5_10_0_p2  ..  GEOSadas-5_11_0 \n \
512  : GEOSadas-5_12_2  .....  GEOSadas-5_16_5\n \
517  : GEOSadas-5_17_0  .....  GEOSadas-5_24_0_p1\n \
525  : GEOSadas-5_25_1  .....  GEOSadas-5_29_4\n  \
\n \
Sample BC version for new structure BC base): \n \
-------------- \n \
NL3   : Newland version 3 \n \
NL4   : Newland version 4 \n \
NL5   : Newland version 5 \n \
v06, v07, v08, v09: Not generated yet \n",
 
            "default": "INL",
            "when": lambda x: not x["input:shared:MERRA-2"],
        },

        {
            "type": "text",
            "name": "output:shared:tag",
            "message": "Enter GCM or DAS tag for new restarts:",
            "default": "GITNL",
            "when": lambda x: not x["input:shared:MERRA-2"],
        },
        # show the message if it is merra2
        {
            "type": "text",
            "name": "output:shared:tag",
            "message": "Enter GCM or DAS tag for new restarts: \n \
\n \
Sample GCM tags for legacy BCs:\n \
--------------- \n \
G40   : Ganymed-4_0  .........  Heracles-5_4_p3 \n \
ICA   : Icarus  ..............  Jason \n \
GITOL : 10.3  ................  10.18 \n \
INL   : Icarus-NL  ...........  Jason-NL \n \
GITNL : 10.19  ...............  10.23 \n \
\n \
Sample DAS tags for legacy BCs:\n \
--------------- \n \
5B0  : GEOSadas-5_10_0_p2  ..  GEOSadas-5_11_0 \n \
512  : GEOSadas-5_12_2  .....  GEOSadas-5_16_5\n \
517  : GEOSadas-5_17_0  .....  GEOSadas-5_24_0_p1\n \
525  : GEOSadas-5_25_1  .....  GEOSadas-5_29_4\n  \
\n \
Sample BC version for new structure BC base): \n \
-------------- \n \
NL3   : Newland version 3 \n \
NL4   : Newland version 4 \n \
NL5   : Newland version 5 \n \
v06, v07, v08, v09: Not generated yet \n",
            "default": "GITNL",
            "when": lambda x: x["input:shared:MERRA-2"],
        },

        {
            "type": "path",
            "name": "input:shared:altbcs",
            "message": "Enter nothing (default) or specify your own absolute bcs path for input restarts: \n\n \
It expects the sub-structure of the path to be the same as one of the three paths that match the tag. \n \
/discover/nobackup/projects/gmao/bcs_shared/fvInput/ExtData/esm/tiles  (structure after NL3 ) \n \
/discover/nobackup/projects/gmao/ssd/aogcm/atmosphere_bcs   ( coupled model) \n \
/discover/nobackup/projects/gmao/bcs_shared/legacy_bcs      ( legacy structure)\n",
            "default": "",
            "when": lambda x: not x.get("input:shared:MERRA-2"),
        },

        {
            "type": "path",
            "name": "output:shared:altbcs",
            "message": "Enter nothing (default) or specify your own absolute bcs path for new restarts: \n ",
            "default": "",
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
            "type": "select",
            "name": "input:surface:catch_model",
            "message": "What is the catchment model? ",
            "choices": ['catch','catchcnclm40','catchcnclm45'],
            "default": 'catch',
            "when": lambda x: x["output:surface:remap"] and not x["input:shared:MERRA-2"]
        },

        {
            "type": "confirm",
            "name": "output:analysis:bkg",
            "message": "Regrid bkg files?",
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
            "message": "What is value of Wemin?",
            "default": lambda x: we_default(x.get('input:shared:tag'))
        },
        {
            "type": "text",
            "name": "output:surface:wemin",
            "message": "What is value of Wemout?",
            "default": lambda x: we_default(x.get('output:shared:tag'))
        },
        {
            "type": "text",
            "name": "input:surface:zoom",
            "message": "What is value of zoom [1-8]?",
            "default": lambda x: zoom_default(x)
        },
        {
            "type": "text",
            "name": "output:shared:expid",
            "message": "Enter new restarts expid:",
            "default": "",
        },

        {
            "type": "text",
            "name": "slurm:qos",
            "message": "qos?",
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
   if not answers.get('input:shared:model') :
      answers['input:shared:model'] = 'data'

   if answers.get('input:shared:ogrid'):
      answers['input:shared:ogrid'] = answers['input:shared:ogrid'].split()[0]
   if answers.get('output:shared:ogrid'):
      answers['output:shared:ogrid'] = answers['output:shared:ogrid'].split()[0]

   if answers['input:shared:MERRA-2']:
      answers['input:shared:rst_dir'] = tmp_merra2_dir(answers)
      answers['input:shared:altbcs'] =''
    
   answers['input:shared:rst_dir'] = os.path.abspath(answers['input:shared:rst_dir'])
   if answers.get('output:shared:ogrid') == 'CS':
      answers['output:shared:ogrid'] = answers['output:shared:agrid']
   answers['output:shared:out_dir']  = os.path.abspath(answers['output:shared:out_dir'])
   
   return answers


if __name__ == "__main__":
   answers = ask_questions()
   cmdl = get_command_line_from_answers(answers)
   config = get_config_from_answers(answers)
   yaml = ruamel.yaml.YAML()
   with open("raw_answers.yaml", "w") as f:
     yaml.dump(config, f)

