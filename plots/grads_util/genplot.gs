function genplot (args)

*******************************************************
****                 INPUT Variables               ****
*******************************************************

'numargs  'args
 numargs = result

PREFIX = NULL
TAYLOR = FALSE
LAND   = FALSE
OCEAN  = FALSE
SCALE  = 1.0
RC     = NULL
LEVEL  = NULL
MATH   = NULL

    numMGCs = 0
    numOGCs = 0

          m = 0
          n = 0
        num = 0
while ( num < numargs )
        num = num + 1

if( subwrd(args,num) = '-DIR'    ) ; DIR    = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-NAME'   ) ; NAME   = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-MATH'   ) ; MATH   = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-EXPID'  ) ; EXPID  = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-OUTPUT' ) ; OUTPUT = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-DEBUG'  ) ; DEBUG  = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-SCALE'  ) ; SCALE  = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-PREFIX' ) ; PREFIX = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-RC'     ) ; RC     = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-LEVEL'  ) ; LEVEL  = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-LAND'   ) ; LAND   = TRUE               ; endif
if( subwrd(args,num) = '-OCEAN'  ) ; OCEAN  = TRUE               ; endif
if( subwrd(args,num) = '-TAYLOR' ) ; TAYLOR = TRUE               ; endif

* Read Model EXPORT:GC
* --------------------
* Note: Each Model Diagnostic may be associated with multiple Model EXPORTs.
*       Each Model EXPORT         is associated with a Specific Model Gridded Component (GC)
* ------------------------------------------------------------------------------------------

if( subwrd(args,num) = '-EXPORT' )
              m = m + 1
       EXPORT.m = subwrd(args,num+m   )
           word = subwrd(args,num+m+1 )
            bit = checkbit(word)
       while( bit != '-' )
              m = m + 1
       EXPORT.m = subwrd(args,num+m   )
           word = subwrd(args,num+m+1 )
            bit = checkbit(word)
       endwhile
         numMGCs = m

       say ' '
       say 'Input Model EXPORT List, numMGCs: 'numMGCs
       numMGC = 1
       while( numMGC <= numMGCs )
       say numMGC': 'EXPORT.numMGC
       numMGC = numMGC + 1
       endwhile
       say ' '
endif

* Read Verification OBS:OBSGC
* ---------------------------
* Note: Each Observation Diagnostic may be associated with multiple Observation EXPORTs.
*       Each Observation EXPORT         is associated with a Specific Observation Gridded Component (GC)
* ------------------------------------------------------------------------------------------------------

if( subwrd(args,num) = '-OBS' )
              n = n + 1
          OBS.n = subwrd(args,num+n   )
           word = subwrd(args,num+n+1 )
            bit = checkbit(word)
       while( bit != '-' )
              n = n + 1
          OBS.n = subwrd(args,num+n   )
           word = subwrd(args,num+n+1 )
            bit = checkbit(word)
       endwhile

         numOGCs = n

       say ' '
       say 'Input OBS EXPORT List, numOGCs: 'numOGCs
       numOGC = 1
       while( numOGC <= numOGCs )
       say numOGC': 'OBS.numOGC
       numOGC = numOGC + 1
       endwhile
       say ' '
endif

* Read SEASONS
* -----------
if( subwrd(args,num) = '-SEASON' )
     seasons = ''
           k = 1
    while( k > 0 )
           L = num + k
        season  = subwrd(args,L)
    if( season  = '' )
        k = -1
    else
        bit = substr(season,1,1)
        if( bit = '-' )
              k = -1
        else
              seasons = seasons % ' ' % season
              k = k+1
        endif
    endif
    endwhile
endif

endwhile


* Construct Model GCs from Model EXPORTS
* --------------------------------------
        m  = 0
        k  = 1
while ( k <= numMGCs )
        EX = ''
         j = 1
       bit = substr(EXPORT.k,j,1)
       while(bit != ':' & bit != '')
        EX = EX''bit
         j = j + 1
       bit = substr(EXPORT.k,j,1)
       endwhile
       if( EX != EXPORT.k )
         m = m + 1
         j = j + 1
       GC.m = ''
       bit = substr(EXPORT.k,j,1)
       while(bit != '')
       GC.m = GC.m''bit
         j = j + 1
       bit = substr(EXPORT.k,j,1)
       endwhile
       EXPORT.k = EX
       endif
k = k + 1
endwhile


* Construct OBS GCs from OBS EXPORTS
* ----------------------------------
if( numOGCs = 0 )

*   Assume OBS GCs are identical to Model GCs
*   -----------------------------------------
    numOGCs = numMGCs
           n  = 1
   while ( n <= numOGCs )
       OBS.n = EXPORT.n
     OBSGC.n =     GC.n
           n = n + 1
   endwhile

else
           n  = 0
           k  = 1
   while ( k <= numOGCs )
           EX = ''
            j = 1
          bit = substr(OBS.k,j,1)
          while(bit != ':' & bit != '')
           EX = EX''bit
            j = j + 1
          bit = substr(OBS.k,j,1)
          endwhile
          if( EX != OBS.k )
            n = n + 1
            j = j + 1
          OBSGC.n = ''
          bit = substr(OBS.k,j,1)
          while(bit != '')
          OBSGC.n = OBSGC.n''bit
            j = j + 1
          bit = substr(OBS.k,j,1)
          endwhile
          OBS.k = EX
          endif
   k = k + 1
   endwhile
endif

**************************************************
**************************************************

* Initialize
* ----------
'reinit'
'set display color white'
'set clab off'
'c'

