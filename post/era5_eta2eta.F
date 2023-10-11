      program  main
      use MAPL_ConstantsMod
      use m_set_eta, only: set_eta
      implicit none

c **********************************************************************
c **********************************************************************
c ****                                                              ****
c ****       Create ECMWF ANA.ETA File from ERA5 eta Level Data     ****
c ****                                                              ****
c **********************************************************************
c **********************************************************************

      integer  im,jm,lm,nq
      real     ptop,pint
      real     rgas,eps,rvap
      real     kappa
      real     grav

      integer     niter,i0,j0
      parameter ( niter = 5 )

! GEOS Restart Variables
! ----------------------
      real, allocatable ::   ak(:)
      real, allocatable ::   bk(:)
      real, allocatable ::  phis(:,:)

c Set analysis, fvdas, date and time
c ----------------------------------
      character*2  cnhms
      character*8  cnymd

      character*256 e5_file, tag, ext

      real    :: phibg, phifg, thbr1, thbr2, delth, cp

      integer    nymd,nhms
      integer    Lbeg,Lend

c variables on output ana.eta grid with lm levels
c -----------------------------------
      real, allocatable ::       ps(:,:)
      real, allocatable ::       dp(:,:,:)
      real, allocatable ::      ple(:,:,:)
      real, allocatable ::        u(:,:,:)
      real, allocatable ::        v(:,:,:)
      real, allocatable ::      thv(:,:,:)
      real, allocatable ::      pke(:,:,:)
      real, allocatable ::      pk (:,:,:)
      real, allocatable ::        q(:,:,:)
      real, allocatable ::   dp_ana(:,:,:)
      real, allocatable ::    p_ana(:,:,:)
      real, allocatable ::  ple_ana(:,:,:)
      real, allocatable :: logp_ana(:,:,:)
      real, allocatable ::     qdum(:,:,:)
      real, allocatable ::    u_ana(:,:,:)
      real, allocatable ::    v_ana(:,:,:)
      real, allocatable ::    q_ana(:,:,:)
      real, allocatable ::    t_ana(:,:,:)

c variables on ERA5 input grid with lm_e5 levels
c ------------------
      real, allocatable :: phis_e5(:,:)
      real, allocatable ::   ps_e5(:,:)
      real, allocatable ::    u_e5(:,:,:)
      real, allocatable ::    v_e5(:,:,:)
      real, allocatable ::    t_e5(:,:,:)
      real, allocatable ::    q_e5(:,:,:)
      real, allocatable ::    p_e5(:,:,:)
      real, allocatable ::  ple_e5(:,:,:)
      real, allocatable :: logp_e5(:,:,:)
      real, allocatable ::   ak_e5(:)
      real, allocatable ::   bk_e5(:)

      real,    allocatable ::    lat(:)
      real,    allocatable ::    lon(:)
      real,    allocatable ::    lev(:)
      real,    allocatable :: vrange(:,:)
      real,    allocatable :: prange(:,:)
      integer, allocatable :: yymmdd(:)
      integer, allocatable :: hhmmss(:)
      integer, allocatable ::  kmvar(:)

      character*256  title
      character*256  source
      character*256  contact
      character*256  levunits
      character*256, allocatable ::  vname(:)
      character*256, allocatable :: vtitle(:)
      character*256, allocatable :: vunits(:)

      integer timinc
      real    undef

      integer id,rc
      integer nvars, ngatts, ntime

      character*256, allocatable :: arg(:)

      integer precision
      integer i,j,k,L,n,nargs,iargc,ks

      real, allocatable :: dumu (:,:,:)
      real, allocatable :: dumv (:,:,:)
      real,     pointer ::  plevs(:)
      logical :: Lzflip

c Analysis Grads CTL File Variables
c ---------------------------------
      character*256  ctlfile
      integer im_e5,jm_e5,lm_e5

      character*256, pointer :: names (:)
      integer,       pointer :: lmvars(:)

C **********************************************************************
C ****           Initialize Filenames, Methods, etc.                ****
C **********************************************************************

         i0 = 0
         j0 = 0
         lm = 72
         im = -999
         jm = -999

      kappa = MAPL_KAPPA
      rgas  = MAPL_RGAS
      rvap  = MAPL_RVAP
      grav  = MAPL_GRAV
      cp    = MAPL_CP
      eps   = rvap/rgas-1.0

      precision = 0       ! 32-bit
        ctlfile = 'xxx'
           nymd = -999
           nhms = -999
            tag = ''

          nargs = iargc()
      if( nargs.eq.0 ) then
          call usage()
      else
          allocate ( arg(nargs) )
          do n=1,nargs
          call getarg(n,arg(n))
          enddo
          do n=1,nargs
             if( trim(arg(n)).eq.'-ecmwf' ) e5_file = trim(arg(n+1))
             if( trim(arg(n)).eq.'-tag'   )     tag = trim(arg(n+1))
             if( trim(arg(n)).eq.'-im'    ) read(arg(n+1), * ) im
             if( trim(arg(n)).eq.'-jm'    ) read(arg(n+1), * ) jm
             if( trim(arg(n)).eq.'-lm'    ) read(arg(n+1), * ) lm
             if( trim(arg(n)).eq.'-i0'    ) read(arg(n+1), * ) i0
             if( trim(arg(n)).eq.'-j0'    ) read(arg(n+1), * ) j0
          enddo
      endif

      if( trim(tag).ne.'' ) tag = trim(tag) // '.'
      ext = 'nc4'


C **********************************************************************
C ****                       Read ANA MetaData                      ****
C **********************************************************************

      call gfio_open ( trim(e5_file),1,id,rc )
      call gfio_diminquire ( id,im_e5,jm_e5,lm_e5,ntime,nvars,ngatts,rc )

      if( im.eq.-999 ) im = im_e5
      if( jm.eq.-999 ) jm = jm_e5

      allocate ( lon(im_e5) )
      allocate ( lat(jm_e5) )
      allocate ( lev(lm_e5) )
      allocate ( yymmdd(ntime) )
      allocate ( hhmmss(ntime) )
      allocate (  vname(nvars) )
      allocate ( vtitle(nvars) )
      allocate ( vunits(nvars) )
      allocate (  kmvar(nvars) )
      allocate ( vrange(2,nvars) )
      allocate ( prange(2,nvars) )

      call gfio_inquire ( id,im_e5,jm_e5,lm_e5,ntime,nvars,
     .                    title,source,contact,undef,
     .                    lon,lat,lev,levunits,
     .                    yymmdd,hhmmss,timinc,
     .                    vname,vtitle,vunits,kmvar,
     .                    vrange,prange,rc )

          print *
          print *, '            ANA File: ',trim(e5_file)
          print *, '                rslv: ',im_e5,jm_e5,lm_e5
          print *, '              lon(1): ',lon(1)
          print *
          print *, ' Number of Variables: ',nvars
          print *
          do n=1,nvars
          write(6,1001) n,trim(vname(n)),trim(vtitle(n)),kmvar(n)
          enddo
 1001     format(1x,i2,3x,a16,2x,a32,2x,i3)
          print *

      nymd = yymmdd(1)
      nhms = hhmmss(1)
      write( cnymd,200 ) nymd
      write( cnhms,300 ) nhms/10000
  200 format(i8.8)
  300 format(i2.2)
  400 format('dset ^',a)
  600 format(a1,i2.2)

C **********************************************************************
C ****                           Get Analysis                       ****
C **********************************************************************

      allocate (   ak_e5(      lm_e5+1) )
      allocate (   bk_e5(      lm_e5+1) )
      allocate (  ple_e5(im,jm,lm_e5+1) )
      allocate (    p_e5(im,jm,lm_e5) )
      allocate ( logp_e5(im,jm,lm_e5) )
      allocate (    u_e5(im,jm,lm_e5) )
      allocate (    v_e5(im,jm,lm_e5) )
      allocate (    t_e5(im,jm,lm_e5) )
      allocate (    q_e5(im,jm,lm_e5) )
      allocate (   ps_e5(im,jm) )
      allocate ( phis_e5(im,jm) )

      print *, 'Reading ERA5 Model Levels for Date: ',nymd,' Time: ',nhms
      print *
      ! Horizontal regrid if necessary
      call get_ana_data  ( id,ps_e5,u_e5,v_e5,t_e5,q_e5,phis_e5,
     .                     im,   jm,   lm_e5,nymd,nhms,
     .                     im_e5,jm_e5,lm_e5,undef)

