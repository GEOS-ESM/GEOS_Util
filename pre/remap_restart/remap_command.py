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
import argparse
from remap_utils import *
from remap_params import * 

def parse_args(program_description):

    parser = argparse.ArgumentParser(description='Remap restarts',epilog=program_description,formatter_class=argparse.RawDescriptionHelpFormatter)

    p_sub = parser.add_subparsers(help = 'Sub command help')
    p_config  = p_sub.add_parser(
     'config_file',
     help = "Use config file as input",
    )

    p_config.add_argument('-c', '--config_file',  help='YAML config file')

    p_command = p_sub.add_parser(
     'command_line',
     help = "Use command line as input",
    )
    p_command.add_argument('-merra2', action='store_true', default= False, help='use merra2 restarts')
    p_command.add_argument('-ymdh', help='yyyymmddhh year month date hour of input and output restarts')
    p_command.add_argument('-grout', help='Grid ID of the output restart, format Cxxx')
    p_command.add_argument('-levsout', help='levels of output restarts')

    p_command.add_argument('-out_dir', help='directory for output restarts')
    p_command.add_argument('-rst_dir', help='directory for input restarts')

    p_command.add_argument('-expid', help='restart id for input restarts')
    p_command.add_argument('-newid', default="",help='restart id for output restarts')

    p_command.add_argument('-tagin',  help='GCM or DAS tag associated with inputs')
    p_command.add_argument('-tagout', help='GCM or DAS tag associated with outputs')

    p_command.add_argument('-wemin',   help='minimum water snow water equivalent for input catch/cn')
    p_command.add_argument('-wemout',  help='minimum water snow water equivalent for output catch/cn')

    p_command.add_argument('-oceanin',  help='ocean horizontal grid of inputs \n \
                                          data model: 360x180,1440x720,2880x1440,CS \n \
                                          coupled model:  72x36, 360x200,720x410,1440x1080')
    p_command.add_argument('-oceanout', help='ocean horizontal grid of outputs \n \
                                          data model: 360x180,1440x720,2880x1440,CS \n \
                                          coupled model:  72x36, 360x200,720x410,1440x1080')

    p_command.add_argument('-ocnmdlin', default='data',  help='ocean input model: data, MOM5, MOM6')
    p_command.add_argument('-ocnmdlout',default='data',  help='ocean output model: data, MOM5, MOM6')
    p_command.add_argument('-catch_model',default='catch',  help='catchment model: catch, catchcnclm40, catchcnclm45')

    p_command.add_argument('-nobkg', action='store_true', help="Don't remap bkg files")
    p_command.add_argument('-nolcv', action='store_true', help="Don't remap lcv files")
    p_command.add_argument('-lbl',   action='store_true', help="Label output restart with tag and resolution")
    p_command.add_argument('-in_altbcs',  default="", help= "users' alternative boundary condition files for input")
    p_command.add_argument('-out_altbcs', default="", help= "users' alternative boundary condition files for output")
    p_command.add_argument('-zoom',   help= "zoom for the surface input")

    p_command.add_argument('-qos',    default="debug", help= "queue of slurm job")
    account = get_account()
    p_command.add_argument('-account', default= account,  help= "account of slurm job")
    p_command.add_argument('-constraint', default= 'sky', help= "machine of slurm job")
    p_command.add_argument('-rs', default=3, help='flag indicating which restarts to regrid: 1 (upper air); 2 (surface) 3 (both)')

    # Parse using parse_known_args so we can pass the rest to the remap scripts
    args, extra_args = parser.parse_known_args()
    return args, extra_args


def get_answers_from_command_line(cml):

   answers = {}
   answers["input:shared:MERRA-2"]     = cml.merra2
   answers["input:shared:yyyymmddhh"]  = cml.ymdh
   answers["input:shared:model"]       = cml.ocnmdlin
   if not cml.merra2:
      answers["input:shared:tag"]      = cml.tagin
      answers["input:shared:ogrid"]    = cml.oceanin
   answers["input:surface:catch_model"] = cml.catch_model
 
   answers["output:shared:agrid"]      = cml.grout
   answers["output:air:nlevel"]        = cml.levsout
   answers["output:shared:out_dir"]    = os.path.abspath(cml.out_dir + '/')
   answers["output:shared:expid"]      = cml.newid
   answers["output:shared:tag"]        = cml.tagout
   answers["output:shared:model"]      = cml.ocnmdlout
   answers["output:shared:ogrid"]      = cml.oceanout
   answers["output:shared:label"]      = cml.lbl

   if cml.in_altbcs.strip():
      answers["input:shared:altbcs"]  =  cml.in_altbcs
   if cml.out_altbcs.strip():
      answers["output:shared:altbcs"] =  cml.out_altbcs


   answers["output:analysis:bkg"]      = not cml.nobkg
   answers["output:analysis:lcv"]      = not cml.nolcv
   if cml.rs == '1':
     answers["output:air:remap"]     = True
   if cml.rs == '2':
     answers["output:surface:remap"] = True
   if cml.rs == '3':
     answers["output:surface:remap"] = True
     answers["output:air:remap"]     = True

   if cml.merra2 and not cml.rst_dir:
      answers['input:shared:rst_dir'] = tmp_merra2_dir(answers)
   else:
      answers["input:shared:rst_dir"] = os.path.abspath(cml.rst_dir + '/')


   # zoom_default fills 'input:shared:agrid'
   answers["input:surface:zoom"] = zoom_default(answers)
   if cml.zoom:  answers["input:surface:zoom"] = cml.zoom
   if answers.get('input:shared:ogrid') == 'CS':
      answers['input:shared:ogrid'] = answers['input:shared:agrid']
   if answers.get('output:shared:ogrid') == 'CS':
      answers['output:shared:ogrid'] = answers['output:shared:agrid']

   if not cml.wemin :
     answers["input:surface:wemin"]  = we_default(answers['input:shared:tag'])
   else:
     answers["input:surface:wemin"]  = cml.wemin

   if not cml.wemout :
     answers["output:surface:wemin"] = we_default(answers['output:shared:tag'])
   else:
     answers["output:surface:wemin"] = cml.wemout


   answers["slurm:account"]    = cml.account
   answers["slurm:qos"]        = cml.qos
   answers["slurm:constraint"] = cml.constraint
  
   return answers

if __name__ == "__main__":

   yaml = ruamel.yaml.YAML()
   cmdl, extra_args = parse_args("test_args")
   print(cmdl)
   answers = get_answers_from_command_line(cmdl)
   config = get_config_from_answers(answers)
   with open("raw_command.yaml", "w") as f:
     yaml.dump(config, f)

   params = remap_params(config) 
   with open("params_from_command.yaml", "w") as f:
     yaml.dump(params.config, f)

