function genplt (args)

expid    = getarg( args,EXPID   )
EXPORT   = getarg( args,EXPORT  )
GC       = getarg( args,GC      )
alias    = getarg( args,ALIAS   )
season   = getarg( args,SEASON  )
begdate  = getarg( args,MBDATE  )
enddate  = getarg( args,MEDATE  )
climexp  = getarg( args,CLIMEXP )
begdateo = getarg( args,CBDATE  )
enddateo = getarg( args,CEDATE  )
climcmp  = getarg( args,CLIMCMP )
output   = getarg( args,OUTPUT  )
level    = getarg( args,LEVEL   )
nmod     = getarg( args,NMOD    )
nobs     = getarg( args,CMOD    )
expfile  = getarg( args,MFILE   )
cmpfile  = getarg( args,CFILE   )
cmpid    = getarg( args,CNAME   )
obsname  = getarg( args,CDESC   )
debug    = getarg( args,DEBUG   )
expdsc   = getarg( args,MDESC   )
stat     = getarg( args,STAT    )

blak   = 0

* Check for Contour Level Type
* ----------------------------
'run getenv "LEVTYPE"'
           CLEVS  = result

* Get Plotting Values from Resource File
* --------------------------------------
'run getenv "GEOSUTIL"'
             geosutil = result
PLOTRC = geosutil'/plots/grads_util/plot.rc'

    PRFX = ''
if( stat = 'STD' )
    PRFX = 'STD_'
endif
if( stat = 'RMS' )
    PRFX = 'RMS_'
endif
if( stat = 'BIAS' )
    PRFX = 'BIAS_'
endif

say 'LEVTYPE: 'CLEVS
                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_'level'_CBSCALE'
if( result = 'NULL' ) ; 'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_CBSCALE' ; endif
                                                                  cbscale = result

                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_'level'_FACTOR'
if( result = 'NULL' ) ; 'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_FACTOR' ; endif
                                                                  fact = result

                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_FIXED_PLOT_FACTOR'
                                                                  fixpltfact = result
                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_FIXED_PLOT_CINT'
                                                                  fixpltcint = result

                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_'level'_TITLE'
if( result = 'NULL' ) ; 'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_TITLE' ; endif
                                                   title  = result

                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_'level'_CCOLS'
if( result = 'NULL' ) ; 'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_CCOLS' ; endif
                                                   ccols  = result

                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_'level'_'CLEVS
if( result = 'NULL' ) ; 'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_'level'_CLEVS' ; endif
if( result = 'NULL' ) ; 'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_'CLEVS ; endif
if( result = 'NULL' ) ; 'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_CLEVS' ; endif
                                                                  clevs = result

                        'getresource 'PLOTRC' 'mname'_'GC'_'level'_DPCT'
if( result = 'NULL' ) ; 'getresource 'PLOTRC' 'mname'_'GC'_DPCT' ; endif
                                                   dpct  = result

                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_REGRID'
                                                                  method = result
                        'getresource 'PLOTRC' 'PRFX''EXPORT'_'GC'_MASK'
                                                                  mask   = result

* Remove possible BLANKS from mask
* --------------------------------
DUMMY = ''
length = strlen(result)
i = 1
while( i<=length )
  bit = substr(result,i,1)
  if( bit != ' ' )
      if( DUMMY = '' )
          DUMMY = bit
else
          DUMMY = DUMMY''bit
      endif
  endif
i = i+1
endwhile
mask = DUMMY


if( title   = 'NULL' )
   'run getdesc 'alias'  'expfile
    title   =  result
endif
    title   =  EXPORT':'GC'  'title

if( cbscale = 'NULL' ) ; cbscale =  0.8         ; endif
if( clab    = 'NULL' ) ; clab    =  on          ; endif
if( dpct    = 'NULL' ) ; dpct    =  0.1         ; endif

                     'd 'dpct
                         dpct    = subwrd(result,4)
