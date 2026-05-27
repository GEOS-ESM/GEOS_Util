file(GLOB pythonscripts CONFIGURE_DEPENDS remap* bin2nc_merra2* tests/*.*)

list(FILTER pythonscripts EXCLUDE REGEX "remap_utils.py")

foreach (file ${pythonscripts})
  install(PROGRAMS ${file} DESTINATION bin)
endforeach()

set(file remap_utils.py)
configure_file(${file} ${file} @ONLY)
install(PROGRAMS ${CMAKE_CURRENT_BINARY_DIR}/${file} DESTINATION bin)
