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
 
  INTEGER                 :: nymd_in
  INTEGER                 :: nymd_out, NLON, NLAT
  REAL                    :: LON(2880), LAT(1440)

  INTEGER                 :: year
  INTEGER                 :: clim_tom, clim_tom_year, clim_tom_mon, clim_tom_day
  CHARACTER (LEN = 200)   :: year_str, sst_file, ice_file
  CHARACTER (LEN = 8)     :: clim_date_str
  REAL                    :: mean_sst(1440, 2880), mean_ice(1440, 2880)
  REAL                    ::      sst(1440, 2880),      ice(1440, 2880)
  
! should be user inputs
  clim_year  = 1 ! Can't be "0" since GEOS/ESMF does not like that!
  year_start = 2007
  year_end   = 2023
  month      = 1
  day        = 2
  data_path= '/discover/nobackup/projects/gmao/share/dao_ops/fvInput/g5gcm/bcs/realtime/OSTIA_REYNOLDS/2880x1440/'
  sst_file_pref = 'dataoceanfile_OSTIA_REYNOLDS_SST.2880x1440.'
  ice_file_pref = 'dataoceanfile_OSTIA_REYNOLDS_ICE.2880x1440.'
  sst_file_suff = '.data'
  ice_file_suff = '.data'

  print *, " "
! mean over year_start: year_end
  do year = year_start, year_end
    write (year_str,'(I4.0)') year
    sst_file = trim(data_path)//"/"//trim(sst_file_pref)//trim(year_str)//trim(sst_file_suff)
    ice_file = trim(data_path)//"/"//trim(ice_file_pref)//trim(year_str)//trim(ice_file_suff)

    nymd_in = year*10000 + month*100 + day
    !print *, year, year_str,nymd_in
    !print *, sst_file, ice_file

    CALL read_bin_SST_ICE( sst_file, nymd_in, nymd_out, NLON, NLAT, LON, LAT, sst)
    CALL read_bin_SST_ICE( ice_file, nymd_in, nymd_out, NLON, NLAT, LON, LAT, ice)
    print *, "Read SST and FRACI for: ", nymd_out

    if (year == year_start) then
      mean_sst = sst
      mean_ice = ice
    else
      mean_sst = mean_sst + sst 
      mean_ice = mean_ice + ice
    endif
    !print *, " "
  end do
  print *, " "
  
  print *, "Number of years= ", year_end-year_start+1
  mean_sst = mean_sst/(year_end-year_start+1)
  mean_ice = mean_ice/(year_end-year_start+1)
! --

  print *, " "
  clim_tom = INCYMD( clim_year*10000+month*100+day, 1)
  clim_tom_year = int(clim_tom/10000)
  clim_tom_mon  = int((clim_tom-clim_tom_year*10000)/100)
  clim_tom_day = clim_tom - (clim_tom_year*10000+clim_tom_mon*100)
  !print *, "Tomorrow day:", clim_tom_year, clim_tom_mon, clim_tom_day
  write (clim_date_str,'(I0.8)') clim_year*10000+month*100+day
  !print *, clim_date_str
  print *, "Write out the data..."
  CALL write_bin(    clim_year, month, day, clim_tom_year, clim_tom_mon, clim_tom_day, clim_date_str, 1440, 2880, transpose(mean_sst), transpose(mean_ice))
  CALL write_netcdf( clim_year, month, day, clim_date_str, 1440, 2880, transpose(mean_sst), transpose(mean_ice))
  print *, "Done."
  print *, " "

!---------------------------------------------------------------------------
END PROGRAM daily_clim_SST_FRACI_eight
