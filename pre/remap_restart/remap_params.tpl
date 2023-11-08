#
# remap_restarts package:
#   this template file can be filled via the questionary (remap_questions.py) or manually
#
#

input:
  air:
    drymass: 1
    hydrostatic: 0
  shared:
    # bc_version info here is not critical. It is used in command_line options
    bc_version: none
    MERRA-2: false
    stretch: false
    agrid:
    bcs_dir:
    expid:
    ogrid:
    # (coupled) ocean model: data, MOM5, MOM6
    omodel: data
    rst_dir:
    yyyymmddhh:
  surface:
    zoom:
    wemin:
    # it supports three models: catch, catchcnclm40, catchcnclm45
    catch_model: null
    # if catch_tilefile is null, it searches bcs_dir
    catch_tilefile: null
output:
  shared:
    # bc_version info here is not critical. It is used in command_line options
    bc_version: none
    label: false
    # SG001,SG002
    stretch: false
    agrid:
    bcs_dir:
    expid:
    ogrid:
    # (coupled) ocean model: data, MOM5, MOM6
    omodel: data
    out_dir:
  air:
    # remap upper air or not
    remap: true
    nlevel:
  surface:
    split_saltwater: false
    surflay: 50.
    wemin:
    # remap lake, saltwater, landicet
    remap_water: true
    # remap catch(cn)
    remap_catch: true
    # if catch_tilefile is null, it searches bcs_dir
    catch_tilefile: null
  analysis:
    bkg: true
    aqua: False
    lcv: false
slurm:
  account:
  qos:
  partition:
