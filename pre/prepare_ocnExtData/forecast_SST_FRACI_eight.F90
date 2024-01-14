PROGRAM forecast_SST_FRACI_eight
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
  real               :: sst0(nlat, nlon), ice0(nlat, nlon)

  integer               :: extract_date
  integer               :: date_out, nlon_out, nlat_out

  character (len = 200) :: data_path
  character (len = 200) :: sst_file_pref, ice_file_pref
  character (len = 200) :: sst_file_suff, ice_file_suff

  character (len=8)     :: format_str = "(I8)"
  character (len=8)     :: date_str, today_str, tom_str
  character (len = 200) :: sst_file, ice_file

  integer :: i, iarg, argc, iargc
  character (len=255) :: argv
  integer :: numArgs
  integer :: year_s, month_s, day_s, tom
  integer :: tom_year, tom_mon, tom_day
  integer :: today_year, today_mon, today_day

  integer :: fcst_nDays

  character (len=255), parameter :: method = "persistence"
!----

  print *, " "
  print *, "-----------------------------------------------------------"
  print *, "        Generating SST and FRACI for forecasts             "
  print *, "-----------------------------------------------------------"
  print *, " "

  argc = iargc()
  if (argc < 3)  then
    print *, "Need minmum 3 inputs, see below examples. Try again!"
    print *, "gen_forecast_bcs.x -year 2010 -month 1 -day 1"
    print *, " "
    print *, "** 2 additional optional inputs are allowed ** "
    print *, "gen_forecast_bcs.x -year 2010 -month 1 -day 1 -fcst_nDays NN"
    print *, " "
    print *, "gen_forecast_bcs.x -year 2010 -month 1 -day 1 -input_data_path xx"
    print *, " "
    print *, "gen_forecast_bcs.x -year 2010 -month 1 -day 1 -fcst_nDays NN -input_data_path xx"
    print *, " "
    STOP
  end if

  ! Following 2 variables have defaults that can be overridden by user inputs.
  fcst_nDays = 15 ! default length of each forecast: 15 days.
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
      case("-fcst_nDays")
        iarg = iarg + 1
        call getarg ( iarg, argv )
        read(argv, '(I14)') fcst_nDays
      case ("-input_data_path")
        iarg = iarg + 1
        call getarg ( iarg, argv )
        read(argv, *) data_path
        data_path = trim(data_path)
      case default
    end select
  end do 
  print *, "Inputs: "
  print *, year_s, month_s, day_s, fcst_nDays, data_path
  print *, " "

  ! --- Read forecast start date data ---
  ! --
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

  ! read start date sst
  CALL read_bin_SST_ICE( sst_file, extract_date, date_out, nlon_out, nlat_out, lon, lat, sst0)
  ! read start date fraci
  CALL read_bin_SST_ICE( ice_file, extract_date, date_out, nlon_out, nlat_out, lon, lat, ice0)
  ! --

  print *, " "
  print *, "For:  ", date_out
  print *, "Read: ", sst_file, ice_file
  print *, " "

  ! day 1: [year_s,   month_s,   day_s   --> year_s+1, month_s+1, day_s+1]
  ! day 2: [year_s+1, month_s+1, day_s+1 --> year_s+2, month_s+2, day_s+2]
  ! ..
  print *, "Write out: ", trim(method), " BCs data..."
  print *, " "

  today_year=year_s; today_mon=month_s; today_day=day_s
  do i = 1, fcst_nDays
    
    tom = INCYMD( today_year*10000+today_mon*100+today_day, 1) ! tomorrow = today + (1 day)
    tom_year = int(tom/10000)
    tom_mon  = int((tom-tom_year*10000)/100)
    tom_day  = tom - (tom_year*10000+tom_mon*100)

    if (method == "persistence") then
     sst = sst0; ice = ice0
    end if

    write (today_str, format_str) today_year*10000+today_mon*100+today_day
    write (tom_str,   format_str) tom_year*10000  +tom_mon*100  +tom_day

    !print *, today_year,"/",today_mon,"/",today_day, ">>", tom_year,"/",tom_mon,"/",tom_day
    print *, trim(today_str), "---->", trim(tom_str)

    CALL write_bin( 'bcs_2880x1440', today_year, today_mon, today_day, tom_year, tom_mon, tom_day, today_str, &
    nlat, nlon, transpose(sst), transpose(ice))

    CALL write_netcdf( 'sst_ice', today_year, today_mon, today_day, today_str, &
    nlat, nlon, transpose(sst), transpose(ice))

    ! done with today; increment it to tomorrow
    today_year=tom_year; today_mon=tom_mon; today_day=tom_day
  end do

  print *, " "
  print *, "Done."
  print *, " "

!---------------------------------------------------------------------------
END PROGRAM forecast_SST_FRACI_eight
