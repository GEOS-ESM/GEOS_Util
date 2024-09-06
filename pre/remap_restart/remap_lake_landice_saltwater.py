#!/usr/bin/env python3
#
# remap_restarts package:
#   remap_lake_landice_saltwater.py remaps lake, landice, and (data) ocean restarts 
#   using config inputs from `remap_params.yaml`
#
# to run, must first load modules (incl. python3) as follows:
#
#   source g5_modules.sh    [bash]
#   source g5_modules       [csh]
#
import os
import subprocess as sp
import shutil
import glob
import ruamel.yaml
import shlex
from remap_base import remap_base
from remap_utils import *
from remap_utils import get_geomdir
from remap_bin2nc import bin2nc

class lake_landice_saltwater(remap_base):
  def __init__(self, **configs):
     super().__init__(**configs)
     self.copy_merra2()

  def remap(self):
     if not self.config['output']['surface']['remap_water']:
        return

     restarts_in = self.find_rst()
     if len(restarts_in) == 0:
       return

     print("\nRemapping land, landice, saltwater.....\n")
     config = self.config
     cwdir  = os.getcwd()
     bindir  = os.path.dirname(os.path.realpath(__file__)) 

     in_bc_base    = config['input']['shared']['bc_base']
     in_bc_version = config['input']['shared']['bc_version']
     out_bc_base   = config['output']['shared']['bc_base']
     out_bc_version= config['output']['shared']['bc_version']

     agrid         = config['input']['shared']['agrid']
     ogrid         = config['input']['shared']['ogrid']
     omodel        = config['input']['shared']['omodel']
     stretch       = config['input']['shared']['stretch']

     in_geomdir    = get_geomdir(in_bc_base, in_bc_version, agrid=agrid, ogrid=ogrid, omodel=omodel, stretch=stretch)
     in_tile_file  = glob.glob(in_geomdir+ '/*-Pfafstetter.til')[0]
     out_geomdir   = get_geomdir(out_bc_base, out_bc_version, agrid=agrid, ogrid=ogrid, omodel=omodel, stretch=stretch)
     out_tile_file = glob.glob(out_geomdir+ '/*-Pfafstetter.til')[0]

     types = '.bin'
     type_str = sp.check_output(['file','-b', os.path.realpath(restarts_in[0])])
     type_str = str(type_str)
     if 'Hierarchical' in type_str:
        types = '.nc4'
     yyyymmddhh_ = str(config['input']['shared']['yyyymmddhh'])

     label = get_label(config) 
     suffix = yyyymmddhh_[0:8]+'_'+yyyymmddhh_[8:10] +'z' + types + label

     out_dir    = config['output']['shared']['out_dir']
     expid = config['output']['shared']['expid']
     if (expid) :
        expid = expid + '.'
     else:
        expid = ''

     no_remap = self.copy_without_remap(restarts_in, in_tile_file, out_tile_file, suffix)
     if no_remap : return

     if not os.path.exists(out_dir) : os.makedirs(out_dir)
     print( "cd " + out_dir)
     os.chdir(out_dir)

     InData_dir = out_dir+'/InData/'
     if os.path.exists(InData_dir) : sp.call(['rm', '-rf',InData_dir])
     print ("mkdir " + InData_dir)
     os.makedirs(InData_dir)

     OutData_dir = out_dir+'/OutData/'
     if os.path.exists(OutData_dir) : sp.call(['rm', '-rf',OutData_dir])
     print ("mkdir " + OutData_dir)
     os.makedirs(OutData_dir)


     saltwater = ''
     seaice    = ''
     landice   = ''
     lake      = ''
     route     = ''
     openwater = ''
     for rst in restarts_in:
        f = os.path.basename(rst)
        dest = InData_dir+'/'+f
        if os.path.exists(dest) : shutil.remove(dest)
        print('\nCopy ' + rst + ' to ' +dest)
        shutil.copy(rst,dest)
        if 'saltwater' in f : saltwater = f
        if 'seaice'    in f : seaice    = f
        if 'landice'   in f : landice   = f
        if 'lake'      in f : lake      = f
        if 'roue'      in f : route     = f
        if 'openwater' in f : openwater = f

     in_til  = InData_dir+'/' + os.path.basename(in_tile_file)
     out_til = OutData_dir+'/'+ os.path.basename(out_tile_file)

     if os.path.exists(in_til)  : shutil.remove(in_til)
     if os.path.exists(out_til) : shutil.remove(out_til)
     print('\n Copy ' + in_tile_file + ' to ' + in_til)
     shutil.copy(in_tile_file, in_til)
     print('\n Copy ' + out_tile_file + ' to ' + out_til)
     shutil.copy(out_tile_file, out_til)

     exe = bindir + '/mk_LakeLandiceSaltRestarts.x '
     zoom = config['input']['surface']['zoom']
     log_name = out_dir+'/remap_lake_landice_saltwater_log'
     if os.path.exists(log_name):
        os.remove(log_name)

     if (saltwater):
       cmd = exe + out_til + ' ' + in_til + ' InData/'+ saltwater + ' 0 ' + str(zoom)
       self.run_and_log(cmd, log_name)
  
       # split Saltwater
       if  config['output']['surface']['split_saltwater']:
         print("\nSplitting Saltwater...\n")
         cmd = bindir+'/SaltIntSplitter.x ' + out_til + ' ' + 'OutData/' + saltwater
