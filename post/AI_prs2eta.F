      program  main
      use MAPL_ConstantsMod
      use m_set_eta, only: set_eta
      implicit none

c **********************************************************************
c **********************************************************************
c ****                                                              ****
c ****       Create AI ANA.ETA File from Pressure Level Data     ****
c ****                                                              ****
c **********************************************************************
c **********************************************************************

      integer  im,jm,lm,nq
      real     ptop,pint
      real     rgas,eps,rvap
      real     kappa
      real     grav

      integer     niter
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

      character*256 prsdata, tag, ext

      real    :: phibg, phifg, thbr1, thbr2, delth, cp

      integer    nymd,nhms
      integer    Lbeg,Lend

c fv restart variables and topography
c -----------------------------------
      real, allocatable ::   ps(:,:)
      real, allocatable ::   dp(:,:,:)
      real, allocatable ::  ple(:,:,:)
      real, allocatable ::    u(:,:,:)
      real, allocatable ::    v(:,:,:)
      real, allocatable ::  thv(:,:,:)
      real, allocatable ::  pke(:,:,:)
      real, allocatable ::  pk (:,:,:)
      real, allocatable ::    q(:,:,:)

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

c Analysis variables
c ------------------
      real, allocatable :: phis_ana(:,:)
      real, allocatable ::   ps_ana(:,:)
      real, allocatable ::    u_ana(:,:,:)
      real, allocatable ::    v_ana(:,:,:)
      real, allocatable ::    z_ana(:,:,:)
      real, allocatable ::   er_ana(:,:,:)
      real, allocatable ::    q_ana(:,:,:)
      real, allocatable ::    p_ana(:,:,:)
      real, allocatable ::   dp_ana(:,:,:)
      real, allocatable ::   pl_ana(:,:,:)
      real, allocatable ::    t_ana(:,:,:)
      real, allocatable ::     t_ai(:,:,:)
      real, allocatable ::    h_ana(:,:,:)
      real, allocatable ::  ple_ana(:,:,:)
      real, allocatable ::    logp (:,:,:)
      real, allocatable ::    logpl(:,:,:)
      real, allocatable ::    qdum (:,:,:)
      real, allocatable ::   pl_min(:)
      real, allocatable ::   pl_avg(:)
      real, allocatable ::   pl_max(:)
      real, allocatable ::    q_min(:)
      real, allocatable ::    q_avg(:)
      real, allocatable ::    q_max(:)
      integer id,rc
      integer nvars, ngatts, ntime

      character*256, allocatable :: arg(:)

      integer precision
      integer i,j,k,L,n,nargs,iargc,ks
      logical norecon

c Analysis Grads CTL File Variables
c ---------------------------------
      character*256  ctlfile
      integer imana,jmana,lmana

      character*256, pointer :: names (:)
      integer,       pointer :: lmvars(:)
      real,          pointer ::  plevs(:)

C **********************************************************************
C ****           Initialize Filenames, Methods, etc.                ****
C **********************************************************************

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
        norecon =.false.

          nargs = iargc()
      if( nargs.eq.0 ) then
          call usage()
      else
          allocate ( arg(nargs) )
          do n=1,nargs
          call getarg(n,arg(n))
          enddo
          do n=1,nargs
             if( trim(arg(n)).eq.'-AI'     ) prsdata = trim(arg(n+1))
             if( trim(arg(n)).eq.'-tag'    )     tag = trim(arg(n+1))
             if( trim(arg(n)).eq.'-im'     ) read(arg(n+1), * ) im
             if( trim(arg(n)).eq.'-jm'     ) read(arg(n+1), * ) jm
             if( trim(arg(n)).eq.'-lm'     ) read(arg(n+1), * ) lm
             if( trim(arg(n)).eq.'-norecon') norecon =.true.
          enddo
      endif

      if( trim(tag).ne.'' ) tag = trim(tag) // '.'
      ext = 'nc4'


