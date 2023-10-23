PROGRAM extract_day_SST_FRACI_eight
!---------------------------------------------------------------------------
  USE sst_ice_helpers, only: read_bin_SST_ICE, &
!                            write_bin,        &
                             write_netcdf

  IMPLICIT NONE

  integer, parameter :: nlon = 2880
  integer, parameter :: nlat = 1440
  real               :: lon(nlon), lat(nlat)
  real               :: sst(nlat, nlon), ice(nlat, nlon)

  integer               :: extract_date
  integer               :: date_out, nlon_out, nlat_out

  character (len=8)     :: date_str, format_str = "(I8)"
  character (len = 200) :: sst_file, ice_file

  character (len=4) :: arg
  integer :: numArgs
  integer :: year_s, month_s, day_s
!----

  numArgs = iargc()!nargs() for ifort
  if (numArgs < 3)  then
    print *, "Need 3 inputs, in following format. Try again!"
    print *, "year month day"
    STOP
  end if

  !-- read user inputs
  call getarg(1, arg)
  read(arg, '(I14)') year_s ! default
  call getarg(2, arg)
  read(arg, '(I14)') month_s
  call getarg(3, arg)
  read(arg, '(I14)') day_s
  
  !-- form a string of input date
  extract_date = year_s*10000+month_s*100+day_s
  write (date_str, format_str) extract_date

  sst_file = 'dataoceanfile_OSTIA_REYNOLDS_SST.2880x1440.'//trim(date_str(1:4))//'.data'
  ice_file = 'dataoceanfile_OSTIA_REYNOLDS_ICE.2880x1440.'//trim(date_str(1:4))//'.data'

  print *, " "
  print *, "Read: ", sst_file, ice_file
  print *, " "

  ! read sst
  CALL read_bin_SST_ICE( sst_file, extract_date, date_out, nlon_out, nlat_out, lon, lat, sst)
  ! read sea ice
  CALL read_bin_SST_ICE( ice_file, extract_date, date_out, nlon_out, nlat_out, lon, lat, ice)

  print *, date_out
  print *, " "
  print *, "Write out the data..."

  ! binary write
  ! CALL write_bin( 2023, 1, 1, 2023, 1, 2, '20230101',  1440, 2880, transpose(sst), transpose(ice))

  ! netcdf
  CALL write_netcdf( year_s, month_s, day_s, date_str, nlat, nlon, transpose(sst), transpose(ice))

  print *, "Done."
  print *, " "

!---------------------------------------------------------------------------
END PROGRAM extract_day_SST_FRACI_eight