say ''
say 'title: 'title
say ' fact: ' fact
say 'ccols: 'ccols
say 'clevs: 'clevs
say ' mask: ' mask
say ''

* Remove possible BLANKS from FACTOR
* ----------------------------------
DESC = ''
length = getlength(fact)
i = 1
while( i<=length )
  bit = substr(fact,i,1)
  if( bit != ' ' )
      if( DESC = '' )
          DESC = bit
      else
          DESC = DESC''bit
      endif
  endif
i = i+1
endwhile
fact = DESC

* Set Default Plotting Variables
********************************

if( fact    = 'NULL' ) ; fact    = 1         ; endif

* Plot Mean Field
* ---------------
'c'
'set display color white'
'set vpage off'
'set parea off'
'set grid  off'
'set mproj scaled'
'set frame on'
'set xlopts 1 3 .11'
'set ylopts 1 3 .11'
'rgbset'
'set rgb 84 204 204 204'
'set rgb 85 137 137 137'

'set dfile 'expfile
'setlons'
'setlats'
if( level = 0 )
   'set z 1'
else
   'set lev 'level
endif
'set t 1'
'q dims'
say 'EXP DIMS Environment: 'result

* Get Dimension of Environment
* ----------------------------
'getinfo lonmin'
         lonbeg = result
'getinfo lonmax'
         lonend = result
'getinfo latmin'
         latbeg = result
'getinfo latmax'
         latend = result

say 'Environment Dimension: 'lonbeg' 'lonend' 'latbeg' 'latend

'define qmod  = mod'season'*'fact
'define qmod  = regrid2( qmod,0.25,0.25,bs_p1,'lonbeg','latbeg')'

if( mask != NULL )
   'setmask'
   'define lwmask = regrid2( lwmask,0.25,0.25,bs_p1,'lonbeg','latbeg')'
   if( mask = 'LAND' )
       say 'define qmod = maskout( qmod, 0.5-lwmask )'
           'define qmod = maskout( qmod, 0.5-lwmask )'
   endif
   if( mask = 'OCEAN' )
       say 'define qmod = maskout( qmod, lwmask-0.5 )'
           'define qmod = maskout( qmod, lwmask-0.5 )'
   endif
endif

'define maskm = 1 + qmod-qmod'



* Determine DLAT & DLON of Comparison Experiment
* ----------------------------------------------
'set dfile 'cmpfile
'set z 1'
'set t 1'
'getinfo dlat'
         dlat = result
'getinfo dlon'
         dlon = result
'set gxout shaded'

say 'CMPID DLAT: 'dlat
say 'CMPID DLON: 'dlon

'set lon 'lonbeg' 'lonend
'set lat 'latbeg' 'latend
'define qobs  = obs'season'*'fact
'define qobs  = regrid2( qobs,0.25,0.25,bs_p1,'lonbeg','latbeg')'
'define qobs  = maskout(qobs,maskm)'

   'set gxout stat'
   'd qmod'
   qminmax = sublin(result,8)
   qmin    = subwrd(qminmax,4)
   qmax    = subwrd(qminmax,5)
   say 'QMin Value: 'qmin
   say 'QMax Value: 'qmax
   'set gxout shaded'
   'd abs('qmin')'
           qmin = subwrd(result,4)
   'd abs('qmax')'
           qmax = subwrd(result,4)
   if( qmin > qmax ) ; qmax = qmin ; endif

   say 'Absolute QMAX: 'qmax

m = 0
if( ccols = NULL )
   if( qmax > 0 )
      'd log10('qmax')'
       m = subwrd(result,4)
   else
       m = 0
   endif
   say '    Log Factor: 'm
   if( m<0 ) ; m = m-2 ; endif
   'getint 'm
            m = result
   if( m>0 )
       if( m<=2 )
           m = 0
       else
           m = m-2
       endif
   endif
   say 'Field Scaling Factor: 'm
   if( m<0 )
       j = -1 * m
      'define qmod = qmod * 1e'j
      'define qobs = qobs * 1e'j
   else
      'define qmod = qmod / 1e'm
      'define qobs = qobs / 1e'm
