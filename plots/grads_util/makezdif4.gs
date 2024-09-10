function makezdif4 (args)

'numargs  'args
 numargs = result

       abs = FALSE
      name = 'q'
      ptop =  0
       num =  0
while( num < numargs )
       num = num + 1
if( subwrd(args,num)='-q1'    ) ; q1     = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-q2'    ) ; q2     = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-file1' ) ; file1  = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-file2' ) ; file2  = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-name'  ) ; name   = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-ptop'  ) ; ptop   = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-abs'   ) ; abs    = TRUE               ; endif
endwhile

'run getenv "GEOSUTIL"'
             geosutil = result

* Get Current Environment Settings
* --------------------------------
'getinfo file'
        dfile = result

'q gxout'
   gxout = sublin(result,4)
   gxout = subwrd(gxout ,6)

'getinfo zfreq'
         zfreq = result
     if( zfreq = 'varying' )
         'getinfo zmin'
                  zmin = result
         'getinfo zmax'
                  zmax = result
     endif
     if( zfreq = 'fixed' )
         'getinfo zpos'
                  zmin = result
                  zmax = result
     endif

'getinfo tfreq'
         tfreq = result
     if( tfreq = 'varying' )
        'getinfo tmin'
                 tmin = result
        'getinfo tmax'
                 tmax = result
     endif
     if( tfreq = 'fixed' )
        'getinfo time'
                 tmin = result
                 tmax = result
     endif
    'q ctlinfo'
       ctlinfo = result
            n = 1
     while( n > 0 )
             line = sublin(ctlinfo,n)
             word = subwrd(line,1)
         if( word = 'tdef' )
             tinc = subwrd(line,5)
                n = 0
          else
                n = n + 1
          endif
     endwhile
say 'tmin: 'tmin'  tmax: 'tmax'  tinc: 'tinc
'set t 'tmin
'run getinfo date'
     begdate = result
say 'BEGDATE = 'begdate

'getinfo dlat'
         dlat = result
         dlon = dlat
         xdim =   360 / dlon
         ydim = ( 180 / dlat ) + 1
         lon1 = -180
         lon2 =  180 - dlon
say 'dlat = 'dlat'  xdim = 'xdim'  LONS: 'lon1','lon2
say 'dlon = 'dlon'  ydim = 'ydim
pause

'getinfo lonmin'
         lonbeg = result
'getinfo lonmax'
         lonend = result
'getinfo latmin'
         latbeg = result
'getinfo latmax'
         latend = result

* Find ZDIM for each File
* -----------------------
'set dfile 'file1
'getinfo zdim'
         zdim1 = result

'set dfile 'file2
'getinfo zdim'
         zdim2 = result
'set z  'zdim2
        'getinfo level'
                 level = result
if( level >  ptop ) ; ptop = level ; endif
say 'PTOP = 'ptop
*pause

* Create Array of Target Pressure Levels based on File2
* -----------------------------------------------------
levs = ''
nlev = 0
       z = 1
while( z<=zdim2 )
      'set z 'z
      'getinfo level'
               level   = result
               level.z = result
           if( level  >= ptop )
                levs    = levs % level.z % " "
                nlev    = nlev + 1
           endif
       z = z + 1
endwhile

say ''
say 'Number of Target Pressure Levels from File2: 'nlev
say '          Target Pressure Levels from File2: 'levs
say ''


* Create Temporary File at 0.25x0.25 degree resolution with consistent levels
* ---------------------------------------------------------------------------
if( lonbeg != lonend )
   'setlons'
   'getinfo lon'
            lon = result
   if( lon < 0 )
      'set lon   -180 179.75'
           lon = -180
   else
      'set lon   0 359.75'
           lon = 0
   endif
else
   'set x 1'
endif
'set lat -90 90'

* Loop over Time
* --------------
'!remove 'name'.data'
    tdim = tmax-tmin+1
       t = tmin
while( t<= tmax )


* ------------------------------------------------------------
* ------------------------------------------------------------
* Interpolate Q1 Variable to Target Pressure Levels from File2
* ------------------------------------------------------------
* ------------------------------------------------------------

'set dfile 'file1
'set t 't
'run getinfo date'
     curdate = result
say 'CURRENT DATE = 'curdate

* Populate Q1(x=1) for all longitudes
* -----------------------------------
'set x 1'
'sety'
'setz'
'define q1x1 = 'q1
'set lon -180 180'
'define q1tmp = q1x1 + lon-lon'

 z = 1