C **********************************************************************
C ****                       Read ANA MetaData                      ****
C **********************************************************************

      call gfio_open ( trim(prsdata),1,id,rc )
      call gfio_diminquire ( id,imana,jmana,lmana,ntime,nvars,ngatts,rc )

      if( im.eq.-999 ) im = imana
      if( jm.eq.-999 ) jm = jmana

      allocate ( lon(imana) )
      allocate ( lat(jmana) )
      allocate ( lev(lmana) )
      allocate ( yymmdd(ntime) )
      allocate ( hhmmss(ntime) )
      allocate (  vname(nvars) )
      allocate ( vtitle(nvars) )
      allocate ( vunits(nvars) )
      allocate (  kmvar(nvars) )
      allocate ( vrange(2,nvars) )
      allocate ( prange(2,nvars) )

      call gfio_inquire ( id,imana,jmana,lmana,ntime,nvars,
     .                    title,source,contact,undef,
     .                    lon,lat,lev,levunits,
     .                    yymmdd,hhmmss,timinc,
     .                    vname,vtitle,vunits,kmvar,
     .                    vrange,prange,rc )

          allocate ( plevs(lmana) )
          do L=1,lmana
          plevs(L) = lev(lmana-L+1)
          enddo

          print *
          print *, '            ANA File: ',trim(prsdata)
          print *, '                rslv: ',imana,jmana,lmana
          print *, '             lon_beg: ',lon(1)
          print *
          print *, ' Number of Variables: ',nvars
          print *
          do n=1,nvars
          write(6,1001) n,trim(vname(n)),trim(vtitle(n)),kmvar(n)
          enddo
 1001     format(1x,i2,3x,a16,2x,a32,2x,i3)
          print *
                                            L = 1
          print *, '     Pressure Levels: ',L,plevs(L)
          do L=2,lmana
          print *, '                      ',L,plevs(L)
          enddo
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

      allocate (   p_ana(im,jm,lmana) )
      allocate (  er_ana(im,jm,lmana) )
      allocate (   z_ana(im,jm,lmana) )
      allocate (   u_ana(im,jm,lmana) )
      allocate (   v_ana(im,jm,lmana) )
      allocate (   t_ana(im,jm,lmana) )
      allocate (   t_ai (im,jm,lmana) )
      allocate (   h_ana(im,jm,lmana) )
      allocate (   q_ana(im,jm,lmana) )
      allocate (  ps_ana(im,jm) )
      allocate (phis_ana(im,jm) )


      print *, 'Reading AI-prs Analysis for Date: ',nymd,' Time: ',nhms
      print *
      call get_ana_data  ( id,ps_ana,u_ana,v_ana,t_ana,q_ana,h_ana,phis_ana,
     .                     im,jm,lmana,nymd,nhms,
     .                     imana,jmana,lmana,undef,plevs )
      t_ai = t_ana

