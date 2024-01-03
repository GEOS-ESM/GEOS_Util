#!/usr/bin/env python3
#
# remap_restarts package:
#   remap_params.py uses the dictionary `answers` (from remap_questions.py) as inputs and 
#   generates a yaml config file named `remap_params.yaml`.
#
import os,sys
import ruamel.yaml
import shutil
import glob
import time
import shlex
import subprocess
from datetime import datetime
from datetime import timedelta
from remap_utils import *

class remap_params(object):
  def __init__(self, config = None, answers = None):

     # load template and fill in answers
     if answers :
       config_tpl = get_config_from_answer(answers, config_tpl = True)

     bc_version = config_tpl['output']['shared'].get('bc_version')
     config_tpl['output']['surface']['split_saltwater'] = True
     if 'Ganymed' in bc_version :
       config_tpl['output']['surface']['split_saltwater'] = False

     self.config = config_tpl

if __name__ == "__main__":
  yaml = ruamel.yaml.YAML()
  stream =''
  with open("raw_answers.yaml", "r") as f:
     stream = f.read()
  config = yaml.load(stream)
  answers = flatten_nested(config)
  param = remap_params(answers, config_tpl = True) 
  config_to_yaml(param.config, 'remap_params.yaml') 
