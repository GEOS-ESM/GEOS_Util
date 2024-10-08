function plot_season (args)

    talats = subwrd(args,1)
    output = subwrd(args,2)
    M2FLAG = subwrd(args,3)

'run getenv NSMOOTH'
            nsmooth = result
'run getenv SEASON'
            season = result
'run getenv TIME'
            time = result
'run getenv MASKFILE'
            maskfile = result

'run getenv BEGDATE'
            begdate = result
'run getenv ENDDATE'
            enddate = result

* Test to see if Source Experiment is an ANALYSIS
* -----------------------------------------------
'run getenv "ANALYSIS"'
             analysis = result


'q gxout'
   gxout = sublin(result,4)
   gxout = subwrd(gxout,6)

* Choose "indv" or "avrg" for Turn-Around Lats (talats) based on Turn-Around Functions (tafunc) "wstr" or "psi"
* -------------------------------------------------------------------------------------------------------------
    if( talats = avrg ) ; talatsz = 'Averaged'        ; endif
    if( talats = indv ) ; talatsz = 'Individual'      ; endif
    if( talats = hard ) ; talatsz = 'Hard-Wired'      ; endif
    if( talats = levl ) ; talatsz = 'Level-Dependent' ; endif

    tafunc = psi
    tafunc = wstr

    type = mean
    type = eddy
    type = star

    levmin = 20
    levmax = 100

*   Set Default Turn-Around Latitudes
*   ---------------------------------
    hardmin = -999
    hardmax = -999

*   Set Turn-Around Latitudes to User-Defined Values
*   ------------------------------------------------
    if( talats = hard )
       hardmin = -90.00
       hardmax =  90.00
       hardmin = -47.34
       hardmax =  27.74
    endif

* ------------------------------------

'numargs  'args
 numargs = result

'getinfo numfiles'
         numfiles = result
'getinfo ydim'
          RSLV = (result-1)/2
         CRSLV = C''RSLV


    tags = ''
    exps = ''
if( numargs=2 )
    n = 1
    while( n<=numfiles )
    pltfile.n = n
    n = n + 1
    endwhile
endif

if( numargs>2 & M2FLAG != 'NOM2' )
    n = 1
    while( n<=numargs+2 )
          index = subwrd(args,n+2)
      if( index=a ) ; pltfile.n =  1 ; endif
      if( index=b ) ; pltfile.n =  2 ; endif
      if( index=c ) ; pltfile.n =  3 ; endif
      if( index=d ) ; pltfile.n =  4 ; endif
      if( index=e ) ; pltfile.n =  5 ; endif
      if( index=f ) ; pltfile.n =  6 ; endif
      if( index=g ) ; pltfile.n =  7 ; endif
      if( index=h ) ; pltfile.n =  8 ; endif
      if( index=i ) ; pltfile.n =  9 ; endif
      if( index=j ) ; pltfile.n = 10 ; endif
      if( index=k ) ; pltfile.n = 11 ; endif
      if( index=l ) ; pltfile.n = 12 ; endif
      if( index=m ) ; pltfile.n = 13 ; endif
      if( index=n ) ; pltfile.n = 14 ; endif
      if( index=o ) ; pltfile.n = 15 ; endif
    say 'n = 'n'  index = 'index'  pltfile = 'pltfile.n
    n = n + 1
    endwhile
endif

if( numargs>2 & M2FLAG = 'NOM2' )
    n = 1
    while( n<=numargs+3 )
          index = subwrd(args,n+3)
      if( index=a ) ; pltfile.n =  1 ; endif
      if( index=b ) ; pltfile.n =  2 ; endif
      if( index=c ) ; pltfile.n =  3 ; endif
      if( index=d ) ; pltfile.n =  4 ; endif
      if( index=e ) ; pltfile.n =  5 ; endif
      if( index=f ) ; pltfile.n =  6 ; endif
      if( index=g ) ; pltfile.n =  7 ; endif
      if( index=h ) ; pltfile.n =  8 ; endif
      if( index=i ) ; pltfile.n =  9 ; endif
      if( index=j ) ; pltfile.n = 10 ; endif
      if( index=k ) ; pltfile.n = 11 ; endif
      if( index=l ) ; pltfile.n = 12 ; endif
      if( index=m ) ; pltfile.n = 13 ; endif
      if( index=n ) ; pltfile.n = 14 ; endif
      if( index=o ) ; pltfile.n = 15 ; endif
    say 'n = 'n'  index = 'index'  pltfile = 'pltfile.n
    n = n + 1
    endwhile
