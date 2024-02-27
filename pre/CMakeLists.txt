set (alldirs
  NSIDC-OSTIA_SST-ICE_blend
  prepare_ocnExtData
  )
esma_add_subdirectories (${alldirs})

file(GLOB pythonscripts CONFIGURE_DEPENDS ./remap_restart/remap*  ./remap_restart/bin2nc_merra2* ./remap_restart/tests/*.*)

list(FILTER pythonscripts EXCLUDE REGEX "remap_utils.py")

foreach (file ${pythonscripts})
  install(PROGRAMS ${file} DESTINATION bin)
endforeach()

set(file ./remap_restart/remap_utils.py)
configure_file(${file} ${file} @ONLY)
install(PROGRAMS ${CMAKE_CURRENT_BINARY_DIR}/${file} DESTINATION bin)

if (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/regrid.pl)
   install(
      PROGRAMS regrid.pl
      DESTINATION bin)
endif()
