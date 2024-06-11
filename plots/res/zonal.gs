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
say ' '

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
*                Check for TEM_Collection Diagnostic Files under source home directory
* -------------------------------------------------------------------------------------------------

'run getenv "SOURCE"'
             source = result

'run getenv "HISTORYRC"'
             HISTORYRC = result

'!remove     TEM_NAME'
'!/bin/grep  TEM_Collection 'HISTORYRC' > TEM_NAME'
             dummy  = read(TEM_NAME)
             ioflag = sublin( dummy,1 )
             record = sublin( dummy,2 )
             say expid' ioflag: 'ioflag
             say expid' record: 'record
             if( ioflag = 0 )
                 TEM_Collection = subwrd( record,2 )
             else
                 TEM_Collection = 'TEM_Diag'
             endif
             dummy = close(TEM_NAME)
say ' '
say 'EXPID Transformed Eulerian Mean (TEM) Diagnostic Collection: 'TEM_Collection
say '----------------------------------------------------------- '
say ' '
say 'Checking for 'source'/'TEM_Collection'/'expid'.'TEM_Collection'.monthly.ddf'

'!remove   CHECKFILE.txt'
'!chckfile 'source'/'TEM_Collection'/'expid'.'TEM_Collection'.monthly.ddf'
 'run getenv CHECKFILE'
             expid.ddf = result
        say 'expid.ddf: 'expid.ddf
             pause
 
if( expid.ddf = 'NULL' )
*    Check for old format residual.EXPID.data under plot Output directory
*    --------------------------------------------------------------------
     say 'Checking for 'pwd'/../residual.'expid'.ctl'

    '!remove   CHECKFILE.txt'
    '!chckfile 'pwd'/../residual.'expid'.ctl'
     'run getenv CHECKFILE'
                 expid.ctl = result

    '!remove   CHECKFILE.txt'
    '!chckfile 'pwd'/../residual.'expid'.data'
     'run getenv CHECKFILE'
                 expid.data = result

     if( ( expid.ctl = 'NULL' & expid.data != 'NULL' ) | ( expid.ctl != 'NULL' & expid.data = 'NULL' ) )
           say 'Inconsistent 'expid' ctl and data files:'
           say 'expid.ctl : 'expid.ctl
           say 'expid.data: 'expid.data
           return
     endif

     if( expid.ctl != 'NULL' & expid.data != 'NULL' )
        '!/bin/cp 'pwd'/../residual.'expid'.ctl  .'
        '!/bin/cp 'pwd'/../residual.'expid'.data .'

*         Create TEM_Collection Diagnostic data based on old format
*         ---------------------------------------------------------
        '!'geosutil'/plots/grads_util/Create_TEM_ddf.csh 'expid' 'TEM_Collection

          say 'Create TEM_Collection Directory under SOURCE'
*         -------------------------------------------------
        '!/bin/mkdir -p 'source'/'TEM_Collection
        '!/bin/cp 'expid'.'TEM_Collection'.monthly.* 'source'/'TEM_Collection

          say 'Move TEM_Collection Diagnostic data to OUTPUT directory'
*         ------------------------------------------------------------
        '!/bin/mv 'expid'.'TEM_Collection'.monthly.* ../'

        '!remove   CHECKFILE.txt'
        '!chckfile ../'expid'.'TEM_Collection'.monthly.ddf'
         'run getenv CHECKFILE'
                     expid.ddf = result
     endif
     pause
endif
 
* -------------------------------------------------------------------------------------------------
*        Using existing EXPID.TEM_Collection data to create corresponding VERIFICATION rc file
* -------------------------------------------------------------------------------------------------

if( expid.ddf != 'NULL' )
         say 'Creating VERIFICATION.expid.rc associated with existing 'expid'.'TEM_Collection'.monthly.ddf'
             '!remove sedfile'
             '!touch  sedfile'
             '!echo "s?@EXPID?"'expid'?g                                             >> sedfile'
             '!echo "s?@EXPDSC?"'expdsc'?g                                           >> sedfile'
             '!echo "s?@filename?"'expid.ddf'?g                                      >> sedfile'
             '!/bin/cp 'geosutil'/plots/res/VERIFICATION.rc.tmpl .'
             '!sed -f   sedfile VERIFICATION.rc.tmpl > VERIFICATION.'expid'.rc'
             '!remove VERIFICATION.rc.tmpl'
              pause
endif

* -------------------------------------------------------------------------------------------------
*                        Compute EXPID TEM_Diagnostic calculations if needed
                                   if( expid.ddf = 'NULL' )
* -------------------------------------------------------------------------------------------------

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

* Run Fortran Code to Produce Old Format residual.EXPID.ctl and residual.EXPID.data
* ---------------------------------------------------------------------------------
say ' 'geosutil'/plots/zonal_'arch'.x -tag 'expid' -desc 'descm
'!    'geosutil'/plots/zonal_'arch'.x -tag 'expid' -desc 'descm


