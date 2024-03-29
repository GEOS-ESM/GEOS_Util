function zonal (args)

* Note: To produce residual data for new verifications, simply continue
*       after quit command to read VERIFICATION.rc prog files.
* ---------------------------------------------------------------------

'run getvar V DYN'
        vname  = subwrd(result,1)
        vfile  = subwrd(result,2)
        vscale = subwrd(result,3)
        expdsc = subwrd(result,4)
        expid  = subwrd(result,5)
'run getvar T DYN'
        tname  = subwrd(result,1)
        tfile  = subwrd(result,2)
'run getvar U DYN'
        uname  = subwrd(result,1)
        ufile  = subwrd(result,2)
'run getvar OMEGA DYN'
        wname  = subwrd(result,1)
        wfile  = subwrd(result,2)

say ' EXPID: 'expid
say 'EXPDSC: 'expdsc

'run getenv "GEOSUTIL"'
         geosutil = result

'run getenv "VERIFICATION"'
         verification = result

'run getenv "ARCH"'
         arch = result

'run getpwd'
        pwd = result

'!/bin/cp 'geosutil'/plots/res/VERIFICATION*rc .'

* -------------------------------------------------------------------------------------------------
* Note: Assume that we ALWAYS want to create an updated residual.EXPID.ctl and residual.EXPID.data
* -------------------------------------------------------------------------------------------------

* Check for residual.EXPID.data under source home directory
* ---------------------------------------------------------
'run getenv "SOURCE"'
             source = result
say 'Checking for 'source'/residual.'expid'.ctl'

'!remove   CHECKFILE.txt'
'!chckfile 'source'/residual.'expid'.ctl'
 'run getenv CHECKFILE'
             expid.ctl = result
'!remove   CHECKFILE.txt'
'!chckfile 'source'/residual.'expid'.data'
 'run getenv CHECKFILE'
             expid.data = result
             expid.ctl = NULL
             pause EXPID.CTL = expid.ctl
 
* Check for residual.EXPID.data under plot Output directory
* ---------------------------------------------------------
if( expid.ctl = 'NULL' )
    say 'Checking for 'pwd'/../residual.'expid'.ctl'

    '!remove   CHECKFILE.txt'
    '!chckfile 'pwd'/../residual.'expid'.ctl'
     'run getenv CHECKFILE'
                 expid.ctl = result
    '!remove   CHECKFILE.txt'
    '!chckfile 'pwd'/../residual.'expid'.data'
     'run getenv CHECKFILE'
                 expid.data = result
                 pause EXPID.DATA = expid.data
endif
 
* Check EP_UPDATE to over-ride defaults
* -------------------------------------
 'run getenv EP_UPDATE'
             EP_UPDATE = result

* Setting EP_UPDATE = TRUE to force re-calculation
* ------------------------------------------------
*            EP_UPDATE = TRUE

if( expid.ctl = 'NULL' | EP_UPDATE != 'NULL' )

*            Updated method to overwrite existing residual.EXPID.data
*            --------------------------------------------------------
         say '!/bin/mv -f 'source'/residual.'expid'.ctl  'source'/residual.'expid'.ctl.old  '
         say '!/bin/mv -f 'source'/residual.'expid'.data 'source'/residual.'expid'.data.old '

         '!remove   CHECKFILE.txt'
         '!chckfile 'source'/residual.'expid'.ctl'
         'run getenv CHECKFILE'
             CHECKFILE  = result
         if( CHECKFILE != 'NULL' )
          '!/bin/mv -f 'source'/residual.'expid'.ctl  'source'/residual.'expid'.ctl.old  '
         endif

         '!remove   CHECKFILE.txt'
         '!chckfile 'source'/residual.'expid'.data'
         'run getenv CHECKFILE'
             CHECKFILE  = result
         if( CHECKFILE != 'NULL' )
          '!/bin/mv -f 'source'/residual.'expid'.data 'source'/residual.'expid'.data.old  '
         endif

         expid.ctl = 'NULL'

else
*            Using existing residual.EXPID.data
*            ----------------------------------
         say 'Using existing residual.EXPID.data'
*            '!/bin/cp 'source'/residual.'expid'.ctl  .'
*            '!/bin/cp 'source'/residual.'expid'.data .'
             '!/bin/cp 'expid.ctl'  .'
             '!/bin/cp 'expid.data' .'
             '!remove sedfile'
             '!touch  sedfile'
             '!echo "s?@EXPID?"'expid'?g   >> sedfile'
             '!echo "s?@EXPDSC?"'expdsc'?g >> sedfile'
             '!echo "s?@pwd?"'pwd'?g       >> sedfile'
             '!/bin/cp 'geosutil'/plots/res/VERIFICATION.rc.tmpl .'
             '!sed -f   sedfile VERIFICATION.rc.tmpl > VERIFICATION.'expid'.rc'
             '!remove VERIFICATION.rc.tmpl'
         endif

