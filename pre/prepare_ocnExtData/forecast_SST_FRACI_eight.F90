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
  real               :: sst_daily_clim(nlat, nlon), ice_daily_clim(nlat, nlon)
  real               :: anom_sst0(nlat, nlon), anom_ice0(nlat, nlon)

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
  character (len=255) :: method
  integer :: numArgs
  integer :: year_s, month_s, day_s, tom
  integer :: tom_year, tom_mon, tom_day
  integer :: today_year, today_mon, today_day

  integer :: fcst_nDays

  real, parameter :: T_f = 271.35d0 ! 273.15-1.8d0 sea water freezing temperature in K
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
    print *, "** 3 additional optional inputs are allowed ** "
    print *, "gen_forecast_bcs.x -year 2010 -month 1 -day 1 -fcst_nDays NN"
    print *, " "
    print *, "gen_forecast_bcs.x -year 2010 -month 1 -day 1 -input_data_path xx"
    print *, " "
    print *, "gen_forecast_bcs.x -year 2010 -month 1 -day 1 -fcst_nDays NN -input_data_path xx"
    print *, " "
    print *, "gen_forecast_bcs.x -year 2010 -month 1 -day 1 -fcst_nDays NN -input_data_path xx -method yy"
    print *, " "
    STOP
  end if

  ! Following variables have defaults that can be overridden by user inputs.
  fcst_nDays = 15 ! default length of each forecast: 15 days.
  ! GMAO OPS data path
  data_path= '/discover/nobackup/projects/gmao/share/dao_ops/fvInput/g5gcm/bcs/realtime/OSTIA_REYNOLDS/2880x1440/'
  method   = 'persistence'

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
      case ("-method")
        iarg = iarg + 1
        call getarg ( iarg, argv )
        read(argv, *) method
        method = trim(method)
      case default
    end select
  end do 
  print *, "Inputs: "
  print *, year_s, month_s, day_s, fcst_nDays, data_path, method
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

    write (today_str, format_str) today_year*10000+today_mon*100+today_day
    write (tom_str,   format_str) tom_year*10000  +tom_mon*100  +tom_day
    print *, trim(today_str), "---->", trim(tom_str)

    if (method == "persistence") then
      sst = sst0; ice = ice0
    else if (method == "persist_anomaly") then
      call get_daily_clim( today_str, nlat_out, nlon_out, sst_daily_clim, ice_daily_clim)
      if (i > 1) then
        sst = sst_daily_clim + anom_sst0
        ice = ice_daily_clim + anom_ice0

        ! -- check bounds of sst and ice --
        ! -- why? because above amounts to taking lagged differences in climatologies, which can lead to unphysical values.
        ! -- easier to start with ice, since we dont't know "good" bounds for sst.
        ! first ice
        where (ice < 0.d0)
          ice = 0.0d0
          ! second sst
          ! if sst < (273.15-1.8d0) ! 273.15-1.8d0 = T_f is sea water freezing temperature in K
          !   sst = what temperature? ! don't know where to melt! So leave it as is (for now).
          ! else
          !   ok
          ! endif
        end where

        where (ice > 1.d0)
          ice = 1.0d0
          ! second sst
          where ( sst > T_f) 
             sst = T_f
          endwhere
        end where
        !
        ! min and max sst for = ?? again, we dont't know "good" bounds!
        ! -- alternatively, one could apply thresholds on anomalies, but that needs careful work -- later, if and when possible.
        ! 
      else
        sst = sst0; ice = ice0 ! forecast day-1: just write out the same field(s).
       anom_sst0 = sst0 - sst_daily_clim
       anom_ice0 = ice0 - ice_daily_clim
      end if
    else
      print *, "Unknown method: ", method, "Exiting. Fix and try again."
      STOP
    end if

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
  CONTAINS
  SUBROUTINE get_daily_clim(today_str, nlat_out, nlon_out, sst_daily_clim, ice_daily_clim)

    integer :: date_out, nlon_out, nlat_out
    real    :: sst_daily_clim(nlat, nlon), ice_daily_clim(nlat, nlon)
    character (len = 200) :: clim_data_path, sst_clim_pref, ice_clim_pref
    character (len=8)     :: today_str

    clim_data_path = "/discover/nobackup/projects/gmao/advda/sakella/future_sst_fraci/data/binFiles/"
    sst_clim_pref  = "daily_clim_mean_sst_0001" !clim_year  = 1 ! from daily_clim_SST_FRACI_eight.F90
    ice_clim_pref  = "daily_clim_mean_ice_0001"

    sst_file = trim(clim_data_path)//"/"//trim(sst_clim_pref)//trim(today_str(5:8))//".bin"
    ice_file = trim(clim_data_path)//"/"//trim(ice_clim_pref)//trim(today_str(5:8))//".bin"
    print *, "Reading daily clim from: "
    print *, sst_file
    print *, ice_file

    CALL read_daily_clim(sst_file, sst_daily_clim, nlat, nlon) ! read sst anomaly
    CALL read_daily_clim(ice_file, ice_daily_clim, nlat, nlon) ! read fraci anomaly
    print *, nlat, nlon
  END SUBROUTINE get_daily_clim

  SUBROUTINE read_daily_clim(fName, bcs_field, nlat, nlon)
    integer, intent(in) :: nlat, nlon
    character (len=*), intent(in) :: fName
    real, intent(out) :: bcs_field(nlat, nlon)

    real    year1,month1,day1,hour1,min1,sec1, year2,month2,day2,hour2,min2,sec2
    real    dum1,dum2, field(nlon,nlat)
    integer rc

    open (10,file=fName,form='unformatted',access='sequential', STATUS = 'old') ! these files only 1 record (header+data)
    rc = 0
    do while (rc.eq.0)
      ! read header
      read (10,iostat=rc) year1,month1,day1,hour1,min1,sec1,&
                          year2,month2,day2,hour2,min2,sec2,dum1,dum2
      ! read data
      if( rc.eq.0 ) read (10,iostat=rc) field
      bcs_field = TRANSPOSE(field)
      close(10)
    end do
  END SUBROUTINE read_daily_clim
!---------------------------------------------------------------------------
END PROGRAM forecast_SST_FRACI_eight
