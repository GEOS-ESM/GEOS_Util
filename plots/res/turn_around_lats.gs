function wstarave (args)

            season  = subwrd(args,1)
            output  = subwrd(args,2)
            nsmooth = subwrd(args,3)
            print   = subwrd(args,4)

if( season = '' )
    say 'You must supply a season!'
    return
endif
if( nsmooth = '' )
    nsmooth = 0
endif
if( print   = '' )
    print   = TRUE
endif

levmax = 100
levmin = 20

* Hardwire Averaged WSTAR Lats for taabs=TRUE
* -------------------------------------------
      taabs = FALSE
* wstrlatmx =  32
* wstrlatmn = -49

'run setenv SEASON  'season
'run setenv NSMOOTH 'nsmooth

'uppercase 'season
            season = result

'run getenv TIME '
            time = result

'getinfo numfiles'
         numfiles = result

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
    color.5  = 6
    color.6  = 7
    color.7  = 8

'set datawarn off'
nbeg = 1
nmax = numfiles

'run getenv BEGDATE'
            begdate = result
'run getenv ENDDATE'
            enddate = result

'run getenv MASKFILE'
            maskfile = result
say 'MASKFILE: 'maskfile
*pause

wstrlatmx = 0
wstrlatmn = 0
 psilatmx = 0
 psilatmn = 0

* Loop over Files
* ---------------
       n =nbeg
while( n<=nmax )
'set dfile 'n
'set x 1'
'sety'

'set lev 'levmax
'getinfo zpos'
         zmin = result
'set lev 'levmin
'getinfo zpos'
         zmax = result

* Initialization
* --------------
z = zmin
'set z 'z
'define wstr'season''time''n' = lev-lev' 
'define  psi'season''time''n' = lev-lev' 

* Integrate WSTAR and RES from zmin to zmax
* -----------------------------------------
ptot = 0.0
while( z<=zmax )

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

'run setenv TAABS 'taabs
if( taabs = TRUE )
 'define wstr'season''time''n' = wstr'season''time''n' + ( wstar'season''time''n' + abs( wstar'season''time''n' ) )/2 *'delp
else
 'define wstr'season''time''n' = wstr'season''time''n' + wstar'season''time''n'*'delp
endif
 'define  psi'season''time''n' =  psi'season''time''n' +   res'season''time''n'*'delp



         ptot  = ptot + delp
say 'File: 'n'  levm1: 'levm1'  lev: 'level'  levp1: 'levp1'  delp = 'delp'  ptot = 'ptot
z = z + 1
endwhile
say ' '
'define wstr'season''time''n' = wstr'season''time''n' / 'ptot
'define  psi'season''time''n' =  psi'season''time''n' / 'ptot


* Smooth possible noise
* ---------------------
'sety'
 if( nsmooth > 0 )
    'define wstrsmth = smth9( wstr'season''time''n' )'
    'define  psismth = smth9(  psi'season''time''n' )'
     count = 1
     while( count < nsmooth )
           'define wstrsmth = smth9( wstrsmth )'
           'define  psismth = smth9(  psismth )'
     count = count + 1
     endwhile
    'define wstr'season''time''n' = wstrsmth '
    'define  psi'season''time''n' =  psismth '
 endif
*'d wstr'season''time''n


* Get Latitudes for Locations of Maximum and Minimum psi from each individual file
* --------------------------------------------------------------------------------
 'minmax   psi'season''time''n
  psiymx = subwrd(result,4)
  psiymn = subwrd(result,6)
 'set y   'psiymx
 'getinfo lat'
            psilatmx.n = result
 'set y   'psiymn
 'getinfo lat'
            psilatmn.n = result


* Find Latitudes of Zero Line Crossings for wstr from each individual file
* ------------------------------------------------------------------------
latbegS = -30
latendS = -60
latbegN = 15
latendN = 60

    dummy   = get_lats( 'wstr'season''time''n )
wstrlatmn.n = subwrd(dummy,1)
wstrlatmx.n = subwrd(dummy,2)

* Compute Averaged LatMax and LatMin from Integrated wstr and psi
* ---------------------------------------------------------------
'set dfile 1'
say 'wstrlatmx = 'wstrlatmx' + 'wstrlatmx.n
wstrlatmx = wstrlatmx + wstrlatmx.n
wstrlatmn = wstrlatmn + wstrlatmn.n

 psilatmx =  psilatmx +  psilatmx.n
 psilatmn =  psilatmn +  psilatmn.n
