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
    MERRA-2: false
    stretch: false
    # (coupled) ocean model: data, MOM5, MOM6
    omodel: data
    agrid:
    bc_base:
    bc_version: none
    expid:
    ogrid:
    rst_dir:
    yyyymmddhh:
  surface:
    zoom:
    wemin:
    # it supports three models: catch, catchcnclm40, catchcnclm45
    catch_model: null
    # if catch_tilefile is null, it searches bc_dir
    catch_tilefile: null
output:
  shared:
    label: false
    # SG001,SG002
    stretch: false
    # (coupled) ocean model: data, MOM5, MOM6
    omodel: data
    agrid:
    bc_base:
    bc_version: none
    expid:
    ogrid:
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
    # if catch_tilefile is null, it searches bc_dir
    catch_tilefile: null
    # the name of ease grid
    EASE_grid: null
  analysis:
    bkg: true
    aqua: true
    lcv: false
slurm_pbs:
  account:
  qos:
  partition: ''
