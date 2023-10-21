!
PROGRAM daily_clim_SST_FRACI_eight
!---------------------------------------------------------------------------
  USE sst_ice_helpers, only: read_bin_SST_ICE, &
                             write_bin,        &
                             write_netcdf

  IMPLICIT NONE

  CHARACTER (LEN = 200)   :: sst_file, ice_file
 
! CHARACTER(LEN = 4)      :: Year
! CHARACTER(LEN = 2)      :: Mon, Day

  INTEGER                 :: nymd_in
  INTEGER                 :: nymd_out, NLON, NLAT
  REAL                    :: LON(2880), LAT(1440)

  REAL                    :: sst(1440, 2880), ice(1440, 2880)
  
  sst_file = 'dataoceanfile_OSTIA_REYNOLDS_SST.2880x1440.2023.data'
  ice_file = 'dataoceanfile_OSTIA_REYNOLDS_ICE.2880x1440.2023.data'

  nymd_in  = 20230101

  CALL read_bin_SST_ICE( sst_file, nymd_in, nymd_out, NLON, NLAT, LON, LAT, sst)
  CALL read_bin_SST_ICE( ice_file, nymd_in, nymd_out, NLON, NLAT, LON, LAT, ice)

  print *, " "
  print *, "Read: ", sst_file
  print *, nymd_out
  print *, " "
  print *, "Write out the data..."

  CALL write_bin( 2023, 1, 1, 2023, 1, 2, '20230101',  1440, 2880, transpose(sst), transpose(ice))
  CALL write_netcdf( 2023, 1, 1, '20230101',  1440, 2880, transpose(sst), transpose(ice))

  print *, "Done."
  print *, " "

!---------------------------------------------------------------------------
END PROGRAM daily_clim_SST_FRACI_eight
!