'set dfile 'n

n = n + 1
endwhile

wstrlatmx = wstrlatmx / (nmax-nbeg+1)
wstrlatmn = wstrlatmn / (nmax-nbeg+1)

 psilatmx =  psilatmx / (nmax-nbeg+1)
 psilatmn =  psilatmn / (nmax-nbeg+1)

say ' '
n = nbeg
while( n<=nmax )
say 'File: 'n'    psi'season'latmn = '  psilatmn.n '    psi'season'latmx = '  psilatmx.n
n = n + 1
endwhile
say 'Average    psi'season'latmn = '  psilatmn '    psi'season'latmx = '  psilatmx
say ' '


say ' '
n = nbeg
while( n<=nmax )
say 'File: 'n'    wstr'season'latmn = '  wstrlatmn.n '    wstr'season'latmx = '  wstrlatmx.n

'run setenv wstr'season'latmx'n' 'wstrlatmx.n
'run setenv wstr'season'latmn'n' 'wstrlatmn.n
'run setenv  psi'season'latmx'n' ' psilatmx.n
'run setenv  psi'season'latmn'n' ' psilatmn.n

n = n + 1
endwhile
say 'Average    wstr'season'latmn = '  wstrlatmn '    wstr'season'latmx = '  wstrlatmx
say ' '

* ----------------------------------------------------

'set vpage off'
'set parea off'
'set vpage 0.0 11 0 8.5'
'set mproj off'
'set grid  off'

'set xlopts 1 3 0.14'
'set ylopts 1 3 0.11'

'set ylab %.1f'

left  = 1.5
right = 1.2
top   = 0.5
bot   = 0.3

'parea 1 1 1 2.5 -left 'left' -right 'right' -top 'top' -bot 'bot

xmid_wstar   = subwrd(result,1)
ymid_wstar   = subwrd(result,4)
ytop_wstar   = subwrd(result,3)
ybot_wstar   = subwrd(result,2)



'set axlim -2.5001 1.0001'
'set axlim -2.5001 3.5001'
'set axlim -2.5001 1.5001'

'set dfile 1'
'sety'
'define wstrave = lat-lat'
'getinfo dlat'
         dlat1 = result

count = 0
n = nbeg
while( n<=nmax )
'set dfile 'n
'getinfo dlat'
         dlat = result
say 'File 'n'  dlat'n' = 'dlat
'sety'
if( dlat = dlat1 )
   'set dfile 1'
   'define wstrave = wstrave + 1000*wstr'season''time''n
    count = count + 1
endif
n = n + 1
endwhile
'set dfile 1'
'define wstrave = wstrave / 'count


'minmax wstrave'
 axmax = 10*1.7*subwrd(result,1)
 axmin = 10*1.7*subwrd(result,2)
'getint 'axmax
         axmax = result/10
'getint 'axmin
         axmin = result/10
say 'set axlim 'axmin' 'axmax
'set axlim 'axmin' 'axmax


count = 0
n = nbeg
while( n<=nmax )
'set dfile 'n
'getinfo dlat'
         dlat = result
'sety'
'set ccolor 'color.n
'set cstyle 1'
'set cmark  0'
'set cthick 1'
'd 1000*wstr'season''time''n
n = n + 1
endwhile
'set dfile 1'

'set cstyle 1'
'set cmark  0'
'set cthick 8'
'set ccolor 1'
'd wstrave'

'set cmark 0'
'set ccolor 1'
'set cthick 1'
'set z 1'
'd lev-lev'

* Compute Turn-Around Lats based on wstrave
* -----------------------------------------
'set dfile 1'
 
    dummy = get_lats( 'wstrave' )
wstrlatmn = subwrd(dummy,1)
wstrlatmx = subwrd(dummy,2)


'set string 1 c 6'
'set strsiz 0.14'

               if( maskfile != 'NULL' )
                  'run count.gs "'season'" 'begdate' 'enddate' -field wstar.'maskfile
                   nseasons = result
               else
                  'run count.gs "'season'" 'begdate' 'enddate
                   nseasons = result
               endif

if( taabs = TRUE )
   'draw string 'xmid_wstar' 'ytop_wstar+0.1' Vert.Int. [WSTAR + ABS(WSTAR)]/2  'season'  'begdate'-'enddate'  Levels: 'levmax' 'levmin