c These are hard coded ECMWF 137-level aks and bks
c NOTE: They are different than GEOS 137 level
c ------------------------------------------------
      ak_e5 = [0.000001,      2.000365,      3.102241,      4.666084,      6.827977,      9.746966,
     .        13.605424,     18.608931,     24.985718,     32.985710,     42.879242,     54.955463,
     .        69.520576,     86.895882,    107.415741,    131.425507,    159.279404,    191.338562,
     .       227.968948,    269.539581,    316.420746,    368.982361,    427.592499,    492.616028,
     .       564.413452,    643.339905,    729.744141,    823.967834,    926.344910,   1037.201172,
     .      1156.853638,   1285.610352,   1423.770142,   1571.622925,   1729.448975,   1897.519287,
     .      2076.095947,   2265.431641,   2465.770508,   2677.348145,   2900.391357,   3135.119385,
     .      3381.743652,   3640.468262,   3911.490479,   4194.930664,   4490.817383,   4799.149414,
     .      5119.895020,   5452.990723,   5798.344727,   6156.074219,   6526.946777,   6911.870605,
     .      7311.869141,   7727.412109,   8159.354004,   8608.525391,   9076.400391,   9562.682617,
     .     10065.978516,  10584.631836,  11116.662109,  11660.067383,  12211.547852,  12766.873047,
     .     13324.668945,  13881.331055,  14432.139648,  14975.615234,  15508.256836,  16026.115234,
     .     16527.322266,  17008.789063,  17467.613281,  17901.621094,  18308.433594,  18685.718750,
     .     19031.289063,  19343.511719,  19620.042969,  19859.390625,  20059.931641,  20219.664063,
     .     20337.863281,  20412.308594,  20442.078125,  20425.718750,  20361.816406,  20249.511719,
     .     20087.085938,  19874.025391,  19608.572266,  19290.226563,  18917.460938,  18489.707031,
     .     18006.925781,  17471.839844,  16888.687500,  16262.046875,  15596.695313,  14898.453125,
     .     14173.324219,  13427.769531,  12668.257813,  11901.339844,  11133.304688,  10370.175781,
     .      9617.515625,   8880.453125,   8163.375000,   7470.343750,   6804.421875,   6168.531250,
     .      5564.382813,   4993.796875,   4457.375000,   3955.960938,   3489.234375,   3057.265625,
     .      2659.140625,   2294.242188,   1961.500000,   1659.476563,   1387.546875,   1143.250000,
     .       926.507813,    734.992188,    568.062500,    424.414063,    302.476563,    202.484375,
     .       122.101563,     62.781250,     22.835938,      3.757813,      0.000000,      0.000000]

      bk_e5 = [0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000000,      0.000000,      0.000000,      0.000000,      0.000000,
     .         0.000000,      0.000007,      0.000024,      0.000059,      0.000112,      0.000199,
     .         0.000340,      0.000562,      0.000890,      0.001353,      0.001992,      0.002857,
     .         0.003971,      0.005378,      0.007133,      0.009261,      0.011806,      0.014816,
     .         0.018318,      0.022355,      0.026964,      0.032176,      0.038026,      0.044548,
     .         0.051773,      0.059728,      0.068448,      0.077958,      0.088286,      0.099462,
     .         0.111505,      0.124448,      0.138313,      0.153125,      0.168910,      0.185689,
     .         0.203491,      0.222333,      0.242244,      0.263242,      0.285354,      0.308598,
     .         0.332939,      0.358254,      0.384363,      0.411125,      0.438391,      0.466003,
     .         0.493800,      0.521619,      0.549301,      0.576692,      0.603648,      0.630036,
     .         0.655736,      0.680643,      0.704669,      0.727739,      0.749797,      0.770798,
     .         0.790717,      0.809536,      0.827256,      0.843881,      0.859432,      0.873929,
     .         0.887408,      0.899900,      0.911448,      0.922096,      0.931881,      0.940860,
     .         0.949064,      0.956550,      0.963352,      0.969513,      0.975078,      0.980072,
     .         0.984542,      0.988500,      0.991984,      0.995003,      0.997630,      1.000000]

! Construct ERA5 (input grid) Pressure Variables
! ----------------------------

      do L=1,lm_e5+1
          ple_e5(:,:,L) = ak_e5(L) + ps_e5(:,:)*bk_e5(L)
      enddo
      do L=1,lm_e5
          p_e5(:,:,L) = 0.5*(ple_e5(:,:,L+1)+ple_e5(:,:,L))
          logp_e5(:,:,L) = log( p_e5(:,:,L) )
      enddo

! Construct GEOS (output grid) Pressure Variables
! ----------------------------
      allocate(   dp_ana(im,jm,lm)   )
      allocate(   p_ana(im,jm,lm)    )
      allocate(  ple_ana(im,jm,lm+1) )
      allocate( logp_ana(im,jm,lm)   )

      allocate( ak(lm+1) )
      allocate( bk(lm+1) )

      call set_eta ( lm,ks,ptop,pint,ak,bk )

      do L=1,lm+1
          ple_ana(:,:,L) = ak(L) + ps_e5(:,:)*bk(L)
      enddo
      do L=1,lm
          dp_ana(:,:,L)   =           ple_ana(:,:,L+1)-ple_ana(:,:,L)
          p_ana(:,:,L)    =      0.5*(ple_ana(:,:,L+1)+ple_ana(:,:,L))
          logp_ana(:,:,L) = log( 0.5*(ple_ana(:,:,L+1)+ple_ana(:,:,L)) )
      enddo

          if( i0.ne.0 .and. j0.ne.0 ) then
              print *, 'Sample ANA Data at GEOS-5 Location: (',i0,',',j0,')'
              print *, '   ANA_PS: ',ps_e5(i0,j0)/100,'  ANA_PHIS: ',phis_e5(i0,j0)
              print *, '   ANA_UNDEF: ',undef
              print *, '   ANA Temperature and Wind Profile:'
          else
              print *, 'Sample ANA Data:'
              print *, '   ANA_PS: ',ps_e5(1,jm/2)/100,'  ANA_PHIS: ',phis_e5(1,jm/2)
              print *, '   ANA_UNDEF: ',undef
              print *, '   ANA_Temperature and Wind Profile:'
          endif
          print *

C **********************************************************************
C ****           Interpolate quantities from lm_e5 to lm            ****
C **********************************************************************

          allocate    ( qdum(im,jm,lm) )

          if ( (im.ne.im_e5) .or. (jm.ne.jm_e5) .or. (lm.ne.lm_e5) ) then
          call interp ( qdum,u_e5,logp_ana,logp_e5,p_e5,p_ana,ple_ana,im,jm,lm,lm_e5,undef,'UWND',niter,i0,j0,1 )
          deallocate  ( u_e5 )
            allocate  ( u_ana(im,jm,lm) )
                        u_ana = qdum
          endif

          if ( (im.ne.im_e5) .or. (jm.ne.jm_e5) .or. (lm.ne.lm_e5) ) then
          call interp ( qdum,v_e5,logp_ana,logp_e5,p_e5,p_ana,ple_ana,im,jm,lm,lm_e5,undef,'VWND',niter,i0,j0,1 )
          deallocate  ( v_e5 )
            allocate  ( v_ana(im,jm,lm) )
                        v_ana = qdum
          endif

          if ( (im.ne.im_e5) .or. (jm.ne.jm_e5) .or. (lm.ne.lm_e5) ) then
          call interp ( qdum,t_e5,logp_ana,logp_e5,p_e5,p_ana,ple_ana,im,jm,lm,lm_e5,undef,'TMPU',niter,i0,j0,1 )
          deallocate  ( t_e5 )
            allocate  ( t_ana(im,jm,lm) )
                        t_ana = qdum
          endif

          if ( (im.ne.im_e5) .or. (jm.ne.jm_e5) .or. (lm.ne.lm_e5) ) then
          call interp ( qdum,q_e5,logp_ana,logp_e5,p_e5,p_ana,ple_ana,im,jm,lm,lm_e5,undef,'SPHU',niter,i0,j0,-1 )
          deallocate  ( q_e5 )
            allocate  ( q_ana(im,jm,lm) )
                        q_ana = qdum
          endif

C **********************************************************************
C ****                      Remap for Analysis                      ****
C **********************************************************************

      allocate( phis(im,jm)    )
      allocate(   ps(im,jm)    )
      allocate(   dp(im,jm,lm) )
      allocate(    u(im,jm,lm) )
      allocate(    v(im,jm,lm) )
      allocate(    q(im,jm,lm) )
      allocate(   pk(im,jm,lm) )
      allocate(  thv(im,jm,lm) )
      allocate(  ple(im,jm,lm+1) )
      allocate(  pke(im,jm,lm+1) )

        ps =   ps_e5
        dp =   dp_ana
      phis = phis_e5

!     if( i0.ne.0 .and. j0.ne.0 ) then
          print *
          print *, 'Before REMAP: '
          print *, 'GEOS5 PHIS/grav: ',phis(i0,j0)/grav,   ' ps: ',   ps(i0,j0)/100
          print *, 'ANA   PHIS/grav: ',phis_e5(i0,j0)/grav,' ps: ',ps_e5(i0,j0)/100
          print *, 'ANA          dp: ',dp_ana(i0,j0,5)
          print *, 'ANA           u: ', u_ana(i0,j0,5)
          print *
!     endif

      print *, 'Calling Remap'
      print *, '  im:', im, ' jm:', jm, ' lm:', lm

      call remap  ( ps,   dp,    u,    v,    thv,   q,    lm,
     .              ps_e5,dp_ana,u_ana,v_ana,t_ana, q_ana,lm,im,jm,1 )
      print *, '   Fini Remap'

      if( i0.ne.0 .and. j0.ne.0 ) then
          print *
          print *, 'AFter  REMAP: '
          print *, 'GEOS5 PHIS/grav: ',phis(i0,j0)/grav,' ps: ',ps(i0,j0)/100
          print *, 'ANA   PHIS/grav: ',phis_e5(i0,j0)/grav,' ps: ',ps_e5(i0,j0)/100
          print *
      endif

C **********************************************************************
C ****                 Write ECMWF ANA.ETA File                     ****
C **********************************************************************

      nq = 1
      call put_fveta ( ps,dp,u,v,thv,q,phis,
     .                 im,jm,lm,nq,nymd,nhms,tag,ext,lon(1),
     .                 timinc,precision )

      stop
      end

      subroutine interp ( q,qana,logp,logpl,pana,pl,ple,im,jm,lm,lmana,undef,name,niter,i0,j0,flag )
      implicit none
      integer im,jm,lm,lmana,niter,i0,j0,flag
      real undef
      real    q (im,jm,lm)
      real   pl (im,jm,lm)
      real  ple (im,jm,lm+1)
      real   er (im,jm,lm)
      real logp (im,jm,lm)
      real pana (im,jm,lmana)
      real qana (im,jm,lmana)
      real zana (im,jm,lmana)
      real erana(im,jm,lmana)
      real logpl(im,jm,lmana)
      character*4 name

      integer i,j,L,n

c Interpolate Analysis to GEOS Model Levels
c -----------------------------------------
          do L=1,lm
          call  sigtopl( q(:,:,L),qana(:,:,:),logpl(:,:,:),logp(:,:,L),im,jm,lmana,undef )
          enddo
          if( flag.eq.-1 ) then
              q = max( q,0.0 )
          endif

          if( i0.ne.0 .and. j0.ne.0 ) then
          print *
          print *, 'Initial ANA ',trim(name),' Profile at GEOS-5 Levels:'
          do L=1,lm
              print *, L,exp(logp(i0,j0,L))/100.,q(i0,j0,L)
          enddo
          print *
          else
          print *, 'Interpolating ',trim(name),' ...'
          endif

#ifdef DEBUG
          call writit (q,im,jm,lm,66)
#endif
          do n=1,niter
c            Interpolate GEOS Model Back to EC Levels and Compute Error
c            ----------------------------------------------------------
             do L=1,lmana
                call  sigtopl( zana(:,:,L),q(:,:,:),logp(:,:,:),logpl(:,:,L),im,jm,lm,undef )
                erana(:,:,L) = zana(:,:,L)-qana(:,:,L)
             enddo
             if( i0.ne.0 .and. j0.ne.0 ) then
             print *
             print *, 'ANA ',trim(name),' Profile Comparison, ITER: ',n
             print *, '----------------------------------------------'
             do L=1,lmana
                 print *, L,exp(logpl(i0,j0,L))/100.,zana(i0,j0,L),qana(i0,j0,L),erana(i0,j0,L)
             enddo
             print *
             endif

c            Interpolate and Add Error to GEOS Model Levels
c            ----------------------------------------------
             call interp3 ( erana,pana,im,jm,lmana, er,pl,lm,ple(:,:,lm+1) )
             q = q - er
             if( flag.eq.-1 ) then
                 q = max( q,0.0 )
             endif
#ifdef DEBUG
             call writit (q,im,jm,lm,66)
#endif
          enddo

          if( i0.ne.0 .and. j0.ne.0 ) then
          print *
          print *, 'Final ANA ',trim(name),' Profile at GEOS-5 Levels:'
          do L=1,lm
              print *, L,exp(logp(i0,j0,L))/100.,q(i0,j0,L)
          enddo
          print *
          endif

      return
      end

      subroutine get_ana_data  ( id,ps,u,v,t,q,phis,
     .                           im,jm,lm,nymd,nhms,
     .                           imana,jmana,lmana,undef )
      use MAPL_ConstantsMod
      implicit none
      integer  id,im,jm,lm,nymd,nhms,rc
      integer  imana,jmana,lmana

      real     ps(im,jm)
      real      u(im,jm,lm)
      real      v(im,jm,lm)
      real      t(im,jm,lm)
      real      q(im,jm,lm)
      real   phis(im,jm)
      real    slp(im,jm)

      real, allocatable :: dum2d(:,:)
      real, allocatable :: dum3d(:,:,:)
      real, allocatable :: dumu (:,:,:)
      real, allocatable :: dumv (:,:,:)

      real    undef,kappa,grav,dum,beta,cp,rgas
      integer L,i,j,LM1

      allocate ( dum2d(imana,jmana)       )
      allocate ( dum3d(imana,jmana,lmana) )
      allocate ( dumu (imana,jmana,lmana) )
      allocate ( dumv (imana,jmana,lmana) )

      kappa = MAPL_KAPPA
      rgas  = MAPL_RGAS
      grav  = MAPL_GRAV
      cp    = MAPL_CP
      beta  = 6.5e-3

c Read ANA Variables
c ------------------

      call gfio_getvar     ( id,'lnsp',nymd,nhms,imana,jmana,0,1 ,dum2d ,rc )  ! New ECMWF Format 2011/05/11 06z
      if( rc.ne.0 ) then
           print *, 'Could not find ECMWF Surface Pressure variable'
           call exit(7)
      endif
      dum2d = exp(dum2d)
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum2d,imana,jmana,ps,im,jm,1,undef )
      else
              ps = dum2d
      endif

      call gfio_getvar ( id,'z',nymd,nhms,imana,jmana,0,1 ,dum2d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find ECMWF Surf.Geop.Height variable'
          call exit(7)
      endif
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum2d,imana,jmana,phis,im,jm,1,undef )
      else
              phis = dum2d
      endif

c Winds
c -----
      call gfio_getvar ( id,'u',nymd,nhms,imana,jmana,1,lmana,dumu,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find ECMWF U-Wind variable'
          call exit(7)
      endif
      call gfio_getvar ( id,'v',nymd,nhms,imana,jmana,1,lmana,dumv,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find ECMWF V-Wind variable'
          call exit(7)
      endif

      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dumu,imana,jmana,u,im,jm,lm,undef )
      else
              u = dumu
      endif

      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dumv,imana,jmana,v,im,jm,lm,undef )
      else
              v = dumv
      endif

c Temperature
c -----------
      call gfio_getvar ( id,'t',nymd,nhms,imana,jmana,1,lmana,dum3d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find ECMWF Temperature variable'
          call exit(7)
      endif
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum3d,imana,jmana,t,im,jm,lm,undef )
      else
              t = dum3d
      endif

c Specific Humidity
c -----------------
      call gfio_getvar ( id,'q',nymd,nhms,imana,jmana,1,lmana,dum3d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find ECMWF Spec.Hum. variable'
          call exit(7)
      endif
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum3d,imana,jmana,q,im,jm,lm,undef )
      else
              q = dum3d
      endif
      q = max( q,0.0 )

      return
      end

      subroutine hflip ( q,im,jm,lm )
      implicit none
      integer  im,jm,lm,i,j,L
      real*4 q(im,jm,lm),dum(im)
      do L=1,lm
      do j=1,jm
      do i=1,im/2
         dum(i) = q(i+im/2,j,L)
         dum(i+im/2) = q(i,j,L)
      enddo
         q(:,j,L) = dum(:)
      enddo
      enddo
      return
      end

      subroutine zflip ( q,im,jm,lm )
      implicit none
      integer  im,jm,lm,L
      real*4 q(im,jm,lm),dum(im,jm,lm)
      dum = q
      do L=1,lm
      q(:,:,L) = dum(:,:,lm+1-L)
      enddo
      return
      end

      subroutine writit (q,im,jm,lm,ku)
      real   q (im,jm,lm)
      real*4 q2(im,jm)
      do L=lm,1,-1
      q2(:,:) = q(:,:,L)
      write(ku) q2
      enddo
      return
      end

      subroutine qsat (tt,p,q,dqdt,ldqdt)
C***********************************************************************
C
C  PURPOSE:
C  ========
C    Compute Saturation Specific Humidity
C
C  INPUT:
C  ======
C    TT ......... Temperature (Kelvin)
C    P .......... Pressure (mb)
C    LDQDT ...... Logical Flag to compute QSAT Derivative
C
C  OUTPUT:
C  =======
C    Q .......... Saturation Specific Humidity
C    DQDT ....... Saturation Specific Humidity Derivative wrt Temperature
C
C
C***********************************************************************
C*                  GODDARD LABORATORY FOR ATMOSPHERES                 *
C***********************************************************************

      IMPLICIT NONE
      REAL TT, P, Q, DQDT
      LOGICAL LDQDT
      REAL AIRMW, H2OMW

      PARAMETER ( AIRMW  = 28.97      )
      PARAMETER ( H2OMW  = 18.01      )

      REAL ESFAC, ERFAC
      PARAMETER ( ESFAC = H2OMW/AIRMW       )
      PARAMETER ( ERFAC = (1.0-ESFAC)/ESFAC )

      real aw0, aw1, aw2, aw3, aw4, aw5, aw6
      real bw0, bw1, bw2, bw3, bw4, bw5, bw6
      real ai0, ai1, ai2, ai3, ai4, ai5, ai6
      real bi0, bi1, bi2, bi3, bi4, bi5, bi6

      real d0, d1, d2, d3, d4, d5, d6
      real e0, e1, e2, e3, e4, e5, e6
      real f0, f1, f2, f3, f4, f5, f6
      real g0, g1, g2, g3, g4, g5, g6

c ********************************************************
c ***  Polynomial Coefficients WRT Water (Lowe, 1977) ****
c ***              (Valid +50 C to -50 C)             ****
c ********************************************************

      parameter ( aw0 =  6.107799961e+00 * esfac )
      parameter ( aw1 =  4.436518521e-01 * esfac )
      parameter ( aw2 =  1.428945805e-02 * esfac )
      parameter ( aw3 =  2.650648471e-04 * esfac )
      parameter ( aw4 =  3.031240396e-06 * esfac )
      parameter ( aw5 =  2.034080948e-08 * esfac )
      parameter ( aw6 =  6.136820929e-11 * esfac )

      parameter ( bw0 = +4.438099984e-01 * esfac )
      parameter ( bw1 = +2.857002636e-02 * esfac )
      parameter ( bw2 = +7.938054040e-04 * esfac )
      parameter ( bw3 = +1.215215065e-05 * esfac )
      parameter ( bw4 = +1.036561403e-07 * esfac )
      parameter ( bw5 = +3.532421810e-10 * esfac )
      parameter ( bw6 = -7.090244804e-13 * esfac )


c ********************************************************
c ***   Polynomial Coefficients WRT Ice  (Lowe, 1977) ****
c ***              (Valid  +0 C to -50 C)             ****
c ********************************************************

      parameter ( ai0 = +6.109177956e+00 * esfac )
      parameter ( ai1 = +5.034698970e-01 * esfac )
      parameter ( ai2 = +1.886013408e-02 * esfac )
      parameter ( ai3 = +4.176223716e-04 * esfac )
      parameter ( ai4 = +5.824720280e-06 * esfac )
      parameter ( ai5 = +4.838803174e-08 * esfac )
      parameter ( ai6 = +1.838826904e-10 * esfac )

      parameter ( bi0 = +5.030305237e-01 * esfac )
      parameter ( bi1 = +3.773255020e-02 * esfac )
      parameter ( bi2 = +1.267995369e-03 * esfac )
      parameter ( bi3 = +2.477563108e-05 * esfac )
      parameter ( bi4 = +3.005693132e-07 * esfac )
      parameter ( bi5 = +2.158542548e-09 * esfac )
      parameter ( bi6 = +7.131097725e-12 * esfac )


