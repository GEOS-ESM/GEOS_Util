      subroutine TEM( TEM_VARS,im,jm,lm,TEM_NVARS,                          &
                      EXPID,lon,lat,lev,levunits,nymd,nhms,timinc,undef )
      implicit none
      character*6   date

      integer       id,nvars,precision,rc
      integer       im,jm,lm,TEM_NVARS
      integer       nymd,nhms,ntime,timinc
      integer       i,j,L,imz
      real          undef

      real     lat(jm)
      real     lon(im)
      real     lev(lm)

      real     TEM_VARS(im,jm,lm,TEM_NVARS)

      character*256  filename
      character*256  title
      character*256  EXPID
      character*256  output
      character*256  source
      character*256  contact
      character*256  levunits
      character*256, allocatable ::  vname(:)
      character*256, allocatable :: vtitle(:)
      character*256, allocatable :: vunits(:)

      real,    allocatable :: vrange(:,:)
      real,    allocatable :: prange(:,:)
      integer, allocatable ::  lmvar(:)

      real,    allocatable ::    pl3d(:,:,:)
      real,    allocatable ::    pk3d(:,:,:)
      real,    allocatable ::     u3d(:,:,:)
      real,    allocatable ::     v3d(:,:,:)
      real,    allocatable ::     t3d(:,:,:)
      real,    allocatable ::    th3d(:,:,:)
      real,    allocatable :: omega3d(:,:,:)
      real,    allocatable ::  upvp3d(:,:,:)
      real,    allocatable ::  upwp3d(:,:,:)
      real,    allocatable ::  vptp3d(:,:,:)
      real,    allocatable :: vpthp3d(:,:,:)

      real,   allocatable ::     uz(:,:)
      real,   allocatable ::     vz(:,:)
      real,   allocatable ::     tz(:,:)
      real,   allocatable ::     wz(:,:)
      real,   allocatable ::    omg(:,:)
      real,   allocatable ::    thz(:,:)
      real,   allocatable ::  upvpz(:,:)
      real,   allocatable ::  upwpz(:,:)
      real,   allocatable ::  vptpz(:,:)
      real,   allocatable :: vpthpz(:,:)
      real,   allocatable ::     pl(:,:)
      real,   allocatable ::     pk(:,:)
      real,   allocatable ::   strm(:,:)
      real,   allocatable ::    res(:,:)
      real,   allocatable ::  vstar(:,:)
      real,   allocatable ::  veddy(:,:)
      real,   allocatable ::  wstar(:,:)
      real,   allocatable ::  wmean(:,:)
      real,   allocatable ::  weddy(:,:)
      real,   allocatable ::   psi1(:,:)  ! Residual Mass StreamFunction (Method 1)
      real,   allocatable ::   psi2(:,:)  ! Residual Mass StreamFunction (Method 2)
      real,   allocatable ::   psim(:,:)  ! Mean     Mass StreamFunction
      real,   allocatable ::   epfy(:,:)  ! Eliassen-Palm Flux in Northward Direction
      real,   allocatable ::   epfz(:,:)  ! Eliassen-Palm Flux in    Upward Direction
      real,   allocatable :: epfdiv(:,:)  ! Eliassen-Palm Flux Divergence
      real,   allocatable ::   vstr(:,:)
      real,   allocatable ::  vstar2(:,:)
      real,   allocatable ::  wstar2(:,:)
      real,   allocatable ::  wmean2(:,:)
      real,   allocatable ::  weddy2(:,:)
      real*4, allocatable ::    dum(:)

      real,allocatable :: upvp  (:,:)
      real,allocatable :: upwp  (:,:)
      real,allocatable :: dudp  (:,:)
      real,allocatable :: dudphi(:,:)
      real,allocatable :: psie  (:,:)
      real,allocatable :: dfdphi(:,:)
      real,allocatable :: dfdp  (:,:)
      real,allocatable :: plz   (:,:)
      real,allocatable :: delp  (:,:)

      integer        n,nt

! Read data from grads.fwrite: Data is written BOT (L=1) to TOP (L=LM)
! --------------------------------------------------------------------
 
          ntime = 1

          print *
          print *, 'Creating TEM_Diag Data for EXPID: ',trim(EXPID)
          print *, '--------------------------------- '
          print *
          print *, 'IM: ',im
          print *, 'JM: ',jm
          print *, 'LM: ',lm
          print *
          print *, ' NYMD: ',nymd
          print *, ' NHMS: ',nhms
          print *

          allocate (    pl3d(im,jm,lm) )
          allocate (    pk3d(im,jm,lm) )

          allocate (     u3d(im,jm,lm) )
          allocate (     v3d(im,jm,lm) )
          allocate (     t3d(im,jm,lm) )
          allocate (    th3d(im,jm,lm) )
          allocate (  upvp3d(im,jm,lm) )
          allocate (  upwp3d(im,jm,lm) )
          allocate (  vptp3d(im,jm,lm) )
          allocate ( vpthp3d(im,jm,lm) )
          allocate ( omega3d(im,jm,lm) )

          ! Initialize Variables from BOT (L=1) to TOP (L=LM)
          ! -------------------------------------------------
          do L=1,lm
                 u3d(:,:,L) = TEM_VARS(:,:,L,1)
                 v3d(:,:,L) = TEM_VARS(:,:,L,2)
                 t3d(:,:,L) = TEM_VARS(:,:,L,3)
             omega3d(:,:,L) = TEM_VARS(:,:,L,4)
              upvp3d(:,:,L) = TEM_VARS(:,:,L,5)
              upwp3d(:,:,L) = TEM_VARS(:,:,L,6)
              vptp3d(:,:,L) = TEM_VARS(:,:,L,7)
          enddo

        ! Define Pressure Variables from BOT (L=1) to TOP (L=LM)
        ! ------------------------------------------------------
          do L=1,lm
          do j=1,jm
          do i=1,im
             pl3d(i,j,L) = lev(L)                 ! mb
             pk3d(i,j,L) = pl3d(i,j,L)**(2.0/7.0) ! mb**kappa
          enddo
          enddo
          enddo

          do L=1,lm
          !  print *, 'L: ',L,' LEV: ',pl3d(1,jm/2,L),' T: ',t3d(1,jm/2,L)
          do j=1,jm
          do i=1,im
             if( t3d(i,j,L).ne.undef ) then
                th3d(i,j,L) = t3d(i,j,L)/pk3d(i,j,L)       ! K/(mb**kappa)
             else
                th3d(i,j,L) = undef
             endif
             if( vptp3d(i,j,L).ne.undef ) then
                vpthp3d(i,j,L) = vptp3d(i,j,L)/pk3d(i,j,L) ! m/sec K / (mp**kappa)
             else
                vpthp3d(i,j,L) = undef
             endif
          enddo
          enddo
          enddo

      allocate(     uz(jm,lm)  )
      allocate(     vz(jm,lm)  )
      allocate(     tz(jm,lm)  )
      allocate(     wz(jm,lm)  )
      allocate(    omg(jm,lm)  )
      allocate(    thz(jm,lm)  )
      allocate(  upvpz(jm,lm)  )
      allocate(  upwpz(jm,lm)  )
      allocate(  vptpz(jm,lm)  )
      allocate( vpthpz(jm,lm)  )
      allocate(     pl(jm,lm)  )
      allocate(     pk(jm,lm)  )
      allocate(   strm(jm,lm)  )
      allocate(    res(jm,lm)  )
      allocate(  vstar(jm,lm)  )
      allocate(  veddy(jm,lm)  )
      allocate(  wstar(jm,lm)  )
      allocate(  wmean(jm,lm)  )
      allocate(  weddy(jm,lm)  )
      allocate(   psi1(jm,lm)  )
      allocate(   psi2(jm,lm)  )
      allocate(   psim(jm,lm)  )
      allocate(   epfy(jm,lm)  )
      allocate(   epfz(jm,lm)  )
      allocate( epfdiv(jm,lm)  )
      allocate(   vstr(jm,lm)  )
      allocate(    dum(jm)     )
      allocate(  vstar2(jm,lm) )
      allocate(  wstar2(jm,lm) )
      allocate(  wmean2(jm,lm) )
      allocate(  weddy2(jm,lm) )
                                                                                                                                
      allocate(  upvp  (jm,LM)  )
      allocate(  upwp  (jm,LM)  )
      allocate(  dudp  (jm,LM)  )
      allocate(  dudphi(jm,LM)  )
      allocate(  psie  (jm,LM)  )
      allocate(  dfdphi(jm,LM)  )
      allocate(  dfdp  (jm,LM)  )
      allocate(  plz   (jm,LM)  )
      allocate(  delp  (jm,LM)  )

      call zonal (    v3d,im,jm,lm,    vz,undef)
      call zonal (    t3d,im,jm,lm,    tz,undef)
      call zonal ( vptp3d,im,jm,lm, vptpz,undef)

      call zonal (   pl3d,im,jm,lm,    pl,undef)
      call zonal (   pk3d,im,jm,lm,    pk,undef)
      call zonal (    u3d,im,jm,lm,    uz,undef)
      call zonal ( upvp3d,im,jm,lm, upvpz,undef)
      call zonal ( upwp3d,im,jm,lm, upwpz,undef)
      call zonal (omega3d,im,jm,lm,   omg,undef)

      call zonal (   th3d,im,jm,lm,   thz,undef)
      call zonal (vpthp3d,im,jm,lm,vpthpz,undef)