#         subprocess.call(shlex.split(cmd))
         openwater = ''
         seaice  = ''
         self.run_and_log(cmd, log_name)

     if (openwater):
       cmd = exe + out_til + ' ' + in_til + ' InData/' + openwater + ' 0 ' + str(zoom)
       self.run_and_log(cmd, log_name)

     if (seaice):
       cmd = exe + out_til + ' ' + in_til + ' InData/' + seaice + ' 0 ' + str(zoom)
       print('\n'+cmd)
       self.run_and_log(cmd, log_name)

     if (lake):
       cmd = exe + out_til + ' ' + in_til + ' InData/' + lake + ' 19 ' + str(zoom)
       self.run_and_log(cmd, log_name)

     if (landice):
       cmd = exe + out_til + ' ' + in_til + ' InData/' + landice + ' 20 ' + str(zoom)
       self.run_and_log(cmd, log_name)

     if (route):
       route = bindir + '/mk_RouteRestarts.x '
       cmd = route + out_til + ' ' + yyyymmddhh_[0:6]
       self.run_and_log(cmd, log_name)

     suffix = '_rst.' + suffix
     for out_rst in glob.glob("OutData/*_rst*"):
       filename = expid + os.path.basename(out_rst).split('_rst')[0].split('.')[-1]+suffix
       print('\n Move ' + out_rst + ' to ' + out_dir+"/"+filename)
       shutil.move(out_rst, out_dir+"/"+filename)
     print('cd ' + cwdir)
     os.chdir(cwdir)


     agrid  = config['output']['shared']['agrid']
     if agrid[0].upper() == 'C':
       imout = int(agrid[1:])
     else:
       exit("Only support cs grid so far")

     if (imout <90):
       NPE =   12; nwrit = 1
     elif (imout<=180):
       NPE =   24; nwrit = 1
     elif (imout<=540):
       NPE =   96; nwrit = 1
     elif (imout<=720):
       NPE =  192; nwrit = 2
     elif (imout<=1080):
       NPE =  384; nwrit = 2
     elif (imout<=1440):
       NPE =  576; nwrit = 2
     elif (imout< 2880):
       NPE =  768; nwrit = 2
     elif (imout>=2880):
       NPE = 5400; nwrit = 6

     PARTITION =''
     QOS  = config['slurm_pbs']['qos']
     TIME = "1:00:00"
     if NPE > 532:
        assert config['slurm_pbs']['qos'] != 'debug', "qos should be 'allnccs' for NCCS or 'normal' for NAS"
        TIME = "12:00:00"
     NNODE = ''
     job=''
     if GEOS_SITE == "NAS":
       CONSTRAINT = 'cas_ait'
       NNODE = (NPE-1)//40 + 1
       job='PBS'
     else:
       job='SLURM'
       partition = config['slurm_pbs']['partition']
       if (partition != ''):
         PARTITION = "#SBATCH --partition=" + partition

       CONSTRAINT = '"[cas|sky]"'
       if BUILT_ON_SLES15:
         CONSTRAINT = 'mil'


     remap_template = job_directive[job] + \