* Create TEM_Collection Diagnostic data based on old format
* ---------------------------------------------------------
  '!'geosutil'/plots/grads_util/Create_TEM_ddf.csh 'expid' 'TEM_Collection


say 'Create TEM_Collection Directory under SOURCE'
* -----------------------------------------------
  '!/bin/mkdir -p 'source'/'TEM_Collection
  '!/bin/cp 'expid'.'TEM_Collection'.monthly.* 'source'/'TEM_Collection

say 'Move TEM_Collection Diagnostic data to OUTPUT directory'
* ----------------------------------------------------------
  '!/bin/mv 'expid'.'TEM_Collection'.monthly.* ../'

  '!remove   CHECKFILE.txt'
  '!chckfile ../'expid'.'TEM_Collection'.monthly.ddf'
  'run getenv CHECKFILE'
              expid.ddf = result

say 'Creating VERIFICATION.expid.rc associated with 'expid'.'TEM_Collection'.monthly.ddf'
    '!remove sedfile'
    '!touch  sedfile'
    '!echo "s?@EXPID?"'expid'?g                                                             >> sedfile'
    '!echo "s?@EXPDSC?"'expdsc'?g                                                           >> sedfile'
    '!echo "s?@filename?"'expid.ddf'?g                                                      >> sedfile'
    '!/bin/cp 'geosutil'/plots/res/VERIFICATION.rc.tmpl .'
    '!sed -f   sedfile VERIFICATION.rc.tmpl > VERIFICATION.'expid'.rc'
    '!remove VERIFICATION.rc.tmpl'
      pause

* -------------------------------------------------------------------------------------------------
*                               End Computation of EXPID TEM_Diagnostics
                                                endif
* -------------------------------------------------------------------------------------------------



* -------------------------------------------------------------------------------------------------
*                        Loop over Possible Experiment Datasets for Comparison
* -------------------------------------------------------------------------------------------------

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

           '!remove NODE.txt'
           '!basename 'exp' >> NODE.txt'
           'run getenv "NODE"'
                        cmpid = result
say '    CMPID: 'cmpid
pause

'!remove   CHECKFILE.txt'
'!chckfile 'exp'/.HOMDIR'
 'run getenv CHECKFILE'
             CHECKFILE  = result
         if( CHECKFILE != 'NULL' )
            '!/bin/cp `cat 'exp'/.HOMDIR`/HISTORY.rc .'
         else
            '!/bin/cp 'exp'/HISTORY.rc .'
         endif

'!remove     TEM_NAME'
'!/bin/grep  TEM_Collection HISTORY.rc > TEM_NAME'
             dummy  = read(TEM_NAME)
             ioflag = sublin( dummy,1 )
             record = sublin( dummy,2 )
             say cmpid' ioflag: 'ioflag
             say cmpid' record: 'record
             if( ioflag = 0 )
                 TEM_Collection = subwrd( record,2 )
             else
                 TEM_Collection = 'TEM_Diag'
             endif
             dummy = close(TEM_NAME)
say ' '
say 'CMPID Transformed Eulerian Mean (TEM) Diagnostic Collection: 'TEM_Collection
say '----------------------------------------------------------- '
say ' '
pause

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


* Check for Transport Diagnostic Files under comparison experiment directory
* --------------------------------------------------------------------------
  say 'Checking for 'exp'/'TEM_Collection'/'obsid'.'TEM_Collection'.monthly.ddf'

'!remove   CHECKFILE.txt'
'!chckfile 'exp'/'TEM_Collection'/'obsid'.'TEM_Collection'.monthly.ddf'
 'run getenv CHECKFILE'
             obsid.ddf = result
        say 'obsid.ddf: 'obsid.ddf
pause

* Check for old format residual.OBSID.data in plot Output directory
* -----------------------------------------------------------------
if( obsid.ddf = 'NULL' )
    say 'Checking for 'pwd'/../residual.'obsid'.ctl'

    '!remove   CHECKFILE.txt'
    '!chckfile 'pwd'/../residual.'obsid'.ctl'
     'run getenv CHECKFILE'
                 obsid.ctl = result

    '!remove   CHECKFILE.txt'
    '!chckfile 'pwd'/../residual.'obsid'.data'
     'run getenv CHECKFILE'
                 obsid.data = result

     if( ( obsid.ctl = 'NULL' & obsid.data != 'NULL' ) | ( obsid.ctl != 'NULL' & obsid.data = 'NULL' ) )
           say 'Inconsistent 'obsid' ctl and data files:'
           say 'expid.ctl : 'expid.ctl
           say 'expid.data: 'expid.data
           return
     endif

     if( obsid.ctl != 'NULL' & obsid.data != 'NULL' )
        '!/bin/cp 'pwd'/../residual.'obsid'.ctl  .'
        '!/bin/cp 'pwd'/../residual.'obsid'.data .'

        '!'geosutil'/plots/grads_util/Create_TEM_ddf.csh 'obsid' 'TEM_Collection

        '!remove   CHECKFILE.txt'
        '!chckfile 'obsid'.'TEM_Collection'.monthly.ddf'
         'run getenv CHECKFILE'
                     obsid.ddf = result
          say 'obsid.ddf: 'obsid.ddf
          pause
     endif
