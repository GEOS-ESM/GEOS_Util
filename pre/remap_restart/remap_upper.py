#!/usr/bin/env python3
#
# remap_restarts package:
#   remap_upper.py remaps atmospheric model restarts using config inputs from `remap_params.yaml`
#
# to run, must first load modules (incl. python3) as follows:
#
#   source g5_modules.sh    [bash]
#   source g5_modules       [csh]
#
import os
import ruamel.yaml
import subprocess
import shlex
import shutil
import glob
from remap_base import remap_base
from remap_utils import get_label 
from remap_utils import STRETCH_GRID
from remap_utils import get_topodir
from remap_bin2nc import bin2nc

class upperair(remap_base):
  def __init__(self, **configs):
     super().__init__(**configs)
     self.copy_merra2()

  def remap(self):
     if not self.config['output']['air']['remap'] :
        return
     self.air_restarts =["fvcore_internal_rst"      ,
                    "moist_internal_rst"       ,
                    "agcm_import_rst"          ,
                    "agcm_internal_rst"        ,
                    "carma_internal_rst"       ,
                    "achem_internal_rst"   ,
                    "geoschemchem_internal_rst",
                    "gmichem_internal_rst"     ,
                    "gocart_internal_rst"      ,
                    "hemco_internal_rst"       ,
                    "mam_internal_rst"         ,
                    "matrix_internal_rst"      ,
                    "pchem_internal_rst"       ,
                    "stratchem_internal_rst"   ,
                    "ss_internal_rst"          ,
                    "du_internal_rst"          ,
                    "cabr_internal_rst"        ,
                    "cabc_internal_rst"        ,
                    "caoc_internal_rst"        ,
                    "ni_internal_rst"          ,
                    "su_internal_rst"          ,
                    "tr_internal_rst"]
     restarts_in = self.find_rst()
     if len(restarts_in) == 0:
       return

     print( "\nRemapping upper air......\n")
     config = self.config
     cwdir  = os.getcwd()
     bindir  = os.path.dirname(os.path.realpath(__file__))
     out_dir    = config['output']['shared']['out_dir']

     if not os.path.exists(out_dir) : os.makedirs(out_dir)
     print( "cd " + out_dir)
     os.chdir(out_dir)

     tmpdir = out_dir+'/upper_data/'
     if os.path.exists(tmpdir) : subprocess.call(['rm', '-rf',tmpdir])
     print ("mkdir " + tmpdir)
     os.makedirs(tmpdir)

     print( "cd " + tmpdir)
     os.chdir(tmpdir)

     print('\nUpper air restart file names link from "_rst" to "_restart_in" \n')
     types = '.bin'
     type_str = subprocess.check_output(['file','-b', restarts_in[0]])
     type_str = str(type_str)
     if type_str.find('Hierarchical') >=0:
        types = '.nc4'
     yyyymmddhh_ = str(config['input']['shared']['yyyymmddhh'])

     label = get_label(config)
     suffix = yyyymmddhh_[0:8]+'_'+yyyymmddhh_[8:10] +'z' + types + label
     for rst in restarts_in :
       f = os.path.basename(rst).split('_rst')[0].split('.')[-1]+'_restart_in'
       cmd = '/bin/ln -s  ' + rst + ' ' + f
       print('\n'+cmd)
       subprocess.call(shlex.split(cmd))
 
     in_bc_base     = config['input']['shared']['bc_base'] 
     in_bc_version  = config['input']['shared']['bc_version']
     agrid       = config['input']['shared']['agrid']
     ogrid       = config['input']['shared']['ogrid']
     omodel      = config['input']['shared']['omodel']
     stretch     = config['input']['shared']['stretch']
     topo_bcsdir = get_topodir(in_bc_base, in_bc_version,  agrid, ogrid, omodel, stretch)

     topoin = glob.glob(topo_bcsdir+'/topo_DYN_ave*.data')[0]
     # link topo file

     cmd = '/bin/ln -s ' + topoin + ' .'
     print('\n'+cmd)
     subprocess.call(shlex.split(cmd))

     out_bc_base    = config['output']['shared']['bc_base'] 
     out_bc_version = config['output']['shared']['bc_version']
     agrid       = config['output']['shared']['agrid']
     ogrid       = config['output']['shared']['ogrid']
     omodel      = config['output']['shared']['omodel']
     stretch     = config['output']['shared']['stretch']
     topo_bcsdir = get_topodir(out_bc_base, out_bc_version, agrid, ogrid, omodel, stretch)

     topoout = glob.glob(topo_bcsdir+'/topo_DYN_ave*.data')[0]
     cmd = '/bin/ln -s ' + topoout + ' topo_dynave.data'
     print('\n'+cmd)
     subprocess.call(shlex.split(cmd))
     #fname = os.path.basename(topoout)
     #cmd = '/bin/ln -s ' + fname + ' topo_dynave.data'
     #print('\n'+cmd)
     #subprocess.call(shlex.split(cmd))

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

     QOS = "#SBATCH --qos="+config['slurm']['qos']
     TIME ="#SBATCH --time=1:00:00"
     if NPE > 532: 
       assert config['slurm']['qos'] != 'debug', "qos should be allnccs"
       TIME = "#SBATCH --time=12:00:00"

     PARTITION = "#SBATCH --partition=" + config['slurm']['partition']

     log_name = out_dir+'/remap_upper_log'

     # We need to create an input.nml file which is different if we are running stretched grid
     # If we are running stretched grid, we need to pass in the target lon+lat and stretch factor
     # to interp_restarts.x. Per the code we use:
     #  -stretched_grid target_lon target_lat stretch_fac
     # If we are not running stretched grid, we should pass in a blank string
     stretch = config['output']['shared']['stretch']
     stretch_str = ""
     if stretch:
        if stretch == 'SG001':
          stretch_fac = STRETCH_GRID['SG001'][0]
          target_lat  = STRETCH_GRID['SG001'][1]
          target_lon  = STRETCH_GRID['SG001'][2]
        elif stretch == 'SG002':
          stretch_fac = STRETCH_GRID['SG002'][0]
          target_lat  = STRETCH_GRID['SG002'][1]
          target_lon  = STRETCH_GRID['SG002'][2]
        else:
          exit("This stretched grid option is not supported " + str(stretch))

        # note "reversed" order of args (relative to order in definition of STRETCH_GRID)  

        stretch_str = "-stretched_grid " + str(target_lon) + " " + str(target_lat) + " " + str(stretch_fac)

     # Now, let's create the input.nml file
     # We need to create a namelist for the upper air remapping
     # All resolutions get an &fms_nml namelist
     nml_file ="""
&fms_nml
    print_memory_usage=.false.
    domains_stack_size = 24000000
/
"""
     # Now, let's write the input.nml file
     with open('input.nml', 'w') as f:
        f.write(nml_file)

     remap_template="""#!/bin/csh -xf
#SBATCH --account={account}
#SBATCH --ntasks={NPE}
#SBATCH --job-name=remap_upper
#SBATCH --output={log_name}
{TIME}
{QOS}
{PARTITION}

unlimit

cd {out_dir}/upper_data
source {Bin}/g5_modules
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
     account = config['slurm']['account']
     drymassFLG  = config['input']['air']['drymass']
     hydrostatic = config['input']['air']['hydrostatic']
     nlevel = config['output']['air']['nlevel']

     remap_upper_script = remap_template.format(Bin=bindir, account = account, \
             out_dir = out_dir, log_name = log_name, drymassFLG = drymassFLG, \
             imout = imout, nwrit = nwrit, NPE = NPE, \
             QOS = QOS, TIME = TIME, PARTITION = PARTITION, nlevel = nlevel, hydrostatic = hydrostatic,
             stretch_str = stretch_str)

     script_name = './remap_upper.j'

     upper = open(script_name,'wt')
     upper.write(remap_upper_script)
     upper.close()

     interactive = os.getenv('SLURM_JOB_ID', default = None)

     if (interactive) :
       print('interactive mode\n')
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
     else :
       print('sbatch -W '+ script_name +'\n')
       subprocess.call(['sbatch', '-W', script_name])

#
#    post process
#
     expid = config['output']['shared']['expid']
     if (expid) :
        expid = expid + '.'
     else:
        expid = ''
     suffix = '_rst.' + suffix

     for out_rst in glob.glob("*_rst*"):
       filename = expid + os.path.basename(out_rst).split('_rst')[0].split('.')[-1]+suffix
       print('\n Move ' + out_rst + ' to ' + out_dir+"/"+filename)
       shutil.move(out_rst, out_dir+"/"+filename)

     print('\n Move remap_upper.j to ' + out_dir)
     shutil.move('remap_upper.j', out_dir+"/remap_upper.j")
     with open(out_dir+'/cap_restart', 'w') as f:
        yyyymmddhh_ = str(config['input']['shared']['yyyymmddhh'])
        time = yyyymmddhh_[0:8]+' '+yyyymmddhh_[8:10]+'0000'
        print('Create cap_restart')
        f.write(time)
     print('cd ' + cwdir)
     os.chdir(cwdir)

     self.remove_merra2()

  def find_rst(self):
     rst_dir = self.config['input']['shared']['rst_dir']
     yyyymmddhh_ = str(self.config['input']['shared']['yyyymmddhh'])
     time = yyyymmddhh_[0:8]+'_'+yyyymmddhh_[8:10]
     restarts_in=[]
     for f in self.air_restarts :
        files = glob.glob(rst_dir+ '/*'+f+'*'+time+'*')
        if len(files) >0:
          restarts_in.append(files[0])
     if (len(restarts_in) == 0) :
        print("\n try restart file names without time stamp\n")
        for f in self.air_restarts :
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
    print(' Stage MERRA-2 upper air restarts \n from \n    ' + merra_2_rst_dir + '\n to\n    '+ rst_dir +'\n')

    upperin =[merra_2_rst_dir +  expid+'.fvcore_internal_rst.' + suffix,
              merra_2_rst_dir +  expid+'.moist_internal_rst.'  + suffix,
              merra_2_rst_dir +  expid+'.gocart_internal_rst.' + suffix,
              merra_2_rst_dir +  expid+'.pchem_internal_rst.'  + suffix,
              merra_2_rst_dir +  expid+'.agcm_import_rst.'     + suffix ]
    bin2nc_yaml = ['bin2nc_merra2_fv.yaml', 'bin2nc_merra2_moist.yaml', 'bin2nc_merra2_gocart.yaml', 'bin2nc_merra2_pchem.yaml','bin2nc_merra2_agcm.yaml']
    bin_path = os.path.dirname(os.path.realpath(__file__))
    for (f, yf) in zip(upperin,bin2nc_yaml) :
       fname = os.path.basename(f)
       dest = rst_dir + '/'+fname
       print("Stage file "+f +" to " + rst_dir)
       shutil.copy(f, dest)
       ncdest = dest.replace('z.bin', 'z.nc4')
       yaml_file = bin_path + '/'+yf
       print('Convert bin to nc4:' + dest + ' to \n' + ncdest + '\n')
       if '_fv' in yf:
         bin2nc(dest, ncdest, yaml_file, isDouble=True, hasHeader=True)
       else:
         bin2nc(dest, ncdest, yaml_file)
       os.remove(dest)

if __name__ == '__main__' :
   air = upperair(params_file='remap_params.yaml')
   air.remap()