c ********************************************************
c ***         Polynomial Coefficients WRT Ice         ****
c ***   Starr and Cox (1985) (Valid -40 C to -70 C)   ****
c ********************************************************


      parameter ( d0 = 0.535098336e+01 * esfac )
      parameter ( d1 = 0.401390832e+00 * esfac )
      parameter ( d2 = 0.129690326e-01 * esfac )
      parameter ( d3 = 0.230325039e-03 * esfac )
      parameter ( d4 = 0.236279781e-05 * esfac )
      parameter ( d5 = 0.132243858e-07 * esfac )
      parameter ( d6 = 0.314296723e-10 * esfac )

      parameter ( e0 = 0.469290530e+00 * esfac )
      parameter ( e1 = 0.333092511e-01 * esfac )
      parameter ( e2 = 0.102164528e-02 * esfac )
      parameter ( e3 = 0.172979242e-04 * esfac )
      parameter ( e4 = 0.170017544e-06 * esfac )
      parameter ( e5 = 0.916466531e-09 * esfac )
      parameter ( e6 = 0.210844486e-11 * esfac )


c ********************************************************
c ***         Polynomial Coefficients WRT Ice         ****
c ***   Starr and Cox (1985) (Valid -65 C to -95 C)   ****
c ********************************************************

      parameter ( f0 = 0.298152339e+01 * esfac )
      parameter ( f1 = 0.191372282e+00 * esfac )
      parameter ( f2 = 0.517609116e-02 * esfac )
      parameter ( f3 = 0.754129933e-04 * esfac )
      parameter ( f4 = 0.623439266e-06 * esfac )
      parameter ( f5 = 0.276961083e-08 * esfac )
      parameter ( f6 = 0.516000335e-11 * esfac )

      parameter ( g0 = 0.312654072e+00 * esfac )
      parameter ( g1 = 0.195789002e-01 * esfac )
      parameter ( g2 = 0.517837908e-03 * esfac )
      parameter ( g3 = 0.739410547e-05 * esfac )
      parameter ( g4 = 0.600331350e-07 * esfac )
      parameter ( g5 = 0.262430726e-09 * esfac )
      parameter ( g6 = 0.481960676e-12 * esfac )

      REAL        TMAX, TICE
      PARAMETER ( TMAX=323.15, TICE=273.16)

      REAL T, D, W, QX, DQX
      T = MIN(TT,TMAX) - TICE
      DQX = 0.
      QX  = 0.

c Fitting for temperatures above 0 degrees centigrade
c ---------------------------------------------------
      if(t.gt.0.) then
       qx = aw0+T*(aw1+T*(aw2+T*(aw3+T*(aw4+T*(aw5+T*aw6)))))
      if (ldqdt)  then
      dqx = bw0+T*(bw1+T*(bw2+T*(bw3+T*(bw4+T*(bw5+T*bw6)))))
      endif
      endif

c Fitting for temperatures between 0 and -40
c ------------------------------------------
      if( t.le.0. .and. t.gt.-40.0 ) then
        w = (40.0 + t)/40.0
       qx =     w *(aw0+T*(aw1+T*(aw2+T*(aw3+T*(aw4+T*(aw5+T*aw6))))))
     .    + (1.-w)*(ai0+T*(ai1+T*(ai2+T*(ai3+T*(ai4+T*(ai5+T*ai6))))))
      if (ldqdt)  then
      dqx =     w *(bw0+T*(bw1+T*(bw2+T*(bw3+T*(bw4+T*(bw5+T*bw6))))))
     .    + (1.-w)*(bi0+T*(bi1+T*(bi2+T*(bi3+T*(bi4+T*(bi5+T*bi6))))))
      endif
      endif

c Fitting for temperatures between -40 and -70
c --------------------------------------------
      if( t.le.-40.0 .and. t.ge.-70.0 ) then
       qx = d0+T*(d1+T*(d2+T*(d3+T*(d4+T*(d5+T*d6)))))
      if (ldqdt) then
      dqx = e0+T*(e1+T*(e2+T*(e3+T*(e4+T*(e5+T*e6)))))
      endif
      endif

c Fitting for temperatures less than -70
c --------------------------------------
      if(t.lt.-70.0) then
       qx = f0+t*(f1+t*(f2+t*(f3+t*(f4+t*(f5+t*f6)))))
      if (ldqdt) then
      dqx = g0+t*(g1+t*(g2+t*(g3+t*(g4+t*(g5+t*g6)))))
      endif
      endif

c Compute Saturation Specific Humidity
c ------------------------------------
      D = (P-ERFAC*QX)
      IF(D.LT.0.) THEN
       Q = 1.0
       IF (LDQDT)  DQDT = 0.
      ELSE
       D = 1.0 / D
       Q = MIN(QX * D,1.0)
       IF (LDQDT)  DQDT = (1.0 + ERFAC*Q) * D * DQX
      ENDIF
      RETURN
      END

      function defined ( q,undef )
      implicit none
      logical  defined
      real     q,undef
      defined = abs(q-undef).gt.0.1*abs(undef)
      return
      end

      subroutine getchar (name,num)
      character*2  num2
      character*3  num3
      integer      num
      character*1  junk(256)
      character*1  name(256)
      data junk /256*' '/
      equivalence ( num2,junk )
      equivalence ( num3,junk )

      num2 = '  '
      num3 = '   '

      if( num.lt.100 ) then
          write(num2,102) num
      else if( num.lt.1000 ) then
          write(num3,103) num
      endif

      name = junk

  102 format(i2.2)
  103 format(i3.3)

      return
      end

      subroutine usage()
      print *, "Usage:  "
      print *
      print *, " era5_eta2eta.x  -ecmwf ecmwf.data "
      print *, "              [-im    im]"
      print *, "              [-jm    jm]"
      print *, "              [-tag   tag]"
      print *
      print *, "where:"
      print *
      print *, "  -ecmwf ecmwf.data: Filename of ECMWF Eta-Level analysis data"
      print *, "  -im            im:  Optional Zonal      Dimenstion for Output (Default: IM from File)"
      print *, "  -jm            jm:  Optional Meridional Dimenstion for Output (Default: JM from File)"
      print *, "  -tag          tag:  Optional Prefix tag            for Output (Default: era5_eta2eta)"
      print *
      call exit(7)
      end

      subroutine hinterp ( qin,iin,jin,qout,iout,jout,mlev,undef )
      implicit   none
      integer    iin,jin,       iout,jout, mlev
      real   qin(iin,jin,mlev), qout(iout,jout,mlev)
      real undef,pi,dlin,dpin,dlout,dpout
      real dlam(iin), lons(iout*jout), lon
      real dphi(jin), lats(iout*jout), lat
      integer i,j,loc

      pi = 4.0*atan(1.0)
      dlin = 2*pi/iin
      dpin = pi/(jin-1)
      dlam(:) = dlin
      dphi(:) = dpin

      dlout = 2*pi/ iout
      dpout =   pi/(jout-1)

      loc = 0
      do j=1,jout
      do i=1,iout
      loc = loc + 1
      lon = -pi + (i-1)*dlout
      lons(loc) = lon
      enddo
      enddo

      loc = 0
      do j=1,jout
      lat = -pi/2.0 + (j-1)*dpout
      do i=1,iout
      loc = loc + 1
      lats(loc) = lat
      enddo
      enddo

      call interp_h ( qin,iin,jin,mlev,dlam,dphi,
     .                qout,iout*jout,lons,lats,undef, -pi )

      return
      end

      subroutine interp_h ( q_cmp,im,jm,lm,dlam,dphi,
     .                       q_geo,irun,lon_geo,lat_geo, undef, lon_min )
C***********************************************************************
C
C  PURPOSE:
C  ========
C    Performs a horizontal interpolation from a field on a computational grid
C    to arbitrary locations.
C
C  INPUT:
C  ======
C    q_cmp ...... Field q_cmp(im,jm,lm) on the computational grid
C    im ......... Longitudinal dimension of q_cmp
C    jm ......... Latitudinal  dimension of q_cmp
C    lm ......... Vertical     dimension of q_cmp
C    dlam ....... Computational Grid Delta Lambda
C    dphi ....... Computational Grid Delta Phi
C    irun ....... Number of Output Locations
C    lon_geo .... Longitude Location of Output
C    lat_geo .... Latitude  Location of Output
C
C  OUTPUT:
C  =======
C    q_geo ...... Field q_geo(irun,lm) at arbitrary locations
C
C
C***********************************************************************
C*                  GODDARD LABORATORY FOR ATMOSPHERES                 *
C***********************************************************************

      implicit none

c Input Variables
c ---------------
      integer im,jm,lm,irun

      real      q_geo(irun,lm)
      real    lon_geo(irun)
      real    lat_geo(irun)

      real    q_cmp(im,jm,lm)
      real     dlam(im)
      real     dphi(jm)

      real :: lon_min

c Local Variables
c ---------------
      integer  i,j,l
      integer, allocatable    :: ip1(:), ip0(:), im1(:), im2(:)
      integer, allocatable    :: jp1(:), jp0(:), jm1(:), jm2(:)

c Bi-Linear Weights
c -----------------
      real, allocatable       ::    wl_ip0jp0 (:)
      real, allocatable       ::    wl_im1jp0 (:)
      real, allocatable       ::    wl_ip0jm1 (:)
      real, allocatable       ::    wl_im1jm1 (:)

c Bi-Cubic Weights
c ----------------
      real, allocatable       ::    wc_ip1jp1 (:)
      real, allocatable       ::    wc_ip0jp1 (:)
      real, allocatable       ::    wc_im1jp1 (:)
      real, allocatable       ::    wc_im2jp1 (:)
      real, allocatable       ::    wc_ip1jp0 (:)
      real, allocatable       ::    wc_ip0jp0 (:)
      real, allocatable       ::    wc_im1jp0 (:)
      real, allocatable       ::    wc_im2jp0 (:)
      real, allocatable       ::    wc_ip1jm1 (:)
      real, allocatable       ::    wc_ip0jm1 (:)
      real, allocatable       ::    wc_im1jm1 (:)
      real, allocatable       ::    wc_im2jm1 (:)
      real, allocatable       ::    wc_ip1jm2 (:)
      real, allocatable       ::    wc_ip0jm2 (:)
      real, allocatable       ::    wc_im1jm2 (:)
      real, allocatable       ::    wc_im2jm2 (:)

      real    ap1, ap0, am1, am2
      real    bp1, bp0, bm1, bm2

      real    lon_cmp(im)
      real    lat_cmp(jm)
      real    q_tmp(irun)

      real    pi,d
      real    lam,lam_ip1,lam_ip0,lam_im1,lam_im2
      real    phi,phi_jp1,phi_jp0,phi_jm1,phi_jm2
      real    dl,dp
      real    lam_cmp
      real    phi_cmp
      real    undef
      integer im1_cmp,icmp
      integer jm1_cmp,jcmp

