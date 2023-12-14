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

'set xlab on'


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

'set vpage off'
'set parea off'

'set xlopts 1 4 0.10'
'set ylopts 1 4 0.10'
'set string 1 c 5'
'set strsiz 0.07'

'set vpage 0 11 0 8.5'
'set parea 1.0 7 0.75 8'
'set grads off'
axmax = -1e15
axmin =  1e15
n = 1
while( n<=numfiles )

* Note: Scaling will be based on ALL experiments
* ----------------------------------------------
*  m = 1
*  while( m<=numfiles )
*    if( pltfile.m = n )

       'set dfile 'n
       'set lev 'levmax' 'levmin
       'set y 1'

 if( talats=indv | talats=avrg | talats=hard )

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

        say 'LATMIN: 'latmin
        say 'LATMAX: 'latmax

       'getint 'latmax*100
                latmax = result/100
       'getint 'latmin*100
                latmin = result/100

       say 'Turn-Around wstr'n' latmin: 'latmin
       say 'Turn-Around wstr'n' latmax: 'latmax

       'define dumdum = ave(w'type''season''time''n',lat='latmin',lat='latmax')*1000'
       'minmax dumdum'
          dmax = subwrd(result,1)
          dmin = subwrd(result,2)
       say 'File: 'n'  min = 'dmin' max = 'dmax
       if(dmax > axmax ) ; axmax = dmax ; endif
       if(dmin < axmin ) ; axmin = dmin ; endif

 else

       'q gxout'
          gxout = sublin(result,4)
          gxout = subwrd(gxout,6)
        levels = ''
       'set lev 'levmax
       'getinfo undef'
                undef = result
       'getinfo zpos'
                zmin = result
       'set lev 'levmin
       'getinfo zpos'
                zmax = result
                zdim = zmax - zmin + 1
        say 'File: 'n'  zmax: 'zmax'  zmin: 'zmin'  zdim: 'zdim

            ptot = 0
       latminave = 0
       latmaxave = 0
              z  = zmin
       while( z <= zmax )
                'set z ' z
        'getinfo level'
                 level = result

                 zm1 = z-1
         'set z 'zm1
         'getinfo level'
                  levm1 = result
                  delph = (levm1 - level)/2
         zp1 = z+1
         'set z 'zp1
         'getinfo level'
                  levp1 = result
                  delp  = delph + (level - levp1)/2

         'set z 'z
         'set x 1'
         'sety'
         'getinfo level'
                  level = result
         levels = levels' 'level
*        Find Latitudes of Zero Line Crossings for wstar from each experiment for each level
*        -----------------------------------------------------------------------------------
         dummy    = get_lats( 'w'type''season''time''n )
         latmin.z = subwrd(dummy,1)
         latmax.z = subwrd(dummy,2)
         foundS   = subwrd(dummy,3)
         foundN   = subwrd(dummy,4)
         'set x 1'
         'set y 1'
         if( foundS = TRUE & foundN = TRUE )
            'define dumdum'z' = ave(w'type''season''time''n',lat='latmin.z',lat='latmax.z')*1000'
            'd      dumdum'z
             dumdum.z = subwrd(result,4)
             say 'latmina: 'latminave'  latmin.z: 'latmin.z'  delp: 'delp'  dumdum.z: 'dumdum.z
             latminave = latminave + latmin.z * delp
             latmaxave = latmaxave + latmax.z * delp
                 ptot  = ptot      +            delp
         else
             dumdum.z = undef
         endif
         say 'File: 'n'  z: 'z'  Level: 'level'  LatMin: 'latmin.z'  LatMax: 'latmax.z'  FoundS: 'foundS'   FoundN: 'foundN'  wstar: 'dumdum.z
         z = z+1
       endwhile
       if( ptot != 0 )
           latminave = latminave / ptot
           latmaxave = latmaxave / ptot
       else
           latminave = undef
           latmaxave = undef
       endif