! ------------------------------------------------------------------------------

      do L=1,lm
      do j=1,jm
         if( abs(tz(j,L)-undef).gt.0.1 ) then
                thz(j,L) = tz(j,L)/pk(j,L)          ! K/mb**kappa
         else
                thz(j,L) = undef
         endif
         if( abs(vptpz(j,L)-undef).gt.0.1 ) then
                 vpthpz(j,L) = vptpz(j,L)/pk(j,L)   ! m/sec K/mb**kappa
         else
                 vpthpz(j,L) = undef
         endif
      enddo
      enddo

! Compute Meridional Streamfunction
! ---------------------------------
      call stream ( vz,pl,jm,lm,strm,undef )
 
      call make_psi ( uz,vz,thz,omg,upvpz,upwpz,vpthpz,pl,jm,lm,psi1,psi2,psim,epfy,epfz,epfdiv, &
                      undef,upvp,upwp,dudp,dudphi,psie,dfdphi,dfdp,vstar2,veddy,wstar2,wmean2,weddy2,plz,delp)

! Compute Mean Vertical Velocity from Continuity
! ----------------------------------------------
      call make_w ( vz,pl,jm,lm,wz,undef )

! Compute Residual Circulation using wmean2 from model data rather than wz from continuity
! ----------------------------------------------------------------------------------------
      call residual ( vz,vpthpz,thz,wmean2,pl,jm,lm,res,vstar,wstar,wmean,weddy,undef )
 

! **********************************************************************
! ****               Write TEM_Diag Monthly Output File             ****
! **********************************************************************

      title    = 'Transformed Eulerian Mean (TEM) Diagnostics'
      source   = 'Goddard Modeling and Assimilation Office, NASA/GSFC'
      contact  = 'data@gmao.gsfc.nasa.gov'

      imz   = 1
      nvars = 26

      allocate (    vname(nvars) )
      allocate (   vtitle(nvars) )
      allocate (   vunits(nvars) )
      allocate (    lmvar(nvars) )
      allocate ( vrange(2,nvars) )
      allocate ( prange(2,nvars) )

      vrange(:,:) = undef
      prange(:,:) = undef
      lmvar (:)   = lm
      vunits(:)   = 'unknown'

      vname(01) = 'str'    ; vtitle(01) = 'Streamfunction'
      vname(02) = 'res'    ; vtitle(02) = 'Residual Circulation'
      vname(03) = 'vstar'  ; vtitle(03) = 'vstar'
      vname(04) = 'wstar'  ; vtitle(04) = 'wstar'
      vname(05) = 'wmean'  ; vtitle(05) = 'wmean'
      vname(06) = 'weddy'  ; vtitle(06) = 'weddy'
      vname(07) = 'psi1'   ; vtitle(07) = 'Res1 Streamfunction'
      vname(08) = 'psi2'   ; vtitle(08) = 'Res2 Streamfunction'
      vname(09) = 'psim'   ; vtitle(09) = 'Mass Streamfunction'
      vname(10) = 'epfy'   ; vtitle(10) = 'Eliassen-Palm flux y'
      vname(11) = 'epfz'   ; vtitle(11) = 'Eliassen-Palm flux z'
      vname(12) = 'epfdiv' ; vtitle(12) = 'Eliassen-Palm flux Divergence'
      vname(13) = 'upvp'   ; vtitle(13) = 'Uprime Vprime'
      vname(14) = 'upwp'   ; vtitle(14) = 'Uprime Omegaprime'
      vname(15) = 'dudp'   ; vtitle(15) = 'DuDp'
      vname(16) = 'dudphi' ; vtitle(16) = 'DuDphi'
      vname(17) = 'psie'   ; vtitle(17) = 'Eddy Streamfunction'
      vname(18) = 'dfdphi' ; vtitle(18) = 'DfDphi'
      vname(19) = 'dfdp'   ; vtitle(19) = 'DfDp'
      vname(20) = 'plz'    ; vtitle(20) = 'Pressure'
      vname(21) = 'delp'   ; vtitle(21) = 'Pressure Thickness'
      vname(22) = 'vstar2' ; vtitle(22) = 'Alternate vstar Calculation'
      vname(23) = 'veddy2' ; vtitle(23) = 'Alternate veddy Calculation'
      vname(24) = 'wstar2' ; vtitle(24) = 'Alternate wstar Calculation'
      vname(25) = 'wmean2' ; vtitle(25) = 'Alternate wmean Calculation'
      vname(26) = 'weddy2' ; vtitle(26) = 'Alternate weddy Calculation'

      precision = 1  ! 64-bit
      precision = 0  ! 32-bit

      write(date,1000) nymd/100
 1000 format(i6.6)

      filename = trim(EXPID) // '.TEM_Diag.monthly.' // date // '.nc4'

      call GFIO_Create ( trim(filename), trim(title), source, contact, undef, &
                         imz, jm, lm, lon(1), lat, lev, levunits,       &
                         nymd, nhms, timinc,                            &
                         nvars, vname, vtitle, vunits, lmvar,           &
                         vrange, prange, precision,                     &
                         id, rc )

      call Gfio_putVar ( id,trim(vname(01)),nymd,nhms,imz,jm,1,lm,strm   ,rc ) ;  print *, 'Writing variable: ',trim(vname(01))
      call Gfio_putVar ( id,trim(vname(02)),nymd,nhms,imz,jm,1,lm,res    ,rc ) ;  print *, 'Writing variable: ',trim(vname(02))
      call Gfio_putVar ( id,trim(vname(03)),nymd,nhms,imz,jm,1,lm,vstar  ,rc ) ;  print *, 'Writing variable: ',trim(vname(03))
      call Gfio_putVar ( id,trim(vname(04)),nymd,nhms,imz,jm,1,lm,wstar  ,rc ) ;  print *, 'Writing variable: ',trim(vname(04))
      call Gfio_putVar ( id,trim(vname(05)),nymd,nhms,imz,jm,1,lm,wmean  ,rc ) ;  print *, 'Writing variable: ',trim(vname(05))
      call Gfio_putVar ( id,trim(vname(06)),nymd,nhms,imz,jm,1,lm,weddy  ,rc ) ;  print *, 'Writing variable: ',trim(vname(06))
      call Gfio_putVar ( id,trim(vname(07)),nymd,nhms,imz,jm,1,lm,psi1   ,rc ) ;  print *, 'Writing variable: ',trim(vname(07))
      call Gfio_putVar ( id,trim(vname(08)),nymd,nhms,imz,jm,1,lm,psi2   ,rc ) ;  print *, 'Writing variable: ',trim(vname(08))
      call Gfio_putVar ( id,trim(vname(09)),nymd,nhms,imz,jm,1,lm,psim   ,rc ) ;  print *, 'Writing variable: ',trim(vname(09))
      call Gfio_putVar ( id,trim(vname(10)),nymd,nhms,imz,jm,1,lm,epfy   ,rc ) ;  print *, 'Writing variable: ',trim(vname(10))
      call Gfio_putVar ( id,trim(vname(11)),nymd,nhms,imz,jm,1,lm,epfz   ,rc ) ;  print *, 'Writing variable: ',trim(vname(11))
      call Gfio_putVar ( id,trim(vname(12)),nymd,nhms,imz,jm,1,lm,epfdiv ,rc ) ;  print *, 'Writing variable: ',trim(vname(12))
      call Gfio_putVar ( id,trim(vname(13)),nymd,nhms,imz,jm,1,lm,upvp   ,rc ) ;  print *, 'Writing variable: ',trim(vname(13))
      call Gfio_putVar ( id,trim(vname(14)),nymd,nhms,imz,jm,1,lm,upwp   ,rc ) ;  print *, 'Writing variable: ',trim(vname(14))
      call Gfio_putVar ( id,trim(vname(15)),nymd,nhms,imz,jm,1,lm,dudp   ,rc ) ;  print *, 'Writing variable: ',trim(vname(15))
      call Gfio_putVar ( id,trim(vname(16)),nymd,nhms,imz,jm,1,lm,dudphi ,rc ) ;  print *, 'Writing variable: ',trim(vname(16))
      call Gfio_putVar ( id,trim(vname(17)),nymd,nhms,imz,jm,1,lm,psie   ,rc ) ;  print *, 'Writing variable: ',trim(vname(17))
      call Gfio_putVar ( id,trim(vname(18)),nymd,nhms,imz,jm,1,lm,dfdphi ,rc ) ;  print *, 'Writing variable: ',trim(vname(18))
      call Gfio_putVar ( id,trim(vname(19)),nymd,nhms,imz,jm,1,lm,dfdp   ,rc ) ;  print *, 'Writing variable: ',trim(vname(19))
      call Gfio_putVar ( id,trim(vname(20)),nymd,nhms,imz,jm,1,lm,plz    ,rc ) ;  print *, 'Writing variable: ',trim(vname(20))
      call Gfio_putVar ( id,trim(vname(21)),nymd,nhms,imz,jm,1,lm,delp   ,rc ) ;  print *, 'Writing variable: ',trim(vname(21))
      call Gfio_putVar ( id,trim(vname(22)),nymd,nhms,imz,jm,1,lm,vstar2 ,rc ) ;  print *, 'Writing variable: ',trim(vname(22))
      call Gfio_putVar ( id,trim(vname(23)),nymd,nhms,imz,jm,1,lm,veddy  ,rc ) ;  print *, 'Writing variable: ',trim(vname(23))
      call Gfio_putVar ( id,trim(vname(24)),nymd,nhms,imz,jm,1,lm,wstar2 ,rc ) ;  print *, 'Writing variable: ',trim(vname(24))
      call Gfio_putVar ( id,trim(vname(25)),nymd,nhms,imz,jm,1,lm,wmean2 ,rc ) ;  print *, 'Writing variable: ',trim(vname(25))
      call Gfio_putVar ( id,trim(vname(26)),nymd,nhms,imz,jm,1,lm,weddy2 ,rc ) ;  print *, 'Writing variable: ',trim(vname(26))
      print *

      call gfio_close ( id,rc )

#if 0
! Write Grads Binary Data
! -----------------------
      call GLAWRT  (strm  ,jm,LM,20,undef)
      call GLAWRT  (res   ,jm,LM,20,undef)
      call GLAWRT  (vstar ,jm,LM,20,undef)
      call GLAWRT  (wstar ,jm,LM,20,undef)
      call GLAWRT  (wmean ,jm,LM,20,undef)
      call GLAWRT  (weddy ,jm,LM,20,undef)
      call GLAWRT  (psi1  ,jm,LM,20,undef)
      call GLAWRT  (psi2  ,jm,LM,20,undef)
      call GLAWRT  (psim  ,jm,LM,20,undef)
      call GLAWRT  (epfy  ,jm,LM,20,undef)
      call GLAWRT  (epfz  ,jm,LM,20,undef)
      call GLAWRT  (epfdiv,jm,LM,20,undef)

      call GLAWRT  (upvp  ,jm,LM,20,undef)
      call GLAWRT  (upwp  ,jm,LM,20,undef)
      call GLAWRT  (dudp  ,jm,LM,20,undef)
      call GLAWRT  (dudphi,jm,LM,20,undef)
      call GLAWRT  (psie  ,jm,LM,20,undef)
      call GLAWRT  (dfdphi,jm,LM,20,undef)
      call GLAWRT  (dfdp  ,jm,LM,20,undef)
      call GLAWRT  (plz   ,jm,LM,20,undef)
      call GLAWRT  (delp  ,jm,LM,20,undef)
      call GLAWRT  (vstar2,jm,LM,20,undef)
      call GLAWRT  (veddy ,jm,LM,20,undef)
      call GLAWRT  (wstar2,jm,LM,20,undef)
      call GLAWRT  (wmean2,jm,LM,20,undef)
      call GLAWRT  (weddy2,jm,LM,20,undef)

! Write Grads Control File
! ------------------------
      output = '^residual.' // 'test' // '.data'
      output = '^fort.20'

      write(30,101) trim(output),trim(title),undef,jm,lat(1),2.0*abs(lat(1))/(jm-1),lm,lev(1:lm)
      do L=1,lm
      print *, 'Pressure = ',lev(L)
      enddo
      print *
      write(30,103) '00Z01DEC2012',lm,lm,lm,lm,lm,lm,lm,lm,lm,lm,lm,lm,  &
                                     lm,lm,lm,lm,lm,lm,lm,lm,lm,lm,lm,lm,lm,lm
  101 format('dset  ',a,/,                           &
             'title ',a,/,                           &
             'options sequential big_endian',/,      &
             'undef ',e15.6,/,                       &
             'xdef  1 linear -180 1',/,              &
             'ydef ',i4,' linear ',f8.3,2x,f8.3,/,   &
             'zdef ',i3,' levels ',999(f8.3,1x))
  102 format(10x,f8.3)
  103 format('tdef ','1 linear ',a,' 1mo',/,                   &
             'vars 26',/,                                        &
             'str   ',i3,' 0 Streamfunction',/,                  &
             'res   ',i3,' 0 Residual Circulation',/,            &
             'vstar ',i3,' 0 Vstar',/,                           &
             'wstar ',i3,' 0 wstar',/,                           &
             'wmean  ',i3,' 0 wmean ',/,                         &
             'weddy  ',i3,' 0 weddy ',/,                         &
             'psi1   ',i3,' 0 Res1 streamfunction ',/,           &
             'psi2   ',i3,' 0 Res2 streamfunction ',/,           &
             'psim   ',i3,' 0 Mass streamfunction ',/,           &
             'epfy   ',i3,' 0 Eliassen-Palm flux y',/,           &
             'epfz   ',i3,' 0 Eliassen-Palm flux z',/,           &
             'epfdiv ',i3,' 0 Eliassen-Palm flux Divergence',/,  &
             'upvp   ',i3,' 0 Uprime Vprim',/,                   &
             'upwp   ',i3,' 0 Uprime Omegaprime',/,              &
             'dudp   ',i3,' 0 DuDp',/,                           &
             'dudphi ',i3,' 0 DuDphi',/,                         &
             'psie   ',i3,' 0 Eddy Streamfunction',/,            &
             'dfdphi ',i3,' 0 DfDphi',/,                         &
             'dfdp   ',i3,' 0 DfDp',/,                           &
             'plz    ',i3,' 0 Pressure',/,                       &
             'delp   ',i3,' 0 Pressure Thickness',/,             &
             'vstar2 ',i3,' 0 vstar2',/,                         &
             'veddy2 ',i3,' 0 veddy2 ',/,                        &
             'wstar2 ',i3,' 0 wstar2',/,                         &
             'wmean2 ',i3,' 0 wmean2',/,                         &
             'weddy2 ',i3,' 0 weddy2',/,                         &
             'endvars')
#endif

      return
      end

    ! ************************************************************************************************************

      subroutine zonal (q,im,jm,lm,qz,undef)
      implicit none
      integer im,jm,lm
      integer i,j,L,isum
      real q(im,jm,lm), qz(jm,lm)
      real undef
      real*8 qsum
      logical defined

      do L=1,lm
      do j=1,jm
         qsum = 0.0D0
         isum = 0
      do i=1,im
         if( defined(q(i,j,L),undef) ) then
             qsum = qsum + q(i,j,L)
             isum = isum + 1
         endif
      enddo
         if( isum.ne.0 ) then
             qz(j,L) = qsum/isum
         else
             qz(j,L) = undef
         endif
      enddo
      enddo

      return
      end

    ! ************************************************************************************************************

      SUBROUTINE  GLAWRT  (A, JM,LM, KTP, undef)
      real        A   (JM,LM)
      real*4      TEM (JM), undef
      logical defined
      DO  L=1,LM
          DO  J=1,JM
              if( defined(a(J,L),undef) ) then
                  if( abs(a(J,L)).gt.1.e-20 ) then
                      TEM (J) = A(J,L)
                  else
                      TEM (J) = 0.
                  endif
              else
                  TEM (J) = undef
              endif
          ENDDO
          WRITE(KTP)  TEM
      ENDDO
      RETURN
      END

      subroutine make_psi( u0,v0,th0,w0,upvp0,upwp0,vpthp0,p0,jm,lm,psi1,psi2,psim,epfy,epfz,epfdiv,undef, &
                           upvp,upwp,dudp,dudphi,psie,dfdphi,dfdp,vstar,veddy,wstar,wmean,weddy,p,delp)
      use MAPL_ConstantsMod
      implicit none
      integer j,k,L,jm,lm
      real undef,dphi,a,g,pi,phi,pk0,H
      logical defined
       
      real    th0(jm,lm),    th(jm,lm)
      real  upvp0(jm,lm),  upvp(jm,lm)
      real  upwp0(jm,lm),  upwp(jm,lm)
      real vpthp0(jm,lm), vpthp(jm,lm)
      real     u0(jm,lm),     u(jm,lm)
      real     v0(jm,lm),     v(jm,lm)
      real     p0(jm,lm),     p(jm,lm)
      real     w0(jm,lm),     w(jm,lm)

      real   psi1(jm,lm)
      real   psi2(jm,lm)
      real   psim(jm,lm)
      real   epfy(jm,lm)
      real   epfz(jm,lm)
      real epfdiv(jm,lm)

      real   dudp(jm,lm)
      real   dfdp(jm,lm)
      real  dthdp(jm,lm)
      real dudphi(jm,lm)
      real dfdphi(jm,lm)
      real   psie(jm,lm)
      real   delp(jm,lm)
      real  veddy(jm,lm)
      real  vstar(jm,lm)
      real  weddy(jm,lm)
      real  wstar(jm,lm)
      real  wmean(jm,lm)
      real  stuff(jm,lm)
      real   dume(jm,0:lm) ! dummy edge
      real    the(jm,0:lm) ! theta_edge
      real    ple(jm,0:lm) !     p_edge
      real     pm(jm,1:lm) ! mid-point of p_edges
      real     ue(jm,0:lm) !     u_edge
      real  epfze(jm,0:lm) !  epfz_edge
      real      f(jm)
      real    dum(jm)
      integer method
      real airmw,runiv,cpd,rgas,akap, sum

      PARAMETER ( AIRMW  = MAPL_AIRMW  )
      PARAMETER ( RUNIV  = MAPL_RUNIV  )
      PARAMETER ( CPD    = MAPL_CP     )
      PARAMETER ( RGAS   = RUNIV/AIRMW )
      PARAMETER ( AKAP   = MAPL_KAPPA  )

! Define Constants
! ----------------
        pi = 4.*atan(1.)
      dphi = pi/(jm-1)
        a  = MAPL_RADIUS
        g  = MAPL_GRAV
        H  = 7000.0

      Method = 0

! Invert level index (in order to be top=>bottom)
! -----------------------------------------------
      do L=1,lm
           u(:,L) =     u0(:,lm-L+1)  ! m/sec
           v(:,L) =     v0(:,lm-L+1)  ! m/sec
           w(:,L) =     w0(:,lm-L+1)  ! Pa/sec
           p(:,L) =     p0(:,lm-L+1)  ! mb
          th(:,L) =    th0(:,lm-L+1)  ! K/mb**kappa
        upvp(:,L) =  upvp0(:,lm-L+1)  ! m/sec m/sec
        upwp(:,L) =  upwp0(:,lm-L+1)  ! m/sec Pa/sec
       vpthp(:,L) = vpthp0(:,lm-L+1)  ! m/sec K/mb**kappa
      enddo

      pk0 = (1000.0)**(2.0/7.0)      ! mb**kappa

      where( abs(p    -undef).gt.0.1 ) ; p     =     p*100  ; endwhere
      where( abs(th   -undef).gt.0.1 ) ; th    =    th*pk0  ; endwhere
      where( abs(vpthp-undef).gt.0.1 ) ; vpthp = vpthp*pk0  ; endwhere

! Compute PLE Edge Values
! -----------------------
        ple(:,0) = max( 0.0, p(:,1) - 0.5*( p(:,2)-p(:,1) ) )
      do L=1,lm-1
      do j=1,jm
        ple(j,L) = (  p(j,L+1)+ p(j,L) )*0.5
      enddo
      enddo
      ple(:,lm) =  p(:,lm) + 0.5*( p(:,lm)-p(:,lm-1) )

      do L=1,lm
        delp(:,L) = ple(:,L)-ple(:,L-1)
      enddo

! Compute Mid-Point of PLE Edge Values
! ------------------------------------
      do L=1,lm
        pm(:,L) = ( ple(:,L)+ple(:,L-1) )*0.5
      enddo

! Compute Mass Streamfunction
! ---------------------------
        pi = 4.*atan(1.)
      dphi = pi/(jm-1)
        a  = MAPL_RADIUS
        g  = MAPL_GRAV

      do L=1,LM
         dum(:) = 0.0
         do k=1,L
            where( abs(v(:,k)-undef).gt.0.1 )
                     dum(:) = dum(:) + v(:,k)*delp(:,k)
            endwhere
         enddo
         do j=1,jm
            phi       = -pi/2 + (j-1)*dphi
            psim(j,L) = 2*pi*a*cos(phi)/g * dum(j)
         enddo
      enddo

      sum = 0.0
      do k=1,lm
      do j=1,jm
      sum = sum + abs( psim(j,k) )
      enddo
      enddo
      if( sum.eq.0.0 ) psim = undef

! Define Eddy Streamfunction:  psie = vpthp/dthdp
! -----------------------------------------------

      call map1_cubic( lm,p,th, lm+1,ple,the, jm, Method, undef)
      call compute_d_dp( the,delp,jm,lm,undef,stuff )
      call map1_cubic( lm,pm,stuff, lm,p,dthdp, jm, Method, undef)

      do L=1,lm
      do j=1,jm
         if( defined(dthdp(j,L),undef)  .and.  &
             defined(vpthp(j,L),undef) ) then
              dthdp(j,L) = min( -0.003*pk0/100, dthdp(j,L) )
               psie(j,L) = vpthp(j,L) / dthdp(j,L)
         else
               psie(j,L) = undef
         endif
      enddo
      enddo

! Compute Veddy = D/Dp[ psie ]
! ----------------------------

      call map1_cubic( lm,p,psie, lm+1,ple,dume, jm, Method, undef)
      call compute_d_dp( dume,delp,jm,lm,undef,stuff )
      call map1_cubic( lm,pm,stuff, lm,p,veddy, jm, Method, undef)

! Compute Vstar = v - veddy
! -------------------------
      do L=1,lm
      do j=1,jm
         if( defined( veddy(j,L),undef)  .and. &
             defined(     v(j,L),undef) ) then
             vstar(j,L) = v(j,L) - veddy(j,L)
         else
             vstar(j,L) = undef
         endif
      enddo
      enddo


! Compute weddy = -d(psie*cos)/(a*cos*dphi)
! -----------------------------------------

      do L=1,lm
      do j=1,jm
         if( defined( psie(j,L),undef ) ) then
             stuff(j,L) = psie(j,L)
      else
             stuff(j,L) = undef
      endif
      enddo
      enddo

      call compute_d_dphi( stuff,jm,lm,undef,weddy )


! Compute wstar = w - weddy
! -------------------------
      do L=1,lm
      do j=1,jm
         if( defined( weddy(j,L),undef)  .and. &
             defined(     w(j,L),undef) ) then
             wstar(j,L) = w(j,L) + weddy(j,L)
         else
             wstar(j,L) = undef
         endif
      enddo
      enddo

      do L=1,lm
      do j=1,jm
         if( defined( wstar(j,L),undef) ) then
             wstar(j,L) = -H*wstar(j,L)/p(j,L)
         endif
         if( defined( w(j,L),undef) ) then
             wmean(j,L) = -H*w(j,L)/p(j,L)
         else
             wmean(j,L) = undef
         endif
         if( defined( weddy(j,L),undef) ) then
             weddy(j,L) = -H*weddy(j,L)/p(j,L)
         endif
      enddo
      enddo


! Construct Residual Streamfunction from Vstar (Method 1)
! -------------------------------------------------------
      do L=1,LM
         dum(:) = 0.0
         do k=1,L
            where( abs(vstar(:,k)-undef).gt.0.1 )
                     dum(:) = dum(:) + vstar(:,k)*delp(:,k)
            endwhere
         enddo
         do j=1,jm
            phi       = -pi/2 + (j-1)*dphi
            psi1(j,L) = 2*pi*a*cos(phi)/g * dum(j)
         enddo
      enddo

      sum = 0.0
      do k=1,lm
      do j=1,jm
      sum = sum + abs( psi1(j,k) )
      enddo
      enddo
      if( sum.eq.0.0 ) psi1 = undef


! Compute Residual Streamfunction (Method 2)
! ------------------------------------------
      do L=1,lm
      do j=1,jm
             phi = -pi/2 + (j-1)*dphi
         if( defined(psie(j,L),undef) ) then
             psi2(j,L) = 2*pi*a*cos(phi)/g * psie(j,L)
         else
             psi2(j,L) = undef
         endif
      enddo
      enddo

      do L=1,lm
         where( abs(psim(:,L)-undef).gt.0.1 .and.  &
                abs(psi2(:,L)-undef).gt.0.1 )
                    psi2(:,L) = psim(:,L) - psi2(:,L)
         elsewhere
                    psi2(:,L) = undef
         endwhere
      enddo


! Compute Eliassen-Palm Flux
! --------------------------
      do j=1,jm
         phi  = -pi/2 + (j-1)*dphi
         f(j) = 2*MAPL_OMEGA*sin(phi)
      enddo

      !------------------------- Compute du/dp --------------------------------

      call map1_cubic( lm,p,u, lm+1,ple,ue, jm, Method, undef)
      call compute_d_dp( ue,delp,jm,lm,undef,stuff )
      call map1_cubic( lm,pm,stuff, lm,p,dudp, jm, Method, undef)

      !--------------------- Compute d(u*cos)/(a*cos*dphi) ---------------------

      call compute_d_dphi( u,jm,lm,undef,dudphi )

      !----------------------- Compute epfy & epfz ----------------------------

      do L=1,lm
      do j=1,jm
               phi = -pi/2 + (j-1)*dphi
          if( defined( dudp(j,L),undef)  .and. &
              defined( psie(j,L),undef)  .and. &
              defined( upvp(j,L),undef) ) then 
                       epfy(j,L) = a*cos(phi)*( dudp(j,L)*psie(j,L) - upvp(j,L) )
          else
                       epfy(j,L) = undef
          endif
          if( defined( dudphi(j,L),undef)  .and.& 
              defined(   psie(j,L),undef)  .and. &
              defined(   upwp(j,L),undef) ) then 
                         epfz(j,L) = a*cos(phi)*( (f(j)-dudphi(j,L))*psie(j,L) - upwp(j,L) )
          else
                         epfz(j,L) = undef
          endif
      enddo
      enddo

      !----------------------- Compute d(epfy*cos)/(a*cos*dphi) -----------------------

      call compute_d_dphi( epfy,jm,lm,undef,dfdphi )

      !------------------------- Compute d(epfz)/dp ---------------------------

      call map1_cubic( lm,p,epfz, lm+1,ple,epfze, jm, Method, undef)
      call compute_d_dp( epfze,delp,jm,lm,undef,stuff )
      call map1_cubic( lm,pm,stuff, lm,p,dfdp, jm, Method, undef)

      !----------------------- Compute EPFlux Divergence ----------------------

      do L=1,lm
      do j=1,jm
          if( defined(   dfdp(j,L),undef)  .and. &
              defined( dfdphi(j,L),undef) ) then 
                       epfdiv(j,L) = dfdphi(j,L) + dfdp(j,L)
          else
                       epfdiv(j,L) = undef
          endif
      enddo
      enddo

! Invert Streamfunction for grads output (in order to be bottom=>top)
! -------------------------------------------------------------------

      call flipz( psim  ,jm,lm,1.0e-10       ,undef,'psim' )
      call flipz( psi1  ,jm,lm,1.0e-10*2.4892,undef,'psi1' )
      call flipz( psi2  ,jm,lm,1.0e-10*2.4892,undef,'psi2' )
      call flipz( epfy  ,jm,lm,1.0           ,undef,'epfy' )
      call flipz( epfz  ,jm,lm,1.0           ,undef,'epfz' )
      call flipz( epfdiv,jm,lm,1.0           ,undef,'epfdiv' )

      call flipz( upvp  ,jm,lm,1.0           ,undef,'upvp' )
      call flipz( upwp  ,jm,lm,1.0           ,undef,'upwp' )
      call flipz( dudp  ,jm,lm,1.0           ,undef,'dudp' )
      call flipz( dudphi,jm,lm,1.0           ,undef,'dudphi' )
      call flipz( psie  ,jm,lm,1.0           ,undef,'psie' )
      call flipz( dfdphi,jm,lm,1.0           ,undef,'dfdphi' )
      call flipz( dfdp  ,jm,lm,1.0           ,undef,'dfdp' )
      call flipz( p     ,jm,lm,1.0           ,undef,'p' )
      call flipz( delp  ,jm,lm,1.0           ,undef,'delp' )

      call flipz( vstar ,jm,lm,1.0           ,undef,'vstar' )
      call flipz( veddy ,jm,lm,1.0           ,undef,'veddy' )
      call flipz( wstar ,jm,lm,1.0           ,undef,'wstar' )
      call flipz( wmean ,jm,lm,1.0           ,undef,'wmean' )
      call flipz( weddy ,jm,lm,1.0           ,undef,'weddy' )

      return
      end

      subroutine flipz( q,jm,lm,scale,undef,name )
      implicit none
      character(*) name
      integer j,L,jm,lm
      real undef,scale
      logical defined
      real q(jm,lm)
      real z(jm,lm)
      do L=1,lm
      do j=1,jm
         if( isnan(q(j,LM-L+1)) ) then
            print *, trim(name),'  LM-L+1: ',LM-L+1,' J: ',j,' q: ',q(j,LM-L+1)
         endif
         if( defined(q(j,LM-L+1),undef) ) then
                z(j,L) = q(j,LM-L+1)*scale
         else
                z(j,L) = undef
         endif
      enddo
      enddo
      do L=1,lm
         q(:,L) = z(:,L)
      enddo

      return
      end

      subroutine stream ( v0,p0,jm,lm,s,undef )
      use MAPL_ConstantsMod
      implicit none
      integer j,k,L,jm,lm
      real pi,dp,a,g,const,phi,undef
       
      real  v(jm,lm), v0(jm,lm)
      real  s(jm,lm)
      real p0(jm,lm),  p(jm,lm)
      real dum(jm), sum

      real  ple(jm,0:lm)
      real delp(jm,  lm)

! Invert VWND and P level index (in order to be top=>bottom)
! ----------------------------------------------------------
      do L=1,lm
      p(:,L) = p0(:,lm-L+1)
      v(:,L) = v0(:,lm-L+1)
      enddo

! Compute Edge Pressures and Thickness
! ------------------------------------
        ple(:,0) = max( 0.0, p(:,1) - 0.5*( p(:,2)-p(:,1) ) )
      do L=1,lm-1
        ple(:,L) = (  p(:,L)+ p(:,L+1) )*0.5
      enddo
        ple(:,lm) =  p(:,lm) + 0.5*( p(:,lm)-p(:,lm-1) )
      do L=1,lm
        delp(:,L) = ple(:,L)-ple(:,L-1)
      enddo

      pi = 4.*atan(1.)
      dp = pi/(jm-1)
      a  = MAPL_RADIUS
      g  = MAPL_GRAV

      const = 2*pi*a/g * 1.0e-8

      do k=1,lm
         dum(:) = 0.0
         do L=1,k
         do j=1,jm
         phi = -pi/2+(j-1)*dp
         if( abs(v(j,L)-undef).gt.0.1 ) then
               dum(j) = dum(j) + v(j,L)*cos(phi)*delp(j,L)
         endif
         enddo
         enddo
         s(:,k) = dum(:)*const
      enddo

      sum = 0.0
      do k=1,lm
      do j=1,jm
      sum = sum + abs( s(j,k) )
      enddo
      enddo
      if( sum.eq.0.0 ) s = undef

! Invert Streamfunction for grads output (in order to be bottom=>top)
! -------------------------------------------------------------------
      do k=1,lm
      do j=1,jm
      v(j,k) = s(j,lm-k+1)
      enddo
      enddo

      do k=1,lm
      do j=1,jm
      s(j,k) = v(j,k)
      enddo
      enddo

      return
      end
      subroutine residual ( v0,vpthp0,th0,w0,p0,jm,lm,res,vstar,wstar,wmean,weddy,undef )
      use MAPL_ConstantsMod
      implicit none
      integer j,k,L,jm,lm
      real pi,dp,a,g,H,ps,ts,rhos,z,phi,undef
      real airmw,runiv,cpd,rgas,akap, sum
       
      real     v0(jm,lm),   v(jm,lm)
      real     w0(jm,lm),   w(jm,lm)
      real vpthp0(jm,lm), th0(jm,lm)
      real vpthp (jm,lm), th (jm,lm), dthdp(jm,lm)
      real stuff (jm,lm)
      real  res  (jm,lm)
      real  vtlda(jm,lm)
      real  vstar(jm,lm)
      real  wstar(jm,lm), wmean(jm,lm), weddy(jm,lm)
      real    s  (jm,lm)
      real p0(jm,lm), p(jm,lm), rho0(jm,lm)
      real pm(jm,lm)
      real   cosp(jm), dum(jm,lm)
      real ddcosp(jm,lm)
      real    the(jm,0:lm)
      real    ple(jm,0:lm)
      real stuffe(jm,0:lm)
      real   delp(jm,  lm)
      integer method
      logical defined

      PARAMETER ( AIRMW  = MAPL_AIRMW  )
      PARAMETER ( RUNIV  = MAPL_RUNIV  )
      PARAMETER ( CPD    = MAPL_CP     )
      PARAMETER ( RGAS   = RUNIV/AIRMW )
      PARAMETER ( AKAP   = MAPL_KAPPA  )

! Invert v,th,vpthp, and P level index (in order to be top=>bottom)
! -----------------------------------------------------------------
      do L=1,lm
          w(:,L) =     w0(:,lm-L+1)
          v(:,L) =     v0(:,lm-L+1)
          p(:,L) =     p0(:,lm-L+1)
         th(:,L) =    th0(:,lm-L+1)
      vpthp(:,L) = vpthp0(:,lm-L+1)
      enddo

      pi = 4.*atan(1.)
      dp = pi/(jm-1)
      a  = MAPL_RADIUS
      g  = MAPL_GRAV
      H  = 7000.0
      ps = 1000.0
      ts =  240.0
      rhos = ps/(rgas*ts)

      Method = 0
!     print *, '  rhos = ',    rhos
!     print *, '1/rhos = ',1.0/rhos

! Compute Mean Air Density
! ------------------------
      do L=1,lm
      do j=1,jm
             z  = -H*log(p(j,L)/ps)
      rho0(j,L) = rhos*exp(-z/H)
      enddo
      enddo
      
      do j=1,jm
      phi = -pi/2 + (j-1)*dp
      cosp(j) = cos(phi)
      enddo

! Compute Edge Pressures and Thickness
! ------------------------------------
        the(:,0) = th(:,1)
        ple(:,0) = max( 0.0, p(:,1) - 0.5*( p(:,2)-p(:,1) ) )
      do L=1,lm-1
      do j=1,jm
        ple(j,L) = (  p(j,L)+ p(j,L+1) )*0.5
      enddo
      enddo
      ple(:,lm) =  p(:,lm) + 0.5*( p(:,lm)-p(:,lm-1) )

      do L=1,lm
        delp(:,L) = ple(:,L)-ple(:,L-1)
      enddo

! Compute Mid-Point of PLE Edge Values
! ------------------------------------
      do L=1,lm
        pm(:,L) = ( ple(:,L)+ple(:,L-1) )*0.5
      enddo


! Compute THE at PLE Edge Values
! ------------------------------
      call map1_cubic( lm,p,th, lm+1,ple,the, jm, Method, undef)


! Compute D(Theta)/DZ (with a forced minimum to prevent dthdz => 0)
! -----------------------------------------------------------------
      call compute_d_dp( the,delp,jm,lm,undef,stuff )
      call map1_cubic( lm,pm,stuff, lm,p,dthdp, jm, Method, undef)

      do L=1,lm
      do j=1,jm
         if( defined(the(j,L  ),undef )  .and. &
             defined(the(j,L-1),undef ) ) then
             dthdp(j,L) = min( -0.003, dthdp(j,L) )
         else
             dthdp(j,L) = undef
         endif
      enddo
      enddo

! Compute Vtlda based on D(rho*vpthp/dthdz)/DZ
! --------------------------------------------
      do L=1,lm
      do j=1,jm
      if( defined(dthdp(j,L),undef) .and. &
          defined(vpthp(j,L),undef) .and. &
          dthdp(j,L).ne.0.0       ) then
          stuff(j,L) = rho0(j,L)*vpthp(j,L)/(p(j,L)*dthdp(j,L))
      else
          stuff(j,L) = undef
      endif
      enddo
      enddo

      call map1_cubic( lm,p,stuff, lm+1,ple,stuffe, jm, Method, undef)
      call compute_d_dp( stuffe,delp,jm,lm,undef,stuff )
      call map1_cubic( lm,pm,stuff, lm,p,vtlda, jm, Method, undef)

      do L=1,lm
      do j=1,jm
      if( defined(vtlda(j,L),undef) ) then
                  vtlda(j,L) = p(j,L)/rho0(j,L) * vtlda(j,L)
      endif
      enddo
      enddo

! Compute Vstar
! -------------
      do L=1,lm
      do j=1,jm
      if( defined( vtlda(j,L),undef)  .and. &
          defined(     v(j,L),undef) ) then
          vstar(j,L) = v(j,L) - vtlda(j,L)
      else
          vstar(j,L) = undef
      endif
      enddo
      enddo

! Construct Residual Streamfunction from Vstar
! --------------------------------------------
      do k=1,lm
         dum(:,1) = 0.0
         do L=1,k
         do j=1,jm
         if( defined(vstar(j,L),undef) ) then
             dum(j,1) = dum(j,1) + vstar(j,L)*delp(j,L)*cosp(j)*rho0(j,L)*H/p(j,L)
         endif
         enddo
         enddo
         res(:,k) = dum(:,1)
      enddo

      sum = 0.0
      do k=1,lm
      do j=1,jm
      sum = sum + abs( res(j,k) )
      enddo
      enddo
      if( sum.eq.0.0 ) res = undef