else
   'draw string 'xmid_wstar' 'ytop_wstar+0.1' Vert.Int. WSTAR  'season' ('nseasons')  'begdate'-'enddate'  Levels: 'levmax' 'levmin
endif

* ----------------------------------------------------

left  = 1.5
right = 1.2
top   = 0.3
bot   = 0.5

'set vpage 0.0 11 0 8.5'
'set mproj off'
'set grid  off'
'parea 1 2 1 2.5 -left 'left' -right 'right' -top 'top' -bot 'bot

xmid_psi   = subwrd(result,1)
ymid_psi   = subwrd(result,4)
ytop_psi   = subwrd(result,3)
ybot_psi   = subwrd(result,2)

'set axlim -0.6001 1.8001'
'set axlim -4.5001 15.2001'
'set axlim -0.6001 2.2001'

'set dfile 1'
'define psiave = lat-lat'
count = 0
n = nbeg
while( n<=nmax )
'set dfile 'n
'getinfo dlat'
         dlat = result
'sety'
if( dlat = dlat1 )
   'set dfile 1'
   'define psiave = psiave + psi'season''time''n
    count = count + 1
endif
n = n + 1
endwhile
'set dfile 1'
'define psiave = psiave / 'count


'minmax psiave'
 axmax = 10*1.7*subwrd(result,1)
 axmin = 10*1.7*subwrd(result,2)
'getint 'axmax
         axmax = result/10
'getint 'axmin
         axmin = result/10
say 'set axlim 'axmin' 'axmax
'set axlim 'axmin' 'axmax

'set dfile 1'
n = nbeg
while( n<=nmax )
'set dfile 'n
'getinfo dlat'
         dlat = result
'sety'
'set ccolor 'color.n
'set cstyle 1'
'set cmark  0'
'set cthick 1'
'd psi'season''time''n
n = n + 1
endwhile

'set dfile 1'
'set cstyle 1'
'set cmark  0'
'set cthick 8'
'set ccolor 1'
'd psiave'

'set cmark 0'
'set ccolor 1'
'set z 1'
'd lev-lev'

* Compute Turn-Around Lats based on psiave
* -----------------------------------------
'set lat -60'
'getinfo ypos'
         ybeg = result
'set lat 0'
'getinfo ypos'
         yend = result
'set y 'ybeg' 'yend
'minmax   psiave'
 psiymx = subwrd(result,4)
'set y   'psiymx
'getinfo lat'
           psilatmx

'set lat 0'
'getinfo ypos'
         ybeg = result
'set lat 60'
'getinfo ypos'
         yend = result
'set y 'ybeg' 'yend
'minmax   psiave'
 psiymn = subwrd(result,6)
'set y   'psiymn
'getinfo lat'
           psilatmn

* ----------------------------------------------------

say ' '
say 'Average    wstr'season'latmn = '  wstrlatmn '    wstr'season'latmx = '  wstrlatmx
say 'Average    psi'season'latmn = '  psilatmn '    psi'season'latmx = '  psilatmx
say ' '

'run setenv wstr'season'latmx 'wstrlatmx
'run setenv wstr'season'latmn 'wstrlatmn
'run setenv  psi'season'latmx ' psilatmx
'run setenv  psi'season'latmn ' psilatmn

* ----------------------------------------------------

    'q w2xy 'wstrlatmn' 0'
say 'q w2xy 'wstrlatmn' 0'
say result
xmin = subwrd(result,3)
ymin = subwrd(result,6)
    'q w2xy 'wstrlatmx' 0'
say 'q w2xy 'wstrlatmx' 0'
say result
xmax = subwrd(result,3)
ymax = subwrd(result,6)
'set line 2 2 6'
'draw line 'xmin' 'ybot_wstar' 'xmin' 'ytop_wstar
'draw line 'xmax' 'ybot_wstar' 'xmax' 'ytop_wstar

'set string 2 c 6'
'getint 'wstrlatmn*100
         wstrlatmn = result/100
'getint 'wstrlatmx*100
         wstrlatmx = result/100
'draw string 'xmin' 'ymid_wstar' 'wstrlatmn' deg'
'draw string 'xmax' 'ymid_wstar' 'wstrlatmx' deg'

    'q w2xy 'psilatmn' 0'
say 'q w2xy 'psilatmn' 0'
say result
xmin = subwrd(result,3)
ymin = subwrd(result,6)
    'q w2xy 'psilatmx' 0'