while( z<=nlev )
       say 'Regrid Q2 to DLATxDLAT-Deg RSLV at File2 Target Pressure: 'level.z
       say '--------------------------------------------------------- '
      'set dfile 'file2
      'set lev 'level.z
      'set x 1'
      'define q2x1 = 'q2
      'set lon -180 180'
      'define qtmp = q2x1 + lon-lon'
      'define qobs = regrid2( qtmp,'dlon','dlat',bs_p1,-180,-90)'
    'undefine qtmp'

       if( z=1 & t=tmin )
          'set gxout stat'
          'd q2x1'
           undef = sublin(result,6)
           undef = subwrd(undef,4)
          'set gxout fwrite'
          'set fwrite 'name'.data'
       endif


       say 'Find File1 Bounding Levels around File2 Target Pressure: 'level.z
       say '---------------------------------------------------------  '
      'set dfile 'file1
       k = 1
      'set z 'k
      'getinfo level'
               level = result
       while(  level > level.z & k < zdim1 )
               k = k + 1
              'set z 'k
              'getinfo level'
                       level = result
       endwhile
*      say 'File1 Bounding Levels to File2 Target Pressure: 'level.z
*      say '----------------------------------------------- '
*      say 'k above: 'k  '  Pressure Above: 'level
       if(  k > 1 )
              'set z 'k-1
              'getinfo level'
                       levm1 = result
       say 'k below: 'k-1'  Pressure Below: 'levm1
              'set z 'k
       endif

       if( level = level.z )
             say 'Q1 Level: 'level' matches Q2 Level: 'level.z
             say 'Simply Regrid Q1 to DLATxDLAT-Deg RSLV at File1 Pressure: 'level
             say '-------------------------------------------------------- '
            'set lon -180 180'
            'define qmod = regrid2( q1tmp,'dlon','dlat',bs_p1,-180,-90)'
                 'set lon 'lon1' 'lon2
                  if( abs = TRUE )
            '         d abs(qmod-qobs)'
                  else
            '         d qmod-qobs'
                  endif
                 'set lon -180 180'

       else

             if( k > 1 )
                 kp1 = k+1
                 kp0 = k
*                            p <= level.z
                 km1 = k-1
                 km2 = k-2

                'set z 'km1
                'getinfo level'
                         levm1 = result
                         PLM1  = math_log(''levm1'')
                'define   qkm1 = q1tmp'

                 if( km1 > 1 & kp0 < zdim1 )
                    'set z 'kp1
                    'getinfo level'
                             levp1 = result
                             PLP1  = math_log(''levp1'')
                    'define   qkp1 = q1tmp'
                     say 'k: 'k'  kp1: 'kp1'  levp1: 'levp1'  LOG(levp1): 'PLP1
         
                    'set z 'kp0
                    'getinfo level'
                             levp0 = result
                             PLP0  = math_log(''levp0'')
                    'define   qkp0 = q1tmp'
                     say 'k: 'k'  kp0: 'kp0'  levp0: 'levp0'  LOG(levp0): 'PLP0

                     P    = math_log(''level.z'')
                     say '      Target Pressure: 'level.z'  LOG(Target) 'P

                     say 'k: 'k'  km1: 'km1'  levm1: 'levm1'  LOG(levm1): 'PLM1

                    'set z 'km2
                    'getinfo level'
                             levm2 = result
                             PLM2  = math_log(''levm2'')
                    'define   qkm2 = q1tmp'
                     say 'k: 'k'  km2: 'km2'  levm2: 'levm2'  LOG(levm2): 'PLM2
  
                     DLP0 = PLP1-PLP0
                     DLM1 = PLP0-PLM1 
                     DLM2 = PLM1-PLM2

                      ap1 = (P-PLP0)*(P-PLM1)*(P-PLM2)/( DLP0*(DLP0+DLM1)*(DLP0+DLM1+DLM2) )
                      ap0 = (PLP1-P)*(P-PLM1)*(P-PLM2)/( DLP0*      DLM1 *(     DLM1+DLM2) )
                      am1 = (PLP1-P)*(PLP0-P)*(P-PLM2)/( DLM1*      DLM2 *(DLP0+DLM1     ) )
                      am2 = (PLP1-P)*(PLP0-P)*(PLM1-P)/( DLM2*(DLM1+DLM2)*(DLP0+DLM1+DLM2) )

                     say 'AP1: 'ap1' AP0: 'ap0' AM1: 'am1' AM2: 'am2' sum: 'ap1+ap0+am1+am2

                    'set z 'k
                    'define qint = 'ap1'*qkp1 + 'ap0'*qkp0 + 'am1'*qkm1 + 'am2'*qkm2'

                     say 'Using Q2 Level   Indices:'kp1' 'kp0' 'km1' 'km2
                     say 'Using Q2 Pressure Levels:'levp1' 'levp0' 'levm1' 'levm2
                     say '------------ '
                 else
                    'set z 'k
                    'define   qint = qkm1 + (qk-qkm1)*( log('level.z'/'levm1') / log('level'/'levm1') )'
