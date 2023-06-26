function epflx (args)
expid  = subwrd(args,1)
season = subwrd(args,2)
index  = subwrd(args,3)
output = subwrd(args,4)

time = substr(index,1,1)
num  = substr(index,2,2)


'set dfile 'num
'setz '
           'getinfo desc'
                    desc = result
            node = ''
            m = 2
           '!remove NODE.txt'
           '!basename 'desc' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            EXP = node
            say 'EXP = 'EXP
            m = m + 1
           '!remove NODE.txt'
           '!basename 'desc' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            while( node != 'ctl' )
            EXP = EXP'.'node
            say 'EXP = 'EXP
            m = m + 1
           '!remove NODE.txt'
           '!basename 'desc' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            endwhile
            desc = EXP

   'run getenv MASKFILE'
               maskfile = result

if( time = 'A' )
   'run getenv BEGDATE'
               begdate = result
   'run getenv ENDDATE'
               enddate = result
else
   'set t 1'
   'run getinfo date'
                begdate = result
   'run getinfo tdim'
                tdim    = result
   'set t 'tdim
   'run getinfo date'
                enddate = result
endif

say 'BEGDATE = 'begdate
say 'ENDDATE = 'enddate

'define   epfy'season' =   epfy'season''index
'define   epfz'season' =   epfz'season''index
'define epfdiv'season' = epfdiv'season''index

' set lev 1000 1'
' define epfdiv = epfdiv'season'/1e2'
  nmax = 20
     n = 1
  while( n<=nmax )
   'define epfdiv = smth9(epfdiv)'
  n = n + 1
  endwhile
' getinfo dlat'
          dlat = result
       skipval = 1.25/dlat
       skipval = 2.00/dlat
' getint 'skipval
          skipval = result
       if(skipval < 1 ) ; skipval = 1 ; endif

'set gxout shaded'

' set vpage  off '
' set parea  off '
' set grads  off '
' set arrlab off '
' set ylopts 1 3 0.15 '

' vpage 1 1 2 2 -top 0.6 -bot -0.10'
' set ccolor rainbow'
' set csmooth on'
' set lev 925 0.8'
' setlevs '
' shades 1.00'
' d epfdiv'
' cbarn -xmid 6 '
' draw ylab hPa '
 arrfct = 100
 arrlen = 1
 arrscl = 2.5e9
'define arry    =  epfy'season
'define arrz    = -epfz'season'*'arrfct
'define arryskp = skip(arry,'skipval')'
'set arrscl 'arrlen' 'arrscl
' set ccolor 1'
'd arryskp;arrz'
xrit = 4.0
ybot = 0.6
rc = arrow(xrit-0.25,ybot+0.2,arrlen,arrscl)
' set string 1 c 4 '
' set strsiz 0.10'
' draw string 8.25 0.7 Z/Y Ratio: 'arrfct


' vpage 2 1 2 2 -top 0.6 -bot -0.10'
' set ccolor rainbow'
' set csmooth on'
' set lev 1000 100 '
' set lev 1000 80 '
' set lev 925 80 '
' shades 1.00'
' d epfdiv'
' cbarn -xmid 6 '
' draw ylab hPa '
 arrfct = 100
 arrlen = 1
 arrscl = 2.5e9
'define arry    =  epfy'season
'define arrz    = -epfz'season'*'arrfct
'define arryskp = skip(arry,'skipval')'
'set arrscl 'arrlen' 'arrscl
' set ccolor 1'
'd arryskp;arrz'
xrit = 4.0
ybot = 0.6
rc = arrow(xrit-0.25,ybot+0.2,arrlen,arrscl)
' set strsiz 0.10'
' draw string 8.25 0.7 Ratio Z/Y: 'arrfct

' vpage 1 2 2 2 -top 0.25 -bot 0.25'
' set ccolor rainbow'
' set csmooth on'
' set lev 1000 100 '
' set lev 1000 80 '
' set lev 925 80 '
' set zlog off '
' shades 1.00'
' d epfdiv'
' cbarn -xmid 6 '
' draw ylab hPa '
 arrfct = 100
 arrlen = 1
 arrscl = 2.5e9
'define arry    =  epfy'season
'define arrz    = -epfz'season'*'arrfct
'define arryskp = skip(arry,'skipval')'
'set arrscl 'arrlen' 'arrscl
' set ccolor 1'
'd arryskp;arrz'
xrit = 4.0
ybot = 0.6
rc = arrow(xrit-0.25,ybot+0.2,arrlen,arrscl)
' set strsiz 0.10'
' draw string 8.25 0.7 Ratio Z/Y: 'arrfct

' vpage 2 2 2 2 -top 0.25 -bot 0.25'
' set csmooth on'
' set ccolor rainbow'
' set grads off '
' set lev 100 8'
' set zlog on '
' shades 0.1 '
' d epfdiv'
' cbarn -xmid 6 '
' draw ylab hPa '
 arrfct = 500
 arrlen = 1
 arrscl = 8e8
'define arry    =  epfy'season
'define arrz    = -epfz'season'*'arrfct
'define arryskp = skip(arry,'skipval')'
'set arrscl 'arrlen' 'arrscl
' set ccolor 1'
'd arryskp;arrz'
xrit = 4.0
ybot = 0.6
rc = arrow(xrit-0.25,ybot+0.2,arrlen,arrscl)
' set strsiz 0.10'
' draw string 8.25 0.7 Ratio Z/Y: 'arrfct



' set vpage off '

if( maskfile != 'NULL' )
   'run count.gs "'season'" 'begdate' 'enddate' -field epfdiv.'maskfile
    nseasons = result
else
   'run count.gs "'season'" 'begdate' 'enddate
    nseasons = result
endif

' set string 1 c 6 '
' set strsiz 0.12 '
' draw string 5.60501 8.4 Eliassen-Palm Flux Divergence from 'desc
' set strsiz 0.12 '
' draw string 5.60501 8.1 'season' ('nseasons') Climatology   ('begdate' - 'enddate')'

'myprint -name 'output'/EP_Flux_'expid'.'season

return

function arrow(x,y,len,scale)
'set line 1 1 4'
'draw line 'x-len/2.' 'y' 'x+len/2.' 'y
'draw line 'x+len/2.-0.05' 'y+0.025' 'x+len/2.' 'y
'draw line 'x+len/2.-0.05' 'y-0.025' 'x+len/2.' 'y
'set string 1 c'
'set strsiz 0.1'
'draw string 'x' 'y-0.1' 'scale
return