say  ' '
say  'expid: 'expid
say  'expid.ctl: 'expid.ctl
say  'expid.data: 'expid.data
say  ' '
*pause

* Perform residual calculations
* -----------------------------
if( expid.ctl = 'NULL' )
 
* Initialize Environment using V-Wind File
* ----------------------------------------
'set dfile 'vfile
'set y 1'
'getinfo lat'
         lat0 = result

'getinfo xdim'
         xdim = result
'getinfo ydim'
         ydim = result
'getinfo zdim'
         zdim = result

'run getenv "TBEG"'
             tbeg = result
'run getenv "TEND"'
             tend = result

if( (tbeg != "NULL") & (tend != "NULL") )
    'run setdates'
endif

'getdates'
'getinfo tmin'
         tmin = result
     if( tmin < 1 )
         tmin = 1
     endif
'getinfo tdim'
         tdim = result
'getinfo tmax'
         tmax = result
     if( tmax > tdim )
         tmax = tdim
     endif
         tdim = tmax-tmin+1

'set t 'tmin
'getinfo date'
      begdate = result
'run setenv "BEGDATE.'expid'" 'begdate


'run setenv    "LAT0.'expid'" 'lat0
'run setenv    "XDIM.'expid'" 'xdim
'run setenv    "YDIM.'expid'" 'ydim
'run setenv    "ZDIM.'expid'" 'zdim
'run setenv    "TDIM.'expid'" 'tdim

'setx'
'sety'
'setz'
'set t 'tmin' 'tmax

'makezf lev-lev zeros z'

* Create Zonal Means
* ------------------

    'set dfile 'vfile
    'makezf    'vname' 'vname' z0'

    'set dfile 'tfile
    'makezf    'tname' 'tname' z0'

    'set dfile 'ufile
    'makezf    'uname' 'uname' z0'

    'set dfile 'wfile
    'makezf    'wname' 'wname' z0'


* Assume VSTS Quadratic is in TFILE
* ---------------------------------
    'set dfile ' tfile 
         rc=checkname(vsts)
     if( rc=0 )
       'makezf vsts vsts z0'
     else
        say '[Vstar Tstar] not found, setting to zero'
       'set x 1'
       'sety'
       'setz'
       'set t 'tmin' 'tmax
       'define vstsz0 = zerosz'
     endif

* Assume USVS Quadratic is in UFILE
* ---------------------------------
    'set dfile ' ufile 
         rc=checkname(usvs)
     if( rc=0 )
       'makezf usvs usvs z0'
     else
        say '[Ustar Vstar] not found, setting to zero'
       'set x 1'
       'sety'
       'setz'
       'set t '1' 'tdim
       'set t 'tmin' 'tmax
       'define usvsz0 = zerosz'
     endif

* Assume USWS Quadratic is in UFILE
* ---------------------------------
    'set dfile ' ufile 
         rc=checkname(usws)
     if( rc=0 )
       'makezf usws usws z0'
     else
        say '[Ustar Wstar] not found, setting to zero'
       'set x 1'
       'sety'
       'setz'
       'set t '1' 'tdim
       'set t 'tmin' 'tmax
       'define uswsz0 = zerosz'
     endif


* Define Pressure Variables
* -------------------------
'set dfile 'vfile
'set x 1'
'sety'
'setz'
'set t 'tmin

'define pl = lat-lat + lev'
'define pk = pow(pl,2/7)'


* Write data
* ----------
'set gxout fwrite'
'set fwrite grads.'expid'.fwrite'

t=tmin
while(t<=tmax)
  'set t 't
   say 'Writing Data Time = 't'  zdim = 'zdim'  EXPID = 'expid

   say '          Writing VZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  vfile != "NULL" ) ; 'd ' vname'z0' ; else ; say  vname' not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing TZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  tfile != "NULL" ) ; 'd ' tname'z0' ; else ; say  tname' not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing VSTSZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  tfile != "NULL" ) ; 'd    vstsz0' ; else ; say 'vsts not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing PL'
   z=1
   while(z<=zdim)
  'set z 'z
  'd pl'
   z=z+1
   endwhile

   say '          Writing PK'
   z=1
   while(z<=zdim)
  'set z 'z
  'd pk'
   z=z+1
   endwhile

   say '          Writing UZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  ufile != "NULL" ) ; 'd ' uname'z0' ; else ; say  uname' not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing USVSZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  ufile != "NULL" ) ; 'd     usvsz0' ; else ; say 'usvs not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing USWSZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  ufile != "NULL" ) ; 'd     uswsz0' ; else ; say 'usws not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing WZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  wfile != "NULL" ) ; 'd ' wname'z0' ; else ; say wname' not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