'run getenv "GEOSUTIL"'
             geosutil = result

'run getenv "VERIFICATION"'
             verification = result

'run uppercase 'seasons
                seasons = result

'run getenv "CMPEXP_ONLY"'
             cmpexp_only = result

**************************************************
****            Echo Calling Sequence         ****
**************************************************

say ' '
say 'NAME   = 'NAME
say 'EXPID  = 'EXPID
say 'OUTPUT = 'OUTPUT
say 'DEBUG  = 'DEBUG
say 'SCALE  = 'SCALE
say 'RC     = 'RC
say 'LAND   = 'LAND
say 'OCEAN  = 'OCEAN
say 'TAYLOR = 'TAYLOR
say 'SEASON = 'seasons
say ' '

m = 1
while( m<=numMGCs )
   say 'EXPORT.'m' = 'EXPORT.m
   say '    GC.'m' = 'GC.m
m = m + 1
endwhile
say ' '

n = 1
while( n<=numOGCs )
   say '   OBS.'n' = 'OBS.n
   say ' OBSGC.'n' = 'OBSGC.n
n = n + 1
endwhile
say ' '

**************************************************
**************************************************

* Get Model Variable Parameters for each Model EXPORT needed for Diagnostic
* -------------------------------------------------------------------------
        m  = 1
while ( m <= numMGCs )
'run getvar 'EXPORT.m' 'GC.m
        qname.m = subwrd(result,1)
        qfile.m = subwrd(result,2)
        qscal.m = subwrd(result,3)
        qdesc.m = subwrd(result,4)
         qtag.m = subwrd(result,5)
    if( qname.m = 'NULL' ) ; return ; endif
         m  = m + 1
endwhile


* Set proper ZDIM
* ---------------
 'set dfile 'qfile.1
 'getlevs   'qname.1
    nlevs = result
if( nlevs != 'NULL' )
   'run setenv "ZDIM" 'nlevs
endif


* Ensure NAMES have no underscores
* --------------------------------
        m=1
while ( m<numMGCs+1 )
'fixname 'qname.m
          alias.m = result
say 'Alias #'m' = 'alias.m
        m = m+1
endwhile


* Set Geographic Environment from Model Dataset
* ---------------------------------------------
'set dfile 'qfile.1
'setlons'
'setlats'
'getinfo dlon'
         dlon = result
'getinfo dlat'
         dlat = result
'getinfo lonmin'
         lonmin = result
'getinfo latmin'
         latmin = result

* Check for Model Name Consistency
* --------------------------------
 m = 1
while( m <= numMGCs )
'set dfile 'qfile.m
if( LEVEL = "NULL" )
   'set z 1'
else
   'set lev 'LEVEL
endif
'sett'
if( qname.m != alias.m ) ; 'rename 'qname.m ' 'alias.m ; endif
m = m + 1
endwhile

* Set BEGDATE and ENDDATE for Seasonal Calculations
* -------------------------------------------------
'setdates'

* Extract Beginning and Ending Dates for Plots
* --------------------------------------------
'run getenv "BEGDATE"'
             begdate  = result
'run getenv "ENDDATE"'
             enddate  = result

'getdates'
   bdate = subwrd(result,1)
   edate = subwrd(result,2)

if( begdate = "NULL" )
   'set dfile 'qfile.1
   'set t    '1
   'getinfo date'
         begdate = result
endif
if( enddate = "NULL" )
   'set dfile 'qfile.1
   'getinfo tdim'
            tdim     = result
   'set t  'tdim
   'getinfo date'
         enddate = result
endif


* Land/Water Masks
* ----------------
if( LAND = 'TRUE' | OCEAN = 'TRUE' )
   'set t 1'
   'setmask     mod'
   'define lwmaskmod = regrid2( lwmaskmod,0.25,0.25,bs_p1,'lonmin','latmin')'
   'define  omaskmod = maskout( 1, lwmaskmod-0.5 )'
   'define  lmaskmod = maskout( 1, 0.5-lwmaskmod )'
endif


* Perform Model Formula Calculation
* ---------------------------------
'set dfile 'qfile.1
'sett'
if( numMGCs = 1 )
   'define qmod = 'alias.1'.'qfile.1'*'qscal.1
else
    filename  = geosutil'/plots/'NAME'/modform.gs'
    ioflag    = sublin( read(filename),1 )
    if(ioflag = 0)
       close  = close(filename)
       mstring = ''
               m  = 1
       while ( m <= numMGCs )
          if( qname.m != alias.m )
              mstring = mstring' 'alias.m'*'qscal.m
          else
              mstring = mstring' 'alias.m'.'qfile.m'*'qscal.m
          endif
              m  = m + 1
       endwhile
      'run 'geosutil'/plots/'NAME'/modform 'mstring
    else
       mstring = NAME
               m  = 1
       while ( m <= numMGCs )
          if( qname.m != alias.m )
              mstring = mstring' 'alias.m'*'qscal.m
          else
              mstring = mstring' 'alias.m'.'qfile.m'*'qscal.m
          endif
              m  = m + 1
       endwhile
      'run 'geosutil'/plots/'DIR'/'NAME'.gs 'mstring
      'define qmod = 'NAME'.1'
    endif
endif
                          'define qmod = regrid2( qmod,0.25,0.25,bs_p1,'lonmin','latmin')'
if(    LAND  = 'TRUE'   |  OCEAN = 'TRUE' )
   if( LAND  = 'TRUE' ) ; 'define qmod = maskout( 'SCALE'*qmod,lmaskmod )' ; endif
   if( OCEAN = 'TRUE' ) ; 'define qmod = maskout( 'SCALE'*qmod,omaskmod )' ; endif
