#!/usr/bin/env python3
#
# remap_restarts package:
#   remap_restarts.py is the main script for remapping GEOS restart files to a different  
#   resolution and/or a different version of the associated model boundary conditions
#
# to run, must first load modules (incl. python3) as follows:
#
#   source g5_modules.sh    [bash]
#   source g5_modules       [csh]
#
import sys
import argparse
import textwrap
import ruamel.yaml
import questionary
from remap_utils import *
from remap_questions import *
from remap_command_line import *
from remap_params import *
from remap_upper import *
from remap_lake_landice_saltwater import *
from remap_analysis  import *
from remap_catchANDcn  import *


program_description = textwrap.dedent(f'''
      USAGE:

      This script provides three options for remapping GEOS restart files:

      1. Use the interactive questionary:
           ./remap_restarts.py
         The questionary concludes with the option to submit the remapping job.  
         It also creates a yaml configuration file (`remap_params.yaml`) and 
         a command line options string (`remap_restarts.CMD`), which can be edited 
         manually and used in the other two ways of running `remap_restarts.py`.

      2. Use an existing yaml config file:
           ./remap_restarts.py config_file -c my_config.yaml

      3. Use command line arguments:
           ./remap_restarts.py command_line -ymdh 2004041421  ....

      Help commands:
           ./remap_restarts.py -h
           ./remap_restarts.py config_file -h
           ./remap_restarts.py command_line -h

      For more information, refer to https://github.com/GEOS-ESM/GEOS_Util/wiki

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
      # just for debugging
      # raw_config = get_config_from_answers(answers)
      # with open("raw_answers.yaml", "w") as f:
      #   yaml.dump(raw_config, f)
      params = remap_params(answers)
      config = params.config
      config_yaml = answers['output:shared:out_dir']+'/remap_params.yaml'

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

     if not noprompt :
       submit = questionary.confirm("Submit the jobs now ?" , default=True).ask()
       if not submit :
         print("\nYou can submit the jobs by the command later on: \n")
         print("./remap_restarts.py config_file -c " + config_yaml + "\n")
         sys.exit(0)

  print(config_yaml)
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
  
