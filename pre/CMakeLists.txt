add_subdirectory(NSIDC-OSTIA_SST-ICE_blend)
add_subdirectory(prepare_ocnExtData)

file(GLOB pythonscripts CONFIGURE_DEPENDS ./remap_restart/remap*  ./remap_restart/bin2nc_merra2* ./remap_restart/tests/*.*)
install(
   PROGRAMS ${pythonscripts}
   DESTINATION bin)

install(
   PROGRAMS regrid.pl
   DESTINATION bin)