! Construct Pressure Variables
! ----------------------------
      allocate(  dp_ana(im,jm,lm)   )
      allocate(  pl_ana(im,jm,lm)   )
      allocate( ple_ana(im,jm,lm+1) )
      allocate(   logp (im,jm,lm)   )
      allocate(   logpl(im,jm,lm)   )

      allocate( ak(lm+1) )
      allocate( bk(lm+1) )

      call set_eta ( lm,ks,ptop,pint,ak,bk )

      allocate( pl_min(lm) )
      allocate( pl_avg(lm) )
      allocate( pl_max(lm) )
      do L=1,lm+1
          ple_ana(:,:,L) = ak(L) + ps_ana(:,:)*bk(L)
      enddo
      do L=1,lm
           dp_ana(:,:,L) = ple_ana(:,:,L+1)-ple_ana(:,:,L)
           pl_ana(:,:,L) =      0.5*(ple_ana(:,:,L+1)+ple_ana(:,:,L))
             logp(:,:,L) = log( 0.5*(ple_ana(:,:,L+1)+ple_ana(:,:,L)) )
           pl_min(l) =  1.e16
           pl_max(l) = -1.e16
           pl_avg(l) =  0.0
           do j=1,jm
              do i=1,im
                 pl_min(l) = min(pl_min(l),pl_ana(i,j,l))
                 pl_max(l) = max(pl_max(l),pl_ana(i,j,l))
                 pl_avg(l) = pl_avg(l) + pl_ana(i,j,l)
              enddo
           enddo
           pl_avg(l) = pl_avg(l)/FLOAT(im*jm)
           print*, L, pl_min(l), pl_avg(L), pl_max(l)
      enddo

      do L=1,lmana
          p_ana(:,:,L) =      100.0*plevs(L)
          logpl(:,:,L) = log( 100.0*plevs(L) )
      enddo

      allocate( q_min(lm) )
      allocate( q_avg(lm) )
      allocate( q_max(lm) )
      allocate( qdum(im,jm,lm) )

      call interp ( qdum,u_ana,logp,logpl,p_ana,pl_ana,ple_ana,im,jm,lm,lmana,undef,'UWND',niter,1 )
      deallocate  ( u_ana )
        allocate  ( u_ana(im,jm,lm) )
                    u_ana = qdum
      do L=1,lm
         q_min(l) =  1.e16
         q_max(l) = -1.e16
         q_avg(l) =  0.0
         do j=1,jm
            do i=1,im
               q_min(l) = min(q_min(l),qdum(i,j,l))
               q_max(l) = max(q_max(l),qdum(i,j,l))
               q_avg(l) = q_avg(l) + qdum(i,j,l)
            enddo
         enddo
         q_avg(l) = q_avg(l)/FLOAT(im*jm)
         print*, L, pl_avg(L), q_min(l), q_avg(l), q_max(l)
      enddo         
         

      call interp ( qdum,v_ana,logp,logpl,p_ana,pl_ana,ple_ana,im,jm,lm,lmana,undef,'VWND',niter,1 )
      deallocate  ( v_ana )
        allocate  ( v_ana(im,jm,lm) )
                    v_ana = qdum
      do L=1,lm
         q_min(l) =  1.e16
         q_max(l) = -1.e16
         q_avg(l) =  0.0
         do j=1,jm
            do i=1,im
               q_min(l) = min(q_min(l),qdum(i,j,l))
               q_max(l) = max(q_max(l),qdum(i,j,l))
               q_avg(l) = q_avg(l) + qdum(i,j,l)
            enddo
         enddo
         q_avg(l) = q_avg(l)/FLOAT(im*jm)
         print*, L, pl_avg(L), q_min(l), q_avg(l), q_max(l)
      enddo

      call interp ( qdum,t_ana,logp,logpl,p_ana,pl_ana,ple_ana,im,jm,lm,lmana,undef,'TMPU',niter,1 )
      deallocate  ( t_ana )
        allocate  ( t_ana(im,jm,lm) )
                    t_ana = qdum
      do L=1,lm
         q_min(l) =  1.e16
         q_max(l) = -1.e16
         q_avg(l) =  0.0
         do j=1,jm
            do i=1,im
               q_min(l) = min(q_min(l),qdum(i,j,l))
               q_max(l) = max(q_max(l),qdum(i,j,l))
               q_avg(l) = q_avg(l) + qdum(i,j,l)
            enddo
         enddo
         q_avg(l) = q_avg(l)/FLOAT(im*jm)
         print*, L, pl_avg(L), q_min(l), q_avg(l), q_max(l)
      enddo

      call interp ( qdum,q_ana,logp,logpl,p_ana,pl_ana,ple_ana,im,jm,lm,lmana,undef,'SPHU',niter,-1 )
      deallocate  ( q_ana )
        allocate  ( q_ana(im,jm,lm) )
                    q_ana = qdum
      do L=1,lm
         q_min(l) =  1.e16
         q_max(l) = -1.e16
         q_avg(l) =  0.0
         do j=1,jm
            do i=1,im
               q_min(l) = min(q_min(l),qdum(i,j,l))
               q_max(l) = max(q_max(l),qdum(i,j,l))
               q_avg(l) = q_avg(l) + qdum(i,j,l)
            enddo
         enddo
         q_avg(l) = q_avg(l)/FLOAT(im*jm)
         print*, L, pl_avg(L), q_min(l), q_avg(l), q_max(l)
      enddo

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

        ps =   ps_ana
        dp =   dp_ana
      phis = phis_ana

      call remap  ( ps,    dp,    u,    v,    thv,  q,    lm,
     .              ps_ana,dp_ana,u_ana,v_ana,t_ana,q_ana,lm,im,jm,1 )