else
                          'define qmod =          'SCALE'*qmod'
endif

'seasonal qmod'

'q dims'
 say 'Model Environment:'
 say result

* Compute CLIMATOLOGY Flag for EXP
* --------------------------------
            'getdates'
'run getenv "CLIMATE"'
             climexp = result

say 'EXP CLIMATE = 'climexp
say ' '


* Create Dummy File with REGRID Dimensions
* ----------------------------------------
  'define qmodr = qmod'
  'getinfo undef'
           undef = result
  'set sdfwrite -5d regrid.nc4'
  'set undef 'undef
  'sdfwrite qmodr'
  'sdfopen regrid.nc4'
  'getinfo    numfiles'
              rgfile = result


***********************************************************************************
*              Loop over Possible Experiment Datasets for Comparison
***********************************************************************************

'!/bin/mv HISTORY.T HISTORY.Tmp'
'run getenv "CMPEXP"'
         cmpexp = result
         numexp = 1

          dummy = get_cmpexp (cmpexp,numexp)
            exp = subwrd(dummy,1)
           type = subwrd(dummy,2)
     exp.numexp = exp
    type.numexp = type

while( exp != 'NULL' )
say ' '
say 'Creating Plots for Comparison Experiment #'numexp': 'exp
say '--------------------------------------------'
say ' '

* analysis = false  EXP=M CMP=M  => ALEVS
* analysis = false  EXP=M CMP=A  => DLEVS
* analysis = true   EXP=A CMP=A  => ALEVS
* analysis = true   EXP=A CMP=M  => DLEVS

* INPUT Experiment is an Analysis
*********************************
if( analysis != "false" )
    if( type = A | type = V )
*   CMP Experiment is an Analysis
       'run setenv "LEVTYPE" 'ALEVS
       'run setenv "DIFFTYPE" 'A

    else
*   CMP Experiment is an Model
       'run setenv "LEVTYPE" 'DLEVS
       'run setenv "DIFFTYPE" 'D
    endif
else

* INPUT Experiment is a Model
*********************************
    if( type = A )
*   CMP Experiment is an Analysis
       'run setenv "LEVTYPE" 'DLEVS
       'run setenv "DIFFTYPE" 'D

    else
*   CMP Experiment is an Model
       'run setenv "LEVTYPE" 'ALEVS
       'run setenv "DIFFTYPE" 'A
    endif
endif

* ------------------------------------------------------

'!chckfile 'exp'/.HOMDIR'
 'run getenv CHECKFILE'
         CHECKFILE  = result
     if( CHECKFILE != 'NULL' )
        '!/bin/cp `cat 'exp'/.HOMDIR`/HISTORY.rc .'
     else
        '!/bin/cp 'exp'/HISTORY.rc .'
     endif
'!remove CHECKFILE.txt'

'!cat HISTORY.rc | sed -e "s/,/ , /g" | sed -e "s/*/@/g" > HISTORY.T'

* Get EXP Comparison Variables
* ----------------------------
FOUND = TRUE
        m  = 1
while ( m <= numMGCs & FOUND = TRUE )
'run getvar 'EXPORT.m' 'GC.m' 'exp
        cname.numexp.m = subwrd(result,1)
        cfile.numexp.m = subwrd(result,2)
        cscal.numexp.m = subwrd(result,3)
        cdesc.numexp.m = subwrd(result,4)
         ctag.numexp.m = subwrd(result,5)

        say ''
        say 'cname.numexp.m = 'cname.numexp.m
        say 'cfile.numexp.m = 'cfile.numexp.m
        say 'cscal.numexp.m = 'cscal.numexp.m
        say ' ctag.numexp.m = ' ctag.numexp.m
        say ''
    
    if( cname.numexp.m = 'NULL' ) ; FOUND = FALSE ; endif
         m  = m + 1
endwhile

if( FOUND = TRUE )
'setlons'
'setlats'

* Land/Water Masks
* ----------------
if( LAND = 'TRUE' | OCEAN = 'TRUE' )
   'set dfile 'cfile.numexp.1
if( LEVEL = "NULL" )
   'set z 1'
else
   'set lev 'LEVEL
endif
   'set t 1'
*  'setmask     obs'
*  'define lwmaskobs = regrid2( lwmaskobs,0.25,0.25,bs_p1,'lonmin','latmin')'
   'define lwmaskobs = lwmaskmod'
   'define  omaskobs = maskout( 1, lwmaskobs-0.5 )'
   'define  lmaskobs = maskout( 1, 0.5-lwmaskobs )'
endif

'set dfile 'cfile.numexp.1
if( LEVEL = "NULL" )
   'set z 1'
else
   'set lev 'LEVEL
endif

* Find Beginning and Ending Dates associated with Comparison Experiment
* ---------------------------------------------------------------------
    'getdates'
     begdate.numexp = subwrd(result,1)
     enddate.numexp = subwrd(result,2)

* Perform OBS Formula Calculation
* -------------------------------
if( numMGCs = 1 )
   'define cmod'numexp' = 'cname.numexp.1'.'cfile.numexp.1'*'cscal.numexp.1
