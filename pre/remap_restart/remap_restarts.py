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
from remap_questions import *
from remap_command import *
from remap_params import *
from remap_upper import *
from remap_lake_landice_saltwater import *
from remap_analysis  import *
from remap_catchANDcn  import *


program_description = textwrap.dedent(f'''
      USAGE:

      There are three ways to use this script to remap restarts.

      1. Use questionary to convert template remap_params.tpl to
         remap_params.yaml and then remap:
           ./remap_restarts.py

      2. Use an existing config file to remap:
           ./remap_restarts.py config_file -c my_config.yaml

      3. Use command line's options as inputs:
          ./remap_restarts.py command_line -ymdh 2004041421  ....
          To see more command options, please use 
          ./remap_restarts.py command_line -h

      There are three help commands:
        ./remap_restarts.py -h
        ./remap_restarts.py config_file -h
        ./remap_restarts.py command_line -h

      NOTE: Each individual script can be executed independently
        1. remap_questions.py generates raw_answer.yaml
        2. If command_line option is used, the command_line option is converted raw_answers.yaml
        3. remap_params.py uses raw_answer.yaml and remap_params.tpl as inputs and generates remap_params.yaml
        4. remap_upper.py uses remap_params.yaml as input for remapping
        5. remap_lake_landice_saltwater.py uses remap_params.yaml as input for remapping
        6. remap_catchANDcn.py uses remap_params.yaml as input for remapping
        7. remap_analysis.py uses remap_params.yaml as input for remapping
    ''')
def main():

  question_flag = False
  config        = ''
  yaml = ruamel.yaml.YAML()
  # Parse the command line arguments from parse_args() capturing the arguments and the rest
  cmdl, extra_args = parse_args(program_description)
  answers = {}
  config_yaml =''
  noprompt = False
  if (len(sys.argv) > 1) :
     if sys.argv[1] == 'config_file' :
      config_yaml = cmdl.config_file
     if sys.argv[1] == 'command_line':
        answers = get_answers_from_command_line(cmdl)
        noprompt = cmdl.np
  if (len(sys.argv) == 1 or answers) :
      if not answers:
         answers = ask_questions()
         question_flag = True
      raw_config = get_config_from_answers(answers)
      cmd = get_command_line_from_answers(answers)
      write_cmd(answers['output:shared:out_dir'], cmd)
      with open("raw_answers.yaml", "w") as f:
        yaml.dump(raw_config, f)
      params = remap_params(raw_config)
      config = params.config
      config_yaml = 'remap_params.yaml'

  print('\n')
  if config:
     print_config(config)

     if not noprompt :
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

       # write config to yaml file
     config_to_yaml(config, config_yaml,noprompt = noprompt)

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
  
