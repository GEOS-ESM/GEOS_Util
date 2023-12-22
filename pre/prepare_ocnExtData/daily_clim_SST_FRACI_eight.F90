PROGRAM daily_clim_SST_FRACI_eight
!---------------------------------------------------------------------------
  USE m_tick, only: INCYMD
  USE sst_ice_helpers, only: read_bin_SST_ICE, &
                             write_bin,        &
                             write_netcdf

  IMPLICIT NONE

  INTEGER                 :: month, day
  INTEGER                 :: clim_year, year_start, year_end
  CHARACTER (LEN = 200)   :: data_path
  CHARACTER (LEN = 200)   :: sst_file_pref, ice_file_pref
  CHARACTER (LEN = 200)   :: sst_file_suff, ice_file_suff
 
  INTEGER                 :: nymd_in, nYears
  INTEGER                 :: nymd_out, NLON, NLAT
  REAL                    :: LON(2880), LAT(1440)

  INTEGER                 :: year
  INTEGER                 :: clim_tom, clim_tom_year, clim_tom_mon, clim_tom_day
  CHARACTER (LEN = 200)   :: year_str, sst_file, ice_file
  CHARACTER (LEN = 8)     :: clim_date_str
  REAL                    :: mean_sst(1440, 2880), mean_ice(1440, 2880)
  REAL                    :: sdev_sst(1440, 2880), sdev_ice(1440, 2880)
  REAL                    ::      sst(1440, 2880),      ice(1440, 2880)
  REAL                    ::     dsst(1440, 2880),     dice(1440, 2880)

  LOGICAL                 :: verbose

  character (len=4) :: arg
  integer :: numArgs
  numArgs = iargc()

  verbose = .false.

! Inputs
  if (numArgs < 4)  then
    print *, "Need 4 inputs, in following format. Try again!"
    print *, "start_year end_year month day. Last 2 inputs are for the climatology of MM/DD."
    STOP
  else ! read user inputs
    call getarg(1, arg)
    read(arg, '(I4)') year_start !2007
    call getarg(2, arg)
    read(arg, '(I4)') year_end   !2023
    call getarg(3, arg)
    read(arg, '(I2)') month
    call getarg(4, arg)
    read(arg, '(I2)') day
  end if
  
! - Set inputs
  clim_year  = 1 ! Set, can't be "0" since GEOS/ESMF does not like that!
! GMAO OPS has following fixed
  data_path= '/discover/nobackup/projects/gmao/share/dao_ops/fvInput/g5gcm/bcs/realtime/OSTIA_REYNOLDS/2880x1440/'
  sst_file_pref = 'dataoceanfile_OSTIA_REYNOLDS_SST.2880x1440.'
  ice_file_pref = 'dataoceanfile_OSTIA_REYNOLDS_ICE.2880x1440.'
  sst_file_suff = '.data'
  ice_file_suff = '.data'

! Check input range
  if (year_start < 2007) then
    print *, "Invalid starting year: ", year_start, "Must be 2007 or later, try again."
    STOP
  endif
  if ( (month < 1) .or. (month > 12)) then
    print *, "Invalid month: ", month, "Try again."
    STOP
  endif
  if ( (day < 1) .or. (day > 31)) then
    print *, "Invalid day: ", day, "Try again."
    STOP
  endif
  if(verbose) print *, "User inputs: ", year_start, year_end, month, day
!--

  print *, " "
! mean and std dev over year_start: year_end
! 1. mean
  nYears = 0
  do year = year_start, year_end
    write (year_str,'(I4.0)') year
    sst_file = trim(data_path)//"/"//trim(sst_file_pref)//trim(year_str)//trim(sst_file_suff)
    ice_file = trim(data_path)//"/"//trim(ice_file_pref)//trim(year_str)//trim(ice_file_suff)

    nymd_in = year*10000 + month*100 + day
    if(verbose) then
      print *, year, year_str, nymd_in
      print *, sst_file, ice_file
      print *, nymd_in
    endif

    CALL read_bin_SST_ICE( sst_file, nymd_in, nymd_out, NLON, NLAT, LON, LAT, sst) ! Read GMAO OPS dataset
    CALL read_bin_SST_ICE( ice_file, nymd_in, nymd_out, NLON, NLAT, LON, LAT, ice)

    if ( (nymd_out-nymd_in) .eq. 0) then ! Found data for matching dates
      print *, "Read SST and FRACI for: ", nymd_out
      if (verbose) print *, "Found data in file, number of years =", nYears
      nYears = nYears + 1

      if (nYears == 1) then
        mean_sst = sst
        mean_ice = ice
      else
        mean_sst = mean_sst + sst 
        mean_ice = mean_ice + ice
      endif
    endif
  end do

  print *, " "
  print *, "Number of years= ", nYears

  mean_sst = mean_sst/REAL(nYears) ! nYears should be _promoted_ to real, being safe!
  mean_ice = mean_ice/REAL(nYears)

! 2. sdev
  nYears = 0
  do year = year_start, year_end

    write (year_str,'(I4.0)') year
    sst_file = trim(data_path)//"/"//trim(sst_file_pref)//trim(year_str)//trim(sst_file_suff)
    ice_file = trim(data_path)//"/"//trim(ice_file_pref)//trim(year_str)//trim(ice_file_suff)

    nymd_in = year*10000 + month*100 + day
    CALL read_bin_SST_ICE( sst_file, nymd_in, nymd_out, NLON, NLAT, LON, LAT, sst)
    CALL read_bin_SST_ICE( ice_file, nymd_in, nymd_out, NLON, NLAT, LON, LAT, ice)

    if ( (nymd_out-nymd_in) .eq. 0) then
      nYears = nYears + 1

      if (nYears == 1) then
        dsst = (sst - mean_sst)**2.
        dice = (ice - mean_ice)**2.
      else
        dsst = dsst + (sst - mean_sst)**2.
        dice = dice + (ice - mean_ice)**2.
      endif
    endif
  end do

  print *, "Number of years= ", nYears
! based on a sample not population
  sdev_sst = sqrt( dsst/REAL(nYears-1))
  sdev_ice = sqrt( dice/REAL(nYears-1))
! --

  print *, " "
  clim_tom = INCYMD( clim_year*10000+month*100+day, 1)
  clim_tom_year = int(clim_tom/10000)
  clim_tom_mon  = int((clim_tom-clim_tom_year*10000)/100)
  clim_tom_day = clim_tom - (clim_tom_year*10000+clim_tom_mon*100)
  if(verbose) print *, "Tomorrow day:", clim_tom_year, clim_tom_mon, clim_tom_day
  write (clim_date_str,'(I0.8)') clim_year*10000+month*100+day
  if(verbose) print *, clim_date_str

! Only write mean in binary format- good enough.
  print *, "Write output ..."
  CALL write_bin(    'daily_clim_mean', clim_year, month, day, clim_tom_year, clim_tom_mon, clim_tom_day, clim_date_str, 1440, 2880, transpose(mean_sst), transpose(mean_ice))

! mean
  CALL write_netcdf( 'daily_clim_mean_sst_fraci', clim_year, month, day, clim_date_str, 1440, 2880, transpose(mean_sst), transpose(mean_ice))
! std dev
  CALL write_netcdf( 'daily_clim_sdev_sst_fraci', clim_year, month, day, clim_date_str, 1440, 2880, transpose(sdev_sst), transpose(sdev_ice))
  print *, "Done."
  print *, " "

!---------------------------------------------------------------------------
END PROGRAM daily_clim_SST_FRACI_eight