endif

* ------------------------------------------------------------------------
* ------------------------------------------------------------------------
*                          Get Experiment Names
* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

* Loop over Experiment Datasets to get Experiment IDs
* ---------------------------------------------------
say ''
'getpwd'
    pwd = result

'getnumrc 'pwd
     rcinfo = result
     numrc  = subwrd( rcinfo,1 )
       num  = 1
       cnt  = 0
while( num <= numrc )
        loc = num + 1
     rcfile = subwrd( rcinfo,loc )
     say 'num = 'num'  rcfile = 'rcfile

   '!grep filename 'rcfile' | cut -d'"\' -f2 > CTLFILE.txt"
    'run getenv CTLFILE '
                CTLFILE.num = result

   '!basename 'rcfile' > BASENAME.txt'
    'run getenv BASENAME'
                basename = result
     length   = strlen(basename) - 3
     say 'original length = 'length
    '!echo 'basename' | cut -b14-'length' > CMPID.txt'
    'run getenv CMPID '
                CMPID.num = result

   say '    CMPID #'num' = 'CMPID.num
   say '  CTLFILE #'num' = 'CTLFILE.num

           '!remove TEM_NAME.txt.'
           '!basename 'CTLFILE.num' | cut -d. -f2 > TEM_NAME.txt'
       say 'run getenv "TEM_NAME"'
           'run getenv "TEM_NAME"'
                        TEM_NAME.num = result
            say 'TEM_Collection = 'TEM_NAME.num

*       Generate and Use WSTAR files stored in OUTPUT directory
*       -------------------------------------------------------
          FILE.num = 'WSTAR_'talats'.'CMPID.num
          LOCATION = '../'
          LOCATION = ''

   num = num + 1
endwhile

    axmax = -1e15
    axmin =  1e15

* ------------------------------------------------------------------------
* ------------------------------------------------------------------------
*      Loop over ALL experiments to Compute Latitudinally-Averged Data
* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

n = 1
while( n<=numfiles )

       'set dfile 'n
        if( (analysis = true) | ( (analysis != true) & (CMPID.n != 'MERRA-2') ) )

       'run getdates'
       'getinfo tmin'
                tmin = result
       'getinfo tmax'
                tmax = result
                tdim = tmax - tmin + 1

       'set lev 'levmax
       'getinfo zpos'
                zmin = result
       'set lev 'levmin
       'getinfo zpos'
                zmax = result
                zdim = zmax - zmin + 1
        say 'File: 'n'  zmax: 'zmax'  zmin: 'zmin'  zdim: 'zdim

        levels = ''
               z  = zmin
        while( z <= zmax )
          'set z '  z
          'getinfo level'
                   level = result
           levels = levels' 'level
                z = z+1
        endwhile
        say 'Levels: 'levels
        say ' '

