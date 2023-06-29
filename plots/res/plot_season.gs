function plot_season (args)

    talats = subwrd(args,1)
    output = subwrd(args,2)

'run getenv NSMOOTH'
            nsmooth = result
'run getenv SEASON'
            season = result
'run getenv TIME'
            time = result
'run getenv MASKFILE'
            maskfile = result

* Choose "indv" or "avrg" for Turn-Around Lats (talats) based on Turn-Around Functions (tafunc) "wstr" or "psi"
* -------------------------------------------------------------------------------------------------------------
*   talats = avrg
*   talats = indv

    tafunc = psi
    tafunc = wstr

    type = mean
    type = eddy
    type = star

    levmin = 20
    levmax = 100
* ------------------------------------

'numargs  'args
 numargs = result

'getinfo numfiles'
         numfiles = result
'getinfo ydim'
          RSLV = (result-1)/2
         CRSLV = C''RSLV

'set xlab on'

    hardmin = 60
    hardmax = 90
    hardmin = -999
    hardmax = -999

    numargs = numfiles
    n = 1
    while( n<=numfiles )
    pltfile.n = n
    n = n + 1
    endwhile

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
   m = 1
   while( m<=numargs )
     if( pltfile.m = n )
       'set dfile 'n
       'set lev 'levmax' 'levmin
       'set y 1'


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

       if( hardmin != -999 ) ; latmin = latmax  ; endif
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
     endif
   m = m + 1
   endwhile
n = n + 1
endwhile
  axmin = axmin - ( 0.1*axmax )
  axmax = axmax * 1.1

 'set axlim  0.22999 0.44001'
  if( axmin < 0.22999 | axmax > 0.44001 )
 'set axlim  'axmin' 'axmax
  endif

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


* Plot Turn-Around Average
* ------------------------
n = 1
while( n<=numfiles )
   m = 1
   while( m<=numargs )
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


       if( hardmin != -999 ) ; latmin = latmax  ; endif
       if( hardmax != -999 ) ; latmax = hardmax ; endif

       'getint 'latmax*100
                latmax = result/100
       'getint 'latmin*100
                latmin = result/100

       say 'Turn-Around wstr'n' latmin: 'latmin
       say 'Turn-Around wstr'n' latmax: 'latmax


 

* Perform Smoothing Option
* ------------------------
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
   while( m<=numargs )
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

       if( hardmin != -999 ) ; latmin = latmax  ; endif
       if( hardmax != -999 ) ; latmax = hardmax ; endif

       'getint 'latmax*100
                latmax = result/100
       'getint 'latmin*100
                latmin = result/100

       say 'Turn-Around wstr'n' latmin: 'latmin
       say 'Turn-Around wstr'n' latmax: 'latmax

        'set strsiz 0.055'
        'draw string 'xmid' 'ytit' Turnaround Lats: 'latmin' 'latmax

         ydif = ydif + ydel
         say 'ydif: 'ydif

*        pause

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


'run getenv BEGDATE'
            begdate = result
'run getenv ENDDATE'
            enddate = result

'set vpage off'
'set parea off'
'set string 1 c 6'
'set strsiz 0.14'

if( tafunc = wstr )
      func = 'w*'
else
      func = tafunc
endif

if(talats=avrg)
   if(type=star)
     'draw string 3.94 8.38 w* (Using Averaged Turn-Around Lats)'
   else
     'draw string 3.94 8.38 W_'type' (Using Averaged 'func' Turn-Around Lats)'
   endif
endif

if(talats=indv) 
   if(type=star)
     'draw string 3.94 8.38 w* (Using Individual Turn-Around Lats)'
   else
     'draw string 3.94 8.38 W_'type' (Using Individual 'func' Turn-Around Lats)'
   endif
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
       while( m<=numargs )
          if( pltfile.m = n )
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

if(talats=indv) ; filename = 'WSTAR_Profile_using_Individual_TALATS.'season ; endif
if(talats=avrg) ; filename = 'WSTAR_Profile_using_Averaged_TALATS.'season ; endif

'myprint -name 'output'/'filename
