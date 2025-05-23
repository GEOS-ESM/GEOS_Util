#!/usr/bin/env python3
#
# remap_restarts package:
#   remap_catchANDcn.py remaps Catchment[CN] land model restarts using config inputs from `remap_params.yaml`
#
# to run, must first load modules (incl. python3) as follows:
#
#   source g5_modules.sh    [bash]
#   source g5_modules       [csh]
#
import os
import sys
import subprocess
import shutil
import glob
import ruamel.yaml
import shlex
import mimetypes
import netCDF4 as nc
from remap_base import remap_base
from remap_utils import *

class catchANDcn(remap_base):
  def __init__(self, **configs):
     super().__init__(**configs)
     if self.config['input']['shared']['MERRA-2']:
        self.copy_merra2()
     if self.config['input']['shared']['GEOS-IT']:
        self.copy_geosit()

  def remap(self):
     if not self.config['output']['surface']['remap_catch']:
        return

     config = self.config
     rst_dir = config['input']['shared']['rst_dir']
     model = config['input']['surface']['catch_model']
     in_rstfile = ''
     yyyymmddhh_ = str(self.config['input']['shared']['yyyymmddhh'])
     time = yyyymmddhh_[0:8]+'_'+yyyymmddhh_[8:10]
     in_rstfiles = glob.glob(rst_dir+'/*'+model+'_*'+time+'*')
     if len(in_rstfiles) == 0:
        print('\n try catch[cn] restart file without time stamp')
        in_rstfiles = glob.glob(rst_dir+'/*'+model+'_internal_rst')
     if len(in_rstfiles) == 0:
        print("Can not find restart file in " + rst_dir)
        print("Please use the name format as *"  + model+'_*'+time+'*')
        print(" Or *"+model+"_internal_rst")
        return
     in_rstfile = in_rstfiles[0]


     cwdir          = os.getcwd()
     bindir         = os.path.dirname(os.path.realpath(__file__))
     in_bc_base     = config['input']['shared']['bc_base']
     in_bc_version  = config['input']['shared']['bc_version']
     out_bc_base    = config['output']['shared']['bc_base']
     out_bc_version = config['output']['shared']['bc_version']
     out_dir        = config['output']['shared']['out_dir']
     expid          = config['output']['shared']['expid']
     in_wemin       = config['input']['surface']['wemin']
     out_wemin      = config['output']['surface']['wemin']
     surflay        = config['output']['surface']['surflay']
     in_tilefile    = config['input']['surface']['catch_tilefile']

     if "gmao_SIteam/ModelData" in out_bc_base:
        assert  GEOS_SITE == "NAS", "wrong site to run the package"

     if not in_tilefile :
        agrid        = config['input']['shared']['agrid']
        ogrid        = config['input']['shared']['ogrid']
        omodel       = config['input']['shared']['omodel']
        stretch      = config['input']['shared']['stretch']
        EASE_grid    = config['input']['surface'].get('EASE_grid', None)

        bc_geomdir   = get_geomdir(in_bc_base, in_bc_version, agrid=agrid, ogrid=ogrid, omodel=omodel, stretch=stretch, grid=EASE_grid)
        in_tilefile  = glob.glob(bc_geomdir + '/*.til')[0]

     agrid        = config['output']['shared']['agrid']
     ogrid        = config['output']['shared']['ogrid']
     omodel       = config['output']['shared']['omodel']
     stretch      = config['output']['shared']['stretch']
     out_tilefile = config['output']['surface']['catch_tilefile']
     EASE_grid    = config['output']['surface'].get('EASE_grid', None)

     if not out_tilefile :
        bc_geomdir  = get_geomdir(out_bc_base, out_bc_version, agrid=agrid, ogrid=ogrid, omodel=omodel, stretch=stretch, grid=EASE_grid)
        out_tilefile = glob.glob(bc_geomdir+ '/*.til')[0]

     out_bc_landdir = get_landdir(out_bc_base, out_bc_version, agrid=agrid, ogrid=ogrid, omodel=omodel, stretch=stretch, grid=EASE_grid)

     label = get_label(config)

     suffix     = time+'z.nc4' + label

     if (expid) :
        expid = expid + '.'
     else:
        expid = ''

     no_remap = self.copy_without_remap([in_rstfile], in_tilefile, out_tilefile, suffix, catch=True)
     if (no_remap) : return

     print("\nRemapping " + model + ".....\n")
 # determine NPE based on *approximate* number of input and output tile

     in_Ntile  = 0
     mime = mimetypes.guess_type(in_rstfile)
     if mime[0] and 'stream' in mime[0]: # binary
       in_Ntile  = 1684725 # if it is binary, it is safe to assume the maximum is M09
     else : # nc4 file
       ds = nc.Dataset(in_rstfile)
       in_Ntile = ds.dimensions['tile'].size

     out_Ntile = 0
     with open( out_bc_landdir+'/clsm/catchment.def') as f:
       out_Ntile = int(next(f))
     max_Ntile = max(in_Ntile, out_Ntile)
     NPE = 0
     if   (max_Ntile <=  112573) : # no more than EASEv2_M36
        NPE = 40
     elif (max_Ntile <= 1684725) : # no more than EASEv2_M09
        NPE = 80
     elif (max_Ntile <= 2496756) : # no more than C720
        NPE = 120
     else:
        NPE = 160

     PARTITION =''
     QOS  = config['slurm_pbs']['qos']
     TIME  = "1:00:00"
     if QOS != "debug": TIME="12:00:00"

     NNODE = ''
     job = ''
     if GEOS_SITE == 'NAS':
       job = "PBS"
       CONSTRAINT = 'cas_ait'
       NNODE = (NPE-1)//40 + 1
     else:
       job = "SLURM"
       partition = config['slurm_pbs']['partition']
       if (partition != ''):
         PARTITION = "#SBATCH --partition=" + partition

       CONSTRAINT = '"[cas|mil]"'

     account    = config['slurm_pbs']['account']
     # even if the (MERRA-2) input restarts are binary, the output restarts will always be nc4 (remap_bin2nc.py)
     suffix = '_rst.' + suffix
     out_rstfile = expid + os.path.basename(in_rstfile).split('_rst')[0].split('.')[-1]+suffix

     if not os.path.exists(out_dir) : os.makedirs(out_dir)
     print( "cd " + out_dir)
     os.chdir(out_dir)

     InData_dir = out_dir+'/InData/'
     print ("mkdir -p " + InData_dir)
     os.makedirs(InData_dir, exist_ok = True)

     f = os.path.basename(in_rstfile)
     dest = InData_dir+'/'+f
     # file got copy because the computing node cannot access archive
     print('\nCopy ' + in_rstfile + ' to ' +dest)
     shutil.copyfile(in_rstfile,dest)
     in_rstfile = dest

     log_name = out_dir+'/'+'mk_catchANDcn_log'
     job_name = "mk_catchANDcn"
     mk_catch_j_template = job_directive[job]+ \