*      Write ctl file
*      --------------
      '!remove FILE_'n'.ctl'
      '!touch  FILE_'n'.ctl'
      '!echo dset ^FILE_'n'.data                        >> FILE_'n'.ctl'
      '!echo title WSTAR                                >> FILE_'n'.ctl'
      '!echo undef 1e15                                 >> FILE_'n'.ctl'
      '!echo xdef  1     linear  0 1                    >> FILE_'n'.ctl'
      '!echo ydef  1     linear  0 1 1                  >> FILE_'n'.ctl'
      '!echo zdef 'zdim' levels 'levels'                >> FILE_'n'.ctl'
      '!echo tdef  1     linear 'begdate' 1mo           >> FILE_'n'.ctl'
      '!echo vars  5                                    >> FILE_'n'.ctl'
      '!echo minlata  1     0 average minlats           >> FILE_'n'.ctl'
      '!echo maxlata  1     0 average maxlats           >> FILE_'n'.ctl'
      '!echo minlats 'zdim' 0 minlats                   >> FILE_'n'.ctl'
      '!echo maxlats 'zdim' 0 maxlats                   >> FILE_'n'.ctl'
      '!echo wstar   'zdim' 0 wstar                     >> FILE_'n'.ctl'
      '!echo endvars                                    >> FILE_'n'.ctl'

      'set gxout fwrite'
      'set fwrite FILE_'n'.data'
         'd 'latminave
         'd 'latmaxave
              z  = zmin
       while( z <= zmax )
         'set z 'z
         'd 'latmin.z
          z = z+1
       endwhile
              z  = zmin
       while( z <= zmax )
         'set z 'z
         'd 'latmax.z
          z = z+1
       endwhile
              z  = zmin
       while( z <= zmax )
         'set z 'z
         'd 'dumdum.z
          z = z+1
       endwhile

      'disable fwrite'
      'set gxout 'gxout

      'open FILE_'n'.ctl'
       newfile = numfiles + 1
      'set dfile 'newfile
      'set x 1'
      'set y 1'
      'set t 1'
      'setz'
      'define wstarz'n' = wstar'

       'minmax wstarz'n
          dmax = subwrd(result,1)
          dmin = subwrd(result,2)
       say 'File: 'n'  min = 'dmin' max = 'dmax
       if(dmax > axmax ) ; axmax = dmax ; endif
       if(dmin < axmin ) ; axmin = dmin ; endif

      'close 'newfile

 endif

* --------------------------------------------------------------------

        say ' '
       'set lev 'levmax' 'levmin
       'sety'

* Note: Scaling will be based on ALL experiments
* ----------------------------------------------
*    endif
*  m = m + 1
*  endwhile

n = n + 1
endwhile

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

color.1  = 23
color.2  = 25
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

 color.1  = 23
 color.2  = 25
 color.3  = 27
 color.4  = 33
 color.5  = 35
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

*   color.1  = 2
*   color.2  = 5
*   color.3  = 3
*   color.4  = 4

* Plot Latitudinally-Averaged WSTAR
* ---------------------------------
n = 1
while( n<=numfiles )
   m = 1
   while( m<=numfiles )
     if( pltfile.m = n )
       'set dfile 'n
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
       'set t 1'
       'set ccolor 'color.n
                   'set cthick 3'
       if( n=1 ) ; 'set cthick 10' ; endif
                   'set cthick 6'
                    k = n - 3 * math_int(n/3) + 1
       'set cstyle 'k
       'set cstyle '1
*      if( n=2 ) ; 'set cstyle 1' ; endif
       'set cmark  0'
*      'set cmark  3'

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

*      Perform Smoothing Option
*      ------------------------
       if( nsmooth > 0 )
          'sety'
          'define wstrsmth = smth9( w'type''season''time''n')'
           countr = 1
           while( countr < nsmooth )
                 'define wstrsmth = smth9( wstrsmth )'
           countr = countr + 1
           endwhile
          'set y 1'
          'd ave(wstrsmth,lat='latmin',lat='latmax')*1000'
       else
          'd ave(w'type''season''time''n',lat='latmin',lat='latmax')*1000'
       endif

 else

*      Plot wstar based on Level-Dependent Turn-Around Latitudes
*      ---------------------------------------------------------
       'd wstarz'n

 endif

     endif
   m = m + 1
   endwhile
n = n + 1
endwhile
'draw ylab Pressure (hPa)'

