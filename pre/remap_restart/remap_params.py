#!/usr/bin/env python3
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
  def __init__(self, config_from_question):
     self.common_in     = config_from_question['input']['shared']
     self.common_out    = config_from_question['output']['shared']
     self.upper_out     = config_from_question['output']['air']
     self.slurm_options = config_from_question['slurm']
     self.surf_in  = config_from_question['input']['surface']
     self.surf_out = config_from_question['output']['surface']
     self.ana_out  = config_from_question['output']['analysis']

     # load input yaml
     yaml = ruamel.yaml.YAML() 
     stream = ''
     remap_tpl = os.path.dirname(os.path.realpath(__file__)) + '/remap_params.tpl'
     with  open(remap_tpl, 'r') as f:
       stream = f.read()
     config_tpl = yaml.load(stream)

     # params for shared
     config_tpl['input']['shared']['MERRA-2']  = self.common_in.get('MERRA-2')
     config_tpl['input']['shared']['agrid']    = self.common_in.get('agrid')
     config_tpl['input']['shared']['ogrid']    = self.common_in.get('ogrid')
     config_tpl['input']['shared']['rst_dir']  = self.common_in['rst_dir']+'/'
     config_tpl['input']['shared']['expid']    = self.common_in.get('expid')
     config_tpl['input']['shared']['yyyymmddhh'] = self.common_in['yyyymmddhh']
     config_tpl['input']['shared']['tag']        = self.common_in.get('tag')
     config_tpl['input']['surface']['catch_model']       = self.surf_in.get('catch_model')

     config_tpl['output']['air']['nlevel']               = self.upper_out.get('nlevel')
     config_tpl['output']['air']['remap']                = self.upper_out.get('remap')
     config_tpl['output']['surface']['remap_water']      = self.surf_out.get('remap')
     config_tpl['output']['surface']['remap_catch']      = self.surf_out.get('remap')
     config_tpl['output']['shared']['agrid']   = self.common_out['agrid']
     config_tpl['output']['shared']['ogrid']   = self.common_out['ogrid']
     config_tpl['output']['shared']['out_dir'] = self.common_out['out_dir'] + '/'
     config_tpl['output']['shared']['expid']   = self.common_out['expid']
     config_tpl['output']['shared']['tag']     = self.common_out.get('tag')
     config_tpl['output']['shared']['label']  = self.common_out.get('label')

     config_tpl['input']['shared']['bcs_dir']    = self.common_in['bcs_dir']
     config_tpl['output']['shared']['bcs_dir']   = self.common_out['bcs_dir']
     # params for upper air
     config_tpl = self.params_for_air(config_tpl)
     config_tpl = self.params_for_surface(config_tpl)
     config_tpl = self.params_for_analysis(config_tpl)
     config_tpl = self.options_for_slurm(config_tpl)

     self.config = config_tpl

  def params_for_air(self, config_tpl):
     if self.common_in['MERRA-2']:
       return config_tpl 
        
     ogrid = config_tpl['input']['shared']['ogrid']
     tagout = self.common_out['tag']
     bctag  = get_bcTag(tagout, ogrid)
     tagrank = TagsRank[bctag]
     if ( not config_tpl['input']['air']['drymass']) :
        config_tpl['input']['air']['drymass'] = 0
        if tagrank >=12 :
          config_tpl['input']['air']['drymass'] = 1

     return config_tpl

  def options_for_slurm(self, config_tpl):
    config_tpl['slurm']['account'] = self.slurm_options['account']
    config_tpl['slurm']['qos'] = self.slurm_options['qos']
    config_tpl['slurm']['constraint'] = self.slurm_options['constraint']
    return config_tpl

  def params_for_surface(self, config_tpl):
    config_tpl['output']['surface']['surflay'] = 20.
    tagout = self.common_out['tag']
    ogrid = self.common_out['ogrid']
    bctag = get_bcTag(tagout, ogrid)
    tagrank = TagsRank[bctag]
    if tagrank >=12 :
       config_tpl['output']['surface']['surflay'] = 50.
    if tagrank >= TagsRank["Icarus_Reynolds"]:
       config_tpl['output']['surface']['split_saltwater'] = True
    config_tpl['input']['surface']['zoom']= self.surf_in['zoom']
    config_tpl['input']['surface']['wemin']= self.surf_in['wemin']
    config_tpl['output']['surface']['wemin']= self.surf_out['wemin']
    config_tpl['input']['surface']['catch_model'] = self.surf_in.get('catch_model')
    return config_tpl

  def params_for_analysis(self, config_tpl):
    config_tpl['output']['analysis']['lcv'] = self.ana_out.get('lcv')
    config_tpl['output']['analysis']['bkg'] = self.ana_out.get('bkg')
    
    ogrid = self.common_out['ogrid']
    tagout = self.common_out['tag']
    bctag  = get_bcTag(tagout, ogrid)
    tagrank = TagsRank[bctag]
    if tagrank >= TagsRank["Ganymed-4_0_Reynolds"] :
      config_tpl['output']['analysis']['aqua'] = True
    return config_tpl

if __name__ == "__main__":
  yaml = ruamel.yaml.YAML()
  stream =''
  with open("raw_answers.yaml", "r") as f:
     stream = f.read()
  config = yaml.load(stream)
  param = remap_params(config) 
  config_to_yaml(param.config, 'remap_params.yaml') 