c Initialization
c --------------
      pi = 4.*atan(1.)
      dl = 2*pi/ im     ! Uniform Grid Delta Lambda
      dp =   pi/(jm-1)  ! Uniform Grid Delta Phi

c Allocate Memory for Weights and Index Locations
c -----------------------------------------------
      allocate ( wl_ip0jp0(irun) , wl_im1jp0(irun) )
      allocate ( wl_ip0jm1(irun) , wl_im1jm1(irun) )
      allocate ( wc_ip1jp1(irun) , wc_ip0jp1(irun) , wc_im1jp1(irun) , wc_im2jp1(irun) )
      allocate ( wc_ip1jp0(irun) , wc_ip0jp0(irun) , wc_im1jp0(irun) , wc_im2jp0(irun) )
      allocate ( wc_ip1jm1(irun) , wc_ip0jm1(irun) , wc_im1jm1(irun) , wc_im2jm1(irun) )
      allocate ( wc_ip1jm2(irun) , wc_ip0jm2(irun) , wc_im1jm2(irun) , wc_im2jm2(irun) )
      allocate (       ip1(irun) ,       ip0(irun) ,       im1(irun) ,       im2(irun) )
      allocate (       jp1(irun) ,       jp0(irun) ,       jm1(irun) ,       jm2(irun) )

c Compute Input Computational-Grid Latitude and Longitude Locations
c -----------------------------------------------------------------
      lon_cmp(1) = lon_min   ! user supplied orign
      do i=2,im
      lon_cmp(i) = lon_cmp(i-1) + dlam(i-1)
      enddo
      lat_cmp(1) = -pi*0.5
      do j=2,jm-1
      lat_cmp(j) = lat_cmp(j-1) + dphi(j-1)
      enddo
      lat_cmp(jm) =  pi*0.5

c Compute Weights for Computational to Geophysical Grid Interpolation
c -------------------------------------------------------------------
      do i=1,irun
      lam_cmp = lon_geo(i)
      phi_cmp = lat_geo(i)

c Determine Indexing Based on Computational Grid
c ----------------------------------------------
      im1_cmp = 1
      do icmp = 2,im
      if( lon_cmp(icmp).lt.lam_cmp ) im1_cmp = icmp
      enddo
      jm1_cmp = 1
      do jcmp = 2,jm
      if( lat_cmp(jcmp).lt.phi_cmp ) jm1_cmp = jcmp
      enddo

      im1(i) = im1_cmp
      ip0(i) = im1(i) + 1
      ip1(i) = ip0(i) + 1
      im2(i) = im1(i) - 1

      jm1(i) = jm1_cmp
      jp0(i) = jm1(i) + 1
      jp1(i) = jp0(i) + 1
      jm2(i) = jm1(i) - 1

c Fix Longitude Index Boundaries
c ------------------------------
      if(im1(i).eq.im) then
      ip0(i) = 1
      ip1(i) = 2
      endif
      if(im1(i).eq.1) then
      im2(i) = im
      endif
      if(ip0(i).eq.im) then
      ip1(i) = 1
      endif


c Compute Immediate Surrounding Coordinates
c -----------------------------------------
      lam     =  lam_cmp
      phi     =  phi_cmp

c Compute and Adjust Longitude Weights
c ------------------------------------
      lam_im2 =  lon_cmp(im2(i))
      lam_im1 =  lon_cmp(im1(i))
      lam_ip0 =  lon_cmp(ip0(i))
      lam_ip1 =  lon_cmp(ip1(i))

      if( lam_im2.gt.lam_im1 ) lam_im2 = lam_im2 - 2*pi
      if( lam_im1.gt.lam_ip0 ) lam_ip0 = lam_ip0 + 2*pi
      if( lam_im1.gt.lam_ip1 ) lam_ip1 = lam_ip1 + 2*pi
      if( lam_ip0.gt.lam_ip1 ) lam_ip1 = lam_ip1 + 2*pi


c Compute and Adjust Latitude Weights
c Note:  Latitude Index Boundaries are Adjusted during Interpolation
c ------------------------------------------------------------------
          phi_jm1 =  lat_cmp(jm1(i))

      if( jm2(i).eq.0 ) then
          phi_jm2 = phi_jm1 - dphi(1)
      else
          phi_jm2 =  lat_cmp(jm2(i))
      endif

      if( jm1(i).eq.jm ) then
          phi_jp0 = phi_jm1 + dphi(jm-1)
          phi_jp1 = phi_jp0 + dphi(jm-2)
      else
          phi_jp0 =  lat_cmp(jp0(i))
          if( jp1(i).eq.jm+1 ) then
              phi_jp1 = phi_jp0 + dphi(jm-1)
          else
              phi_jp1 =  lat_cmp(jp1(i))
          endif
      endif


c Bi-Linear Weights
c -----------------
              d    = (lam_ip0-lam_im1)*(phi_jp0-phi_jm1)
      wl_im1jm1(i) = (lam_ip0-lam    )*(phi_jp0-phi    )/d
      wl_ip0jm1(i) = (lam    -lam_im1)*(phi_jp0-phi    )/d
      wl_im1jp0(i) = (lam_ip0-lam    )*(phi    -phi_jm1)/d
      wl_ip0jp0(i) = (lam    -lam_im1)*(phi    -phi_jm1)/d

c Bi-Cubic Weights
c ----------------
      ap1 = ( (lam    -lam_ip0)*(lam    -lam_im1)*(lam    -lam_im2) )
     .    / ( (lam_ip1-lam_ip0)*(lam_ip1-lam_im1)*(lam_ip1-lam_im2) )
      ap0 = ( (lam_ip1-lam    )*(lam    -lam_im1)*(lam    -lam_im2) )
     .    / ( (lam_ip1-lam_ip0)*(lam_ip0-lam_im1)*(lam_ip0-lam_im2) )
      am1 = ( (lam_ip1-lam    )*(lam_ip0-lam    )*(lam    -lam_im2) )
     .    / ( (lam_ip1-lam_im1)*(lam_ip0-lam_im1)*(lam_im1-lam_im2) )
      am2 = ( (lam_ip1-lam    )*(lam_ip0-lam    )*(lam_im1-lam    ) )
     .    / ( (lam_ip1-lam_im2)*(lam_ip0-lam_im2)*(lam_im1-lam_im2) )

      bp1 = ( (phi    -phi_jp0)*(phi    -phi_jm1)*(phi    -phi_jm2) )
     .    / ( (phi_jp1-phi_jp0)*(phi_jp1-phi_jm1)*(phi_jp1-phi_jm2) )
      bp0 = ( (phi_jp1-phi    )*(phi    -phi_jm1)*(phi    -phi_jm2) )
     .    / ( (phi_jp1-phi_jp0)*(phi_jp0-phi_jm1)*(phi_jp0-phi_jm2) )
      bm1 = ( (phi_jp1-phi    )*(phi_jp0-phi    )*(phi    -phi_jm2) )
     .    / ( (phi_jp1-phi_jm1)*(phi_jp0-phi_jm1)*(phi_jm1-phi_jm2) )
      bm2 = ( (phi_jp1-phi    )*(phi_jp0-phi    )*(phi_jm1-phi    ) )
     .    / ( (phi_jp1-phi_jm2)*(phi_jp0-phi_jm2)*(phi_jm1-phi_jm2) )

      wc_ip1jp1(i) = bp1*ap1
      wc_ip0jp1(i) = bp1*ap0
      wc_im1jp1(i) = bp1*am1
      wc_im2jp1(i) = bp1*am2

      wc_ip1jp0(i) = bp0*ap1
      wc_ip0jp0(i) = bp0*ap0
      wc_im1jp0(i) = bp0*am1
      wc_im2jp0(i) = bp0*am2

      wc_ip1jm1(i) = bm1*ap1
      wc_ip0jm1(i) = bm1*ap0
      wc_im1jm1(i) = bm1*am1
      wc_im2jm1(i) = bm1*am2

      wc_ip1jm2(i) = bm2*ap1
      wc_ip0jm2(i) = bm2*ap0
      wc_im1jm2(i) = bm2*am1
      wc_im2jm2(i) = bm2*am2

      enddo

c Interpolate Computational-Grid Quantities to Geophysical Grid
c -------------------------------------------------------------
      do L=1,lm
      do i=1,irun

      if( lat_geo(i).le.lat_cmp(2)     .or.
     .    lat_geo(i).ge.lat_cmp(jm-1) ) then

c 1st Order Interpolation at Poles
c --------------------------------
      if( q_cmp( im1(i),jm1(i),L ).ne.undef  .and.
     .    q_cmp( ip0(i),jm1(i),L ).ne.undef  .and.
     .    q_cmp( im1(i),jp0(i),L ).ne.undef  .and.
     .    q_cmp( ip0(i),jp0(i),L ).ne.undef ) then

      q_tmp(i) = wl_im1jm1(i) * q_cmp( im1(i),jm1(i),L )
     .         + wl_ip0jm1(i) * q_cmp( ip0(i),jm1(i),L )
     .         + wl_im1jp0(i) * q_cmp( im1(i),jp0(i),L )
     .         + wl_ip0jp0(i) * q_cmp( ip0(i),jp0(i),L )

      else
      q_tmp(i) = undef
      endif

      else