C **********************************************************************
C ****                      Reconcile Heights                       ****
C **********************************************************************

      do L=1,lm+1
         ple(:,:,L) = ak(L) + ps(:,:)*bk(L)
      enddo
      pke(:,:,:) = ple(:,:,:)**kappa
      do L=1,lm
         pk(:,:,L) = ( pke(:,:,L+1)-pke(:,:,L) )
     .             / ( kappa*log(ple(:,:,L+1)/ple(:,:,L)) )
      enddo

      if( .not.norecon ) then
      do j=1,jm
      do i=1,im
      Lbeg  = lm
      phifg = phis(i,j)
      phibg = phifg
      do k=lmana,1,-1
          ! replace ANA HGT undefs with surface height
          if (h_ana(i,j,k).eq.undef) h_ana(i,j,k) = phis_ana(i,j)/grav
 
          if( p_ana(i,j,k).lt.ps(i,j)                  .and.  ! p_ana is above GEOS Surface Pressure 
     .        h_ana(i,j,k)-phibg/grav.gt.10.0          .and.  ! h_ana is at least 10-meters above previous level
     .        h_ana(i,j,k)-phis_ana(i,j)/grav.gt.10.0 ) then  ! h_ana is at least 10-meters above Topography

              do L=Lbeg,1,-1
                 if( ple(i,j,L).gt.p_ana(i,j,k) ) then
                    phifg = phifg + cp*thv(i,j,L)*( pke(i,j,L+1)-pke(i,j,L) )
                 else
                    exit
                 endif
              enddo
              Lend = L
              if( Lbeg-Lend.le.2 ) then
                  phifg = phibg
                  cycle
              endif

              phifg =   phifg + cp*thv(i,j,Lend)*( pke(i,j,Lend+1)-p_ana(i,j,k)**kappa )

              thbr1 = ( grav*h_ana(i,j,k)-phibg )/( pke(i,j,Lbeg+1)-p_ana(i,j,k)**kappa )/cp
              thbr2 = ( phifg            -phibg )/( pke(i,j,Lbeg+1)-p_ana(i,j,k)**kappa )/cp
              delth = thbr1-thbr2

              do L=Lbeg,Lend,-1
                 thv(i,j,L) = thv(i,j,L) + delth
              enddo

              phifg = phibg
              do L=Lbeg,Lend,-1
                 phifg = phifg + cp*thv(i,j,L)*( pke(i,j,L+1)-pke(i,j,L) )
              enddo
              Lbeg  = Lend-1
              phibg = phifg
          endif
      enddo

      enddo  ! End I-Loop
      enddo  ! End J-Loop
      endif  ! End RECON Test

C **********************************************************************
C ****                 Write AI ANA.ETA File                     ****
C **********************************************************************


      nq = 1
      call put_fveta ( ps,dp,u,v,thv,q,phis,
     .                 im,jm,lm,nq,nymd,nhms,tag,ext,lon(1),
     .                 timinc,precision )


      stop
      end

      subroutine interp ( q,qana,logp,logpl,pana,pl,ple,im,jm,lm,lmana,undef,name,niter,flag )
      implicit none
      integer im,jm,lm,lmana,niter,flag
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
      character*8 name

      integer i,j,L,n

c Interpolate Analysis to GEOS Model Levels
c -----------------------------------------
          do L=1,lm
          do j=1,jm
          do i=1,im
          call  sigtopl( q(i,j,L),qana(i,j,:),logpl(i,j,:),logp(i,j,L),1,1,lmana,undef )
          enddo
          enddo
          enddo
          if( flag.eq.-1 ) then
              q = max( q,0.0 )
          endif

          print *, 'Interpolating ',trim(name),' ...'

#ifdef DEBUG
          call writit (q,im,jm,lm,66)
#endif
          do n=1,niter