* ------------------------------------------------------------------------
*   Compute w* for Level- and Time- Independentment Turn-Around Latitudes
* ------------------------------------------------------------------------

       if( talats=indv | talats=avrg | talats=hard )

       'set lev 'levmax' 'levmin
       'set y 1'

       if( hardmin != -999 ) ; latmin = latmax  ; endif
       if( hardmax != -999 ) ; latmax = hardmax ; endif

       if(talats=avrg)
          if(tafunc=wstr)
            'run getenv wstr'season'latmx'  ; latmax = result
            'run getenv wstr'season'latmn'  ; latmin = result
          endif
          if(tafunc=psi)
            'run getenv  psi'season'latmx'  ; latmax = result
            'run getenv  psi'season'latmn'  ; latmin = result
          endif
         'getint 'latmax*100
                  latmax = result/100
         'getint 'latmin*100
                  latmin = result/100
       endif

       if(talats=indv)
          if(tafunc=wstr)
            'run getenv wstr'season'latmx'n ; latmax = result
            'run getenv wstr'season'latmn'n ; latmin = result
          endif
          if(tafunc=psi)
            'run getenv  psi'season'latmx'n ; latmax = result
            'run getenv  psi'season'latmn'n ; latmin = result
          endif
         'getint 'latmax*100
                  latmax = result/100
         'getint 'latmin*100
                  latmin = result/100
       endif

 say  'define dumdum'n' = ave(w'type''n''season''time',lat='latmin',lat='latmax')*1000'
      'define dumdum'n' = ave(w'type''n''season''time',lat='latmin',lat='latmax')*1000'
      'minmax dumdum'n
         dmax = subwrd(result,1)
         dmin = subwrd(result,2)
       say 'talats: 'talats'  File: 'n'  latmin: 'latmin'  latmax: 'latmax'  wstar_min = 'dmin' wstar_max = 'dmax
       if(dmax > axmax ) ; axmax = dmax ; endif
       if(dmin < axmin ) ; axmin = dmin ; endif
      'q dims'
       say result
*      pause

*      End if( talats=indv | talats=avrg | talats=hard ) test
*      ------------------------------------------------------
       endif

* ------------------------------------------------------------------------
*    Compute w* for Level- and Time- Dependentment Turn-Around Latitudes
* ------------------------------------------------------------------------

   if( talats=levl )

*      Create CTL File for Each Experiment
*      -----------------------------------
       ioflag = 1-sublin( read(LOCATION''FILE.n'.ctl'),1 )
       say 'ioflag for 'LOCATION''FILE.n'.ctl: 'ioflag
*      pause
       if(  ioflag = 0 )

      '!remove 'LOCATION''FILE.n'.ctl'
      '!touch  'LOCATION''FILE.n'.ctl'
      '!echo dset ^'FILE.n'.data                        >> 'LOCATION''FILE.n'.ctl'
      '!echo title WSTAR                                >> 'LOCATION''FILE.n'.ctl'
      '!echo undef 1e15                                 >> 'LOCATION''FILE.n'.ctl'
      '!echo xdef  1     linear -180 1                  >> 'LOCATION''FILE.n'.ctl'
      '!echo ydef  1     linear  -90 1                  >> 'LOCATION''FILE.n'.ctl'
      '!echo zdef 'zdim' levels 'levels'                >> 'LOCATION''FILE.n'.ctl'
      '!echo tdef 'tdim' linear 'begdate'    1mo        >> 'LOCATION''FILE.n'.ctl'
      '!echo vars  3                                    >> 'LOCATION''FILE.n'.ctl'
      '!echo minlats  'zdim' 0 minlats                  >> 'LOCATION''FILE.n'.ctl'
      '!echo maxlats  'zdim' 0 maxlats                  >> 'LOCATION''FILE.n'.ctl'
      '!echo wstrlats 'zdim' 0 wstar                    >> 'LOCATION''FILE.n'.ctl'
      '!echo endvars                                    >> 'LOCATION''FILE.n'.ctl'

*    Loop over Time to create Time-Dependent Level Data
*    --------------------------------------------------
            t = tmin
     while( t<= tmax )
       'set t 't
         'getinfo date'
                  date = result
         say 'Date: 'date

*      Loop over Levels
*      ----------------
              z  = zmin
       while( z <= zmax )
         'set z ' z
         'set x 1'
         'sety'
         'getinfo level'
                  level = result

         dummy = get_lats( 'wstar'n )
         latmin.t.z = subwrd(dummy,1)
         latmax.t.z = subwrd(dummy,2)

*      Compute Transport Poleward of Turn-Around Latitudes
*      ---------------------------------------------------
*         if( latmin.t.z != 1e15 & latmax.t.z != 1e15 )
*             latmin.t.z  = latmax.t.z
*             latmax.t.z  = 90
*         endif

         'd 'latmin.t.z
          a = subwrd(result,4)
         'd 'latmax.t.z
          b = subwrd(result,4)

