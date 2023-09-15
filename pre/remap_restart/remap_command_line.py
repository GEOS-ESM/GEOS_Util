#!/usr/bin/env python3
#
# source install/bin/g5_modules
#
# Newer GEOS code should load a module with GEOSpyD Python3 if not run:
#   module load python/GEOSpyD/Min4.10.3_py3.9
#
#  This script parses and converts the command-line arguments to answers equivalent to that from remap_questions.py


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
    p_command.add_argument('-ymdh',              help='yyyymmddhh year month date hour of input and new restarts')
    p_command.add_argument('-grout',             help='Grid ID of new restarts, format Cxx')
    p_command.add_argument('-levsout',           help='Levels for new restarts')

    p_command.add_argument('-out_dir',           help='Directory for new restarts')
    p_command.add_argument('-rst_dir',           help='Directory of input restarts')

    p_command.add_argument('-expid',             help='Experiment ID of input restarts')
    p_command.add_argument('-newid', default="", help='Experiment ID for new restarts')

    choices_bc   = ['NL3', 'ICA', 'GM4', 'v06']
    p_command.add_argument('-bcvin',             help='Boundary conditions version of input restarts', choices= choices_bc)
    p_command.add_argument('-bcvout',            help='Boundary conditions version for new restarts',  choices= choices_bc)

    p_command.add_argument('-in_wemin',          help='Min. water snow water equivalent param. used with input restarts')
    p_command.add_argument('-out_wemin',         help='Min. water snow water equivalent param. to be used with new restarts')

    ocean_grids=['360x180','1440x720','2880x1440','CS', '72x36', '360x200','720x410','1440x1080']

    p_command.add_argument('-oceanin',           help='Ocean horizontal grid of input restarts. \n \
                                                       data model choices: 360x180,1440x720,2880x1440,CS. \n \
                                                       coupled model choices: 72x36, 360x200,720x410,1440x1080', choices=ocean_grids)
    p_command.add_argument('-oceanout',          help='Ocean horizontal grid of new restarts. \n \
                                                       choices are the same as option "oceanin"', choices=ocean_grids)


    choices_omodel     = ['data', 'MOM5', 'MOM6']
    p_command.add_argument('-ocnmdlin',   default='data',     help='Ocean model of input restarts',  choices=choices_omodel)
    p_command.add_argument('-ocnmdlout',  default='data',     help='Ocean model for new restarts',   choices=choices_omodel)
    

    # Unlike remap_questions.py, command-line feature does not deduce Catch vs. CatchCN[40,45] for simplicity, thus requires input argument
    choices_catchmodel = ['catch', 'catchcnclm40', 'catchcnclm45']
    p_command.add_argument('-catch_model',default='catch',    help='Catchment[CN] model', choices=choices_catchmodel)

    p_command.add_argument('-nobkg', action='store_true',     help="Do not remap bkg files")
    p_command.add_argument('-nolcv', action='store_true',     help="Do not write lcv file")
    p_command.add_argument('-np',    action='store_true',     help="No prompt. Overwrite config files without prompting questions")
    p_command.add_argument('-lbl',   action='store_true',     help="Label output restarts with bc_versions and resolutions")
    p_command.add_argument('-in_bcsdir',  default="",         help="User-supplied directory with boundary conditions of input restarts. If not specified (default), directory deduced from bc_version and resolution info")
    p_command.add_argument('-out_bcsdir', default="",         help="User-supplied directory with boundary conditions for new restarts.  If not specified (default), directory deduced from bc_version and resolution info")
    p_command.add_argument('-zoom',                           help= "Zoom parameter for the input surface restarts")

    p_command.add_argument('-qos',        default = "debug",  help="Quality-of-service of slurm job", choices=['debug', 'allnccs'])
    account = get_account()
    p_command.add_argument('-account',    default = account,  help="Account of slurm job")
    p_command.add_argument('-partition',  default= 'compute', help="Partition of slurm job")
    p_command.add_argument('-rs',         default= '3',       help="Flag indicating which restarts to regrid: 1 (upper air); 2 (surface) 3 (both)", choices=['1','2','3'])

    # Parse using parse_known_args so we can pass the rest to the remap scripts
    args, extra_args = parser.parse_known_args()
    return args, extra_args


def get_answers_from_command_line(cml):

   answers = {}
   answers["input:shared:MERRA-2"]     = cml.merra2
   answers["input:shared:yyyymmddhh"]  = cml.ymdh
   answers["input:shared:omodel"]       = cml.ocnmdlin
   answers["output:shared:out_dir"]    = os.path.abspath(cml.out_dir + '/')
   if  cml.merra2:
      init_merra2(answers)
   else:   
      answers["input:shared:bc_version"]      = cml.bcvin
      answers["input:surface:catch_model"] = cml.catch_model
      answers["input:shared:rst_dir"] = os.path.abspath(cml.rst_dir + '/')
      fvcore_name(answers) 
      ogrid                            = cml.oceanin
      if ogrid == "CS":
         ogrid = answers["input:shared:agrid"]
      answers["input:shared:ogrid"]    = ogrid

   answers["output:shared:agrid"]      = cml.grout
   answers["output:air:nlevel"]        = cml.levsout
   answers["output:shared:expid"]      = cml.newid
   answers["output:shared:bc_version"]        = cml.bcvout
   answers["output:shared:omodel"]      = cml.ocnmdlout
   answers["output:shared:label"]      = cml.lbl
   ogrid                               = cml.oceanout
   if ogrid == "CS":
      ogrid = answers["output:shared:agrid"]
   answers["output:shared:ogrid"]      = ogrid

   if cml.in_bcsdir.strip():
      answers["input:shared:bcs_dir"]  =  cml.in_bcsdir
   else:
      answers["input:shared:bcs_dir"]  = get_bcsdir(answers, "IN")

   if cml.out_bcsdir.strip():
      answers["output:shared:bcs_dir"] =  cml.out_bcsdir
   else:
      answers["output:shared:bcs_dir"]  = get_bcsdir(answers, "OUT")

   answers["output:analysis:bkg"]      = not cml.nobkg
   answers["output:analysis:lcv"]      = not cml.nolcv
   if cml.rs == '1':
     answers["output:air:remap"]     = True
   if cml.rs == '2':
     answers["output:surface:remap"] = True
   if cml.rs == '3':
     answers["output:surface:remap"] = True
     answers["output:air:remap"]     = True

   if cml.zoom: 
      answers["input:surface:zoom"] = cml.zoom
   else:
      # zoom_default fills 'input:shared:agrid'
      answers["input:surface:zoom"] = zoom_default(answers)

   if cml.in_wemin :
     answers["input:surface:wemin"]  = cml.in_wemin
   else:
     answers["input:surface:wemin"]  = wemin_default(answers['input:shared:bc_version'])

   if cml.out_wemin :
     answers["output:surface:wemin"] = cml.out_wemin
   else:
     answers["output:surface:wemin"] = wemin_default(answers['output:shared:bc_version'])

   answers["slurm:account"]    = cml.account
   answers["slurm:qos"]        = cml.qos
   answers["slurm:partition"]  = cml.partition
  
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

