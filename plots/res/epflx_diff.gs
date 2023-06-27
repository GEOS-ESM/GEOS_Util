function epflx_diff (args)

expid  = subwrd(args,1)
cmpid  = subwrd(args,2)
season = subwrd(args,3)
index  = subwrd(args,4)
index2 = subwrd(args,5)
output = subwrd(args,6)
detail = subwrd(args,7)


time = substr(index ,1,1)
num  = substr(index ,2,2)
num2 = substr(index2,2,2)


'set dfile 'num2
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
            desc2 = EXP


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

'makezdif -q1 epfdiv'season''index' -file1 'num' -q2 epfdiv'season'a'num2' -file2 'num2' -name epdiff  -ptop 1' ; 'run getenv ZDIFILE' ;  epfile = result
'makezdif -q1   epfy'season''index' -file1 'num' -q2   epfy'season'a'num2' -file2 'num2' -name epydiff -ptop 1' ; 'run getenv ZDIFILE' ; epyfile = result
'makezdif -q1   epfz'season''index' -file1 'num' -q2   epfz'season'a'num2' -file2 'num2' -name epzdiff -ptop 1' ; 'run getenv ZDIFILE' ; epzfile = result
 
'set dfile 'epfile
'set x 1'
'set t 1'
'sety'

' set lev 1000 1'
' define epdiff = epdiffz'
  nmax = 00
     n = 1
  while( n<=nmax )
   'define epdiff = smth9(epdiff)'
  n = n + 1
  endwhile
' getinfo dlat'
          dlat = result
       skipval = 2/dlat
       skipval = 6/dlat
' getint 'skipval
          skipval = result
       if(skipval < 1 ) ; skipval = 1 ; endif

'set gxout shaded'
'set arrlab off'

' set grads off '
' set ylopts 1 3 0.15 '


' vpage 1 1 2 2 -top 0.6 -bot -0.10'
' set csmooth on'
' set lev 925  1'
' setlevs '

' shades epdiff 0'
         cint = subwrd(result,1)
         cint = 100 * cint
'getint 'cint
         cint = result / 100
'shades 'cint

' d      epdiff'
' cbarn -xmid 6 -ndot 0'
' draw ylab hPa '
' set ccolor 1'
if( detail != '' )
    arrlen = 1
    arrscl = 1e7
    arrfct = 5
else
    arrlen = 1
    arrscl = 1e8
    arrfct = 50
endif
   'define arry    =  epydiffz'
   'define arrz    = -epzdiffz*'arrfct
   'define arryskp = skip(arry,'skipval')'
   'set arrscl 'arrlen' 'arrscl
   'd arryskp;arrz'
xrit = 4.0
ybot = 0.6
rc = arrow(xrit-0.25,ybot+0.2,arrlen,arrscl)
' set string 1 c 4 '
' set strsiz 0.09'
' draw string 8.25 0.7 Z/Y Ratio: 'arrfct


' vpage 2 1 2 2 -top 0.6 -bot -0.10'
' set csmooth on'
' set lev 925 100'

' shades epdiff 0'
         cint = subwrd(result,1)
         cint = 100 * cint
'getint 'cint
         cint = result / 100
'shades 'cint

' d      epdiff'
' cbarn -xmid 6 -ndot 0'
' draw ylab hPa '
' set ccolor 1'
if( detail != '' )
    arrlen = 1
    arrscl = 1e7
    arrfct = 5
else
    arrlen = 1
    arrscl = 1e8
    arrfct = 50
endif
   'define arry    =  epydiffz'
   'define arrz    = -epzdiffz*'arrfct
   'define arryskp = skip(arry,'skipval')'
   'set arrscl 'arrlen' 'arrscl
   'd arryskp;arrz'
xrit = 4.0
ybot = 0.6
rc = arrow(xrit-0.25,ybot+0.2,arrlen,arrscl)
' set string 1 c 4 '
' set strsiz 0.09'
' draw string 8.25 0.7 Z/Y Ratio: 'arrfct
   

' vpage 1 2 2 2 -top 0.25 -bot 0.25'
' set csmooth on'
' set lev 925 100'
' set zlog off '

' shades epdiff 0'
         cint = subwrd(result,1)
         cint = 100 * cint
'getint 'cint
         cint = result / 100
'shades 'cint

' d      epdiff'
' cbarn -xmid 6 -ndot 0'
' draw ylab hPa '
' set ccolor 1'
if( detail != ''   )
    arrlen = 1
    arrscl = 1e7
    arrfct = 5
else
    arrlen = 1
    arrscl = 1e8
    arrfct = 50
endif
   'define arry    =  epydiffz'
   'define arrz    = -epzdiffz*'arrfct
   'define arryskp = skip(arry,'skipval')'
   'set arrscl 'arrlen' 'arrscl
   'd arryskp;arrz'
xrit = 4.0
ybot = 0.6
rc = arrow(xrit-0.25,ybot+0.2,arrlen,arrscl)
' set string 1 c 4 '
' set strsiz 0.09'
' draw string 8.25 0.7 Z/Y Ratio: 'arrfct


' vpage 2 2 2 2 -top 0.25 -bot 0.25'
' set csmooth on'
' set grads off '
' set lev 100 8'
' set lev 100 20'
' set zlog on '

' shades epdiff 0'
         cint = subwrd(result,1)
         cint = 100 * cint
'getint 'cint
         cint = result / 100
'shades 'cint

' d      epdiff'
' cbarn -xmid 6 -ndot 1'
' draw ylab hPa '
' set ccolor 1'
if( detail != ''  )
    arrlen = 1
    arrscl = 5e6
    arrfct = 500
else
    arrlen = 1
    arrscl = 1e8
    arrfct = 500
endif

   'define arry    =  epydiffz'
   'define arrz    = -epzdiffz*'arrfct

   'define arryskp = skip(arry,'skipval')'
   'set arrscl 'arrlen' 'arrscl
   'd arryskp;arrz'
xrit = 4.0
ybot = 0.6
rc = arrow(xrit-0.25,ybot+0.2,arrlen,arrscl)
' set string 1 c 4 '
' set strsiz 0.09'
' draw string 8.25 0.7 Z/Y Ratio: 'arrfct



' set vpage off '

if( maskfile != 'NULL' )
   'run count.gs "'season'" 'begdate' 'enddate' -field epfdiv.'maskfile
    nseasons = result
else
   'run count.gs "'season'" 'begdate' 'enddate
    nseasons = result
endif

' set string 1 c 6 '
' set strsiz 0.14 '
' draw string 5.60501 8.43 Eliassen-Palm Flux Divergence'

' set strsiz 0.10 '
' set string 4 c 6 '
' draw string 2.85 8.2 'desc
' set string 1 c 6 '
' draw string 5.6 8.2 minus'
' set string 5 c 6 '
' draw string 8.35 8.2 'desc2
' set string 1 c 6 '

' set strsiz 0.10 '
' draw string 5.60501 7.88 'season' ('nseasons') Climatology   ('begdate' - 'enddate')'

'myprint -name 'output'/EP_Flux_diff_'expid'-'cmpid'.'season

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