endif
endif

'set dfile 'expfile
'set lon 'lonbeg' 'lonend
'set lat 'latbeg' 'latend


* Make Plot: Top Panel
* --------------------
'set vpage 0 8.5 0.0 11'
'set parea 1.5 7.0 7.70 10.50'
'set grads off'

   'set gxout stat'
   'd qmod'
   qmodminmax = sublin(result,8)
   qmodmin    = subwrd(qmodminmax,4)
   qmodmax    = subwrd(qmodminmax,5)
   say 'QMOD_Max Value: 'qmodmax
   say 'QMOD_Min Value: 'qmodmin
   'set gxout shaded'
   'd abs('qmodmin')'
          aqmodmin = subwrd(result,4)
   'd abs('qmodmax')'
          aqmodmax = subwrd(result,4)
   if( aqmodmin > aqmodmax ) ; aqmodmax = aqmodmin ; endif
   say 'Absolute QMOD_MAX: ' aqmodmax

   'set gxout shaded'
if( ccols != NULL )
   'set clevs 'clevs
   'set ccols 'ccols
   'set clab  'clab
else
   'shades 'qmod' 0'
    cint = result*2
    if( clevs != NULL ) ; 'set clevs 'clevs ; endif
endif
'd qmod'

* Make Plot: Middle Panel
* -----------------------
'set parea off'
'set vpage 0 8.5 0.0 11'
'set parea 1.5 7.0 4.30 7.10'
'set grads off'

   'set gxout stat'
   'd qobs'
   qobsminmax = sublin(result,8)
   qobsmin    = subwrd(qobsminmax,4)
   qobsmax    = subwrd(qobsminmax,5)
   say 'QOBS_Max Value: 'qobsmax
   say 'QOBS_Min Value: 'qobsmin
   'set gxout shaded'
   'd abs('qobsmin')'
          aqobsmin = subwrd(result,4)
   'd abs('qobsmax')'
          aqobsmax = subwrd(result,4)
   if( aqobsmin > aqobsmax ) ; aqobsmax = aqobsmin ; endif
   say 'Absolute QOBS_MAX: ' aqobsmax

if( ccols != NULL )
   'set gxout shaded'
   'set clevs 'clevs
   'set ccols 'ccols
else
   'shades 'qmod' 0'
    if( clevs != NULL ) ; 'set clevs 'clevs ; endif
endif
'd qobs'

   'cbarn -vert -snum 0.8 -ymid 5.7 -scaley 0.9 '

* Make Plot: Bottom Panel
* -----------------------
'set parea off'
'set vpage 0 8.5 0.0 11'
'set parea 1.5 7.0 0.90 3.70'
'set grads off'
'getinfo lon'
         lon = result
'set dfile 'expfile
if( level = 0 )
   'set z 1'
else
   'set lev 'level
endif
'set t 1'
'q dims'

'stats maskout(qmod,abs(qobs))'
 avgmod = subwrd(result,1)
 stdmod = subwrd(result,2)

'stats maskout(qobs,abs(qobs))'
 avgobs = subwrd(result,1)
 stdobs = subwrd(result,2)

'stats maskout(qmod-qobs,abs(qobs))'
     avgdif = subwrd(result,1)
     stddif = subwrd(result,2)
      dqmax = stddif/3