"""
source {Bin}/g5_modules
limit stacksize unlimited

set esma_mpirun_X = ( {Bin}/esma_mpirun -np {NPE} )
set mk_catchANDcnRestarts_X   = ( {Bin}/mk_catchANDcnRestarts.x )

set params = ( -model {model}  -time {time} -in_tilefile {in_tilefile} )
set params = ( $params -out_bcs {out_bcs} -out_tilefile {out_tilefile} -out_dir {out_dir} )
set params = ( $params -surflay {surflay} -in_wemin {in_wemin} -out_wemin {out_wemin} )
set params = ( $params -in_rst {in_rstfile} -out_rst {out_rstfile} )
$esma_mpirun_X $mk_catchANDcnRestarts_X $params

"""
     catch1script =  mk_catch_j_template.format(Bin = bindir, account = account, out_bcs = out_bc_landdir, \
                  model = model, out_dir = out_dir, surflay = surflay, log_name = log_name, job_name = job_name, \
                   NPE = NPE, NNODE=NNODE, \
                  in_wemin   = in_wemin, out_wemin = out_wemin, out_tilefile = out_tilefile, in_tilefile = in_tilefile, \
                  in_rstfile = in_rstfile, out_rstfile = out_rstfile, time = yyyymmddhh_, TIME = TIME, QOS=QOS, CONSTRAINT=CONSTRAINT, PARTITION=PARTITION )

     script_name = './mk_catchANDcn.j'

     catch_scrpt = open(script_name,'wt')
     catch_scrpt.write(catch1script)
     catch_scrpt.close()

     interactive = None
     if GEOS_SITE == 'NAS':
       interactive = os.getenv('PBS_JOBID', default = None)
     else:
       interactive = os.getenv('SLURM_JOB_ID', default = None)

     if ( interactive ) :
       print('interactive mode\n')
       if GEOS_SITE != "NAS":
         ntasks = os.getenv('SLURM_NTASKS', default = None)
         if ( not ntasks):
           nnodes = int(os.getenv('SLURM_NNODES', default = '1'))
           ncpus  = int(os.getenv('SLURM_CPUS_ON_NODE', default = '40'))
           ntasks = nnodes * ncpus
         ntasks = int(ntasks)

         if (ntasks < NPE):
           print("\nYou should have at least {NPE} cores. Now you only have {ntasks} cores ".format(NPE=NPE, ntasks=ntasks))

       subprocess.call(['chmod', '755', script_name])
       print(script_name+  '  1>' + log_name  + '  2>&1')
       os.system(script_name + ' 1>' + log_name+ ' 2>&1')
     elif GEOS_SITE == "NAS" :
       print('qsub -W  block=true '+ script_name +'\n')
       subprocess.call(['qsub', '-W','block=true', script_name])
     else:
       print('sbatch -W '+ script_name +'\n')
       subprocess.call(['sbatch', '-W', script_name])

     print( "cd " + cwdir)
     os.chdir(cwdir)

     if self.config['input']['shared']['MERRA-2']:
        self.remove_merra2()

  def copy_merra2(self):
    if not self.config['input']['shared']['MERRA-2']:
      return

    expid = self.config['input']['shared']['expid']
    yyyymmddhh_ = str(self.config['input']['shared']['yyyymmddhh'])
    yyyy_ = yyyymmddhh_[0:4]
    mm_   = yyyymmddhh_[4:6]
    dd_   = yyyymmddhh_[6:8]
    hh_   = yyyymmddhh_[8:10]

    suffix = yyyymmddhh_[0:8]+'_'+ hh_ + 'z.bin'
    merra_2_rst_dir = '/archive/users/gmao_ops/MERRA2/gmao_ops/GEOSadas-5_12_4/'+expid +'/rs/Y'+yyyy_ +'/M'+mm_+'/'
    rst_dir = self.config['input']['shared']['rst_dir'] + '/'
    os.makedirs(rst_dir, exist_ok = True)
    print(' Copy MERRA-2 catchment Restart \n from \n    ' + merra_2_rst_dir + '\n to\n    '+ rst_dir +'\n')

    f =  merra_2_rst_dir +  expid+'.catch_internal_rst.'    + suffix

    fname = os.path.basename(f)
    dest = rst_dir + '/'+fname
    print("Copy file "+f +" to " + rst_dir)
    shutil.copy(f, dest)