say ' '
t=t+1
endwhile
'disable fwrite'

* Run Fortran Code to Produce StreamFunction and Residual Circulation
* -------------------------------------------------------------------
say ' 'geosutil'/bin/zonal_'arch'.x -tag 'expid' -desc 'descm
'!    'geosutil'/bin/zonal_'arch'.x -tag 'expid' -desc 'descm

'!remove sedfile'
'!touch  sedfile'

'!echo "s?@EXPID?"'expid'?g >> sedfile'
'!echo "s?@EXPDSC?"'expdsc'?g >> sedfile'
'!echo "s?@pwd?"'pwd'?g >> sedfile'
'!/bin/cp 'geosutil'/plots/res/VERIFICATION.rc.tmpl .'
'!sed -f   sedfile VERIFICATION.rc.tmpl > VERIFICATION.'expid'.rc'
'!remove VERIFICATION.rc.tmpl'

* Copy DATA to plot Output and Source Directory
* ---------------------------------------------
'!/bin/cp -f residual.'expid'.ctl     ../'
'!/bin/cp -f residual.'expid'.data    ../'
'!/bin/cp -f VERIFICATION.'expid'.rc  ../'
'!/bin/cp -f ../residual.'expid'.* ../../'

endif
* -----------------------------------------------------

'run setdates'

* Loop over Possible Experiment Datasets for Comparison
* -----------------------------------------------------
'!/bin/mv HISTORY.T HISTORY.Tmp'
'run getenv "CMPEXP"'
         cmpexp = result
            num = 1

          dummy = get_cmpexp (cmpexp,num)
            exp = subwrd(dummy,1)
           type = subwrd(dummy,2)

while( exp != 'NULL' )
say ' '
say 'Comparing  with: 'exp
say 'Comparison type: 'type

'!remove   CHECKFILE.txt'
'!chckfile 'exp'/.HOMDIR'
 'run getenv CHECKFILE'
             CHECKFILE  = result
         if( CHECKFILE != 'NULL' )
            '!/bin/cp `cat 'exp'/.HOMDIR`/HISTORY.rc .'
         else
            '!/bin/cp 'exp'/HISTORY.rc .'
         endif

'!cat HISTORY.rc | sed -e "s/,/ , /g" | sed -e "s/*/@/g" > HISTORY.T'

'run getvar V DYN 'exp
say 'GETVAR output: 'result
        vname  = subwrd(result,1)
        vfile  = subwrd(result,2)
        vscale = subwrd(result,3)
        obsdsc = subwrd(result,4)
        obsid  = subwrd(result,5)
'run getvar T DYN 'exp
        tname  = subwrd(result,1)
        tfile  = subwrd(result,2)
'run getvar U DYN 'exp
        uname  = subwrd(result,1)
        ufile  = subwrd(result,2)
'run getvar OMEGA DYN 'exp
        wname  = subwrd(result,1)
        wfile  = subwrd(result,2)

say 'Comparison   ID: 'obsid
say 'Comparison Desc: 'obsdsc
pause


* Check for residual.OBSID.data in comparison experiment directory
* Note: if  residual.OBSID.data exists, then create an associated VERIFICATION.obsid.rc
* -------------------------------------------------------------------------------------
  say 'Checking for 'exp'/residual.'obsid'.ctl'
'!remove   CHECKFILE.txt'
'!chckfile 'exp'/residual.'obsid'.ctl'
 'run getenv CHECKFILE'
             obsid.ctl = result
'!remove   CHECKFILE.txt'
'!chckfile 'exp'/residual.'obsid'.data'
 'run getenv CHECKFILE'
             obsid.data = result
             obsid.ctl = NULL

* Check for residual.OBSID.data in plot Output directory
* ------------------------------------------------------
if( obsid.ctl = 'NULL' )
    say 'Checking for 'pwd'/../residual.'obsid'.ctl'
    '!remove   CHECKFILE.txt'
    '!chckfile 'pwd'/../residual.'obsid'.ctl'
     'run getenv CHECKFILE'
                 obsid.ctl = result
    '!remove   CHECKFILE.txt'
    '!chckfile 'pwd'/../residual.'obsid'.data'
     'run getenv CHECKFILE'
                 obsid.data = result
endif
 