*      Compute w* Averaged between Turn-Around Latitudes
*      -------------------------------------------------
          if( a = 1e15 | b = 1e15 )
              dumw.t.z = 1e15
          else
*         say 'd ave(wstar'n',lat='a',lat='b')*1000'
              'd ave(wstar'n',lat='a',lat='b')*1000'
               result1  = sublin(result,2)
               dumw.t.z = subwrd(result1,4)
          endif

         say '  Level: 'level'  Lats: 'latmin.t.z' 'latmax.t.z' wstar: 'dumw.t.z

*      End Level Loop
*      --------------
       z = z+1
       endwhile

*    End Time Loop
*    -------------
     t = t+1
     endwhile

* ------------------------------------------------------------------------
*                    Create DATA File for Each Experiment
* ------------------------------------------------------------------------

    'set gxout fwrite'
    'set fwrite 'LOCATION''FILE.n'.data'

            t = tmin
     while( t<= tmax )
       
       'set t 't
       'set y 1'
              z  = zmin
       while( z <= zmax )
         'set z 'z
         'd 'latmin.t.z
          z = z+1
       endwhile
              z  = zmin
       while( z <= zmax )
         'set z 'z
         'd 'latmax.t.z
          z = z+1
       endwhile
              z  = zmin
       while( z <= zmax )
         'set z 'z
         'd 'dumw.t.z
          z = z+1
       endwhile
     t = t+1
     endwhile

    'disable fwrite'
    'set gxout 'gxout

*    End IOFLAG Test
*    ---------------
     endif

* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

* Note: Scaling will be based on ALL experiments
* ----------------------------------------------
    'open 'LOCATION''FILE.n'.ctl'
    'getinfo numfiles'
             dumfile = result
    'set dfile 'dumfile
    'set x 1'
    'set y 1'
    'setz   '
    'run getdates'
*   'run setenv DO_STD TRUE'
    'seasonal wstrlats 'n

    'minmax wstrlats'season''n
       dmax = subwrd(result,1)
       dmin = subwrd(result,2)
       say 'talats: 'talats'  File: 'n'  wstar_min = 'dmin' wstar_max = 'dmax
       if(dmax > axmax ) ; axmax = dmax ; endif
       if(dmin < axmin ) ; axmin = dmin ; endif

    'close 'dumfile

* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

*  End if( talats=levl ) test
*  --------------------------
   endif

* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

*  End if( ANALYSIS ) test
*  -----------------------
   endif

*  End File Loop
*  -------------
   n = n + 1
endwhile


* ------------------------------------------------------------------------
* ------------------------------------------------------------------------
*             Plot Latitudinally-Averaged WSTAR Vertical Profiles
* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

'set vpage off'
'set parea off'

'set xlopts 1 4 0.10'
'set ylopts 1 4 0.10'
'set string 1 c 5'
'set strsiz 0.07'

'set vpage 0 11 0 8.5'
'set parea 1.0 7 0.75 8'
'set grads off'
'set xlab on'

  say 'Initial  axmin: 'axmin'  axmax: 'axmax
  delax = ( axmax - axmin )/15
  axmin =   axmin - delax
  axmax =   axmax + delax
  say 'Adjusted axmin: 'axmin'  axmax: 'axmax

  if( season = 'DJF' ) 
      if( axmin >= 0.24 )
          axmin  = 0.23999
      endif
      if( axmax <= 0.48 )
          axmax  = 0.48001
      endif
  endif
  if( season = 'JJA' ) 
      if( axmin >= 0.14 )
          axmin  = 0.13999
      endif
      if( axmax <= 0.32 )
          axmax  = 0.32001
      endif
  endif

  say 'Final   axmin: 'axmin'  axmax: 'axmax
  say ' '