else
    filename  = geosutil'/plots/'NAME'/modform.gs'
    ioflag    = sublin( read(filename),1 )
    if(ioflag = 0)
       close  = close(filename)
       cstring = ''
       n  = 1
       while ( n <= numMGCs )
          cstring = cstring' 'cname.numexp.n'.'cfile.numexp.n'*'cscal.numexp.n
               n  = n + 1
       endwhile
      'run 'geosutil'/plots/'NAME'/modform 'cstring
      'define cmod'numexp' = qmod'
    else
       cstring = NAME
       n  = 1
       while ( n <= numMGCs )
          ostring = ostring' 'cname.numexp.n'.'cfile.numexp.n'*'cscal.numexp.n
               n  = n + 1
       endwhile
      'run 'geosutil'/plots/'DIR'/'NAME'.gs 'ostring
      'define cmod'numexp' = 'NAME'.1'
    endif
endif

* Check for MERRA Resolution problem
* ----------------------------------
'getinfo xdim'
         xdim = result
if( xdim != 540 )

                              'define cmod'numexp' = regrid2( cmod'numexp',0.25,0.25,bs_p1,'lonmin','latmin')'
    if(    LAND  = 'TRUE'   |  OCEAN = 'TRUE' )
       if( LAND  = 'TRUE' ) ; 'define cmod'numexp' = maskout( 'SCALE'*cmod'numexp',lmaskobs )' ; endif
       if( OCEAN = 'TRUE' ) ; 'define cmod'numexp' = maskout( 'SCALE'*cmod'numexp',omaskobs )' ; endif
    else
                              'define cmod'numexp' =          'SCALE'*cmod'numexp
    endif

else

*                             'define cmod'numexp' = regrid2( cmod'numexp','dlon','dlat',bs_p1,'lonmin','latmin')'
                              'define cmod'numexp' = regrid2( cmod'numexp',0.25,0.25,bs_p1,'lonmin','latmin')'
    if(    LAND  = 'TRUE'   |  OCEAN = 'TRUE' )
       if( LAND  = 'TRUE' ) ; 'define cmod'numexp' = maskout( 'SCALE'*cmod'numexp',lmaskobs )' ; endif
       if( OCEAN = 'TRUE' ) ; 'define cmod'numexp' = maskout( 'SCALE'*cmod'numexp',omaskobs )' ; endif
    else
                              'define cmod'numexp' =          'SCALE'*cmod'numexp
    endif

endif

* Compute Seasonal Means
* ----------------------
'seasonal cmod'numexp


***********************************************************************************

            say ' '
           'q dims'
            say 'CMPEXP  Environment:'
            say result

*              Compute CLIMATOLOGY Flag for CMPEXP
*              Note: CMP Parameters are associated with 1st EXPORT component
*              -------------------------------------------------------------
               'run getenv "CLIMATE"'
                                  climate.numexp = result
                        cmpfile =   cfile.numexp.1
                        cmpdsc  =   cdesc.numexp.1
                  cmpnam.numexp =    ctag.numexp.1

            say 'numexp  = 'numexp
            say 'cmpnam.'numexp' = 'cmpnam.numexp
            say 'climate.'numexp' = 'climate.numexp
                         cmpnam   =  cmpnam.numexp
                 climcmp.cmpnam   =  climate.numexp
            say 'climcmp.'cmpnam' = 'climcmp.cmpnam
            say ' '


* Loop over Seasons to Process
* ----------------------------
       m = 1
while( m > 0 )
    season = subwrd(seasons,m)
if( season = '' )
         m = -1
else
         m = m+1
         say 'Processing Season: 'season

'set dfile 'qfile.1
'set gxout shaded'
'rgbset'

* Horizontal Plot
* ---------------
       mathparm  =  MATH
while( mathparm != 'DONE' )
        flag = ""
while ( flag = "" )

'makplot -MVAR 'qmod' -MNAME 'NAME ' -MFILE 'qfile.1' -MDESC 'qdesc.1' -MBEGDATE 'bdate' -MENDDATE 'edate' -OVAR 'cmod''numexp' -ONAME 'ctag.numexp.1' -OFILE 'cfile.numexp.1' -ODESC 'cdesc.numexp.1' -OBEGDATE 'begdate.numexp' -OENDDATE 'enddate.numexp' -EXPID 'EXPID' -PREFIX 'PREFIX' -SEASON 'season' -OUTPUT 'OUTPUT' -CLIMEXP 'climexp' -CLIMCMP 'climcmp.cmpnam' -GC 'GC.1' -MATH 'mathparm

 if( DEBUG = "debug" )
     say "Hit ENTER to repeat plot, or NON-BLANK to continue"
     pull flag
 else
     flag = "next"
 endif
'c'
endwhile ;* END While_FLAG Loop
       if( mathparm != 'NULL' )
           mathparm  = 'NULL'
       else
           mathparm  = 'DONE'
       endif
endwhile ;* END While_MATH Loop

* Zonal Mean Plot
* ---------------
       mathparm  =  MATH
while( mathparm != 'DONE' )
        flag = ""
while ( flag = "" )

'makplotz -MVAR 'qmod' -MNAME 'NAME ' -MFILE 'qfile.1' -MDESC 'qdesc.1' -MBEGDATE 'bdate' -MENDDATE 'edate' -OVAR 'cmod''numexp' -ONAME 'ctag.numexp.1' -OFILE 'cfile.numexp.1' -ODESC 'cdesc.numexp.1' -OBEGDATE 'begdate.numexp' -OENDDATE 'enddate.numexp' -EXPID 'EXPID' -PREFIX 'PREFIX' -SEASON 'season' -OUTPUT 'OUTPUT' -CLIMATE 'climcmp.cmpnam' -GC 'GC.1' -MATH 'mathparm' -RGFILE 'rgfile

 if( DEBUG = "debug" )
     say "Hit ENTER to repeat plot, or NON-BLANK to continue"
     pull flag
 else
     flag = "next"
 endif