c Cubic Interpolation away from Poles
c -----------------------------------
      if( q_cmp( ip1(i),jp0(i),L ).ne.undef  .and.
     .    q_cmp( ip0(i),jp0(i),L ).ne.undef  .and.
     .    q_cmp( im1(i),jp0(i),L ).ne.undef  .and.
     .    q_cmp( im2(i),jp0(i),L ).ne.undef  .and.

     .    q_cmp( ip1(i),jm1(i),L ).ne.undef  .and.
     .    q_cmp( ip0(i),jm1(i),L ).ne.undef  .and.
     .    q_cmp( im1(i),jm1(i),L ).ne.undef  .and.
     .    q_cmp( im2(i),jm1(i),L ).ne.undef  .and.

     .    q_cmp( ip1(i),jp1(i),L ).ne.undef  .and.
     .    q_cmp( ip0(i),jp1(i),L ).ne.undef  .and.
     .    q_cmp( im1(i),jp1(i),L ).ne.undef  .and.
     .    q_cmp( im2(i),jp1(i),L ).ne.undef  .and.

     .    q_cmp( ip1(i),jm2(i),L ).ne.undef  .and.
     .    q_cmp( ip0(i),jm2(i),L ).ne.undef  .and.
     .    q_cmp( im1(i),jm2(i),L ).ne.undef  .and.
     .    q_cmp( im2(i),jm2(i),L ).ne.undef ) then

      q_tmp(i) = wc_ip1jp1(i) * q_cmp( ip1(i),jp1(i),L )
     .         + wc_ip0jp1(i) * q_cmp( ip0(i),jp1(i),L )
     .         + wc_im1jp1(i) * q_cmp( im1(i),jp1(i),L )
     .         + wc_im2jp1(i) * q_cmp( im2(i),jp1(i),L )

     .         + wc_ip1jp0(i) * q_cmp( ip1(i),jp0(i),L )
     .         + wc_ip0jp0(i) * q_cmp( ip0(i),jp0(i),L )
     .         + wc_im1jp0(i) * q_cmp( im1(i),jp0(i),L )
     .         + wc_im2jp0(i) * q_cmp( im2(i),jp0(i),L )

     .         + wc_ip1jm1(i) * q_cmp( ip1(i),jm1(i),L )
     .         + wc_ip0jm1(i) * q_cmp( ip0(i),jm1(i),L )
     .         + wc_im1jm1(i) * q_cmp( im1(i),jm1(i),L )
     .         + wc_im2jm1(i) * q_cmp( im2(i),jm1(i),L )

     .         + wc_ip1jm2(i) * q_cmp( ip1(i),jm2(i),L )
     .         + wc_ip0jm2(i) * q_cmp( ip0(i),jm2(i),L )
     .         + wc_im1jm2(i) * q_cmp( im1(i),jm2(i),L )
     .         + wc_im2jm2(i) * q_cmp( im2(i),jm2(i),L )

      elseif( q_cmp( im1(i),jm1(i),L ).ne.undef  .and.
     .        q_cmp( ip0(i),jm1(i),L ).ne.undef  .and.
     .        q_cmp( im1(i),jp0(i),L ).ne.undef  .and.
     .        q_cmp( ip0(i),jp0(i),L ).ne.undef ) then

      q_tmp(i) = wl_im1jm1(i) * q_cmp( im1(i),jm1(i),L )
     .         + wl_ip0jm1(i) * q_cmp( ip0(i),jm1(i),L )
     .         + wl_im1jp0(i) * q_cmp( im1(i),jp0(i),L )
     .         + wl_ip0jp0(i) * q_cmp( ip0(i),jp0(i),L )

      else
      q_tmp(i) = undef
      endif

      endif
      enddo

c Load Temp array into Output array
c ---------------------------------
      do i=1,irun
      q_geo(i,L) = q_tmp(i)
      enddo
      enddo

      deallocate ( wl_ip0jp0 , wl_im1jp0 )
      deallocate ( wl_ip0jm1 , wl_im1jm1 )
      deallocate ( wc_ip1jp1 , wc_ip0jp1 , wc_im1jp1 , wc_im2jp1 )
      deallocate ( wc_ip1jp0 , wc_ip0jp0 , wc_im1jp0 , wc_im2jp0 )
      deallocate ( wc_ip1jm1 , wc_ip0jm1 , wc_im1jm1 , wc_im2jm1 )
      deallocate ( wc_ip1jm2 , wc_ip0jm2 , wc_im1jm2 , wc_im2jm2 )
      deallocate (       ip1 ,       ip0 ,       im1 ,       im2 )
      deallocate (       jp1 ,       jp0 ,       jm1 ,       jm2 )

      return

      end

      subroutine sigtopl ( qprs,q,logpl,logp,im,jm,lm,undef )
C***********************************************************************
C
C PURPOSE
C   To interpolate an arbitrary quantity from Model Vertical Grid to Pressure
C
C INPUT
C   Q ..... Q    (im,jm,lm) Arbitrary Quantity on Model Grid
C   PKZ ... PKZ  (im,jm,lm) Pressure to the Kappa at Model Levels (From Phillips)
C   PKSRF . PKSRF(im,jm) Surface Pressure to the Kappa
C   PTOP .. Pressure at Model Top
C   P ..... Output Pressure Level (mb)
C   IM .... Longitude Dimension of Input
C   JM .... Latitude  Dimension of Input
C   LM .... Vertical  Dimension of Input
C
C OUTPUT
C   QPRS .. QPRS (im,jm) Arbitrary Quantity at Pressure p
C
C NOTE
C   Quantity is interpolated Linear in P**Kappa.
C   Between  PTOP**Kappa and PKZ(1),  quantity is extrapolated.
C   Between PKSRF**Kappa and PKZ(LM), quantity is extrapolated.
C   Undefined Model-Level quantities are not used.
C
C***********************************************************************
C*                  GODDARD LABORATORY FOR ATMOSPHERES                 *
C***********************************************************************
C
      implicit none
      integer  i,j,l,im,jm,lm

      real  qprs(im,jm)
      real  q   (im,jm,lm)
      real logpl(im,jm,lm)
      real  logp(im,jm)

      real  undef
      real  temp

c Initialize to UNDEFINED
c -----------------------
      qprs(:,:) = undef

c Interpolate to Pressure Between Model Levels
c --------------------------------------------
      do L=1,lm-1
      if( all( logpl(:,:,L  )>logp(:,:) ) ) exit
      if( all( logpl(:,:,L+1)<logp(:,:) ) ) cycle

         do j=1,jm
         do i=1,im
         if( logp(i,j).le.logpl(i,j,L+1) .and. logp(i,j).ge.logpl(i,j,L) ) then
         temp      = ( logpl(i,j,L)-logp(i,j) ) / ( logpl(i,j,L)-logpl(i,j,L+1) )

                 if( q(i,j,L)  .ne.undef  .and.
     .               q(i,j,L+1).ne.undef ) then
         qprs(i,j) = q(i,j,L+1)*temp + q(i,j,L)*(1.-temp)
            else if( q(i,j,L+1).ne.undef  .and. temp.ge.0.5 ) then
         qprs(i,j) = q(i,j,L+1)
            else if( q(i,j,L)  .ne.undef  .and. temp.le.0.5 ) then
         qprs(i,j) = q(i,j,L)
                 endif

         endif
         enddo
         enddo

      enddo

c Set Values above and below Model Boundaries
c -------------------------------------------
      do j=1,jm
      do i=1,im
      if( logp(i,j).le.logpl(i,j,1 ) ) qprs(i,j) = q(i,j,1 )
      if( logp(i,j).ge.logpl(i,j,lm) ) qprs(i,j) = q(i,j,lm)
      enddo
      enddo

      return
      end subroutine sigtopl

      subroutine interp3 ( q1,p1,im,jm,km, q2,p2,kn, ps )
      implicit none

      integer,  intent(in) :: im                ! Longitude dimension
      integer,  intent(in) :: jm                ! Latitude  dimension
      integer,  intent(in) :: km                ! Original vertical dimension
      integer,  intent(in) :: kn                ! Target   vertical dimension

      real,     intent(in) ::   q1(im,jm,km)    ! Field input
      real,     intent(in) ::   p1(im,jm,km)    ! Pressure at mid-layer in Original coordinate

      real,     intent(inout)::  q2(im,jm,kn)   ! Field output
      real,     intent(in)   ::  p2(im,jm,kn)   ! Pressure at mid-layer in Target   coordinate
      real,     intent(in)   ::  ps(im,jm)      ! Surface Pressure      in Target   coordinate

!-----------------------------------------------------------------------
!
! !LOCAL VARIABLES:
      real   logpl1(im,jm,km)
      real   logpl2(im,jm,kn)
      real   dlogp1(im,jm,km)
      real   am2,am1,ap0,ap1,P,PLP1,PLP0,PLM1,PLM2,DLP0,DLM1,DLM2

      integer i,j,k,kc, LM2,LM1,LP0,LP1

! Initialization
! --------------
      logpl1 = log( p1 )
      logpl2 = log( p2 )

      do k=1,km-1
      dlogp1(:,:,k) = logpl1(:,:,k+1)-logpl1(:,:,k)
      enddo

! Interpolate Q onto target Pressures
! -----------------------------------
      do j=1,jm
      do i=1,im

      kc = 1
      dowhile ( kc.lt.km .and. logpl1(i,j,kc).lt.log(ps(i,j)) )
      kc = kc+1
      enddo
      kc = kc-1

      do k=1,kn
         LM1 = 1
         LP0 = 1
         do while( LP0.le.km )
            if (logpl1(i,j,LP0).lt.logpl2(i,j,k)) then
               LP0 = LP0+1
            else
               exit
            endif
         enddo
         LM1 = max(LP0-1,1)
         LP0 = min(LP0, km)

! Extrapolate Linearly in LogP above first model level
! ----------------------------------------------------
         if( LM1.eq.1 .and. LP0.eq.1 ) then
             q2(i,j,k) = q1(i,j,1)