*         axmin  = 0.21509
*         axmax  = 0.44501
 'set  axlim  'axmin' 'axmax

   id.1  = 'a'
   id.2  = 'b'
   id.3  = 'c'
   id.4  = 'd'
   id.5  = 'e'
   id.6  = 'f'
   id.7  = 'g'
   id.8  = 'h'
   id.9  = 'i'
   id.10 = 'j'
   id.11 = 'k'
   id.12 = 'l'
   id.13 = 'm'
   id.14 = 'n'
   id.15 = 'o'

color.3  = 28
color.4  = 33
color.5  = 35
color.6  = 38
color.7  = 43
color.8  = 45
color.9  = 48
color.10 = 53
color.11 = 55
color.12 = 58
color.13 = 63
color.14 = 65
color.15 = 68

 color.3  = 27
 color.6  = 39
 color.7  = 58
 color.8  = 42
 color.9  = 44
 color.10 = 46
 color.11 = 55
 color.12 = 58
 color.13 = 63
 color.14 = 65
 color.15 = 68

    color.1  = 23
    color.2  = 25
    color.3  = 28
    color.4  = 43
    color.5  = 45
    color.6  = 48
    color.7  = 53
    color.8  = 55
    color.9  = 58
    color.10 = 33
    color.11 = 35
    color.12 = 38
    color.13 = 63
    color.14 = 65
    color.15 = 68

    color.1  = 2
    color.2  = 3
    color.3  = 4
    color.4  = 5
    color.5  = 8
    color.6  = 7
    color.7  = 12

*   color.1  = 4
*   color.2  = 5
*   color.3  = 3
*   color.4  = 1  
*   color.5  = 1
*   color.6  = 3
*   color.7  = 1

* Plot Latitudinally-Averaged WSTAR for Selected Input Files
* ----------------------------------------------------------
n = 1
while( n<=numfiles )
   m = 1
   while( m<=numfiles )
     if( pltfile.m = n )

       'set dfile 'n
        if( (analysis = true) | ( (analysis != true) & (CMPID.n != 'MERRA-2') ) )
       'run getdates'
       'getinfo tmin'
                tmin = result
       'getinfo desc'
                desc.n = result
       '!remove DESC.txt'
       '!echo 'desc.n' | cut -d. -f2 > DESC.txt'
       'run getenv DESC'
                   desc.n = result
        say 'desc.'n' = 'desc.n
       'set lev 'levmax' 'levmin
       'set zlog on'
       'set y 1'
       'set grid on'
       'set t 'tmin
       'set ccolor 'color.n
                   'set cthick 3'
       if( n=1 ) ; 'set cthick 10' ; endif
                   'set cthick 6'
                    k = n - 3 * math_int(n/3) + 1
       'set cstyle 'k
       'set cstyle '1
       'set cmark  0'

*      Plot wstar based on Level-Dependent Turn-Around Latitudes
*      ---------------------------------------------------------
       if( talats=levl )

          'd wstrlats'season''n

*         Add Standard Deviation to selected experiments
*         ----------------------------------------------
*         if( n=4 )
*           'set cstyle 3'
*           'set cthick 1'
*           'set ccolor 1'
*           'd wstrlats'season''n' + wstrlats'season'std'n
*           'set cstyle 3'
*           'set cthick 1'
*           'set ccolor 1'
*           'd wstrlats'season''n' - wstrlats'season'std'n
*         endif

       else

*         Plot wstar based on Level-Independent Turn-Around Latitudes
*         -----------------------------------------------------------
          'd dumdum'n
          'q dims'

       endif

     endif

* ENDIF for ANALYSIS Test
* -----------------------
   endif

   m = m + 1
   endwhile
n = n + 1
endwhile
'draw ylab Pressure (hPa)'

* ------------------------------------------------------------------------
* ------------------------------------------------------------------------
*                 Plot Latitude x Height WSTAR Cross-Sections
* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

if(3>2)
'set vpage off'
'set parea off'
'set vpage 7.2 10.8 1.2 8.5'
'set vpage 7.0 11.0 0.0 8.5'

count = 0
 ymax = 8.55
 ymin = ymax
 ydel = 0.24
 ydif = 0.00