'c'
endwhile ;* END While_FLAG Loop
       if( mathparm != 'NULL' )
           mathparm  = 'NULL'
       else
           mathparm  = 'DONE'
       endif
endwhile ;* END While_MATH Loop


* End Season Test
* ---------------
endif
* End Season Loop
* ---------------
endwhile
* End FOUND Test
* --------------
endif

* Check next Comparison Experiment Dataset
* ----------------------------------------
 numexp = numexp + 1
  dummy = get_cmpexp (cmpexp,numexp)
    exp = subwrd(dummy,1)
   type = subwrd(dummy,2)
   exp.numexp = exp
  type.numexp = type

endwhile
 numexp = numexp - 1

'!/bin/mv HISTORY.Tmp HISTORY.T'

* ---------------------------------------------------------------------------
* Now that we have computed plots for each experiment,
* we can compute the Closeness plots to MERRA-2 and any CMPEXP ending with :V
* ---------------------------------------------------------------------------

       k  = 1
while( k <= numexp )
say ' '
say 'Looping through experiments, k = 'k' CTAG = 'ctag.k.1' TYPE = 'type.k
say '--------------------------------------------------------------'
say ' '

if( ( ctag.k.1 = "MERRA-2" | type.k = V ) & cname.k.1 != 'NULL' )
     TAG   = k
     say 'Performing Closeness plots to: 'ctag.TAG.1' k = 'k
     say '------------------------------------------------'

* Loop over Seasons to Process
* ----------------------------
       m = 1
while( m > 0 )
    season = subwrd(seasons,m)
if( season = '' )
         m = -1
else
         m = m+1
         say 'Processing Season: 'season

'set dfile 'qfile.1
'set gxout shaded'
'rgbset'
'run getenv "DIFFTYPE"'
             DIFFTYPE = result
'run setenv "LEVTYPE" 'DIFFTYPE'LEVS'

* Horizontal Closeness Plot (Experiment_vs_Comparison to Verification)
* --------------------------------------------------------------------
       mathparm  =  MATH
while( mathparm != 'DONE' )

       n  = 1
while( n <= numexp )

     say 'n = 'n' Testing 'qtag.1' and 'ctag.n.1' for closeness with 'ctag.TAG.1

     if( ctag.n.1 != "merra" & ctag.n.1 != "MERRA-2" & ctag.n.1 != ctag.TAG.1 & type.n != V & cname.n.1 != 'NULL' )
     say 'Closeness plot between  exp: 'qtag.1
     say '                       cexp: 'ctag.n.1
     say '                        obs: 'ctag.TAG.1
     say '              Total  numexp: 'numexp
     say ''
                                cmpnam = ctag.n.1
                                obsnam = ctag.TAG.1

     say '                  climcmp.cmpnam: 'climcmp.cmpnam
     say '                  climcmp.obsnam: 'climcmp.obsnam

             flag = ""
     while ( flag = "" )
     
                  'define zobs'TAG''season' = regrid2( cmod'TAG''season',0.25,0.25,bs_p1,0,-90 )'
                  'define zobs'n''season'   = regrid2( cmod'n''season'  ,0.25,0.25,bs_p1,0,-90 )'
                  'define zmod'season'      = regrid2( qmod'season'     ,0.25,0.25,bs_p1,0,-90 )'

     'closeness -CVAR 'zobs''n' -MVAR 'zmod' -OVAR 'zobs''TAG' -CNAME 'ctag.n.1' -MNAME 'NAME' -ONAME 'ctag.TAG.1' -CDESC 'cdesc.n.1' -MDESC 'qdesc.1' -ODESC 'cdesc.TAG.1' -MFILE 'qfile.1' -MBEGDATE 'bdate' -MENDDATE 'edate' -CFILE 'cfile.n.1' -CBEGDATE 'begdate.n' -CENDDATE 'enddate.n' -OFILE 'cfile.TAG.1' -OBEGDATE 'begdate.k' -OENDDATE 'enddate.k' -EXPID 'EXPID' -PREFIX 'PREFIX' -SEASON 'season' -OUTPUT 'OUTPUT' -CLIMEXP 'climexp' -CLIMCMP 'climcmp.cmpnam' -CLIMOBS 'climcmp.obsnam' -GC 'GC.1' -MATH 'mathparm

     if( mathparm != NULL )
         MTH = '_'mathparm
     else
         MTH = ''
     endif
     if( PREFIX != NULL )
         PFX = PREFIX'_'
     else
         PFX = ''
     endif
     
     'myprint -name 'OUTPUT'/'NAME''MTH'_'ctag.n.1'_closeness_'PFX''ctag.TAG.1'.'season

      if( DEBUG = "debug" )
          say "Hit ENTER to repeat plot, or NON-BLANK to continue"
          pull flag
      else
          flag = "next"
      endif

     'c'
     endwhile ;* END While_FLAG Loop 

     endif

n  = n + 1
endwhile ;* END While n<=numexp Loop 

       if( mathparm != 'NULL' )
           mathparm  = 'NULL'
       else
           mathparm  = 'DONE'
       endif
endwhile ;* END While_MATH Loop

* End Season Test
* ---------------
endif
* ---------------
endwhile ;* END While_m>0 Loop

endif ;* END CTAG Test

k = k + 1
endwhile ;* END While_k Loop

if( cmpexp_only = TRUE ) ; return ; endif

***********************************************************************************
*         Loop over All Observational Datasets having VERIFICATION.RC files
***********************************************************************************