* Setting obsid.ctl = NULL to force re-calculation
* ------------------------------------------------
*            obsid.ctl  = 'NULL'

         if( obsid.ctl != 'NULL' )

             say 'Creating VERIFICATION.'obsid'.rc for 'pwd'/../residual.'obsid'.data'
*            '!/bin/cp 'pwd'/../residual.'obsid'.ctl  .'
*            '!/bin/cp 'pwd'/../residual.'obsid'.data .'
             '!/bin/cp 'obsid.ctl'  .'
             '!/bin/cp 'obsid.data' .'
             '!remove sedfile'
             '!touch  sedfile'
             '!echo "s?@EXPID?"'obsid'?g   >> sedfile'
             '!echo "s?@EXPDSC?"'obsdsc'?g >> sedfile'
             '!echo "s?@pwd?"'pwd'?g       >> sedfile'
             '!/bin/cp 'geosutil'/plots/res/VERIFICATION.rc.tmpl .'
             '!sed -f   sedfile VERIFICATION.rc.tmpl > VERIFICATION.'obsid'.rc'
             '!remove VERIFICATION.rc.tmpl'
 
         endif

* Checking for VERIFICATION.obsid.rc
* Note: if VERIFICATION.obsid.rc exists, then its contents should point to residual.'obsid'.ctl 
* ---------------------------------------------------------------------------------------------
'!remove   CHECKFILE.txt'
'!chckfile VERIFICATION.'obsid'.rc'
 'run getenv CHECKFILE'
             obsid.rc  = result
             say 'obsid.rc = 'obsid.rc
         if( obsid.rc != 'NULL' )
             say 'VERIFICATION.'obsid'.rc exists'
         endif


* Setting obsid.rc = NULL to force re-calculation
* -----------------------------------------------
*            obsid.rc = 'NULL'

say  ' '
say  'obsid: 'obsid
say  'obsid.ctl: 'obsid.ctl
say  'obsid.data: 'obsid.data
say  'obsid.rc: 'obsid.rc
say  ' '
*pause

* Perform residual calculations
* -----------------------------
         if( obsid != 'ERA5' & ( obsid.ctl = 'NULL' | obsid.rc = 'NULL' ) )
 
'set dfile 'vfile
'set y 1'
'getinfo lat'
         lat0 = result
'setx'
'sety'
'setz'

'run getdates'
 begdateo = subwrd(result,1)
 enddateo = subwrd(result,2)

'getinfo tmin'
         tmin = result
'getinfo tmax'
         tmax = result

'set t 'tmin
'getinfo   date'
        begdate = result

'run setenv   "BEGDATEO" 'begdateo
'run setenv   "ENDDATEO" 'enddateo
'set t 'tmin' 'tmax
        tdim = tmax-tmin+1

    'getinfo   xdim'
               xdim = result
    'getinfo   ydim'
               ydim = result
    'getinfo   zdim'
               zdim = result

'run setenv    "LAT0.'obsid'" 'lat0
'run setenv    "XDIM.'obsid'" 'xdim
'run setenv    "YDIM.'obsid'" 'ydim
'run setenv    "ZDIM.'obsid'" 'zdim
'run setenv    "TDIM.'obsid'" 'tdim
'run setenv "BEGDATE.'obsid'" 'begdate

'makezf lev-lev zeros z'

* Create Zonal Means
* ------------------

    'set dfile 'vfile
    'makezf    'vname' 'vname' z'num

    'set dfile 'tfile
    'makezf    'tname' 'tname' z'num

    'set dfile 'ufile
    'makezf    'uname' 'uname' z'num

    'set dfile 'wfile
    'makezf    'wname' 'wname' z'num

* Assume VSTS Quadratic is in TFILE
* ---------------------------------
    'set dfile ' tfile 
         rc=checkname(vsts)
     if( rc=0 )
       'makezf vsts vsts z'num
else
       'set x 1'
       'sety'
       'setz'
       'set t 'tmin' 'tmax
        say 'vsts not found, setting to zero ... '
       'define vstsz'num' = zerosz'
endif

* Assume USVS Quadratic is in UFILE
* ---------------------------------
    'set dfile ' ufile 
         rc=checkname(usvs)
     if( rc=0 )
       'makezf usvs usvs z'num
else
       'set x 1'
       'sety'
       'setz'
       'set t 'tmin' 'tmax
        say 'usvs not found, setting to zero ... '
       'define usvsz'num' = zerosz'
endif

* Assume USWS Quadratic is in UFILE
* ---------------------------------
    'set dfile ' ufile 
         rc=checkname(usws)
     if( rc=0 )
       'makezf usws usws z'num