c            q2(i,j,k) = q1(i,j,1) + ( q1(i,j,2)-q1(i,j,1) )*( logpl2(i,j,k)-logpl1(i,j,1) )
c    .                                                      /( logpl1(i,j,2)-logpl1(i,j,1) )

! Extrapolate Linearly in LogP below last model level
! ---------------------------------------------------
         else if( LM1.eq.km .and. LP0.eq.km ) then
             q2(i,j,k) = q1(i,j,kc)
c            q2(i,j,k) = q1(i,j,km) + ( q1(i,j,km)-q1(i,j,km-1) )*( logpl2(i,j,k )-logpl1(i,j,km  ) )
c    .                                                           /( logpl1(i,j,km)-logpl1(i,j,km-1) )

! Interpolate Linearly in LogP between levels 1 => 2 and km-1 => km
! -----------------------------------------------------------------
         else if( LM1.eq.1 .or. LP0.eq.km .or. 1.eq.1 ) then
             q2(i,j,k) = q1(i,j,LP0) + ( q1(i,j,LM1)-q1(i,j,LP0) )*( logpl2(i,j,k  )-logpl1(i,j,LP0) )
     .                                                            /( logpl1(i,j,LM1)-logpl1(i,j,LP0) )

! Interpolate Cubicly in LogP between other model levels
! ------------------------------------------------------
         else
              LP1 = LP0+1
              LM2 = LM1-1
             P    = logpl2(i,j,k)
             PLP1 = logpl1(i,j,LP1)
             PLP0 = logpl1(i,j,LP0)
             PLM1 = logpl1(i,j,LM1)
             PLM2 = logpl1(i,j,LM2)
             DLP0 = dlogp1(i,j,LP0)
             DLM1 = dlogp1(i,j,LM1)
             DLM2 = dlogp1(i,j,LM2)

              ap1 = (P-PLP0)*(P-PLM1)*(P-PLM2)/( DLP0*(DLP0+DLM1)*(DLP0+DLM1+DLM2) )
              ap0 = (PLP1-P)*(P-PLM1)*(P-PLM2)/( DLP0*      DLM1 *(     DLM1+DLM2) )
              am1 = (PLP1-P)*(PLP0-P)*(P-PLM2)/( DLM1*      DLM2 *(DLP0+DLM1     ) )
              am2 = (PLP1-P)*(PLP0-P)*(PLM1-P)/( DLM2*(DLM1+DLM2)*(DLP0+DLM1+DLM2) )

             q2(i,j,k) = ap1*q1(i,j,LP1) + ap0*q1(i,j,LP0) + am1*q1(i,j,LM1) + am2*q1(i,j,LM2)

         endif

      enddo
      enddo
      enddo

      return
      end

      subroutine remap  ( ps1,dp1,u1,v1,thv1,q1,lm1,
     .                    ps2,dp2,u2,v2,t2  ,q2,lm2,im,jm,nq )

C***********************************************************************
C
C  Purpose
C     Driver for remapping input analysis (2) to output model levels (1)
C
C  Argument Description
C     ps1 ...... model surface  pressure
C     dp1 ...... model pressure thickness
C     u1 ....... model zonal      wind
C     v1 ....... model meridional wind
C     thv1 ..... model virtual potential  temperature
C     q1 ....... model specific   humidity
C     oz1 ...... model ozone
C     lm1 ...... model vertical   dimension
C
C     ps2 ...... analysis surface  pressure
C     dp2 ...... analysis pressure thickness
C     u2 ....... analysis zonal      wind
C     v2 ....... analysis meridional wind
C     t2 . ..... analysis dry-bulb temperature
C     q2 ....... analysis specific   humidity
C     oz2 ...... analysis ozone
C     lm2 ...... analysis vertical   dimension
C
C     im ....... zonal      dimension
C     jm ....... meridional dimension
C     nq ....... number of  tracers
C
C***********************************************************************
C*                  GODDARD LABORATORY FOR ATMOSPHERES                 *
C***********************************************************************

      use MAPL_ConstantsMod
      use m_set_eta, only: set_eta
      use GEOS_GmapMod, only: gmap
      implicit none
      integer  im,jm,lm1,lm2,nq

c fv-DAS variables
c ----------------
      real      dp1(im,jm,lm1)
      real       u1(im,jm,lm1)
      real       v1(im,jm,lm1)
      real     thv1(im,jm,lm1)
      real       q1(im,jm,lm1,nq)
      real      ps1(im,jm)

      real      ak(lm1+1)
      real      bk(lm1+1)

c Target analysis variables
c -------------------------
      real     dp2(im,jm,lm2)
      real      u2(im,jm,lm2)
      real      v2(im,jm,lm2)
      real      t2(im,jm,lm2)
      real    thv2(im,jm,lm2)
      real      q2(im,jm,lm2,nq)
      real     ps2(im,jm)

c Local variables
c ---------------
      real   pe1(im,jm,lm1+1)
      real   pe2(im,jm,lm2+1)
      real   pk2(im,jm,lm2  )
      real  pke1(im,jm,lm1+1)
      real  pke2(im,jm,lm2+1)

      real    kappa,cp,ptop,pl,alf,pint
      real    rgas,pref,tref,pkref,tstar,eps,rvap,grav
      integer i,j,L,n,ks

      kappa = MAPL_KAPPA
      rgas  = MAPL_RGAS
      rvap  = MAPL_RVAP
      grav  = MAPL_GRAV
      cp    = MAPL_CP
      eps   = rvap/rgas-1.0

      print *, 'Inside Remap'
c     print *, '  im:', im, ' jm:', jm, ' lm1:', lm1, ' lm2:', lm2

c Construct target analysis pressure variables
c --------------------------------------------
      do j=1,jm
      do i=1,im
      pe2(i,j,lm2+1) = ps2(i,j)
      enddo
      enddo

      do L=lm2,1,-1
      do j=1,jm
      do i=1,im
      pe2(i,j,L) = pe2(i,j,L+1) - dp2(i,j,L)
      enddo
      enddo
      enddo

      do j=1,jm
      do i=1,im
      pe2(i,j,1) = max( pe2(i,j,1),1.0 )  ! Set ptop = 0.01 mb (rather than 0.0 mb from NCEP)
      enddo
      enddo

      do L=1,lm2+1
      do j=1,jm
      do i=1,im
      pke2(i,j,L) = pe2(i,j,L)**kappa
      enddo
      enddo
      enddo

c Construct target virtual potential temperature
c ----------------------------------------------
      do L=1,lm2
      do j=1,jm
      do i=1,im
       pk2(i,j,L) = ( pke2(i,j,L+1)-pke2(i,j,L) )/( kappa*log(pe2(i,j,L+1)/pe2(i,j,L)) )
      thv2(i,j,L) =     t2(i,j,L)*( 1.0+eps*max(0.0,q2(i,j,L,1)) )/pk2(i,j,L)
      enddo
      enddo
      enddo

c Construct fv pressure variables using surface pressure and AK & BK
c ------------------------------------------------------------------
      call set_eta ( lm1,ks,ptop,pint,ak,bk )

      do L=1,lm1+1
      do j=1,jm
      do i=1,im
       pe1(i,j,L) = ak(L) + bk(L)*ps1(i,j)
      pke1(i,j,L) = pe1(i,j,L)**kappa
      enddo
      enddo
      enddo

      do L=1,lm1
      do j=1,jm
      do i=1,im
       dp1(i,j,L) = pe1(i,j,L+1)-pe1(i,j,L)
      enddo
      enddo
      enddo

c Map Input Analysis onto fv grid
c -------------------------------
      call gmap ( im,jm,nq, kappa,
     .            lm2,  pke2,  pe2, u2,  v2,  thv2,  q2,
     .            lm1,  pke1,  pe1, u1,  v1,  thv1,  q1)

      return
      end

      subroutine put_fveta ( ps,dp,u,v,thv,q,phis,
     .                       im,jm,lm,nq,nymd,nhms,tag,ext,lonbeg,
     .                       timeinc,precision )
      use MAPL_BaseMod, only: MAPL_UNDEF
      use MAPL_ConstantsMod
      use m_set_eta, only: set_eta
      implicit  none

      integer   im,jm,lm,nq,nymd,nhms
      real phis(im,jm)
      real   ps(im,jm)
      real   dp(im,jm,lm)
      real    u(im,jm,lm)
      real    v(im,jm,lm)
      real  thv(im,jm,lm)
      real    q(im,jm,lm,nq)
      integer timeinc

      real  ple(im,jm,lm+1)
      real  pke(im,jm,lm+1)
      real   pk(im,jm,lm)
      real   tv(im,jm,lm)
      real    t(im,jm,lm)

      real lats(jm)
      real lons(im)
      real levs(lm)
      real   ak(lm+1)
      real   bk(lm+1)

      real  rgas,rvap,eps,kappa,grav
      real  ptop,dlon,dlat,pref,dpref(lm),undef,lonbeg,pint
      integer i,j,L,m,n,rc,ks
      character*256 tag,ext,filename, fname
      integer nvars,fid,precision

      character*256  levunits
      character*256  title
      character*256  source
      character*256  contact
      character*256, allocatable, dimension(:) ::   vname
      character*256, allocatable, dimension(:) ::  vtitle
      character*256, allocatable, dimension(:) ::  vunits
      integer,       allocatable, dimension(:) ::   lmvar

      real,          allocatable :: v_range(:,:)
      real,          allocatable :: p_range(:,:)

      character*2 cnhms
      character*3 cLM
      character*8 cnymd

      print *, im,jm,lm,nq,nymd,nhms,trim(ext)

      undef = MAPL_UNDEF
      kappa = MAPL_KAPPA
      rgas  = MAPL_RGAS
      rvap  = MAPL_RVAP
      grav  = MAPL_GRAV
      eps   = rvap/rgas-1.0

      write( cnymd,200 ) nymd
      write( cnhms,300 ) nhms/10000
      write(   cLM,400 ) lm
  200 format(i8.8)
  300 format(i2.2)
  400 format(i3.3)
      fname = trim(tag) // 'era5_eta2eta_L' // trim(cLM) // '.' // trim(cnymd) // '_' // trim(cnhms) // 'z.' // trim(ext)
      print *, 'Creating 32-bit eta file: ',trim(fname)

      call set_eta ( lm,ks,ptop,pint,ak,bk )

