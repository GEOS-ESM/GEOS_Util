add_subdirectory(NSIDC-OSTIA_SST-ICE_blend)
add_subdirectory(prepare_ocnExtData)

file(GLOB pythonscripts CONFIGURE_DEPENDS ./remap_restart/remap*  ./remap_restart/bin2nc_merra2* ./remap_restart/tests/*.*)

foreach (file ${pythonscripts})
  if ( NOT ${file} MATCHES "./remap_restart/remap_utils.py") 
    install(PROGRAMS ${file} DESTINATION bin)
  endif()
endforeach()

set(file ./remap_restart/remap_utils.py)
configure_file(${file} ${file} @ONLY)
install(PROGRAMS ${CMAKE_CURRENT_BINARY_DIR}/${file} DESTINATION bin)

install(
   PROGRAMS regrid.pl
   DESTINATION bin)
