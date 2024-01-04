PROGRAM extract_day_SST_FRACI_eight
!---------------------------------------------------------------------------
  USE m_tick, only: INCYMD
  USE sst_ice_helpers, only: read_bin_SST_ICE, &
                             write_bin,        &
                             write_netcdf

  IMPLICIT NONE

  integer, parameter :: nlon = 2880
  integer, parameter :: nlat = 1440
  real               :: lon(nlon), lat(nlat)
  real               :: sst(nlat, nlon), ice(nlat, nlon)

  integer               :: extract_date
  integer               :: date_out, nlon_out, nlat_out

  character (len = 200) :: data_path
  character (len = 200) :: sst_file_pref, ice_file_pref
  character (len = 200) :: sst_file_suff, ice_file_suff

  character (len=8)     :: date_str, format_str = "(I8)"
  character (len = 200) :: sst_file, ice_file

  character (len=4) :: arg
  integer :: numArgs
  integer :: year_s, month_s, day_s
  integer :: tom, tom_year, tom_mon, tom_day

  logical :: save_bin
!----

  numArgs = iargc()!nargs() for ifort
  if (numArgs < 4)  then
    print *, "Need minmum of 4 inputs, in following format (example). Try again!"
    print *, "year month day .false."
    STOP
  end if

  !-- read user inputs
  call getarg(1, arg)
  read(arg, '(I14)') year_s ! default
  call getarg(2, arg)
  read(arg, '(I14)') month_s
  call getarg(3, arg)
  read(arg, '(I14)') day_s
  call getarg(4, arg)
  read(arg, *) save_bin
  
  !-- form a string of input date
  extract_date = year_s*10000+month_s*100+day_s
  write (date_str, format_str) extract_date

  ! GMAO OPS has following fixed
  data_path= '/discover/nobackup/projects/gmao/share/dao_ops/fvInput/g5gcm/bcs/realtime/OSTIA_REYNOLDS/2880x1440/'
  sst_file_pref = 'dataoceanfile_OSTIA_REYNOLDS_SST.2880x1440.'
  ice_file_pref = 'dataoceanfile_OSTIA_REYNOLDS_ICE.2880x1440.'
  sst_file_suff = '.data'
  ice_file_suff = '.data'

  sst_file = trim(data_path)//"/"//trim(sst_file_pref)//trim(date_str(1:4))//trim(sst_file_suff)
  ice_file = trim(data_path)//"/"//trim(ice_file_pref)//trim(date_str(1:4))//trim(ice_file_suff)

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
  if (save_bin) then
    tom = INCYMD( year_s*10000+month_s*100+day_s, 1) ! next day

    tom_year = int(tom/10000)
    tom_mon  = int((tom-tom_year*10000)/100)
    tom_day  = tom - (tom_year*10000+tom_mon*100)
    !print *, "Tomorrow day:", tom_year, tom_mon, tom_day
    CALL write_bin( 'sst_ice', year_s, month_s, day_s, tom_year, tom_mon, tom_day, date_str,  nlat, nlon, transpose(sst), transpose(ice))
  end if
  
  ! netcdf
  CALL write_netcdf( 'sst_ice', year_s, month_s, day_s, date_str, nlat, nlon, transpose(sst), transpose(ice))

  print *, "Done."
  print *, " "

!---------------------------------------------------------------------------
END PROGRAM extract_day_SST_FRACI_eight