'getnumrc 'geosutil'/plots/'NAME
     rcinfo = result
     numrc  = subwrd( rcinfo,1 )

say ' '
say 'Initial RCINFO: 'rcinfo
if( numrc = 0 )
   'getnumrc 'geosutil'/plots/'DIR
    rcinfo = result
    numrc  = subwrd( rcinfo,1 )
    say '  Final RCINFO: 'rcinfo
endif

say ' '
say 'Total Number of VERIFICATION.RC Datasets: 'numrc
say '----------------------------------------- '
say ' '

         k  = 1
while(   k <= numrc )
        loc = k + 1
     rcfile = subwrd( rcinfo,loc )
     RCFILE = rcfile
     if(RC != 'NULL') ; RCFILE = geosutil'/plots/'NAME'/VERIFICATION.'RC'.rc' ; endif
 if( RCFILE =  rcfile )

 say 'k = 'k'  RCFILE = 'RCFILE

* Check for VERIFICATION Formula File
* -----------------------------------
'!remove OBSFORM.txt'
'!echo `basename 'RCFILE' | cut -d. -f2 > OBSFORM.txt`'
'run getenv OBSFORM'
            OBSNAME = result
            OBSFORM = OBSNAME'form.gs'

say 'Checking for OBSFORM: 'geosutil'/plots/'NAME'/'OBSFORM

'!remove CHECKFILE.txt'
'!chckfile 'geosutil'/plots/'NAME'/'OBSFORM
 'run getenv CHECKFILE'
             CHECKFILE  = result

say 'CHECKFILE = 'CHECKFILE
if( CHECKFILE != 'NULL' )
        
         LOBSFORM = 'TRUE'
        'run 'geosutil'/plots/'NAME'/'OBSFORM' -OBS'
         OBS = result
         say 'OBSFORM OBS: 'OBS
        'numargs  'OBS
         numobs = result
         say '     NUMOBS: 'numobs

* Read Verification OBS:OBSGC
* ---------------------------
              n = 1
          OBSNAME.n = subwrd(OBS,n   )
           next = subwrd(OBS,n+1 )
            bit = checkbit(next)
       say 'OBSNAME.'n': 'OBSNAME.n
       while( bit != '' )
              n = n + 1
          OBSNAME.n = subwrd(OBS,n   )
           next = subwrd(OBS,n+1 )
            bit = checkbit(next)
       say 'OBSNAME.'n': 'OBSNAME.n
       endwhile

* Construct OBS GCs from OBS EXPORTS
* ----------------------------------
        m  = 0
        n  = 1
while ( n <= numobs )
        EX = ''
         j = 1
       bit = substr(OBSNAME.n,j,1)
       while(bit != ':' & bit != '')
        EX = EX''bit
         j = j + 1
       bit = substr(OBSNAME.n,j,1)
       endwhile
       if( EX != OBSNAME.n )
         m = m + 1
         j = j + 1
       OBSNAMEGC.m = ''
       bit = substr(OBSNAME.n,j,1)
       while(bit != '')
       OBSNAMEGC.m = OBSNAMEGC.m''bit
         j = j + 1
       bit = substr(OBSNAME.n,j,1)
       endwhile
       OBSNAME.n = EX
       endif
n = n + 1
endwhile

* Get Verification Variables
* --------------------------
FOUND = TRUE
        n  = 1
while ( n <= numobs & FOUND = TRUE )
'run getobs 'OBSNAME.n' 'OBSNAMEGC.n' 'rcfile
        oname.n = subwrd(result,1)
        ofile.n = subwrd(result,2)
        oscal.n = subwrd(result,3)
        odesc.n = subwrd(result,4)
         otag.n = subwrd(result,5)

say 'VERIFICATION_EXPORT_name: 'oname.n
say '             description: 'odesc.n
say '                     tag: ' otag.n
say '                    file: 'ofile.n
say '                 scaling: 'oscal.n
say ''
    if( oname.n = 'NULL' ) ; FOUND = FALSE ; endif
         n  = n + 1
endwhile

* Save Original numOGCs for other RCs
* --------------------------------
  numnorig = numOGCs
  numOGCs  = numobs

else

  LOBSFORM = 'FALSE'
   OBSFORM = 'obsform.gs'

* Get Verification Variables
* --------------------------
FOUND = TRUE
        n  = 1
while ( n <= numOGCs & FOUND = TRUE )
'run getobs 'OBS.n' 'OBSGC.n' 'rcfile
        oname.n = subwrd(result,1)
        ofile.n = subwrd(result,2)
        oscal.n = subwrd(result,3)
        odesc.n = subwrd(result,4)
         otag.n = subwrd(result,5)

say 'VERIFICATION_EXPORT_name: 'oname.n
say '             description: 'odesc.n
say '                     tag: ' otag.n
say '                    file: 'ofile.n
say '                 scaling: 'oscal.n
say ''
    if( oname.n = 'NULL' ) ; FOUND = FALSE ; endif
         n  = n + 1
endwhile

endif

if( FOUND = TRUE )
'setlons'
'setlats'

* Land/Water Masks
* ----------------
if( LAND = 'TRUE' | OCEAN = 'TRUE' )
   'set dfile 'ofile.1
if( LEVEL = "NULL" )
   'set z 1'
else
   'set lev 'LEVEL
endif
   'set t 1'
   'setmask     obs'
   'define lwmaskobs = regrid2( lwmaskobs,0.25,0.25,bs_p1,'lonmin','latmin')'
   'define  omaskobs = maskout( 1, lwmaskobs-0.5 )'
   'define  lmaskobs = maskout( 1, 0.5-lwmaskobs )'