n = 1
while( n<=numfiles )
   m = 1
   while( m<=numfiles )
      if( pltfile.m = n )
        'set dfile 'n
         if( (analysis = true) | ( (analysis != true) & (CMPID.n != 'MERRA-2') ) )

        'set grid off'
        'set xlopts 1 3 0.06'
        'set ylopts 1 3 0.08'

         count = count + 1

         if( count = 1  ) ; i = 1 ; j = 1 ; endif
         if( count = 2  ) ; i = 2 ; j = 1 ; endif
         if( count = 3  ) ; i = 1 ; j = 2 ; endif
         if( count = 4  ) ; i = 2 ; j = 2 ; endif
         if( count = 5  ) ; i = 1 ; j = 3 ; endif
         if( count = 6  ) ; i = 2 ; j = 3 ; endif
         if( count = 7  ) ; i = 1 ; j = 4 ; endif
         if( count = 8  ) ; i = 2 ; j = 4 ; endif
         if( count = 9  ) ; i = 1 ; j = 5 ; endif
         if( count = 10 ) ; i = 2 ; j = 5 ; endif
         if( count = 11 ) ; i = 1 ; j = 6 ; endif
         if( count = 12 ) ; i = 2 ; j = 6 ; endif
         if( count = 13 ) ; i = 2 ; j = 6 ; endif
         if( count = 14 ) ; i = 2 ; j = 6 ; endif

        nhalf = count/2
       'getint 'nhalf
         nhalf = result
         nhalf2 = 2 * nhalf
        say 'check, count: 'count' nhalf2: 'nhalf2
        if( nhalf2 = count )
           'parea 'i' 'j' 2 7 -left 0.2 -right 0.5 -top 0.2 -bot 0.1'
        else
           'parea 'i' 'j' 2 7 -left 0.5 -right 0.2 -top 0.2 -bot 0.1'
        endif

            xmid = subwrd(result,1)
            ybot = subwrd(result,2)
            ytop = subwrd(result,3)
            ymid = subwrd(result,4)
            xlft = subwrd(result,5)
            xrgt = subwrd(result,6)

         xlft = xlft - 0.45
         xrgt = xrgt + 0.27
         ytit = ytop + 0.06

        'set grads off'
        'set gxout shaded'
        'sety'
        'set lev 'levmax' 'levmin
        'shades 0.1'

* Smooth possible noise
* ---------------------
 if( nsmooth > 0 )
    'define wstrsmth = smth9( w'type''n''season''time'*1000 )'
     countr = 1
     while( countr < nsmooth )
           'define wstrsmth = smth9( wstrsmth )'
     countr = countr + 1
     endwhile
    'd wstrsmth '
 else
        'd w'type''n''season''time'*1000'
 endif

        'set strsiz 0.10'
        nhalf = count/2
       'getint 'nhalf
         nhalf = result
         nhalf2 = 2 * nhalf
        say 'check, count: 'count' nhalf2: 'nhalf2
        if( nhalf2 = count )
           'set string 1 r 8'
           'draw string 'xrgt' 'ymid' ('id.n')'
        else
           'set string 1 l 8'
           'draw string 'xlft' 'ymid' ('id.n')'
        endif
           'set string 1 c 4'

 if ( talats=indv | talats=avrg | talats=hard )
       if(talats=indv)
          if(tafunc=wstr)
            'run getenv wstr'season'latmx'n ; latmax = result
            'run getenv wstr'season'latmn'n ; latmin = result
          endif
          if(tafunc=psi)
            'run getenv  psi'season'latmx'n ; latmax = result
            'run getenv  psi'season'latmn'n ; latmin = result
          endif
       endif

       if(talats=avrg)
          if(tafunc=wstr)
            'run getenv wstr'season'latmx'  ; latmax = result
            'run getenv wstr'season'latmn'  ; latmin = result
          endif
          if(tafunc=psi)
            'run getenv  psi'season'latmx'  ; latmax = result
            'run getenv  psi'season'latmn'  ; latmin = result
          endif
       endif

       if( hardmin != -999 ) ; latmin = hardmin ; endif
       if( hardmax != -999 ) ; latmax = hardmax ; endif

       'getint 'latmax*100
                latmax = result/100
       'getint 'latmin*100
                latmin = result/100

       say 'Turn-Around wstr'n' latmin: 'latmin
       say 'Turn-Around wstr'n' latmax: 'latmax

        'set strsiz 0.055'
        'draw string 'xmid' 'ytit' Turnaround Lats: 'latmin' 'latmax

       'set axlim -90 90'
       'set y 1'
       'set xaxis -90 90 30'
       'set digsiz 0.02'
       'set ccolor 1'
       'set cmark  3'
       'define zlatmin = 'latmin
       'define zlatmax = 'latmax
       'd zlatmin'
       'set ccolor 1'
       'set cmark  3'
       'd zlatmax'
       'set lat -90 90'

 else

       'open 'LOCATION''FILE.n'.ctl'
       'getinfo numfiles'
                newfile = result
       'set dfile 'newfile
       'set axlim -90 90'
       'set xaxis -90 90 30'
       'set x 1'
       'set y 1'
       'set t 1'
       'set lev 'levmax' 'levmin
       'seasonal minlats'
       'seasonal maxlats'
       'set t 1'
       'set digsiz 0.02'
       'set ccolor 1'
       'set cmark  3'
       'd minlats'season
       'set ccolor 1'
       'set cmark  3'
       'd maxlats'season
       'close 'newfile
       'set lat -90 90'

 endif

         ydif = ydif + ydel
         say 'ydif: 'ydif

      endif

