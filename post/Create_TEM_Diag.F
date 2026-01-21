      program  main
      use tem_mod, only: TEM
      implicit none

! **********************************************************************
! **********************************************************************
! ****                                                              ****
! ****  Program to create TEM_Diag data from Monthly Mean Prog File ****
! ****                                                              ****
! **********************************************************************
! **********************************************************************

      integer  im,jm,lm,nt
      integer  nymd,nhms

      integer       mem_unit,loc,ios
      logical       lopen
      character*256 cbuff1
      character*1   cbuff2(256)
      equivalence ( cbuff1,cbuff2 )
      character*256 expid
      character*1   char

      character*256 filename
      integer       id,nvars,nsecf
      integer       ntime,ngatts,rc,timinc
      real          undef
      integer       i, m, n, TEM_NVARS, nfiles

      character*256  title
      character*256  source
      character*256  contact
      character*256  levunits
      character*256, allocatable ::  vname(:)
      character*256, allocatable :: vtitle(:)
      character*256, allocatable :: vunits(:)

      real,    allocatable :: TEM_VARS(:,:,:,:)
      real,    allocatable ::      lat(:)
      real,    allocatable ::      lon(:)
      real,    allocatable ::      lev(:)
      real,    allocatable ::   vrange(:,:)
      real,    allocatable ::   prange(:,:)
      integer, allocatable ::   yymmdd(:)
      integer, allocatable ::   hhmmss(:)
      integer, allocatable ::    kmvar(:)

      integer nargs, iargc
      character*256, allocatable ::   arg(:)
      character*256, allocatable :: fname(:)

! **********************************************************************

          nargs = iargc()
      if( nargs.eq.0 ) then
          call usage()
      else
          allocate ( arg(nargs) )
          do n=1,nargs
          call getarg(n,arg(n))
          enddo
      endif

! **********************************************************************
! ****                Store INPUT into variables                    ****
! **********************************************************************

      expid = 'NULL'

      do n=1,nargs
      call getarg(n,arg(n))
        if( trim(arg(n)).eq.'-expid' ) expid = arg(n+1)

        if( trim(arg(n)).eq.'-files' ) then
                 nfiles = 1
                 read(arg(n+nfiles),fmt='(a1)') char
                 do while (char.ne.'-' .and. n+nfiles.ne.nargs )
                 nfiles = nfiles+1
                 read(arg(n+nfiles),fmt='(a1)') char
                 enddo
                 if( char.eq.'-' ) nfiles = nfiles-1
                 allocate  ( fname(nfiles) )
                 do m=1,nfiles
                 fname(m) = arg(n+m)
                 enddo
        endif

      enddo

! **********************************************************************
! ****              Extract EXPID from Filename if needed           ****
! **********************************************************************

      filename = fname(1)

      if( trim(expid).eq.'NULL' ) then
          cbuff1 = '/usr/bin/basename ' // trim(filename) // ' > basename.output'
          call execute_command_line ( trim(cbuff1) )

                 i = 1
          mem_unit = 0
          do while( mem_unit == 0 )
             if( i /= 5 .and. i /= 6 .and. i <= 99 ) then
                 inquire( unit = i, opened = lopen, iostat = ios )
                 if( ios == 0 ) then
                     if( .not. lopen ) mem_unit = i
                 endif
             endif
             i = i+1
          enddo

          open (mem_unit,file='basename.output',form='formatted',access='sequential')
          read (mem_unit,'(a)') cbuff1
          close(mem_unit)

                   expid = ''
                     loc = 1
                    char = cbuff2(loc)
          do while (char.ne.'.')
                   expid = trim(expid) // char
                     loc = loc+1
                    char = cbuff2(loc)
          enddo
      endif

! **********************************************************************
! ****                  Read Monthly Mean Prog File(s)              ****
! **********************************************************************

      do n=1,nfiles

      filename = fname(n)

      call gfio_open       ( trim(filename),1,id,rc )
      call gfio_diminquire ( id,im,jm,lm,ntime,nvars,ngatts,rc )

      TEM_NVARS = 7

      allocate ( lon(im) )
      allocate ( lat(jm) )
      allocate ( lev(lm) )
      allocate ( yymmdd(ntime) )
      allocate ( hhmmss(ntime) )
      allocate (  vname(nvars) )
      allocate ( vtitle(nvars) )
      allocate ( vunits(nvars) )
      allocate (  kmvar(nvars) )
      allocate ( vrange(2,nvars) )
      allocate ( prange(2,nvars) )

      call gfio_inquire ( id,im,jm,lm,ntime,nvars,
     .                    title,source,contact,undef,
     .                    lon,lat,lev,levunits,
     .                    yymmdd,hhmmss,timinc,
     .                    vname,vtitle,vunits,kmvar,
     .                    vrange,prange,rc )

      nymd = yymmdd(1)
      nhms = hhmmss(1)

      allocate ( TEM_VARS(im,jm,lm,TEM_NVARS) )

      call gfio_getvar ( id,'U'    ,nymd,nhms,im,jm,1,lm,TEM_VARS(1,1,1,1),rc )
      call gfio_getvar ( id,'V'    ,nymd,nhms,im,jm,1,lm,TEM_VARS(1,1,1,2),rc )
      call gfio_getvar ( id,'T'    ,nymd,nhms,im,jm,1,lm,TEM_VARS(1,1,1,3),rc )
      call gfio_getvar ( id,'OMEGA',nymd,nhms,im,jm,1,lm,TEM_VARS(1,1,1,4),rc )
      call gfio_getvar ( id,'USVS' ,nymd,nhms,im,jm,1,lm,TEM_VARS(1,1,1,5),rc )
      call gfio_getvar ( id,'USWS' ,nymd,nhms,im,jm,1,lm,TEM_VARS(1,1,1,6),rc )
      call gfio_getvar ( id,'VSTS' ,nymd,nhms,im,jm,1,lm,TEM_VARS(1,1,1,7),rc )

      call gfio_close ( id,rc )

! **********************************************************************
! ****                     Create TEM_Diag File                     ****
! **********************************************************************

      call TEM( TEM_VARS,im,jm,lm,TEM_NVARS,expid,lon,lat,lev,levunits,nymd,nhms,timinc,undef )

      deallocate ( lon )
      deallocate ( lat )
      deallocate ( lev )
      deallocate ( yymmdd )
      deallocate ( hhmmss )
      deallocate (  vname )
      deallocate ( vtitle )
      deallocate ( vunits )
      deallocate (  kmvar )
      deallocate ( vrange )
      deallocate ( prange )
      deallocate ( TEM_VARS )

      enddo

! **********************************************************************

      stop
      end

      subroutine usage()
      write(6,100)
 100  format(  "Usage:  "                                                                                           ,/
     .                                                                                                              ,/
     .         " Create_TEM_Diag.x -files filename(s)"                                                              ,/
     .         "                  [-expid expid]"                                                                   ,/
     .                                                                                                              ,/
     .         "where:"                                                                                             ,/
     .                                                                                                              ,/
     .         "  filename(s):  Filename(s) containing pressure level data for U,V,T,OMEGA,USVS,USWS,VSTS"          ,/
     .         "        expid:  Optional EXPID to use for output filename (Default: 1st node of input filename[1]"  ,/
     .         )
      call exit(7)
      end subroutine usage