* Plot Latitude x Height Cross-Section
* ------------------------------------
if(3>2)
'set vpage off'
'set parea off'
'set vpage 7.2 10.8 1.2 8.5'
'set vpage 7.0 11.0 0.0 8.5'

count = 0
ymax = 8.35
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
    'define wstrsmth = smth9( w'type''season''time''n'*1000 )'
     countr = 1
     while( countr < nsmooth )
           'define wstrsmth = smth9( wstrsmth )'
     countr = countr + 1
     endwhile
    'd wstrsmth '
 else
        'd w'type''season''time''n'*1000'
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

       'open FILE_'n'.ctl'
       'getinfo numfiles'
                newfile = result
       'set dfile 'newfile
       'set axlim -90 90'
       'set xaxis -90 90 30'
       'set y 1'
       'set t 1'
       'set lev 'levmax' 'levmin
       'set digsiz 0.02'
       'set ccolor 1'
       'set cmark  3'
       'd minlats'
       'set ccolor 1'
       'set cmark  3'
       'd maxlats'
       'close 'newfile
       'set lat -90 90'

 endif

         ydif = ydif + ydel
         say 'ydif: 'ydif

      endif
   m = m + 1
   endwhile
n = n + 1
endwhile
endif

*ydif = ymax-ymin
ymax = ybot - 0.2
ymin = ymax-ydif
say 'ymin: 'ymin'  ymax: 'ymax
if( ymin < 0.1 ) ; ymin = 0.1 ; endif
say 'ymin: 'ymin'  ymax: 'ymax


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
           'set dfile 'n
           'getinfo desc'
                    desc = result
            node = ''
            m = 2
           '!remove NODE.txt'
           '!basename 'desc' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            EXP.n = node
            say 'EXP'n' = 'EXP.n
            m = m + 1
           '!remove NODE.txt'
           '!basename 'desc' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            while( node != 'ctl' & node != 'data' )
            EXP.n = EXP.n'.'node
            say 'EXP'n' = 'EXP.n
            m = m + 1
           '!remove NODE.txt'
           '!basename 'desc' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            endwhile
        n = n + 1
    endwhile


    n = 1
    while( n<=numfiles )
       m = 1
       while( m<=numfiles )
          if( pltfile.m = n )
              if( numargs>2 ) 
                   index = id.n
                   tags = tags''index
                   if( exps = '' )
                       exps = EXP.n
                   else
                       exps = exps'.'EXP.n
                   endif
              endif
             'set dfile 'n

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

             '!echo \('id.n'\) ' EXP.n' >> plot_'season'.stack'
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
    filename = 'WSTAR_Profile_using_'talatsz'_TALATS.'season
else
*   filename = 'WSTAR_Profile_using_'talatsz'_TALATS.'tags'.'season
    filename = 'WSTAR_Profile_using_'talatsz'_TALATS.'exps'.'season
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

latbegS = - 5
latendS = -70
latbegN =   5
latendN =  70

'set lat 'latbegS
'getinfo ypos'
         ybeg = result
'set lat 'latendS
'getinfo ypos'
         yend = result

lat1 = latbegS
'set y 'ybeg
'd 'wstr
   val1 = subwrd(result,4)
       y = ybeg-1
while( y>= yend )
   'set y 'y
   'getinfo lat'
            lat2 = result
   'd 'wstr
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
                    y = yend - 1
     else
       val1 = val2
       lat1 = lat2
     endif
   y = y - 1
endwhile

latbegS = -15
latendS = -70
latbegN =  15
latendN =  70

'set lat 'latbegN
'getinfo ypos'
         ybeg = result
'set lat 'latendN
'getinfo ypos'
         yend = result
lat1 = latbegN
'set y 'ybeg
'd 'wstr
   val1 = subwrd(result,4)
say 'y = 'ybeg'  val = 'val1
       y = ybeg+1
while( y<= yend )
   'set y 'y
   'getinfo lat'
            lat2 = result
   'd 'wstr
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
                    y = yend + 1
     else
       val1 = val2
       lat1 = lat2
     endif
   y = y + 1
endwhile

return wstrlatmin' 'wstrlatmax' 'foundS' 'foundN
