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

  integer :: i, iarg, argc, iargc
  character (len=255) :: argv
  integer :: numArgs
  integer :: year_s, month_s, day_s
  integer :: tom, tom_year, tom_mon, tom_day

  logical :: save_bin
!----

  argc = iargc()
  if (argc < 3)  then
    print *, "Need minmum 3 inputs, see below examples. Try again!"
    print *, "extract_daily_sst_ice.x -year 2010 -month 1 -day 1"
    print *, " "
    print *, "** 2 additional optional inputs are allowed ** "
    print *, "extract_daily_sst_ice.x -year 2010 -month 1 -day 1 -save_bin"
    print *, " "
    print *, "extract_daily_sst_ice.x -year 2010 -month 1 -day 1 -input_data_path xx"
    print *, " "
    print *, "extract_daily_sst_ice.x -year 2010 -month 1 -day 1 -save_bin -input_data_path xx"
    print *, " "
    STOP
  end if

  ! Following 2 variables have defaults that can be overridden by user inputs.
  save_bin = .false.
  ! GMAO OPS data path
  data_path= '/discover/nobackup/projects/gmao/share/dao_ops/fvInput/g5gcm/bcs/realtime/OSTIA_REYNOLDS/2880x1440/'

  !-- read user inputs
  iarg = 0
  do i = 1, 99
    iarg = iarg + 1
    if ( iarg > argc ) exit
    call getarg(iarg, argv)

    select case (argv)
      case ("-year")
        iarg = iarg + 1
        call getarg ( iarg, argv )
        read(argv, '(I14)') year_s
      case ("-month")
        iarg = iarg + 1
        call getarg ( iarg, argv )
        read(argv, '(I14)') month_s
      case ("-day")
        iarg = iarg + 1
        call getarg ( iarg, argv )
        read(argv, '(I14)') day_s
      case ("-save_bin")
        save_bin = .true.
      case ("-input_data_path")
        iarg = iarg + 1
        call getarg ( iarg, argv )
        read(argv, *) data_path
        data_path = trim(data_path)
      case default
    end select
  end do 
  print *, year_s, month_s, day_s, save_bin, data_path

  !-- form a string of input date
  extract_date = year_s*10000+month_s*100+day_s
  write (date_str, format_str) extract_date

  ! GMAO OPS has following fixed
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
    CALL write_bin( 'bcs_2880x1440', year_s, month_s, day_s, tom_year, tom_mon, tom_day, date_str,  nlat, nlon, transpose(sst), transpose(ice))
  end if
  
  ! netcdf
  CALL write_netcdf( 'sst_ice', year_s, month_s, day_s, date_str, nlat, nlon, transpose(sst), transpose(ice))

  print *, "Done."
  print *, " "

!---------------------------------------------------------------------------
END PROGRAM extract_day_SST_FRACI_eight