c            Interpolate GEOS Model Back to AI Levels and Compute Error
c            ----------------------------------------------------------
             do L=1,lmana
             do j=1,jm
             do i=1,im
                erana(i,j,L) = 0.0
                call  sigtopl( zana(i,j,L),q(i,j,:),logp(i,j,:),logpl(i,j,L),1,1,lm,undef )
                if (qana(i,j,L) .ne. undef) erana(i,j,L) = zana(i,j,L)-qana(i,j,L)
             enddo
             enddo
             enddo

c            Interpolate and Add Error to GEOS Model Levels
c            ----------------------------------------------
             call interp3 ( erana,pana,im,jm,lmana, er,pl,lm,ple(1,1,lm+1) )
             q = q - er
             if( flag.eq.-1 ) then
                 q = max( q,0.0 )
             endif
#ifdef DEBUG
             call writit (q,im,jm,lm,66)
#endif
          enddo

      return
      end

      subroutine get_ana_data  ( id,ps,u,v,t,q,h,phis,
     .                           im,jm,lm,nymd,nhms,
     .                           imana,jmana,lmana,undef,plevs )
      use MAPL_ConstantsMod
      implicit none
      integer  id,im,jm,lm,nymd,nhms,rc
      integer  imana,jmana,lmana

      real     ps(im,jm)
      real     u(im,jm,lm)
      real     v(im,jm,lm)
      real     t(im,jm,lm)
      real     h(im,jm,lm)
      real     q(im,jm,lm)
      real     phis(im,jm)
      real     t2m(im,jm)
      real     plevs(lm)
      real     slp(im,jm)
      real     tstar(im,jm)

      real, allocatable :: dum2d(:,:)
      real, allocatable :: dum3d(:,:,:)
      real, allocatable :: dumu (:,:,:)
      real, allocatable :: dumv (:,:,:)

      real    undef,kappa,grav,dum,gamma,cp,rgas,factor,gg,a
      integer L,i,j,LM1

      allocate ( dum2d(imana,jmana)       )
      allocate ( dum3d(imana,jmana,lmana) )
      allocate ( dumu (imana,jmana,lmana) )
      allocate ( dumv (imana,jmana,lmana) )

      kappa  = MAPL_KAPPA
      rgas   = MAPL_RGAS
      grav   = MAPL_GRAV
      cp     = MAPL_CP
      gamma  = 6.5e-3
      factor = -1.0 * grav / ( rgas * gamma )
      gg     = gamma / grav

