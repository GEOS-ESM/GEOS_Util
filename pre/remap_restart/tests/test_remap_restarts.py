#!/usr/bin/env python3
#
# source install/bin/g5_modules
#
# Newer GEOS code should load a module with GEOSpyD Python3 if not run:
#   module load python/GEOSpyD/Min4.10.3_py3.9
#
import os
import sys, getopt
import ruamel.yaml
import questionary
import glob
import subprocess as sp
import remap_restarts 
from remap_utils import *
from remap_upper import *
from remap_lake_landice_saltwater import *
from remap_analysis  import *
from remap_catchANDcn  import *

def compare(base, result):
  #1) comparing nc4
  bases   =  glob.glob(base + '/*_rst*.nc4*')
  results =  glob.glob( result + '/*_rst*.nc4*')
  if (len(bases) != len(results)) :
     print(len(bases), len(results))
     print (" number of restart out should be the same")
     return False
  bases.sort()
  results.sort()
  basedir = os.environ['BASEDIR']
  NCCMP   = basedir+'/Linux/bin/nccmp'
  for b, r in zip(bases, results):
     cmd = NCCMP + ' -dmgfs '+ b + ' ' + r
     print(cmd)
     p = sp.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
     (out, err) = p.communicate()
     rc = p.wait()
     out = out.decode().split()
     if "identical." in out :
        print('identical')
     else: 
        print ( b + ' is different from ' + r)
        return False
  return True

def test_remap(config):

  upper = upperair(config_obj=config)
  upper.remap()
  lls  = lake_landice_saltwater(config_obj=config)
  lls.remap()
  catch  = catchANDcn(config_obj=config)
  catch.remap()
  ana = analysis(config_obj=config)
  ana.remap()


if __name__ == '__main__' :

  if GEOS_SITE != "NCCS" :
     print("Test baseline data are only available at NCCS.  Please run tests on Discover.")
     exit()
  yaml = ruamel.yaml.YAML()
  stream =''
  cases_yaml = 'test_remap_cases.yaml'
  with  open(cases_yaml, 'r') as f:
     stream = f.read()
  cases = yaml.load(stream)

  cmd = 'whoami'
  p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
  (user, err) = p.communicate()
  p_status = p.wait()
  user = user.decode().split()[0]  
  
  report ={}
  for case, values in cases.items():
     base_line        = values['base_line']
     config_yaml_file = values['config']

     stream =''
     with  open(config_yaml_file, 'r') as f:
       stream = f.read()
     config  = yaml.load(stream)

     out_dir = '/discover/nobackup/'+user+'/REMAP_TESTS/'+case+'/'
     config['output']['shared']['out_dir'] = out_dir
     config['slurm_pbs']['account'] = get_account()
     
     test_remap(config)
 
     rc = compare(base_line, out_dir)
     if (not rc) :
       print ("failed in " + case)
       report[case] = "Failed"
     else :
       report[case] = "Succeeded"
       print (case +" test is successful")
 
  print("\n\n")
  for case, result in report.items():
     print(case + ":   " + result)