endif


'set dfile 'ofile.1
if( LEVEL = "NULL" )
   'set z 1'
else
   'set lev 'LEVEL
endif
    'getdates'
     begdateo = subwrd(result,1)
     enddateo = subwrd(result,2)

* Perform OBS Formula Calculation
* -------------------------------
if( numOGCs = 1 )
   'define qobs = 'oname.1'.'ofile.1'*'oscal.1
else
    filename  = geosutil'/plots/'NAME'/'OBSFORM
    ioflag    = sublin( read(filename),1 )
    if(ioflag = 0)
       close  = close(filename)
       ostring = ''
       n  = 1
       while ( n <= numOGCs )
          ostring = ostring' 'oname.n'.'ofile.n'*'oscal.n
               n  = n + 1
       endwhile
      'run 'geosutil'/plots/'NAME'/'OBSFORM' 'ostring
    else
       ostring = NAME
       n  = 1
       while ( n <= numOGCs )
          ostring = ostring' 'oname.n'.'ofile.n'*'oscal.n
               n  = n + 1
       endwhile
      'run 'geosutil'/plots/'DIR'/'NAME'.gs 'ostring
      'define qobs = 'NAME'.1'
    endif
endif

* Check for MERRA Resolution problem
* ----------------------------------
'getinfo xdim'
         xdim = result
if( xdim != 540 )

                              'define qobs = regrid2( qobs,0.25,0.25,bs_p1,'lonmin','latmin')'
    if(    LAND  = 'TRUE'   |  OCEAN = 'TRUE' )
       if( LAND  = 'TRUE' ) ; 'define qobs = maskout( qobs,lmaskobs )' ; endif
       if( OCEAN = 'TRUE' ) ; 'define qobs = maskout( qobs,omaskobs )' ; endif
    endif

else

*                             'define qobs = regrid2( qobs,'dlon','dlat',bs_p1,'lonmin','latmin')'
                              'define qobs = regrid2( qobs,0.25,0.25,bs_p1,'lonmin','latmin')'
    if(    LAND  = 'TRUE'   |  OCEAN = 'TRUE' )
       if( LAND  = 'TRUE' ) ; 'define qobs = maskout( qobs,lmaskmod )' ; endif
       if( OCEAN = 'TRUE' ) ; 'define qobs = maskout( qobs,omaskmod )' ; endif
    endif

endif

* Compute Seaonal Means
* ---------------------
'seasonal qobs'

'run getenv "CLIMATE"'
             climate = result

*              Compute CLIMATOLOGY Flag for OBS/Verifications
*              ----------------------------------------------
               'run getenv "CLIMATE"'
                    climate.cnt = result
                climobs.ananam  = climate.cnt

            say 'climate.'cnt'    = 'climate.cnt
            say 'climobs.'ananam' = 'climobs.ananam
            say ' '



* Perform Taylor Plots
* --------------------
'set dfile 'qfile.1
'run getenv "TAYLOR"'
         taylor = result
if(      taylor = 'true' & TAYLOR = 'TRUE' )

'taylor qmodmdjf qobsdjf djf 'EXPID
'taylor qmodmjja qobsjja jja 'EXPID
'taylor qmodmson qobsson son 'EXPID
'taylor qmodmmam qobsmam mam 'EXPID
'taylor qmodmann qobsann ann 'EXPID

'taylor_write 'EXPID' 'NAME' 'OUTPUT
'taylor_read   GFDL   'NAME' 'verification
'taylor_read   CAM3   'NAME' 'verification
'taylor_read   e0203  'NAME' 'verification
                                                                                                   
"taylor_plt 4 CAM3 GFDL e0203 "EXPID" "OUTPUT" "NAME" '"EXPID" "NAME" vs "obsnam"' "DEBUG
endif


* Loop over Seasons to Process
* ----------------------------
       m = 1
while( m > 0 )
    season = subwrd(seasons,m)
if( season = '' )
         m = -1
else
         m = m+1
         say 'Processing Season: 'season

'set dfile 'qfile.1
'set gxout shaded'
'rgbset'
'run setenv "LEVTYPE" 'DLEVS

* Horizontal Plot
* ---------------
       mathparm  =  MATH
while( mathparm != 'DONE' )

* Standard Plot (Experiment_vs_Verification)
* ------------------------------------------
        flag = ""
while ( flag = "" )

'makplot -MVAR 'qmod' -MNAME 'NAME ' -MFILE 'qfile.1' -MDESC 'qdesc.1' -MBEGDATE 'bdate' -MENDDATE 'edate' -OVAR 'qobs' -ONAME 'otag.1' -OFILE 'ofile.1' -ODESC 'odesc.1' -OBEGDATE 'begdateo' -OENDDATE 'enddateo' -EXPID 'EXPID' -PREFIX 'PREFIX' -SEASON 'season' -OUTPUT 'OUTPUT' -CLIMEXP 'climexp' -CLIMCMP 'climobs.ananam' -GC 'GC.1' -MATH 'mathparm

 if( DEBUG = "debug" )
     say "Hit ENTER to repeat plot, or NON-BLANK to continue"
     pull flag
 else
     flag = "next"
 endif
'c'
endwhile ;* END While_FLAG Loop 

* Closeness Plot (Experiment_vs_Comparison to Verification)
* ---------------------------------------------------------
       n  = 1