def ask_catch_questions():
   catch_input_shared_rst_dir = ''
   def has_rs_rc_out(path):
     if os.path.exists(path):
        dirs = os.listdir(path)
        if 'rs' in dirs and 'rc_out' in dirs:
           nonlocal catch_input_shared_rst_dir
           catch_input_shared_rst_dir = path
           return True
     return False

   def has_catch_rst(text):
     if len(text) !=10: return False
     yyyy = text[0:4]
     mm   = text[4:6]
     dd   = text[6:8]
     hh   = text[8:10]
     nonlocal catch_input_shared_rst_dir
     rst_dir   = catch_input_shared_rst_dir + '/rs/ens0000/Y'+yyyy +'/M'+mm+'/'
     rst_files = glob.glob(rst_dir+'*catch*_internal_rst.'+yyyy+mm+dd+'_'+hh+'00')
     if len(rst_files) !=1 :
       return False
     return True

   questions =[
        {
            "type": "path",
            "name": "input:shared:rst_dir",
            "message": "Enter input directory that contains './rs' and './rc_out' subdirectories:\n",
            "validate": lambda path : has_rs_rc_out(path)
        },

        {
            "type": "text",
            "name": "input:shared:yyyymmddhh",
            "message": (message_datetime + " and rst file must exist.)\n"),
            "validate": lambda text: has_catch_rst(text)
        },

        {
            "type": "path",
            "name": "output:shared:out_dir",
            "message": message_out_dir,
        },

        {
            "type": "text",
            "name": "output:shared:expid",
            "message": message_expid,
            "default": "",
        },

        {
            "type": "select",
            "name": "output:shared:bc_base",
            "message": ("\nSelect " + message_bc_base_new),
            "choices": choices_bc_base,
            "default": get_default_bc_base(),
        },

        {
            "type": "select",
            "name": "output:shared:bc_version",
            "message": message_bc_ops_new,
            "choices": choices_bc_ops,
            "default": "NL3",
        },
        {
            "type": "select",
            "name": "output:shared:bc_version",
            "message": message_bc_other_new,
            "choices": choices_bc_other,
            "when": lambda x:  x["output:shared:bc_version"] == 'Other',
        },

        {
            "type": "select",
            "name": "output:surface:EASE_grid",
            "message": "Select grid for new restart:\n",
            "choices": ['EASEv2_M03', 'EASEv2_M09', 'EASEv2_M25', 'EASEv2_M36', 'Cubed-Sphere']
        },

        {
            "type": "text",
            "name": "output:shared:agrid",
            "message": message_agrid_new,
            "default": 'C360',
            "validate": lambda text : text in validate_agrid,
            "when": lambda x : x['output:surface:EASE_grid'] == 'Cubed-Sphere',
        },

        {
            "type": "select",
            "name": "output:shared:ogrid",
            "message": message_ogrid_new,
            "choices": choices_ogrid_data,
            "default": lambda x: data_ocean_default(x.get('output:shared:agrid')),
            "when": lambda x : x['output:surface:EASE_grid'] == 'Cubed-Sphere',
        },

        # dummy (invisible) question to remove parenthetical comments from selected output:shared:ogrid
        {
            "type": "text",
            "name": "output:shared:ogrid",
            "message": "remove the comment of ogrid",
            # always return false, so questions never shows but changes ogrid
            "when": lambda x: remove_ogrid_comment(x, 'OUT')
        },


        {
            "type": "text",
            "name": "slurm_pbs:qos",
            "message": message_qos,
            "default": "debug",
        },

        {
            "type": "text",
            "name": "slurm_pbs:account",
            "message": message_account,
            "default": get_account(),
        },
        {
            "type": "text",
            "name": "slurm_pbs:partition",
            "message": message_partition,
            "default": '',
        },

   ]

   answers = questionary.prompt(questions)
   yyyy = answers['input:shared:yyyymmddhh'][0:4]
   mm   = answers['input:shared:yyyymmddhh'][4:6]
   dd   = answers['input:shared:yyyymmddhh'][6:8]
   hh   = answers['input:shared:yyyymmddhh'][8:10]

   rst_dir      = answers['input:shared:rst_dir']+'/rs/ens0000/Y'+yyyy +'/M'+mm+'/'
   rst_file     = glob.glob(rst_dir+'*catch*_internal_rst.'+yyyy+mm+dd+'_'+hh+'00')[0]
   idx1         = rst_file.find('catch')
   idx2         = rst_file.find('_internal_rst')
   catch_model  = rst_file[idx1:idx2]

   tile_dir     = answers['input:shared:rst_dir']+'/rc_out/'
   in_tilefiles = glob.glob(tile_dir+'*.til')
   for file in in_tilefiles:
      answers['input:surface:catch_tilefile'] = file
      if 'MAPL_' in file:
         answers['input:surface:catch_tilefile'] = file

   answers['input:shared:rst_dir'] = rst_dir
   answers['input:surface:catch_model'] =  catch_model
   answers['input:surface:wemin']  = "13"
   answers['output:surface:wemin'] = "13"
   answers['output:surface:remap_catch'] = True
   bc_base= answers['output:shared:bc_base'].split(": ")[-1]
   answers['output:shared:bc_base'] = bc_base
   answers['output:shared:out_dir'] = os.path.abspath(answers['output:shared:out_dir'])

   if answers['output:surface:EASE_grid'] == 'Cubed-Sphere' :
      remove_ogrid_comment(answers, 'OUT')
      del answers['output:surface:EASE_grid']
   return answers

def remap_land_only():
   print("\n Remap land (catch[cn]) restart only; global domain only; ens0000 only. \n")
   answers = ask_catch_questions()
   config = get_config_from_answers(answers, config_tpl = True)
   config_yaml = config['output']['shared']['out_dir']+'/remap_params.yaml'
   config_to_yaml(config, config_yaml)
   print_config(config)

   question = [
           {
               "type": "confirm",
               "name": "Continue",
               "message": "Above is the YAML config file, would you like to continue?",
               "default": True
           },]
   answer = questionary.prompt(question)

   if not answer['Continue'] :
       print("\nYou answered not to continue, exiting.\n")
       sys.exit(0)

   catch = catchANDcn(params_file=config_yaml)
   catch.remap()
   catch.remove_geosit()

if __name__ == '__main__' :

   remap_land_only()