* ENDIF for ANALYSIS Test
* -----------------------
   endif

   m = m + 1
   endwhile
n = n + 1
endwhile

 ymax = ybot - 0.2
 ymin = ymax-ydif
 say 'ymin: 'ymin'  ymax: 'ymax
 if( ymin < 0.1 ) ; ymin = 0.1 ; endif
say 'ymin: 'ymin'  ymax: 'ymax

endif


'set vpage off'
'set parea off'
'set string 1 c 6'
'set strsiz 0.14'

if( tafunc = wstr )
      func = 'w*'
else
      func = tafunc
endif

if(type=star)
  'draw string 3.94 8.38 w* (Using 'talatsz' Turn-Around Lats)'
else
  'draw string 3.94 8.38 W_'type' (Using Averaged 'func' Turn-Around Lats)'
endif

'set strsiz 0.10'

'!remove plot_'season'.stack'
'!remove DESC.txt'
'!echo 'count' > plot_'season'.stack'

    n = 1
    while( n<=numfiles )
       m = 1
       while( m<=numfiles )
          if( pltfile.m = n )
              'set dfile 'n
              if( (analysis = true) | ( (analysis != true) & (CMPID.n != 'MERRA-2') ) )
              if( numargs>2 ) 
                   index = id.n
                   tags = tags''index
                   if( exps = '' )
                       exps = CMPID.n
                   else
                       exps = exps'.'CMPID.n
                   endif
              endif

             'run getenv BEGDATE'
                         begdate = result
                           bdate = substr(result,6,7)
             'run getenv ENDDATE'
                         enddate = result
                           edate = substr(result,6,7)
              if( maskfile != 'NULL' )
                 'run count.gs "'season'" 'begdate' 'enddate' -field w'type'.'maskfile
                  nseasons = result
              else
                 'run count.gs "'season'" 'begdate' 'enddate
                  nseasons = result
              endif

             'set strsiz 0.12'
             'draw string 3.94 8.15 'bdate' 'edate'  'season' ('nseasons')   'CRSLV

             'getinfo desc'
                      desc.n = result
             '!remove DESC.txt'
             '!echo 'desc.n' | cut -d. -f2 >> DESC.txt'
             'run getenv "DESC"'
                          desc.n = result
                     k = n - 3 * math_int(n/3) + 1
                     k = 1
             '!echo 'k' 6 'color.n' >> plot_'season'.stack'

             '!echo \('id.n'\) ' CMPID.n' >> plot_'season'.stack'
          endif

*     ENDIF for ANALYSIS Test
*     -----------------------
       endif

       m = m + 1
       endwhile
    n = n + 1
    endwhile