endif
 
* Check for new format 'obsid'.'TEM_Collection'.monthly.ddf in plot Output directory
* ----------------------------------------------------------------------------------
if( obsid.ddf = 'NULL' )
    say 'Checking for 'pwd'/../'obsid'.'TEM_Collection'.monthly.ddf'

        '!remove   CHECKFILE.txt'
        '!chckfile 'pwd'/../'obsid'.'TEM_Collection'.monthly.ddf'
         'run getenv CHECKFILE'
                     obsid.ddf = result
          say 'obsid.ddf: 'obsid.ddf
          pause
endif

* -------------------------------------------------------------------------------------
*                  Create an associated VERIFICATION.obsid.rc
* -------------------------------------------------------------------------------------

     if( obsid.ddf != 'NULL' )
         say 'Creating VERIFICATION.obsid.rc associated with 'obsid'.'TEM_Collection'.monthly.ddf'
             '!remove sedfile'
             '!touch  sedfile'
             '!echo "s?@EXPID?"'obsid'?g                                                             >> sedfile'
             '!echo "s?@EXPDSC?"'obsdsc'?g                                                           >> sedfile'
             '!echo "s?@filename?"'obsid.ddf'?g                                                      >> sedfile'
             '!/bin/cp 'geosutil'/plots/res/VERIFICATION.rc.tmpl .'
             '!sed -f   sedfile VERIFICATION.rc.tmpl > VERIFICATION.'obsid'.rc'
             '!remove VERIFICATION.rc.tmpl'
     endif

* -------------------------------------------------------------------------------------
* -------------------------------------------------------------------------------------

* Checking for VERIFICATION.obsid.rc
* Note: if VERIFICATION.obsid.rc exists, then its contents should point to 'obsid'.'TEM_Collection'.monthly.ddf
* ----------------------------------------------------------------------------------------------------------
'!remove   CHECKFILE.txt'
'!chckfile VERIFICATION.'obsid'.rc'
 'run getenv CHECKFILE'
             obsid.rc  = result
             say 'obsid.rc = 'obsid.rc
         if( obsid.rc != 'NULL' )
             say 'VERIFICATION.'obsid'.rc exists'
         endif


say  ' '
say  'obsid: 'obsid
say  'obsid.rc: 'obsid.rc
say  ' '
pause

* -------------------------------------------------------------------------------------------------
*                        Compute OBSID TEM_Diagnostic calculations if needed
                             if( obsid != 'ERA5' & obsid.ddf = 'NULL' )
* -------------------------------------------------------------------------------------------------

* Perform residual calculations
* -----------------------------
 
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


'!pwd'
say 'Current Direcory: 'result
pause

* Run Fortran Code to Produce Old Format residual.OBSID.ctl and residual.OBSID.data
* ---------------------------------------------------------------------------------
say ' 'geosutil'/plots/zonal_'arch'.x -tag 'obsid' -desc 'desco
'!    'geosutil'/plots/zonal_'arch'.x -tag 'obsid' -desc 'desco

pause

* Create TEM_Collection Diagnostic data based on old format
* ---------------------------------------------------------
  '!'geosutil'/plots/grads_util/Create_TEM_ddf.csh 'obsid' 'TEM_Collection

  '!remove   CHECKFILE.txt'
  '!chckfile 'obsid'.'TEM_Collection'.monthly.ddf'
  'run getenv CHECKFILE'
              obsid.ddf = result
pause

say 'Creating VERIFICATION.obsid.rc associated with 'obsid'.'TEM_Collection'.monthly.ddf'
*    --------------------------------------------------------------------------------
             '!remove sedfile'
             '!touch  sedfile'
             '!echo "s?@EXPID?"'obsid'?g                                                             >> sedfile'
             '!echo "s?@EXPDSC?"'obsdsc'?g                                                           >> sedfile'
             '!echo "s?@filename?"'obsid.ddf'?g                                                      >> sedfile'
             '!/bin/cp 'geosutil'/plots/res/VERIFICATION.rc.tmpl .'
             '!sed -f   sedfile VERIFICATION.rc.tmpl > VERIFICATION.'obsid'.rc'
             '!remove VERIFICATION.rc.tmpl'
pause

say 'Copying 'obsid' TEM_Collection Diagnostic data to PLOT directory'
* -------------------------------------------------------------------
  '!/bin/cp 'obsid'.'TEM_Collection'.monthly.* ../'
pause


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