'set gxout shaded'

    say 'QMAX Scaling Factor: 'm
    if( m<0 )
       j = -1 * m
      'd 1e'j
      scaling = subwrd(result,4)
      say 'qmax before scaling: 'qmax
      qmax = qmax * scaling
      say 'qmax after  scaling: 'qmax
    else
      'd 1e'm
      scaling = subwrd(result,4)
      say 'qmax before scaling: 'qmax
      qmax = qmax / scaling
      say 'qmax before scaling: 'qmax
     endif

     say 'Absolute DQMAX: 'dqmax'  qmax: 'qmax
     dqrel = dqmax / qmax  * 100 * 100
    'getint 'dqrel
             dqrel = result/100

     say 'QMAX: 'qmax'  DQMAX: 'dqmax
     say 'Relative PCT Difference: 'dqrel' (100*DQMAX/QMAX)'
     say ' Minimum PCT for  Plots: 'dpct

     if( dqrel < dpct )
         dqrel = dpct
     endif
         dqmax = dqrel * qmax / 100
         say 'Setting CINT using DQREL: 'dqrel'%, DQMAX: 'dqmax

   if( dqmax > 0 )
      'd log10('dqmax')'
       n = subwrd(result,4)
   else
       n = 0
   endif
   say '    Log Factor: 'n
   if( n<0 ) ; n = n-2 ; endif
   'getint 'n
            n = result
   if( n>0 )
       if( n<=2 )
           n = 0
        else
           n = n+2
        endif
   endif

   if( fixpltfact != NULL )
       'd 'fixpltfact
        n =subwrd(result,4)
   endif

   say 'Diff Scaling Factor: 'n

   if( fixpltcint != NULL )
      'd  'fixpltcint
           fixpltcint =subwrd(result,4)
       cint = fixpltcint
   else
      'd 'dqmax'/1e'n
       cint = subwrd(result,4)
endif

      'shades 'cint
      'define qdif = (qmod-qobs)/1e'n
      'd qdif'
      'cbarn -snum 0.55 -xmid 4.25 -ymid 0.4'

      'set gxout stat'
      'd qdif'
      qdifminmax = sublin(result,8)
      qdifmin    = subwrd(qdifminmax,4)
      qdifmax    = subwrd(qdifminmax,5)
      say 'QDIF_Max Value: 'qdifmax
      say 'QDIF_Min Value: 'qdifmin
      'set gxout shaded'
      'd abs('qdifmin')'
             aqdifmin = subwrd(result,4)
      'd abs('qdifmax')'
             aqdifmax = subwrd(result,4)
      if( aqdifmin > aqdifmax ) ; aqdifmax = aqdifmin ; endif
      say 'Absolute QDIF_MAX: ' aqdifmax

      'set gxout stat'
      'd maskout(qdif,abs(qobs))'
         dqminmax = sublin(result,8)
         dqmin    = subwrd(qminmax,4)
         dqmax    = subwrd(qminmax,5)
      say 'DQMin Value: 'dqmin
      say 'DQMax Value: 'dqmax
      'set gxout shaded'

'stats maskout(qdif,abs(qobs))'
 avgdif = subwrd(result,1)
 stddif = subwrd(result,2)

k = m + n

'set vpage off'
'set string 1 l 4'
'set strsiz 0.065'
'draw string 0.05 0.08 ( EXPID: 'expid'  DESC: 'expdsc' )'


'set string 1 c 6'
'set strsiz .125'
'draw string 4.25 10.85 'title

'set strsiz .11'
if( level = 0 )
if( m != 0 )
   'draw string 4.25 10.62 'expid'  'season' ('nmod')  ('climexp') (x 10**'m')'
else
   'draw string 4.25 10.62 'expid'  'season' ('nmod')  ('climexp')'
endif
   'draw string 4.25 7.22 'cmpid'  'season' ('nobs')  ('climcmp')'
   if( k != 0 )
   'draw string 4.25 3.80 Difference (Top-Middle) (x 10**'k')'
else
   'draw string 4.25 3.80 Difference (Top-Middle)'
