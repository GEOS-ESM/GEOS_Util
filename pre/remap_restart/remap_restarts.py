#!/usr/bin/env python3
#
# source install/bin/g5_modules
#
# Newer GEOS code should load a module with GEOSpyD Python3 if not run:
#   module load python/GEOSpyD/Min4.11.0_py3.9
#

import sys
import argparse
import textwrap
import ruamel.yaml
import questionary
from remap_utils import *
from remap_questions import get_config_from_questionary
from remap_params import *
from remap_upper import *
from remap_lake_landice_saltwater import *
from remap_analysis  import *
from remap_catchANDcn  import *

# Define the argument parser
def parse_args():

    program_description = textwrap.dedent(f'''
      USAGE:

      There are three ways to use this script to remap restarts.

      1. Use an existing config file to remap:
           ./remap_restarts.py -c my_config.yaml

      2. Use questionary to convert template remap_params.tpl to
         remap_params.yaml and then remap:
           ./remap_restarts.py

      3. Use command line to input a flattened yaml file:
           ./remap_restarts.py -o input:air:drymass=1 input:air:hydrostatic=0 ...

      NOTE: Each individual script can be executed independently
        1. remap_questions.py generates raw_answer.yaml
        2. remap_params.py uses raw_answer.yaml and remap_params.tpl as inputs and generates remap_params.yaml
        3. remap_upper.py uses remap_params.yaml as input for remapping
        4. remap_lake_landice_saltwater.py uses remap_params.yaml as input for remapping
        5. remap_catchANDcn.py uses remap_params.yaml as input for remapping
        6. remap_analysis.py uses remap_params.yaml as input for remapping
    ''')

    parser = argparse.ArgumentParser(description='Remap restarts',epilog=program_description,formatter_class=argparse.RawDescriptionHelpFormatter)

    p_sub = parser.add_subparsers(help = 'Sub command help')
    p_config  = p_sub.add_parser(
     'config',
     help = "Use config file as input",
    )
    p_command = p_sub.add_parser(
     'command_line',
     help = "Use command line as input",
    )

    p_config.add_argument('-c', '--config_file',  help='YAML config file')

    p_command.add_argument('-merra2', action='store_true', help='use merra2 restarts')
    p_command.add_argument('-ymd', help='yyyymmdd year mone date of input and output restarts')
    p_command.add_argument('-hr', help='hh hours of input and output restarts')
    p_command.add_argument('-grout', help='Grid ID of the output restart')
    p_command.add_argument('-levsout', help='levels of output restarts')

    p_command.add_argument('-outdir', help='directory for output restarts')
    p_command.add_argument('-d', help='directory for input restarts')

    p_command.add_argument('-expid', help='restart id for input restarts')
    p_command.add_argument('-newid', help='restart id for output restarts')

    p_command.add_argument('-tagin',  help='GCM or DAS tag associated with inputs')
    p_command.add_argument('-tagout', help='GCM or DAS tag associated with outputs')

    p_command.add_argument('-wemin',   help='minimum water snow water equivalent for input catch/cn')
    p_command.add_argument('-wemout',  help='minimum water snow water equivalent for output catch/cn')

    p_command.add_argument('-oceanin', default='c', help='ocean horizontal grid of inputs')
    p_command.add_argument('-oceanout', default='c', help='ocean horizontal grid of outputs')

    p_command.add_argument('-ocnmdlin', default='data',  help='ocean input model')
    p_command.add_argument('-ocnmdlout',default='data',  help='ocean output model')

    p_command.add_argument('-nobkg', action='store_true', help="Don't remap bkg files")
    p_command.add_argument('-nolbl', action='store_true', help="label final restarts with 'tagID.gridID' extension")
    p_command.add_argument('-nolcv', action='store_true', help="Don't remap lcv files")
    p_command.add_argument('-bkg', action='store_true', help="Don't remap bkg files")
    p_command.add_argument('-lbl', action='store_true', help="label final restarts with 'tagID.gridID' extension")
    p_command.add_argument('-lcv', action='store_true', help="Don't remap lcv files")
    p_command.add_argument('-altbcs', help= "use user's boundary condition files")

    p_command.add_argument('-rs', default=3, help='flag indicating which restarts to regrid')


#$GEOSBIN/regrid.pl -np -ymd ${year}${month}${day} -hr 21 -grout C${AGCM_IM} -levsout ${AGCM_LM} -outdir . -d . -expid $RSTID -tagin @EMIP_BCS_IN -oceanin e -i -nobkg -lbl -nolcv -tagout @LSMBCS -rs 3 -oceanout @OCEANOUT

    # Parse using parse_known_args so we can pass the rest to the remap scripts
    # If config_file is used, then extra_args will be empty
    # If flattened_yaml is used, then extra_args will be populated
    args, extra_args = parser.parse_known_args()
    return args, extra_args

def main():

  question_flag = False
  config        = ''

  # Parse the command line arguments from parse_args() capturing the arguments and the rest
  args, extra_args = parse_args()

  if (len(sys.argv) > 1) :
     args, extra_args = parse_args()
     print(args)
     if sys.argv[1] == 'config':
        config = yaml_to_config(args.config_yaml)     
     if sys.argv[1] == 'command_line':
        raw_config = get_config_from_command_line(args)
        print(raw_config)
  else:
      raw_config = get_config_from_questionary()
      params = remap_params(raw_config)
      config = params.config
      question_flag = True
      config_yaml = 'remap_params.yaml'

  exit()
  print('\n')
  print_config(config)

  questions = [
        {
            "type": "confirm",
            "name": "Continue",
            "message": "Above is the YAML config file, would you like to continue?",
            "default": True
        },]
  answer = questionary.prompt(questions)

  if not answer['Continue'] :
     print("\nYou answered not to continue, exiting.\n")
     sys.exit(0)

  if config_yaml or question_flag: write_cmd(config)
  if flattened_yaml or question_flag: config_to_yaml(config, config_yaml)

  # upper air
  upper = upperair(params_file=config_yaml)
  upper.remap()

  # lake, landice and saltwater
  lls  = lake_landice_saltwater(params_file=config_yaml)
  lls.remap()

  # catchANDcn
  catch  = catchANDcn(params_file=config_yaml)
  catch.remap()

  # analysis
  ana = analysis(params_file=config_yaml)
  ana.remap()

if __name__ == '__main__' :
  main()
  
