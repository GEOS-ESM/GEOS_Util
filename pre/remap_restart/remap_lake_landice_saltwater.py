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
import subprocess
import glob
import ruamel.yaml
import shlex
from remap_base import remap_base
from remap_utils import (
    get_label,
    get_geomdir,
    get_zoom,
    get_landdir,
    job_directive,
    GEOS_SITE,
)
from remap_bin2nc import bin2nc


class lake_landice_saltwater(remap_base):
    def __init__(self, **configs):
        super().__init__(**configs)
        if self.config["input"]["shared"]["MERRA-2"]:
            self.copy_merra2()
        if self.config["input"]["shared"]["GEOS-IT"]:
            self.copy_geosit()

    def remap(self):
        if not self.config["output"]["surface"]["remap_water"]:
            return

        restarts_in = self.find_rst()
        if len(restarts_in) == 0:
            return

        print("\nRemapping land, landice, saltwater.....\n")
        config = self.config
        cwdir = os.getcwd()
        bindir = os.path.dirname(os.path.realpath(__file__))

        in_bc_base = config["input"]["shared"]["bc_base"]
        in_bc_version = config["input"]["shared"]["bc_version"]
        out_bc_base = config["output"]["shared"]["bc_base"]
        out_bc_version = config["output"]["shared"]["bc_version"]

        agrid = config["input"]["shared"]["agrid"]
        ogrid = config["input"]["shared"]["ogrid"]
        omodel = config["input"]["shared"]["omodel"]
        stretch = config["input"]["shared"]["stretch"]
        in_tile_file = config["input"]["surface"]["catch_tilefile"]
        if not in_tile_file:
            EASE_grid = config["input"]["surface"].get("EASE_grid", None)
            in_geomdir = get_geomdir(
                in_bc_base,
                in_bc_version,
                agrid=agrid,
                ogrid=ogrid,
                omodel=omodel,
                stretch=stretch,
                grid=EASE_grid,
            )
            in_tile_file = glob.glob(in_geomdir + "/*.til")[0]

        agrid = config["output"]["shared"]["agrid"]
        ogrid = config["output"]["shared"]["ogrid"]
        omodel = config["output"]["shared"]["omodel"]
        stretch = config["output"]["shared"]["stretch"]
        EASE_grid = config["output"]["surface"].get("EASE_grid", None)
        out_tile_file = config["output"]["surface"]["catch_tilefile"]
        if not out_tile_file:
            out_geomdir = get_geomdir(
                out_bc_base,
                out_bc_version,
                agrid=agrid,
                ogrid=ogrid,
                omodel=omodel,
                stretch=stretch,
                grid=EASE_grid,
            )
            out_tile_file = glob.glob(out_geomdir + "/*.til")[0]

        types = ".bin"
        type_str = sp.check_output(["file", "-b", os.path.realpath(restarts_in[0])])
        type_str = str(type_str)
        if "Hierarchical" in type_str:
            types = ".nc4"
        yyyymmddhh_ = str(config["input"]["shared"]["yyyymmddhh"])

        label = get_label(config)
        suffix = yyyymmddhh_[0:8] + "_" + yyyymmddhh_[8:10] + "z" + types + label

        out_dir = config["output"]["shared"]["out_dir"]
        expid = config["output"]["shared"]["expid"]
        if expid:
            expid = expid + "."
        else:
            expid = ""

        no_remap = self.copy_without_remap(
            restarts_in, in_tile_file, out_tile_file, suffix
        )
        if no_remap:
            return

        # Determine NPE and TIME based on resolution
        # Lake-landice remapping uses serial execution but needs MPI for MAPL
        NPE = 1

        # Determine output tile count to set appropriate walltime
        out_Ntile = 0
        out_bc_landdir = get_landdir(
            out_bc_base,
            out_bc_version,
            agrid=agrid,
            ogrid=ogrid,
            omodel=omodel,
            stretch=stretch,
            grid=EASE_grid,
        )
        with open(out_bc_landdir + "/clsm/catchment.def") as f:
            out_Ntile = int(next(f))

        # Set TIME based on resolution
        # 30 minutes for lower resolutions, 1 hour for high resolutions
        TIME = "0:30:00"
        if (
            out_Ntile > 277025
        ):  # larger than C360 (~277k tiles) or EASEv2_M25 (~244k tiles)
            TIME = "1:00:00"

        # Get job configuration from config
        account = config["slurm_pbs"]["account"]
        reservation = config["slurm_pbs"]["reservation"]
        partition = config["slurm_pbs"]["partition"]
        qos = config["slurm_pbs"]["qos"]

        # Determine job type and node configuration
        NNODE = 1
        job = ""
        CONSTRAINT = ""
        RESERVATION = ""
        PARTITION = ""
        QOS = ""

        if GEOS_SITE == "NAS":
            job = "PBS"
            CONSTRAINT = "cas_ait"
            if qos != "":
                QOS = "#PBS  -q " + qos
        else:
            job = "SLURM"
            CONSTRAINT = '"[cas|mil]"'
            if reservation != "":
                RESERVATION = "#SBATCH --reservation=" + reservation
            if partition != "":
                PARTITION = "#SBATCH --partition=" + partition
            if qos != "":
                QOS = "#SBATCH  --qos=" + qos

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        print("cd " + out_dir)
        os.chdir(out_dir)

        InData_dir = out_dir + "/InData/"
        if os.path.exists(InData_dir):
            sp.call(["rm", "-rf", InData_dir])
        print("mkdir " + InData_dir)
        os.makedirs(InData_dir)

        OutData_dir = out_dir + "/OutData/"
        if os.path.exists(OutData_dir):
            sp.call(["rm", "-rf", OutData_dir])
        print("mkdir " + OutData_dir)
        os.makedirs(OutData_dir)

        saltwater_internal = ""
        saltwater_import = ""
        seaicethermo_internal = ""
        seaicethermo_import = ""
        landice = ""
        lake = ""
        route = ""
        openwater = ""
        for rst in restarts_in:
            f = os.path.basename(rst)
            dest = InData_dir + "/" + f
            if os.path.exists(dest):
                shutil.remove(dest)
            print("\nCopy " + rst + " to " + dest)
            shutil.copy(rst, dest)
            if "saltwater_internal" in f:
                saltwater_internal = f
            if "saltwater_import" in f:
                saltwater_import = f
            if "seaicethermo_internal" in f:
                seaicethermo_internal = f
            if "seaicethermo_import" in f:
                seaicethermo_import = f
            if "landice" in f:
                landice = f
            if "lake" in f:
                lake = f
            if "roue" in f:
                route = f
            if "openwater" in f:
                openwater = f

        in_til = InData_dir + "/" + os.path.basename(in_tile_file)
        out_til = OutData_dir + "/" + os.path.basename(out_tile_file)

        if os.path.exists(in_til):
            shutil.remove(in_til)
        if os.path.exists(out_til):
            shutil.remove(out_til)
        print("\n Copy " + in_tile_file + " to " + in_til)
        shutil.copy(in_tile_file, in_til)
        print("\n Copy " + out_tile_file + " to " + out_til)
        shutil.copy(out_tile_file, out_til)

        exe = bindir + "/mk_LakeLandiceSaltRestarts.x "
        zoom = config["input"]["surface"]["zoom"]
        if zoom is None:
            zoom = get_zoom(config)

        log_name = out_dir + "/remap_lake_landice_saltwater_log"
        job_name = "remap_lake_landice_saltwater"

        # Build list of commands to execute
        commands = []

        if saltwater_internal:
            cmd = (
                bindir+"/esma_mpirun -np 1 "
                + exe
                + out_til
                + " "
                + in_til
                + " InData/"
                + saltwater_internal
                + " 0 "
                + str(zoom)
            )
            commands.append(cmd)

            # split Saltwater Internal
            # NOTE: split_saltwater==True means that the input restarts are already split.
            #       So we do not split them again.
            if not config["input"]["surface"]["split_saltwater"]:
                commands.append("echo 'Splitting Saltwater Internal...'")
                cmd = (
                    bindir
                    + "/SaltIntSplitter.x "
                    + out_til
                    + " "
                    + "OutData/"
                    + saltwater_internal
                )
                commands.append(cmd)

                # We can now *remove* the unsplit saltwater internal restart to avoid confusion
                commands.append("set unsplit_file = OutData/" + saltwater_internal)
                commands.append("if ( -e $unsplit_file ) then")
                commands.append(
                    "  echo 'Removing unsplit saltwater internal restart: '$unsplit_file"
                )
                commands.append("  /bin/rm -f $unsplit_file")
                commands.append("endif")

        if saltwater_import:
            cmd = (
                bindir +"/esma_mpirun -np 1 "
                + exe
                + out_til
                + " "
                + in_til
                + " InData/"
                + saltwater_import
                + " 0 "
                + str(zoom)
            )
            commands.append(cmd)

            # split Saltwater Import
            # NOTE: split_saltwater==True means that the input restarts are already split.
            #       So we do not split them again.
            if not config["input"]["surface"]["split_saltwater"]:
                commands.append("echo 'Splitting Saltwater Import...'")
                cmd = (
                    bindir
                    + "/SaltIntSplitter.x "
                    + out_til
                    + " "
                    + "OutData/"
                    + saltwater_import
                )
                commands.append(cmd)

        if openwater:
            cmd = (
                bindir+ "/esma_mpirun -np 1 "
                + exe
                + out_til
                + " "
                + in_til
                + " InData/"
                + openwater
                + " 0 "
                + str(zoom)
            )
            commands.append(cmd)

        if seaicethermo_internal:
            cmd = (
                bindir+ "/esma_mpirun -np 1 "
                + exe
                + out_til
                + " "
                + in_til
                + " InData/"
                + seaicethermo_internal
                + " 0 "
                + str(zoom)
            )
            commands.append(cmd)

        if seaicethermo_import:
            cmd = (
                bindir+ "/esma_mpirun -np 1 "
                + exe
                + out_til
                + " "
                + in_til
                + " InData/"
                + seaicethermo_import
                + " 0 "
                + str(zoom)
            )
            commands.append(cmd)

        if lake:
            cmd = (
                bindir + "/esma_mpirun -np 1 "
                + exe
                + out_til
                + " "
                + in_til
                + " InData/"
                + lake
                + " 19 "
                + str(zoom)
            )
            commands.append(cmd)

        if landice:
            cmd = (
                bindir + "/esma_mpirun -np 1 "
                + exe
                + out_til
                + " "
                + in_til
                + " InData/"
                + landice
                + " 20 "
                + str(zoom)
            )
            commands.append(cmd)

        if route:
            cmd = bindir + "/mk_RouteRestarts.x " + out_til + " " + yyyymmddhh_[0:6]
            commands.append(cmd)

        # Create job script with all commands
        commands_str = "\n".join(commands)

        remap_template = (
            job_directive[job]
            + """
source {Bin}/g5_modules
limit stacksize unlimited

cd {out_dir}

set mpi_type = "openmpi"
if ($?I_MPI_ROOT ) then
  set mpi_type = "intel"
endif

if ($mpi_type =~ "openmpi") then
setenv OMPI_MCA_shmem_mmap_enable_nfs_warning 0
setenv OMPI_MCA_mpi_preconnect_all 1
setenv OMPI_MCA_coll_tuned_bcast_algorithm 7
setenv OMPI_MCA_coll_tuned_scatter_algorithm 2
setenv OMPI_MCA_coll_tuned_reduce_scatter_algorithm 3
setenv OMPI_MCA_coll_tuned_allreduce_algorithm 3
setenv OMPI_MCA_coll_tuned_allgather_algorithm 4
setenv OMPI_MCA_coll_tuned_allgatherv_algorithm 3
setenv OMPI_MCA_coll_tuned_gather_algorithm 1
setenv OMPI_MCA_coll_tuned_barrier_algorithm 0
setenv OMPI_MCA_coll_tuned_use_dynamic_rules 1
setenv OMPI_MCA_sharedfp "^lockedfile,individual"
else
setenv I_MPI_FABRICS ofi
setenv I_MPI_OFI_PROVIDER psm3
setenv I_MPI_ADJUST_SCATTER 2
setenv I_MPI_ADJUST_SCATTERV 2
setenv I_MPI_ADJUST_GATHER 2
setenv I_MPI_ADJUST_GATHERV 3
setenv I_MPI_ADJUST_ALLGATHER 3
setenv I_MPI_ADJUST_ALLGATHERV 3
setenv I_MPI_ADJUST_ALLREDUCE 12
setenv I_MPI_ADJUST_REDUCE 10
setenv I_MPI_ADJUST_BCAST 11
setenv I_MPI_ADJUST_REDUCE_SCATTER 4
setenv I_MPI_ADJUST_BARRIER 9
env | grep 'I_MPI\\|FI_'
endif

# Execute remapping commands
{commands}

"""
        )
        script_name = out_dir + "/remap_lake_landice_saltwater.j"

        remap_script_content = remap_template.format(
            Bin=bindir,
            account=account,
            out_dir=out_dir,
            log_name=log_name,
            job_name=job_name,
            NPE=NPE,
            NNODE=NNODE,
            RESERVATION=RESERVATION,
            QOS=QOS,
            TIME=TIME,
            CONSTRAINT=CONSTRAINT,
            PARTITION=PARTITION,
            commands=commands_str,
        )

        with open(script_name, "w") as f:
            f.write(remap_script_content)

        # Determine if running in interactive mode or batch mode
        interactive = None
        if GEOS_SITE == "NAS":
            interactive = os.getenv("PBS_JOBID", default=None)
        else:
            interactive = os.getenv("SLURM_JOB_ID", default=None)

        if interactive:
            print("interactive mode\n")
            subprocess.call(["chmod", "755", script_name])
            print(script_name + "  1>" + log_name + "  2>&1")
            os.system(script_name + " 1>" + log_name + " 2>&1")
        elif GEOS_SITE == "NAS":
            print("qsub -W block=true " + script_name + "\n")
            subprocess.call(["qsub", "-W", "block=true", script_name])
        else:
            print("sbatch -W " + script_name + "\n")
            subprocess.call(["sbatch", "-W", script_name])

        suffix = "_rst." + suffix
        for out_rst in glob.glob("OutData/*_rst*"):
            filename = (
                expid
                + os.path.basename(out_rst).split("_rst")[0].split(".")[-1]
                + suffix
            )
            print("\n Move " + out_rst + " to " + out_dir + "/" + filename)
            shutil.move(out_rst, out_dir + "/" + filename)
        print("cd " + cwdir)
        os.chdir(cwdir)

        if self.config["input"]["shared"]["MERRA-2"]:
            self.remove_merra2()

    def find_rst(self):
        surf_restarts = [
            "route_internal_rst",
            "lake_internal_rst",
            "landice_internal_rst",
            "openwater_internal_rst",
            "saltwater_internal_rst",
            "saltwater_import_rst",
            "seaicethermo_internal_rst",
            "seaicethermo_import_rst",
        ]

        rst_dir = self.config["input"]["shared"]["rst_dir"]
        yyyymmddhh_ = str(self.config["input"]["shared"]["yyyymmddhh"])
        time = yyyymmddhh_[0:8] + "_" + yyyymmddhh_[8:10]
        restarts_in = []
        for f in surf_restarts:
            files = glob.glob(rst_dir + "/*" + f + "*" + time + "*")
            if len(files) > 0:
                restarts_in.append(files[0])
        if len(restarts_in) == 0:
            print("\n try restart file names without time stamp\n")
            for f in surf_restarts:
                fname = rst_dir + "/" + f
                if os.path.exists(fname):
                    restarts_in.append(fname)

        return restarts_in

    def copy_merra2(self):
        if not self.config["input"]["shared"]["MERRA-2"]:
            return

        expid = self.config["input"]["shared"]["expid"]
        yyyymmddhh_ = str(self.config["input"]["shared"]["yyyymmddhh"])
        yyyy_ = yyyymmddhh_[0:4]
        mm_ = yyyymmddhh_[4:6]
        dd_ = yyyymmddhh_[6:8]
        hh_ = yyyymmddhh_[8:10]

        suffix = yyyymmddhh_[0:8] + "_" + hh_ + "z.bin"
        merra_2_rst_dir = (
            "/archive/users/gmao_ops/MERRA2/gmao_ops/GEOSadas-5_12_4/"
            + expid
            + "/rs/Y"
            + yyyy_
            + "/M"
            + mm_
            + "/"
        )
        rst_dir = self.config["input"]["shared"]["rst_dir"] + "/"
        os.makedirs(rst_dir, exist_ok=True)
        print(
            " Copy MERRA-2 surface restarts \n from \n    "
            + merra_2_rst_dir
            + "\n to\n    "
            + rst_dir
            + "\n"
        )

        surfin = [
            merra_2_rst_dir + expid + ".lake_internal_rst." + suffix,
            merra_2_rst_dir + expid + ".landice_internal_rst." + suffix,
            merra_2_rst_dir + expid + ".saltwater_internal_rst." + suffix,
        ]
        bin2nc_yaml = [
            "bin2nc_merra2_lake.yaml",
            "bin2nc_merra2_landice.yaml",
            "bin2nc_merra2_salt.yaml",
        ]
        bin_path = os.path.dirname(os.path.realpath(__file__))
        for f, yf in zip(surfin, bin2nc_yaml):
            fname = os.path.basename(f)
            dest = rst_dir + "/" + fname
            print("Copy file " + f + " to " + rst_dir)
            shutil.copy(f, dest)
            ncdest = dest.replace("z.bin", "z.nc4")
            yaml_file = bin_path + "/" + yf
            print("Convert bin to nc4:" + dest + " to \n" + ncdest + "\n")
            bin2nc(dest, ncdest, yaml_file)
            os.remove(dest)


if __name__ == "__main__":
    lls = lake_landice_saltwater(params_file="remap_params.yaml")
    lls.remap()
    lls.remove_geosit()