while( n <= numexp )
if( ctag.n.1 != "NULL" & ctag.n.1 != "merra" & ctag.n.1 != "MERRA-2" & type.n != V )
say 'Closeness plot between  exp: 'qtag.1
say '                       cexp: 'ctag.n.1
say '                        obs: 'otag.1

                               cmpnam = ctag.n.1
                               obsnam = otag.1

say '                  climcmp.cmpnam: 'climcmp.cmpnam
say '                  climcmp.obsnam: 'climobs.ananam

say ''
        flag = ""
while ( flag = "" )

'closeness -CVAR 'cmod''n' -MVAR 'qmod' -OVAR 'qobs' -CNAME 'ctag.n.1' -MNAME 'NAME' -ONAME 'otag.1' -CDESC 'cdesc.n.1' -MDESC 'qdesc.1' -ODESC 'odesc.1' -MFILE 'qfile.1' -MBEGDATE 'bdate' -MENDDATE 'edate' -CFILE 'cfile.n.1' -CBEGDATE 'begdate.n' -CENDDATE 'enddate.n' -OFILE 'ofile.1' -OBEGDATE 'begdateo' -OENDDATE 'enddateo' -EXPID 'EXPID' -PREFIX 'PREFIX' -SEASON 'season' -OUTPUT 'OUTPUT' -CLIMEXP 'climexp' -CLIMCMP 'climcmp.cmpnam' -CLIMOBS 'climobs.ananam' -GC 'GC.1' -MATH 'mathparm

if( mathparm != NULL )
    MTH = '_'mathparm
else
    MTH = ''
endif
if( PREFIX != NULL )
    PFX = PREFIX'_'
else
    PFX = ''
endif
'myprint -name 'OUTPUT'/'NAME''MTH'_'ctag.n.1'_closeness_'PFX''otag.1'.'season

 if( DEBUG = "debug" )
     say "Hit ENTER to repeat plot, or NON-BLANK to continue"
     pull flag
 else
     flag = "next"
 endif
'c'
endwhile ;* END While_FLAG Loop 

endif
       n  = n + 1
endwhile ;* END While_N Loop 
       if( mathparm != 'NULL' )
           mathparm  = 'NULL'
       else
           mathparm  = 'DONE'
       endif
endwhile ;* END While_MATH Loop

* Zonal Mean Plot
* ---------------
       mathparm  =  MATH
while( mathparm != 'DONE' )
        flag = ""
while ( flag = "" )

'makplotz -MVAR 'qmod' -MNAME 'NAME ' -MFILE 'qfile.1' -MDESC 'qdesc.1' -MBEGDATE 'bdate' -MENDDATE 'edate' -OVAR 'qobs' -ONAME 'otag.1' -OFILE 'ofile.1' -ODESC 'odesc.1' -OBEGDATE 'begdateo' -OENDDATE 'enddateo' -EXPID 'EXPID' -PREFIX 'PREFIX' -SEASON 'season' -OUTPUT 'OUTPUT' -CLIMATE 'climate' -GC 'GC.1' -MATH 'mathparm' -RGFILE 'rgfile

 if( DEBUG = "debug" )
     say "Hit ENTER to repeat plot, or NON-BLANK to continue"
     pull flag
 else
     flag = "next"
 endif
'c'
endwhile ;* END While_FLAG Loop 
       if( mathparm != 'NULL' )
           mathparm  = 'NULL'
       else
           mathparm  = 'DONE'
       endif
endwhile ;* END While_MATH Loop


* End Season Test
* ---------------
endif
* End Season Loop
* ---------------
endwhile
* End FOUND Test
* --------------
endif


* End RC=NULL Test
* ----------------
endif
* Update Verification Loop Index
* ------------------------------
k = k + 1

* Restore Original numOGCs for other RCs
* -----------------------------------
if( LOBSFORM = 'TRUE' )
     numOGCs = numnorig
endif

* End Verification Loop
* ---------------------
endwhile



*******************************************************
****            No Verification Case               ****
*******************************************************

if( numrc = 0 )

* Loop over Seasons to Process
* ----------------------------
       m = 1
while( m > 0 )
    season = subwrd(seasons,m)
if( season = '' )
         m = -1
else
         m = m+1
         say 'Processing Season: 'season

'set dfile 'qfile.1
'set gxout shaded'
'rgbset'

* Horizontal Plot
* ---------------
        flag = ""
while ( flag = "" )

'uniplot 'NAME'  'EXPID' 'PREFIX' 'season' 'OUTPUT' 'qfile.1' 'qdesc.1' 'bdate' 'edate' 'begdateo' 'enddateo' 'climate
 if( DEBUG = "debug" )
     say "Hit ENTER to repeat plot, or NON-BLANK to continue"
     pull flag
 else
     flag = "next"
 endif
'c'
endwhile

* Zonal Mean Plot
* ---------------
        flag = ""
while ( flag = "" )
'uniplotz 'NAME'  'EXPID' 'PREFIX' 'season' 'OUTPUT' 'qfile.1' 'qdesc.1' 'bdate' 'edate' 'begdateo' 'enddateo' 'climate
 if( DEBUG = "debug" )
     say "Hit ENTER to repeat plot, or NON-BLANK to continue"
     pull flag
 else
     flag = "next"
 endif
'c'
endwhile


* End Season Test
* ---------------
endif
* End Season Loop
* ---------------
endwhile


* End Test for NUMRC
* ------------------
endif
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

* To Prevent Problem with BIT: E
* ------------------------------
function checkbit (word)
      bit = substr(word,1,1)
      dum = bit'TEST'
      if( dum = "ETEST" ) ; bit = A ; endif
return bit