! Construct T, TV
! ---------------
      do L=1,lm+1
      ple(:,:,L) = ak(L) + ps(:,:)*bk(L)
      enddo
      pke(:,:,:) = ple(:,:,:)**kappa
      do L=1,lm
      pk(:,:,L) = ( pke(:,:,L+1)-pke(:,:,L) )
     .          / ( kappa*log(ple(:,:,L+1)/ple(:,:,L)) )
      enddo
      tv = thv*pk
      t(:,:,:) = tv(:,:,:)/(1+eps*q(:,:,:,1))

c String and vars settings
c ------------------------
      title    = 'era5_eta2eta Data'
      source   = 'Goddard Modeling and Assimilation Office, NASA/GSFC'
      contact  = 'data@gmao.gsfc.nasa.gov'
      levunits = 'hPa'

      nvars = 7

      allocate (   vname(nvars) )
      allocate (  vtitle(nvars) )
      allocate (  vunits(nvars) )
      allocate (   lmvar(nvars) )
      allocate ( v_range(2,nvars) )
      allocate ( p_range(2,nvars) )

             n  =  1
       vname(n) = 'phis'
      vtitle(n) = 'Topography geopotential'
      vunits(n) = 'meter2/sec2'
       lmvar(n) =  0

             n  =  n + 1
       vname(n) = 'ps'
      vtitle(n) = 'Surface Pressure'
      vunits(n) = 'Pa'
       lmvar(n) =  0

             n  =  n + 1
       vname(n) = 'dp'
      vtitle(n) = 'Pressure Thickness'
      vunits(n) = 'Pa'
       lmvar(n) =  lm

             n  =  n + 1
       vname(n) = 'u'
      vtitle(n) = 'eastward_wind'
      vunits(n) = 'm/s'
       lmvar(n) =  lm

             n  =  n + 1
       vname(n) = 'v'
      vtitle(n) = 'northward_wind'
      vunits(n) = 'm/s'
       lmvar(n) =  lm

             n  =  n + 1
       vname(n) = 'tv'
      vtitle(n) = 'air_virtual_temperature'
      vunits(n) = 'K'
       lmvar(n) =  lm

             n  =  n + 1
       vname(n) = 'qv'
      vtitle(n) = 'Specific Humidity Vapor'
      vunits(n) = 'kg/kg'
       lmvar(n) =  lm

      v_range(:,:) = undef
      p_range(:,:) = undef

c Compute grid
c ------------
      dlon = 360.0/ im
      dlat = 180.0/(jm-1)

      do j=1,jm
      lats(j) = -90.0 + (j-1)*dlat
      enddo
      do i=1,im
      lons(i) =   lonbeg + (i-1)*dlon
      enddo
      do L=1,lm
      dpref(L) = (ak(L+1)-ak(L)) + (bk(L+1)-bk(L))*98400.0
      enddo
      pref    = ptop + 0.5*dpref(1)
      levs(1) = pref
      do L=2,lm
      pref    = pref + 0.5*( dpref(L)+dpref(L-1) )
      levs(L) = pref
      enddo
      levs(:) = levs(:)/100

c Create GFIO file
c ----------------
      call GFIO_Create ( fname, title, source, contact, undef,
     .                   im, jm, lm, lons, lats, levs, levunits,
     .                   nymd, nhms, timeinc,
     .                   nvars, vname, vtitle, vunits, lmvar,
     .                   v_range, p_range, precision,
     .                   fid, rc )
c Write GFIO data
c ---------------
                                                                       n = 1
      call Gfio_putVar ( fid,vname(n),nymd,nhms,im,jm,0, 1,phis,rc ) ; n = n+1
      call Gfio_putVar ( fid,vname(n),nymd,nhms,im,jm,0, 1,ps  ,rc ) ; n = n+1
      call Gfio_putVar ( fid,vname(n),nymd,nhms,im,jm,1,lm,dp  ,rc ) ; n = n+1
      call Gfio_putVar ( fid,vname(n),nymd,nhms,im,jm,1,lm,u   ,rc ) ; n = n+1
      call Gfio_putVar ( fid,vname(n),nymd,nhms,im,jm,1,lm,v   ,rc ) ; n = n+1
      call Gfio_putVar ( fid,vname(n),nymd,nhms,im,jm,1,lm,tv  ,rc ) ; n = n+1
      do m=1,nq
      call Gfio_putVar ( fid,vname(n),nymd,nhms,im,jm,1,lm,q(1,1,1,m),rc ) ; n = n+1
      enddo

c Write GFIO global attributes
c ----------------------------
      call GFIO_PutRealAtt ( fid,'ak',  lm+1,ak   ,precision,rc )
      call GFIO_PutRealAtt ( fid,'bk',  lm+1,bk   ,precision,rc )

      call gfio_close ( fid,rc )
      return
      end

      subroutine get_gmaoana_data  ( id,ps,u,v,t,q,h,phis,
     .                               im,jm,lm,nymd,nhms,lonbeg,
     .                               imana,jmana,lmana,nvars,names,lmvars,undef,plevs )
      use MAPL_ConstantsMod
      implicit none
      integer  id,im,jm,lm,nymd,nhms,rc
      integer  imana,jmana,lmana
      integer              nvars
      integer       lmvars(nvars)
      character*256  names(nvars)
      character*256  filename, format

      real     lonbeg
      real     ps(im,jm)
      real      u(im,jm,lm)
      real      v(im,jm,lm)
      real      t(im,jm,lm)
      real      h(im,jm,lm)
      real     rh(im,jm,lm)
      real      q(im,jm,lm)
      real   phis(im,jm)
      real  plevs(lm)
      real     slp(im,jm)
      real     thv(im,jm)

      real, allocatable :: dum2d(:,:)
      real, allocatable :: dum3d(:,:,:)
      real, allocatable :: dumu (:,:,:)
      real, allocatable :: dumv (:,:,:)

      real    undef,kappa,grav,dum,beta,cp,rgas,gamma,dp
      integer L,i,j,n,LM1

      allocate ( dum2d(imana,jmana)       )
      allocate ( dum3d(imana,jmana,lmana) )
      allocate ( dumu (imana,jmana,lmana) )
      allocate ( dumv (imana,jmana,lmana) )

      kappa = MAPL_KAPPA
      rgas  = MAPL_RGAS
      grav  = MAPL_GRAV
      cp    = MAPL_CP
      beta  = 6.5e-3

!       Writing variable: slp
!       Writing variable: ps
!       Writing variable: hght
!       Writing variable: rh
!       Writing variable: tmpu
!       Writing variable: u
!       Writing variable: v

c Read ANA Variables
c ------------------
      call gfio_getvar ( id,'slp',nymd,nhms,imana,jmana,0,1 ,dum2d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find GMAO SLP variable'
          call exit(7)
      endif
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum2d,imana,jmana,slp,im,jm,1,undef )
      else
              slp = dum2d
      endif

      call gfio_getvar     ( id,'ps',nymd,nhms,imana,jmana,0,1 ,dum2d ,rc )  ! New ECMWF Format 2011/05/11 06z
      if( rc.ne.0 ) then
          print *, 'Could not find GMAO Surface Pressure variable'
          call exit(7)
      endif
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum2d,imana,jmana,ps,im,jm,1,undef )
      else
              ps = dum2d
      endif

      call gfio_getvar ( id,'hght',nymd,nhms,imana,jmana,1,lmana,dum3d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find GMAO Height variable'
          call exit(7)
      endif
                 call zflip( dum3d,imana,jmana,lmana )
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum3d,imana,jmana,h,im,jm,lm,undef )
      else
              h = dum3d
      endif

c Winds
c -----
      call gfio_getvar ( id,'u',nymd,nhms,imana,jmana,1,lmana,dumu,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find GMAO U-Wind variable'
          call exit(7)
      endif
      call gfio_getvar ( id,'v',nymd,nhms,imana,jmana,1,lmana,dumv,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find GMAO V-Wind variable'
          call exit(7)
      endif

                 call zflip( dumu,imana,jmana,lmana )
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dumu,imana,jmana,u,im,jm,lm,undef )
      else
              u = dumu
      endif

                 call zflip( dumv,imana,jmana,lmana )
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dumv,imana,jmana,v,im,jm,lm,undef )
      else
              v = dumv
      endif

c Temperature
c -----------
      call gfio_getvar ( id,'tmpu',nymd,nhms,imana,jmana,1,lmana,dum3d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find GMAO Temperature variable'
          call exit(7)
      endif
                 call zflip( dum3d,imana,jmana,lmana )
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum3d,imana,jmana,t,im,jm,lm,undef )
      else
              t = dum3d
      endif

c Relative Humidity
c -----------------
      call gfio_getvar ( id,'rh',nymd,nhms,imana,jmana,1,lmana,dum3d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find GMAO Rel.Hum. variable'
          call exit(7)
      endif
                 call zflip( dum3d,imana,jmana,lmana )
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum3d,imana,jmana,rh,im,jm,lm,undef )
      else
              rh = dum3d
      endif
      rh = max( rh,0.0 )

c Compute PHIS
c ------------
      do j=1,jm
      do i=1,im
         L=1
         do while( L.lt.lm .and. plevs(L).lt.ps(i,j)/100.0 )
         L=L+1
         enddo
         LM1 = L-1
         phis(i,j) = h(i,j,L) - ( h(i,j,L)-h(i,j,LM1) )*log( 100*plevs(L)/ps(i,j) )/log( plevs(L)/plevs(LM1) )
       enddo
       enddo
       phis = phis*grav

c Load GMAO Variables
c -------------------
      do L=1,lm
      do j=1,jm
      do i=1,im
      call qsat (t(i,j,L),plevs(L),q(i,j,L),dum,.false.)
      q(i,j,L) = rh(i,j,L)*q(i,j,L)*0.01
      enddo
      enddo
      enddo

      return
      end