say 'q w2xy 'psilatmx' 0'
say result
xmax = subwrd(result,3)
ymax = subwrd(result,6)
'set line 3 2 6'
'draw line 'xmin' 'ybot_psi' 'xmin' 'ytop_psi
'draw line 'xmax' 'ybot_psi' 'xmax' 'ytop_psi

'set string 3 c 6'
'getint 'psilatmn*100
         psilatmn = result/100
'getint 'psilatmx*100
         psilatmx = result/100
'draw string 'xmin' 'ymid_psi' 'psilatmn' deg'
'draw string 'xmax' 'ymid_psi' 'psilatmx' deg'

'!remove turn_around_'season'.stack'
'!remove DESC.txt'
'!echo 'numfiles' > turn_around_'season'.stack'

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
    pltfile.n = n
    n = n + 1
    endwhile

    n = 1
    while( n<=numfiles )

    if(n=1) ; id.1  = 'a' ; endif
    if(n=2) ; id.2  = 'b' ; endif
    if(n=3) ; id.3  = 'c' ; endif
    if(n=4) ; id.4  = 'd' ; endif
    if(n=5) ; id.5  = 'e' ; endif
    if(n=6) ; id.6  = 'f' ; endif
    if(n=7) ; id.7  = 'g' ; endif
    if(n=8) ; id.8  = 'h' ; endif
    if(n=9) ; id.9  = 'i' ; endif
    if(n=10) ; id.10 = 'j' ; endif
    if(n=11) ; id.11 = 'k' ; endif
    if(n=12) ; id.12 = 'l' ; endif
    if(n=13) ; id.13 = 'm' ; endif
    if(n=14) ; id.14 = 'n' ; endif
    if(n=15) ; id.15 = 'o' ; endif

           'set dfile 'n

               'run getenv BEGDATE'
                           begdate = result
                             bdate = substr(result,6,7)
               'run getenv ENDDATE'
                           enddate = result
                             edate = substr(result,6,7)

               if( maskfile != 'NULL' )
                  'run count.gs "'season'" 'begdate' 'enddate' -field wstar.'maskfile
                   nseasons = result
               else
                  'run count.gs "'season'" 'begdate' 'enddate
                   nseasons = result
               endif

           'getinfo desc'
                    desc.n = result
           '!remove DESC.txt'
           '!echo 'desc.n' | cut -d. -f2 >> DESC.txt'
           'run getenv "DESC"'
                        desc.n = result
                   k = n - 3 * math_int(n/3) + 1
                   k = 1

       'getint 'wstrlatmx.n*100
                latmax = result/100
       'getint 'wstrlatmn.n*100
                latmin = result/100

           '!echo 'k' 6 'color.n' >> turn_around_'season'.stack'
    say    "!echo \("id.n"\) "EXP.n" \("latmin" , "latmax"\) >> turn_around_"season".stack"
           "!echo \("id.n"\) "EXP.n" \("latmin" , "latmax"\) >> turn_around_"season".stack"
    n = n + 1
    endwhile

'!echo 1.167  >> turn_around_'season'.stack'
'!echo 0.334  >> turn_around_'season'.stack'
'!echo 10.0   >> turn_around_'season'.stack'
'!echo 1.83   >> turn_around_'season'.stack'

'lines turn_around_'season'.stack 1 12'

'set string 1 c 6'
'set strsiz 0.14'

'draw string 'xmid_psi' 'ytop_psi+0.1' Vert.Int. PSI  'season' ('nseasons')  'begdate'-'enddate'  Levels: 'levmax' 'levmin
if( print = TRUE )
   'myprint -name 'output'/WSTAR_Turn_Around_Lats.'season
endif

return

* ------------------------------------------------------------------------
* ------------------------------------------------------------------------
* ------------------------------------------------------------------------

function get_lats( wstr )

say 'inside get_lats, wstr = 'wstr
* Find Latitudes of Zero Line Crossings for wstr from each individual file
* ------------------------------------------------------------------------
latbegS = -30
latendS = -60

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
   say 'lat1: 'lat1'  lat2: 'lat2'  val1: 'val1'  val2: 'val2'  val1*val2: 'val1*val2
*  pause
     if( val1*val2 <= 0 )
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

latbegN = 15
latendN = 60

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
   say 'lat1: 'lat1'  lat2: 'lat2'  val1: 'val1'  val2: 'val2'  val1*val2: 'val1*val2
*  pause
     if( val1*val2 <= 0 )
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

return wstrlatmin' 'wstrlatmax