"""
source {Bin}/g5_modules
limit stacksize unlimited

cd {out_dir}/upper_data
/bin/touch input.nml

# The MERRA fvcore_internal_restarts don't include W or DZ, but we can add them by setting
# HYDROSTATIC = 0 which means HYDROSTATIC = FALSE

if ($?I_MPI_ROOT) then
  # intel scaling suggestions
  #--------------------------
  setenv I_MPI_ADJUST_ALLREDUCE 12
  setenv I_MPI_ADJUST_GATHERV 3

  setenv I_MPI_SHM_HEAP_VSIZE 512
  setenv PSM2_MEMORY large
  setenv I_MPI_EXTRA_FILESYSTEM 1
  setenv I_MPI_EXTRA_FILESYSTEM_FORCE gpfs
  setenv ROMIO_FSTYPE_FORCE "gpfs:"
endif
set infiles = ()
set outfils = ()
foreach infile ( *_restart_in )
   if ( $infile == fvcore_internal_restart_in ) continue
   if ( $infile == moist_internal_restart_in ) continue

   set infiles = ( $infiles $infile )
   set outfil = `echo $infile | sed "s/restart_in/rst_out/"`
   set outfils = ($outfils $outfil)
end

set interp_restartsX = {Bin}/interp_restarts.x
if ( $#infiles ) then
    set ioflag = "-input_files $infiles -output_files $outfils"
    set ftype = `file -Lb --mime-type fvcore_internal_restart_in`
    if ($ftype =~ *stream*) then
      set interp_restartsX = {Bin}/interp_restarts_bin.x
    endif
else
    set ioflag = ""
endif

set drymassFLG = {drymassFLG}
if ($drymassFLG) then
    set dmflag = ""
else
    set dmflag = "-scalers F"
endif

{Bin}/esma_mpirun -np {NPE} $interp_restartsX -im {imout} -lm {nlevel} \\
   -do_hydro {hydrostatic} $ioflag $dmflag -nwriter {nwrit} {stretch_str}

"""
     account = config['slurm_pbs']['account']
     drymassFLG  = config['input']['air']['drymass']
     hydrostatic = config['input']['air']['hydrostatic']
     nlevel = config['output']['air']['nlevel']
     log_name = out_dir+'/remap_lake_landice_saltwater_log'
     job_name = 'remap_lake_landice_saltwater'
     stretch_str = ''
     remap_script = remap_template.format(Bin=bindir, account = account, \
             out_dir = out_dir, log_name = log_name, job_name= job_name, drymassFLG = drymassFLG, \
             imout = imout, nwrit = nwrit, NPE = NPE, NNODE = NNODE, \
             QOS = QOS, TIME = TIME, CONSTRAINT = CONSTRAINT, PARTITION = PARTITION, nlevel = nlevel, hydrostatic = hydrostatic,
             stretch_str = stretch_str)  

     script_name = './remap_lake_landice_saltwater.j'

     lake_landice_saltwater = open(script_name, 'wt')
     lake_landice_saltwater.write(remap_script)
     lake_landice_saltwater.close()

     in_bc_base = config['input']['shared']['bc_base']
     if "gmao_SIteam/ModelData" in in_bc_base:
        assert  GEOS_SITE == "NAS", "wrong site to run the package"

     interactive = None
     if GEOS_SITE == 'NAS':
       interactive = os.getenv('PBS_JOBID', default = None)
     else:
       interactive = os.getenv('SLURM_JOB_ID', default = None)

     if (interactive) :
       print('interactive mode\n')
       if GEOS_SITE != 'NAS':
         ntasks = os.getenv('SLURM_NTASKS', default = None)
         if ( not ntasks):
           nnodes = int(os.getenv('SLURM_NNODES', default = '1'))
           ncpus  = int(os.getenv('SLURM_CPUS_ON_NODE', default = '28'))
           ntasks = nnodes * ncpus
         ntasks = int(ntasks)
         if (ntasks < NPE ):
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