! Invert Streamfunction and Vstar for grads output (in order to be bottom=>top)
! -----------------------------------------------------------------------------
      do L=1,lm
      do j=1,jm
      dum(j,L) = res(j,LM-L+1)
      enddo
      enddo
      do L=1,lm
      do j=1,jm
      res(j,L) = dum(j,L)
      enddo
      enddo

      do L=1,lm
      do j=1,jm
      dum(j,L) = vstar(j,LM-L+1)
      enddo
      enddo
      do L=1,lm
      do j=1,jm
      vstar(j,L) = dum(j,L)
      enddo
      enddo

! Compute D(cos*vpthp/dthdz)/(a*cos*Dphi)
! ---------------------------------------
      do L=1,lm
      do j=1,jm
      if( defined(vpthp(j,L),undef)  .and. &
          defined(dthdp(j,L),undef)  .and. &
                  dthdp(j,L).ne.0.0 ) then
                  stuff(j,L) = -H*vpthp(j,L)/(p(j,L)*dthdp(j,L))
      else
                  stuff(j,L) = undef
      endif
      enddo
      enddo

      call compute_d_dphi( stuff,jm,lm,undef,ddcosp )

! Compute Wstar
! -------------
      do L=1,lm
      do j=1,jm
      if( defined(ddcosp(j,L),undef) ) then
            wmean(j,Lm-L+1) = w(j,L)
            weddy(j,Lm-L+1) =          ddcosp(j,L)
            wstar(j,Lm-L+1) = w(j,L) + ddcosp(j,L)
      else
            wstar(j,Lm-L+1) = undef
            wmean(j,Lm-L+1) = undef
            weddy(j,Lm-L+1) = undef
      endif
      enddo
      enddo


      return
      end

      subroutine make_w ( v0,p0,jm,lm,w,undef )
      use MAPL_ConstantsMod
      implicit none
      integer j,k,L,jm,lm
       
      real     v0(jm,lm),    v(jm,lm)
      real     p0(jm,lm),    p(jm,lm)
      real      w(jm,lm), rho0(jm,lm)
      real      s(jm,lm), cosp(jm)
      real    dum(jm)
      real  dvcos_dphi(jm,lm)
      real         ple(jm,0:lm)
      real        delp(jm,  lm)
      logical defined
      real airmw,runiv,cpd,rgas,akap
      real pi,dp,a,g,H,ps,ts,rhos,phi,z,undef

      PARAMETER ( AIRMW  = MAPL_AIRMW  )
      PARAMETER ( RUNIV  = MAPL_RUNIV  )
      PARAMETER ( CPD    = MAPL_CP     )
      PARAMETER ( RGAS   = RUNIV/AIRMW )
      PARAMETER ( AKAP   = MAPL_KAPPA  )

! Invert v and P level index (in order to be top=>bottom)
! -------------------------------------------------------
      do L=1,lm
         v(:,L) = v0(:,lm-L+1)
         p(:,L) = p0(:,lm-L+1)
      enddo

      pi = 4.*atan(1.)
      dp = pi/(jm-1)
      a  = MAPL_RADIUS
      g  = MAPL_GRAV
      H  = 7000.0
      ps = 1000.0
      ts =  240.0
      rhos = ps/(rgas*ts)

      do L=1,lm
      do j=1,jm
      phi = -pi/2 + (j-1)*dp
      cosp(j)   =  cos(phi)
             z  = -H*log(p(j,L)/ps)
      rho0(j,L) = rhos*exp(-z/H)
      enddo
      enddo

      do L=1,lm
      do j=1,jm
      if( j.gt.1 .and. j.lt.jm ) then
          if( defined(v(j+1,L),undef)  .and. &
              defined(v(j-1,L),undef) ) then
              dvcos_dphi(j,L) = ( v(j+1,L)*cosp(j+1)-v(j-1,L)*cosp(j-1) )/(2*dp)
          else
              dvcos_dphi(j,L) = undef
          endif
      else
              dvcos_dphi(j,L) = undef
      endif
      enddo
      enddo

! Compute Edge Pressures and Thickness
! ------------------------------------
        ple(:,0) = max( 0.0, p(:,1) - 0.5*( p(:,2)-p(:,1) ) )
      do L=1,lm-1
        ple(:,L) = (  p(:,L)+ p(:,L+1) )*0.5
      enddo
        ple(:,lm) =  p(:,lm) + 0.5*( p(:,lm)-p(:,lm-1) )

      do L=1,lm
        delp(:,L) = ple(:,L)-ple(:,L-1)
      enddo

! Construct W from Continuity
! ---------------------------
      do k=1,lm
         dum(:) = 0.0
         do L=1,k
         do j=1,jm
         phi = -pi/2+(j-1)*dp
         if( dvcos_dphi(j,L).ne.undef ) then
             dum(j) = dum(j) + dvcos_dphi(j,L)*delp(j,L)*rho0(j,L)*H/(p(j,L)*a*cosp(j))
         endif
         enddo
         enddo
         s(:,k) = dum(:)/rho0(:,k)
      enddo

! Invert Streamfunction for grads output (in order to be bottom=>top)
! -------------------------------------------------------------------
      do k=1,lm
      do j=1,jm
      w(j,k) = s(j,lm-k+1)
      enddo
      enddo

      return
      end

    ! ************************************************************************************************************

    ! function defined ( q,undef )
    ! implicit none
    ! logical  defined
    ! real     q,undef
    ! defined = abs(q-undef).gt.0.1*undef
    ! return
    ! end function defined

    ! ************************************************************************************************************

      subroutine compute_edge( q,p,pe,jm,lm,undef,qe )
      implicit none
      integer j,L,jm,lm
      real undef
      logical defined
      real  q(jm,  lm),  p(jm,  lm)
      real qe(jm,0:lm), pe(jm,0:lm)

      qe(:,0) = q(:,1)
      do L=1,lm-1
      do j=1,jm
                                                                     qe(j,L) =   undef
        if( defined( q(j,L  ),undef)                              )  qe(j,L) =   q(j,L)
        if( defined( q(j,L+1),undef)                              )  qe(j,L) =   q(j,L+1)

      ! Linear Interpolation to Pressure Edge
      ! -------------------------------------
        if( defined( q(j,L+1),undef) .and. defined( q(j,L),undef) ) then
               qe(j,L) = q(j,L) + ( q(j,L+1)-q(j,L) ) * log(pe(j,L)/p(j,L)) / log(p(j,L+1)/p(j,L))
        endif

      enddo
      enddo
                  qe(:,lm) = undef
      where(  abs( q(:,lm)-undef).gt.0.1 .and. abs( qe(:,lm-1)-undef).gt.0.1 )
                  qe(:,lm) =  qe(:,lm-1) + (  q(:,lm)- qe(:,lm-1) ) * ( log(pe(:,lm)/pe(:,lm-1)) )/( log(p(:,lm)/pe(:,lm-1)) )
      endwhere

      return
      end

    ! ************************************************************************************************************

      subroutine compute_d_dp( qe,dp,jm,lm,undef,dqdp )
      implicit none
      integer j,L,jm,lm
      real undef
      logical defined
      real dp(jm,  lm)
      real qe(jm,0:lm)
      real dqdp(jm,lm)

      do L=1,lm
      do j=1,jm
         if( defined(qe(j,L-1),undef) .and. defined(qe(j,L),undef) ) then
             dqdp(j,L) = ( qe(j,L)-qe(j,L-1) )/ dp(j,L)
         else
             dqdp(j,L) = undef
         endif
      enddo
      enddo

      return
      end

    ! ************************************************************************************************************

      subroutine compute_d_dphi( q,jm,lm,undef,dqdphi )
      use MAPL_ConstantsMod
      implicit none
      integer j,L,jm,lm
      real      q(jm,lm)
      real dqdphi(jm,lm)

      real undef, dphi, phi, pi, a
      real stuff(jm,lm)
      logical defined

        pi = 4.*atan(1.)
      dphi = pi/(jm-1)
        a  = MAPL_RADIUS

      do L=1,lm
      do j=1,jm
                  phi = -pi/2 + (j-1)*dphi
          if( defined(q(j,L),undef) ) then
                  stuff(j,L) = q(j,L)*cos(phi)
          else
                  stuff(j,L) = undef
          endif
      enddo
      enddo

      do L=1,lm
         dqdphi(1 ,L) = undef
         dqdphi(jm,L) = undef
      do j=2,jm-1
         phi = -pi/2 + (j-1)*dphi
         if( defined(stuff(j+1,L),undef)  .and. &
             defined(stuff(j-1,L),undef) ) then 
             dqdphi(j,L) = ( stuff(j+1,L)-stuff(j-1,L) )/(a*cos(phi)*2*dphi)
         else
             dqdphi(j,L) = undef
         endif
      enddo
      enddo

      return
      end

    ! ************************************************************************************************************

      subroutine map1_cubic( km, pe1, q1, kn, pe2, q2, jm, Method, undef)
      use MAPL_ConstantsMod
      implicit none

      real,    intent(in) :: undef
      integer, intent(in) :: Method            ! 0: Linear in P
                                               ! 1: Linear in Log(P)
                                               ! 2: Linear in P**kappa
      integer, intent(in) :: jm                ! Latitude dimension
      integer, intent(in) :: km                ! Original vertical dimension
      integer, intent(in) :: kn                ! Target vertical dimension

      real, intent(in) ::  pe1(jm,km)          ! pressure at mid-layers
                                               ! in the original vertical coordinate

      real, intent(in) ::  pe2(jm,kn)          ! pressure at mid-layers
                                               ! in the new vertical coordinate

      real, intent(in)   ::  q1(jm,km)         ! Field input
      real, intent(inout)::  q2(jm,kn)         ! Field output