* -----------------------------------------------------------------
* Plot Legend (using page settings from Lat_X_Lev contour plots)
* -----------------------------------------------------------------

'set vpage off'
'set parea off'
'set vpage 7.0 10.8 0.0 8.5'
    'parea 'i' 'j' 2 7'

'!echo 7.36   >> plot_'season'.stack'
'!echo 'ymin' >> plot_'season'.stack'
'!echo 10.8   >> plot_'season'.stack'
'!echo 'ymax' >> plot_'season'.stack'

'lines plot_'season'.stack  1 '12

* -------------------------------------------

'set vpage off'
'set parea off'
'set string 1 c 4'
'set strsiz 0.12'
'draw string 3.717 0.22 (mm/sec)'
'set strsiz 0.14'
'set string 1 c 6 90'
'set string 1 c 6 0'

'set vpage off'
'set parea off'

if( tags = '' )
    filename = 'WSTAR_using_'talatsz'_TALATS.'season
else
*   filename = 'WSTAR_using_'talatsz'_TALATS.'tags'.'season
    filename = 'WSTAR_using_'talatsz'_TALATS.'exps'.'season
endif

'myprint -name 'output'/'filename

return

* ------------------------------------------------------------------------
* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

function get_lats( wstr )

* say 'inside get_lats, wstr = 'wstr
* Find Latitudes of Zero Line Crossings for wstr from each individual file
* ------------------------------------------------------------------------
foundS  =  FALSE
foundN  =  FALSE
wstrlatmax = 1e15
wstrlatmin = 1e15

* Create Smoothed Version of Monthly w* for Turn-Around Latitude Calculation
* --------------------------------------------------------------------------
'define wstrsmth = smth9( 'wstr' )'
 countr = 1
 while( countr < 20 )
       'define wstrsmth = smth9( wstrsmth )'
 countr = countr + 1
 endwhile

* --------------------------------------------------------------------------
latendS = -5
latbegS = -60

'set lat 'latbegS
'getinfo ypos'
         ybeg = result
'set lat 'latendS
'getinfo ypos'
         yend = result

lat1 = latbegS
'set y 'ybeg
'd wstrsmth'
   val1 = subwrd(result,4)
       y = ybeg+1
while( y<= yend )
   'set y 'y
   'getinfo lat'
            lat2 = result
    'd wstrsmth'
      val2 = subwrd(result,4)
*  say 'lat1: 'lat1'  lat2: 'lat2'  val1: 'val1'  val2: 'val2'  val1*val2: 'val1*val2
*  pause
     if( val1*val2 <= 0 )
           foundS = TRUE
           if( val1=val2 )
               wstrlatmin = lat1
           else
               wstrlatmin = lat1 - val1*( lat1-lat2 )/( val1-val2 )
           endif
                    y = yend + 1
     else
       val1 = val2
       lat1 = lat2
     endif
   y = y + 1
endwhile

* --------------------------------------------------------------------------
latbegN =  60
latendN =  5

'set lat 'latbegN
'getinfo ypos'
         ybeg = result
'set lat 'latendN
'getinfo ypos'
         yend = result
lat1 = latbegN
'set y 'ybeg
'd wstrsmth'
   val1 = subwrd(result,4)
       y = ybeg-1
while( y>= yend )
   'set y 'y
   'getinfo lat'
            lat2 = result
   'd wstrsmth'
      val2 = subwrd(result,4)
*  say 'lat1: 'lat1'  lat2: 'lat2'  val1: 'val1'  val2: 'val2'  val1*val2: 'val1*val2
*  pause
     if( val1*val2 <= 0 )
           foundN = TRUE
           if( val1=val2 )
               wstrlatmax = lat1
           else
               wstrlatmax = lat1 - val1*( lat1-lat2 )/( val1-val2 )
           endif
                    y = yend - 1
     else
       val1 = val2
       lat1 = lat2
     endif
   y = y - 1
endwhile

return wstrlatmin' 'wstrlatmax' 'foundS' 'foundN