else
       'set x 1'
       'sety'
       'setz'
       'set t 'tmin' 'tmax
        say 'usws not found, setting to zero ... '
       'define uswsz'num' = zerosz'
endif


* Define Pressure Variables
* -------------------------
'set dfile 'vfile
'set x 1'
'sety'
'setz'
'set t 'tmin

'define pl = lev'
'define pk = pow(pl,2/7)'


* Write data
* ----------
'set gxout fwrite'
'set fwrite grads.'obsid'.fwrite'

      t =tmin
while(t<=tmax)
  'set t 't
   say 'Writing Data Time = 't'  zdim = 'zdim'  CMPID = 'obsid

   say '          Writing VZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  vfile != "NULL" ) ; 'd ' vname'z'num ; else ; say vname' not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing TZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  tfile != "NULL" ) ; 'd ' tname'z'num ; else ; say tname' not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing VSTSZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  tfile != "NULL" ) ; 'd    vstsz'num ; else ; say 'vsts not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing PL'
   z=1
   while(z<=zdim)
  'set z 'z
  'd pl'
   z=z+1
   endwhile

   say '          Writing PK'
   z=1
   while(z<=zdim)
  'set z 'z
  'd pk'
   z=z+1
   endwhile

   say '          Writing UZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  ufile != "NULL" ) ; 'd ' uname'z'num ; else ; say uname' not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing USVSZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  ufile != "NULL" ) ; 'd     usvsz'num ; else ; say 'usvs not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing USWSZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  ufile != "NULL" ) ; 'd     uswsz'num ; else ; say 'usws not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

   say '          Writing WZ'
   z=1
   while(z<=zdim)
  'set z 'z
   if(  wfile != "NULL" ) ; 'd ' wname'z'num ; else ; say wname' not found, setting to zero ... ' ; 'd zerosz' ; endif
   z=z+1
   endwhile

say ' '
t=t+1
endwhile
'disable fwrite'

* Run Fortran Code to Produce StreamFunction and Residual Circulation
* -------------------------------------------------------------------
say ' 'geosutil'/bin/zonal_'arch'.x -tag 'obsid' -desc 'desco
'!    'geosutil'/bin/zonal_'arch'.x -tag 'obsid' -desc 'desco

'!remove sedfile'
'!touch  sedfile'

'!echo "s?@EXPID?"'obsid'?g >> sedfile'
'!echo "s?@EXPDSC?"'obsdsc'?g >> sedfile'
'!echo "s?@pwd?"'pwd'?g >> sedfile'
'!/bin/cp 'geosutil'/plots/res/VERIFICATION.rc.tmpl .'
'!sed -f   sedfile VERIFICATION.rc.tmpl > VERIFICATION.'obsid'.rc'
'!remove VERIFICATION.rc.tmpl'
'!cat sedfile'

* Copy DATA to Output Directory
* -----------------------------
'!/bin/cp -f residual.'obsid'.ctl     ../'
'!/bin/cp -f residual.'obsid'.data    ../'
'!/bin/cp -f VERIFICATION.'obsid'.rc  ../'

* End VERIFICATION.obsid.rc CHECKFILE Test
* ----------------------------------------
endif
'!remove CHECKFILE.txt'

* Check next Comparison Experiment Dataset
* ----------------------------------------
    num = num + 1
  dummy = get_cmpexp (cmpexp,num)
    exp = subwrd(dummy,1)
   type = subwrd(dummy,2)
endwhile

'!/bin/mv HISTORY.Tmp HISTORY.T'

'quit'
return

* Get Next EXP from CMPEXP List
* -----------------------------
function get_cmpexp (cmpexp,num)
      exp  = subwrd(cmpexp,num)
      len = get_length (exp)
      bit = substr(exp,len-1,1)
      if( bit = ":" )
          type = substr(exp,len,1)
          exp  = substr(exp,1,len-2)
      else
          type = M
      endif
return exp' 'type

function get_length (string)
tb = ""
i = 1
while (i<=256)
blank = substr(string,i,1)
if( blank = tb )
length = i-1
i = 999
else
i = i + 1
endif
endwhile
return length

  function checkname (args)
                name = subwrd(args,1)
  'lowercase   'name
                name = result

  say 'Inside checkname, name = 'name

  'query file'
  numvar = sublin(result,6)
  numvar = subwrd(numvar,5)

  rc = -1
  n  = 1
  while ( n<numvar+1 )
  field = sublin(result,6+n)
  field = subwrd(field,1)
        if( name=field )
          rc = 0
           n = numvar
        endif
  say 'n: 'n' name: 'name' File_field: 'field' rc = 'rc
  n = n+1
  endwhile

  return rc