c Read ANA Variables
c ------------------
      call gfio_getvar ( id,'SLP',nymd,nhms,imana,jmana,0,1 ,dum2d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find AI SLP variable'
          call exit(7)
      endif
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum2d,imana,jmana,slp,im,jm,1,undef )
      else
              slp = dum2d
      endif

      call gfio_getvar     ( id,'T2M',nymd,nhms,imana,jmana,0,1 ,dum2d ,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find AI T2M variable'
          call exit(7)
      endif
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum2d,imana,jmana,t2m,im,jm,1,undef )
      else
              t2m = dum2d
      endif

      call gfio_getvar     ( id,'PHIS',nymd,nhms,imana,jmana,0,1 ,dum2d ,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find AI PHIS variable'
          call exit(7)
      endif
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum2d,imana,jmana,phis,im,jm,1,undef )
      else
              phis = dum2d
      endif

      call gfio_getvar ( id,'H',nymd,nhms,imana,jmana,1,lmana,dum3d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find AI Height variable'
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
      call gfio_getvar ( id,'U',nymd,nhms,imana,jmana,1,lmana,dumu,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find AI U-Wind variable'
          call exit(7)
      endif
      call gfio_getvar ( id,'V',nymd,nhms,imana,jmana,1,lmana,dumv,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find AI V-Wind variable'
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
      call gfio_getvar ( id,'T',nymd,nhms,imana,jmana,1,lmana,dum3d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find AI Temperature variable'
          call exit(7)
      endif
      call zflip( dum3d,imana,jmana,lmana )
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum3d,imana,jmana,t,im,jm,lm,undef )
      else
              t = dum3d
      endif

c Specific Humidity
c -----------------
      call gfio_getvar ( id,'QV',nymd,nhms,imana,jmana,1,lmana,dum3d,rc )
      if( rc.ne.0 ) then
          print *, 'Could not find AI specific humidity variable'
          call exit(7)
      endif
      call zflip( dum3d,imana,jmana,lmana )
      if( im.ne.imana .or. jm.ne.jmana ) then
              call hinterp ( dum3d,imana,jmana,q,im,jm,lm,undef )
      else
              q = dum3d
      endif
      q = max( q,0.0 )

c Compute PS
c ------------
      do j=1,jm
      do i=1,im
         L=1
         do while( L.lt.lm .and. h(i,j,L+1).ne.undef)
         L=L+1
         enddo
         LM1 = L-1
        !a = ( h(i,j,l) - phis(i,j)/grav ) / ( h(i,j,l) - h(i,j,LM1) )
        !ps(i,j) = 100.*((plevs(L))**(1-a))*((plevs(LM1))**(a))
         tstar(i,j) = t2m(i,j)*(1+0.61*q(i,j,L))
         ps(i,j) = slp(i,j) * ( 1.0+gg*phis(i,j)/tstar(i,j) )**factor
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

      subroutine usage()
      print *, "Usage:  "
      print *
      print *, " AI_prs2eta.x  -AI    AI.data "
      print *, "              [-im    im]"
      print *, "              [-jm    jm]"
      print *, "              [-tag   tag]"
      print *
      print *, "where:"
      print *
      print *, "  -AI       AI.data: Filename of AI Pressure-Level analysis data"
      print *, "  -im            im:  Optional Zonal      Dimenstion for Output (Default: IM from File)"
      print *, "  -jm            jm:  Optional Meridional Dimenstion for Output (Default: JM from File)"
      print *, "  -tag          tag:  Optional Prefix tag            for Output (Default: AI_prs2eta)"
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

      integer L0(im,jm)
      real  qprs(im,jm)
      real  q   (im,jm,lm)
      real logpl(im,jm,lm)

      real  undef
      real  logp,temp

c Initialize to Surface Value
c ---------------------------
      do j=1,jm
      do i=1,im
         L0(i,j)=1
         do while( L0(i,j).le.lm .and. q(i,j,L0(i,j)).ne.undef)
         L0(i,j)=L0(i,j)+1
         enddo
         qprs(i,j) = undef
      enddo
      enddo

c Interpolate to Pressure Between Model Levels
c --------------------------------------------
      do L=1,lm-1
      if( all( logpl(:,:,L  )>logp ) ) exit
      if( all( logpl(:,:,L+1)<logp ) ) cycle

         do j=1,jm
         do i=1,im
         if( logp.le.logpl(i,j,L+1) .and. logp.ge.logpl(i,j,L) ) then
         temp      = ( logpl(i,j,L)-logp ) / ( logpl(i,j,L)-logpl(i,j,L+1) )

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
      if( logp.le.logpl(i,j,1 ) ) qprs(i,j) = q(i,j,1 )
      if( logp.ge.logpl(i,j,lm) ) qprs(i,j) = q(i,j,lm)
      if(  qprs(i,j).eq.undef   ) qprs(i,j) = q(i,j,L0(i,j)-1)
      enddo
      enddo

      return
      end subroutine sigtopl

      subroutine interp3 ( q1,p1,im,jm,km, q2,p2,kn, ps,undef )
      implicit none

      integer,  intent(in) :: im                ! Longitude dimension
      integer,  intent(in) :: jm                ! Latitude  dimension
      integer,  intent(in) :: km                ! Original vertical dimension
      integer,  intent(in) :: kn                ! Target   vertical dimension
 
      real,     intent(in) ::   undef
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
      pke2(:,:,:) = pe2(:,:,:)**kappa

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
      fname = trim(tag) // 'AI_prs2eta_L' // trim(cLM) // '.' // trim(cnymd) // '_' // trim(cnhms) // 'z.' // trim(ext)
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
      title    = 'AI_PRS2ETA Data'
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