! !DESCRIPTION:
!
!     Perform Cubic Interpolation in the vertical
!     -------------------------------------------
!      pe1: pressure associated with q1
!      pe2: pressure associated with q2
!
!-----------------------------------------------------------------------
!
      real       qx(jm,km)
      real   logpl1(jm,km)
      real   logpl2(jm,kn)
      real   dlogp1(jm,km)
      real   am2,am1,ap0,ap1,P,PLP1,PLP0,PLM1,PLM2,DLP0,DLM1,DLM2

      integer j, k, LM2,LM1,LP0,LP1
      logical defined

      real airmw,runiv,cpd,rgas,akap
      PARAMETER ( AIRMW  = MAPL_AIRMW  )
      PARAMETER ( RUNIV  = MAPL_RUNIV  )
      PARAMETER ( CPD    = MAPL_CP     )
      PARAMETER ( RGAS   = RUNIV/AIRMW )
      PARAMETER ( AKAP   = MAPL_KAPPA  )

! Initialization
! --------------

      select case (Method)

    ! Linear in P
    ! -----------
      case(0)
        do k=1,km
            qx(:,k) =  q1(:,k)
        logpl1(:,k) = pe1(:,k)
        enddo
        do k=1,kn
        logpl2(:,k) = pe2(:,k)
        enddo

        do k=1,km-1
        dlogp1(:,k) = logpl1(:,k+1)-logpl1(:,k)
        enddo

    ! Linear in Log(P)
    ! ----------------
      case(1)
        do k=1,km
            qx(:,k) = q1(:,k)
        logpl1(:,k) = log( pe1(:,k) )
        enddo
        do k=1,kn
        logpl2(:,k) = log( pe2(:,k) )
        enddo

        do k=1,km-1
        dlogp1(:,k) = logpl1(:,k+1)-logpl1(:,k)
        enddo

    ! Linear in P**kappa
    ! ------------------
      case(2)
        do k=1,km
            qx(:,k) = q1(:,k)
        logpl1(:,k) = exp( akap*log( pe1(:,k) ))
        enddo
        do k=1,kn
        logpl2(:,k) = exp( akap*log( pe2(:,k) ))
        enddo

        do k=1,km-1
        dlogp1(:,k) = logpl1(:,k+1)-logpl1(:,k)
        enddo

      end select

! Interpolate Q1 onto target Pressures
! ------------------------------------
      do j=1,jm
      do k=1,kn
         LM1 = 1
         LP0 = 1
         do while( LP0.le.km )
            if (logpl1(j,LP0).lt.logpl2(j,k)) then
               LP0 = LP0+1
            else
               exit
            endif
         enddo
         LM1 = max(LP0-1,1)
         LP0 = min(LP0, km)

! Extrapolate Linearly above first model level
! --------------------------------------------
         if( LM1.eq.1 .and. LP0.eq.1 ) then
                                        q2(j,k) = qx(j,1)
           if( defined(qx(j,2),undef) ) q2(j,k) = qx(j,2)
           if( defined(qx(j,1),undef) .and. defined(qx(j,2),undef) ) then
               q2(j,k) = qx(j,1) + ( qx(j,2)-qx(j,1) )*( logpl2(j,k)-logpl1(j,1) ) &
                                                      /( logpl1(j,2)-logpl1(j,1) )
           endif

! Extrapolate Linearly below last model level
! -------------------------------------------
         else if( LM1.eq.km .and. LP0.eq.km ) then
                                           q2(j,k) = qx(j,km)
           if( defined(qx(j,km-1),undef) ) q2(j,k) = qx(j,km-1)
           if( defined(qx(j,km-1),undef) .and. defined(qx(j,km),undef) ) then
               q2(j,k) = qx(j,km) + ( qx(j,km)-qx(j,km-1) )*( logpl2(j,k )-logpl1(j,km  ) ) &
                                                           /( logpl1(j,km)-logpl1(j,km-1) )
           endif

! Interpolate Linearly between levels 1 => 2 and km-1 => km
! ---------------------------------------------------------
         else if( LM1.eq.1 .or. LP0.eq.km ) then
                                          q2(j,k) = qx(j,LP0)
           if( defined(qx(j,LM1),undef) ) q2(j,k) = qx(j,LM1)
           if( defined(qx(j,LP0),undef) .and. defined(qx(j,LM1),undef) ) then
             q2(j,k) = qx(j,LP0) + ( qx(j,LM1)-qx(j,LP0) )*( logpl2(j,k  )-logpl1(j,LP0) ) &
                                                          /( logpl1(j,LM1)-logpl1(j,LP0) )
           endif

! Interpolate Cubicly between other model levels
! ----------------------------------------------
         else
              LP1 = LP0+1
              LM2 = LM1-1
             P    = logpl2(j,k)
             PLP1 = logpl1(j,LP1)
             PLP0 = logpl1(j,LP0)
             PLM1 = logpl1(j,LM1)
             PLM2 = logpl1(j,LM2)
             DLP0 = dlogp1(j,LP0)
             DLM1 = dlogp1(j,LM1)
             DLM2 = dlogp1(j,LM2)

              ap1 = (P-PLP0)*(P-PLM1)*(P-PLM2)/( DLP0*(DLP0+DLM1)*(DLP0+DLM1+DLM2) )
              ap0 = (PLP1-P)*(P-PLM1)*(P-PLM2)/( DLP0*      DLM1 *(     DLM1+DLM2) )
              am1 = (PLP1-P)*(PLP0-P)*(P-PLM2)/( DLM1*      DLM2 *(DLP0+DLM1     ) )
              am2 = (PLP1-P)*(PLP0-P)*(PLM1-P)/( DLM2*(DLM1+DLM2)*(DLP0+DLM1+DLM2) )

           if( defined(qx(j,LP1),undef)  .and. &
               defined(qx(j,LP0),undef)  .and. &
               defined(qx(j,LM1),undef)  .and. &
               defined(qx(j,LM2),undef) ) then
             q2(j,k) = ap1*qx(j,LP1) + ap0*qx(j,LP0) + am1*qx(j,LM1) + am2*qx(j,LM2)

           else if( defined(qx(j,LP0),undef) .and. defined(qx(j,LM1),undef) ) then
             q2(j,k) = qx(j,LP0) + ( qx(j,LM1)-qx(j,LP0) )*( logpl2(j,k  )-logpl1(j,LP0) ) &
                                                          /( logpl1(j,LM1)-logpl1(j,LP0) )

           else
             q2(j,k) = undef
           endif

         endif

      enddo
      enddo

      return
      end subroutine map1_cubic