endif
else
    if( m != 0 )
   'draw string 4.25 10.62 'expid'  'level'-mb  'season' ('nmod')  ('climexp') (x 10**'m')'
    else
   'draw string 4.25 10.62 'expid'  'level'-mb  'season' ('nmod')  ('climexp')'
    endif
   'draw string 4.25 7.22 'cmpid'  'season' ('nobs')  ('climcmp')'
   if( k != 0 )
   'draw string 4.25 3.80 'level'-mb  Difference (Top-Middle) (x 10**'k')'
   else
   'draw string 4.25 3.80 'level'-mb  Difference (Top-Middle)'
   endif
endif

                date = getdate (begdate)
bmnthm = subwrd(date,1)
byearm = subwrd(date,2)
                date = getdate (enddate)
emnthm = subwrd(date,1)
eyearm = subwrd(date,2)
                date = getdate (begdateo)
bmntho = subwrd(date,1)
byearo = subwrd(date,2)
                date = getdate (enddateo)
emntho = subwrd(date,1)
eyearo = subwrd(date,2)

'set string 1 l 4'
'set strsiz .08'

'set string 4 l 5'
'draw string 0.050 10.30 EXP Dates:'
'set string 1 l 4'
'draw string 0.050 10.17 Beg: 'bmnthm' 'byearm
'draw string 0.050 10.04 End: 'emnthm' 'eyearm
'draw string 0.050 9.70  Max: 'qmodmax
'draw string 0.050 9.55  Min: 'qmodmin
'draw string 0.050 9.25 Mean: 'avgmod
'draw string 0.050 9.10  Std: 'stdmod

'set string 4 l 5'
'draw string 0.050 6.98 CMP Dates:'
'set string 1 l 4'
'draw string 0.050 6.85 Beg: 'bmntho' 'byearo
'draw string 0.050 6.70 End: 'emntho' 'eyearo
'draw string 0.050 6.45  Max: 'qobsmax
'draw string 0.050 6.30  Min: 'qobsmin
'draw string 0.050 6.00 Mean: 'avgobs
'draw string 0.050 5.85  Std: 'stdobs

if( climexp != 'Actual' | climcmp != 'Actual' )
   'set string 2 l 7'
   'draw string 0.050 3.50  WARNING:'
   'set string 1 l 4'
   'draw string 0.050 3.35  Actual Dates'
   'draw string 0.050 3.20  NOT Used!'
else
   'set string 4 l 5'
   'draw string 0.050 3.50  Comparison using:'
   'set string 1 l 4'
   'draw string 0.050 3.35  Actual Dates'
endif

'draw string 0.050 2.90  Max: 'qdifmax
'draw string 0.050 2.75  Min: 'qdifmin
'draw string 0.050 2.45 Mean: 'avgdif
'draw string 0.050 2.30  Std: 'stddif

if( CINTDIFF != 'NULL' )
   'set strsiz .07'
   'draw string 0.050 1.77 Plot represents'
   'draw string 0.050 1.62 values > 'dqrel' %'
   'draw string 0.050 1.47 Relative Difference'
   'draw string 0.050 1.32 ( DQ/QMax )'
endif

'myprint -name 'output'/hdiag_'PRFX''cmpid'_'EXPORT'.'GC'_'level'.'season
'set clab on'

'set mproj latlon'
return

function getdate (date,month,year)
       num = 1
       bit = substr(date,num,1)
while( bit != '' )
       num = num+1
       bit = substr(date,num,1)
endwhile
       loc = num-7
     month = substr(date,loc  ,3)
      year = substr(date,loc+3,4)
return month' 'year

function getlength (string)
tb = ""
i = 1
while (i<=80)
blank = substr(string,i,1)
if( blank = tb )
length = i-1
i = 81
else
i = i + 1
endif
endwhile
return length

function getarg (args,name)
'numargs  'args
 numargs = result
        num = 0
while ( num < numargs )
        num = num + 1
if( subwrd(args,num) = '-'name )
    arg = subwrd(args,num+1)
    say name' = 'arg
    return arg
endif
endwhile
return