*                    say 'Using Levels :'k' ('level') and 'km1' ('levm1')'
*                    say '------------ '
                 endif
             else
                 kp1 = k+1
                'set z 'z
                'getinfo level'
                         levp1 = result
                'define   qkp1 = q1tmp'

                'define   qint = qkp1 + (qk-qkp1)*( log('level.z'/'levp1') / log('level'/'levp1') )'
                 say 'Using Levels :'k' ('level') and 'kp1' ('levp1')'
                 say '------------ '
             endif
            'set lon -180 180'
            'define qmod = regrid2( qint,'dlon','dlat',bs_p1,-180,-90)'
                 'set lon 'lon1' 'lon2
                  if( abs = TRUE )
            '         d abs(qmod-qobs)'
                  else
            '         d qmod-qobs'
                  endif
                 'set lon -180 180'
       endif
             say ' '
*pause
z = z + 1
endwhile
t = t + 1
endwhile
'disable fwrite'

say 'Creating 'name'.ctl'
say 'TDIM: 'tdim

'!remove sedfile'
'!remove 'name'.ctl'
'!echo "s@GRADSDATA@"'name'.data@g > sedfile'
'!echo "s@UNDEF@"'undef'@g        >> sedfile'
'!echo "s@XDIM@"'xdim'@g          >> sedfile'
'!echo "s@YDIM@"'ydim'@g          >> sedfile'
'!echo "s@DLON@"'dlon'@g          >> sedfile'
'!echo "s@DLAT@"'dlat'@g          >> sedfile'
'!echo "s@ZDIM2@"'nlev'@g         >> sedfile'
'!echo "s@TDIM@"'tdim'@g          >> sedfile'
'!echo "s@LEVS@"'levs'@g          >> sedfile'
'!echo "s@BEGDATE@"'begdate'@g    >> sedfile'
'!echo "s@TINC@"'tinc'@g          >> sedfile'
'!sed -f  sedfile 'geosutil'/plots/grads_util/zdiff4.template > 'name'.ctl'

'open 'name'.ctl'
'getinfo    numfiles'
            newfile = result
say 'NEWFILE = 'newfile

'set dfile 'newfile
'setx'
'sety'
'setlons'
'setlats'
'setz'
'set t 1 'tdim
say 'DIMS before: makezf q 'name' z'
'q dims'
say result
say ' '
say 'CAT 'name'.ctl'
'!cat 'name'.ctl'
say ' '

'makezf q 'name' z'

maxval = -1e15
minval =  1e15
'set x 1'
 z = 1
 while( z <= nlev )
'set z 'z
'minmax.simple 'name'z'

 qmax = subwrd(result,1)
 qmin = subwrd(result,2)
 qave = subwrd(result,3)
 qrms = subwrd(result,4)
 qstd = subwrd(result,5)
 qfac = 2

*facmax = (qmax-qave)/qstd
*facmin = (qave-qmin)/qstd
*say 'z: 'z'  facmax: 'facmax'  facmin: 'facmin

 if( qmax > qave + qfac*qstd )
     qmax = qave + qfac*qstd
 endif
 if( qmin < qave - qfac*qstd )
     qmin = qave - qfac*qstd
 endif
 
 if( qmax > maxval ) ; maxval = qmax ; endif
 if( qmin < minval ) ; minval = qmin ; endif
 z = z + 1
 endwhile
*say ' '

'!remove ZDIFILE.txt'
say 'run setenv "ZDIFILE" 'newfile
    'run setenv "ZDIFILE" 'newfile

* Reset Initial Environment Settings
* ----------------------------------
'set gxout 'gxout
'set dfile 'dfile
'set lon 'lonbeg' 'lonend
'set lat 'latbeg' 'latend
'set z 'zmin' 'zmax
'set t 'tmin' 'tmax

return maxval' 'minval