#
#    post process
#
     suffix = '_rst.' + suffix

     for out_rst in glob.glob("*_rst*"):
       filename = expid + os.path.basename(out_rst).split('_rst')[0].split('.')[-1]+suffix
       print('\n Move ' + out_rst + ' to ' + out_dir+"/"+filename)
       shutil.move(out_rst, out_dir+"/"+filename)

     print('\n Move remap_lake_landice_saltwater.j to ' + out_dir)
     shutil.move('remap_lake_landice_saltwater.j', out_dir+"/remap_lake_landice_saltwater.j")
     with open(out_dir+'/cap_restart', 'w') as f:
        yyyymmddhh_ = str(config['input']['shared']['yyyymmddhh'])
        time = yyyymmddhh_[0:8]+' '+yyyymmddhh_[8:10]+'0000'
        print('Create cap_restart')
        f.write(time)
     print('cd ' + cwdir)
     os.chdir(cwdir)

     self.remove_merra2()

  def run_and_log(self, cmd, log_name):
     print('\n'+cmd)
     process =sp.Popen(shlex.split(cmd), stdout=sp.PIPE, stderr=sp.PIPE)
     stdout, stderr = process.communicate()
     stdout = stdout.decode()
     stderr = stderr.decode()
     print('\n'+ stdout)
     print('\n'+ stderr)
     with open(log_name, "a") as log_:
        log_.write(cmd)
        log_.write(stdout)
        log_.write(stderr)


  def find_rst(self):
     surf_restarts =[
        "route_internal_rst"       ,
        "lake_internal_rst"        ,
        "landice_internal_rst"     ,
        "openwater_internal_rst"   ,
        "saltwater_internal_rst"   ,
        "seaicethermo_internal_rst"]

     rst_dir = self.config['input']['shared']['rst_dir']
     yyyymmddhh_ = str(self.config['input']['shared']['yyyymmddhh'])
     time = yyyymmddhh_[0:8]+'_'+yyyymmddhh_[8:10]
     restarts_in=[]
     for f in surf_restarts :
        files = glob.glob(rst_dir+ '/*'+f+'*'+time+'*')
        if len(files) >0:
           restarts_in.append(files[0])
     if (len(restarts_in) == 0) :
        print("\n try restart file names without time stamp\n")
        for f in surf_restarts :
           fname = rst_dir+ '/'+f
           if os.path.exists(fname):
              restarts_in.append(fname)

     return restarts_in

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
     print(' Copy MERRA-2 surface restarts \n from \n    ' + merra_2_rst_dir + '\n to\n    '+ rst_dir +'\n')

     surfin = [ merra_2_rst_dir +  expid+'.lake_internal_rst.'     + suffix,
                merra_2_rst_dir +  expid+'.landice_internal_rst.'  + suffix,
                merra_2_rst_dir +  expid+'.saltwater_internal_rst.'+ suffix]
     bin2nc_yaml = ['bin2nc_merra2_lake.yaml', 'bin2nc_merra2_landice.yaml','bin2nc_merra2_salt.yaml']
     bin_path = os.path.dirname(os.path.realpath(__file__))
     for (f,yf) in zip(surfin, bin2nc_yaml):
        fname = os.path.basename(f)
        dest = rst_dir + '/'+fname
        print("Copy file "+f +" to " + rst_dir)
        shutil.copy(f, dest)
        ncdest = dest.replace('z.bin', 'z.nc4')
        yaml_file = bin_path + '/'+yf
        print('Convert bin to nc4:' + dest + ' to \n' + ncdest + '\n')
        bin2nc(dest, ncdest, yaml_file)
        os.remove(dest)

if __name__ == '__main__' :
   lls = lake_landice_saltwater(params_file='remap_params.yaml')
   lls.remap()
