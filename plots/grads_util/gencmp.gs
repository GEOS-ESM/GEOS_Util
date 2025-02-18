function gencmp (args)

*******************************************************
****                 INPUT Variables               ****
*******************************************************

'numargs  'args
 numargs = result

NAME  = NULL
STAT  = NULL
DEBUG = FALSE
LEVEL = 0

        n   = 0
        num = 0
while ( num < numargs )
        num = num + 1

if( subwrd(args,num) = '-EXPID'  ) ; EXPID  = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-OUTPUT' ) ; OUTPUT = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-DEBUG'  ) ; DEBUG  = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-NAME'   ) ; NAME   = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-STAT'   ) ; STAT   = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-LEVEL'  ) ; LEVEL  = subwrd(args,num+1) ; endif

'fixname 'EXPID
          EXPIDa = result

* Read EXPORTS with format  EXPORT:GC[:OPT]
* -----------------------------------------
if( subwrd(args,num) = '-EXPORT' )
              n = n + 1
       EXPORT.n = subwrd(args,num+n   )
           word = subwrd(args,num+n+1 )
            bit = checkbit(word)
       while( bit != '-' )
              n = n + 1
       EXPORT.n = subwrd(args,num+n   )
           word = subwrd(args,num+n+1 )
            bit = checkbit(word)
       endwhile
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

*******************************************************

* Construct GCs from Input EXPORTS, Check for OPTIONAL EXPORTS
* ------------------------------------------------------------
        m  = 0
        k  = 1
while ( k <= n )

        dummy = EXPORT.k
        EXPORT.k = ''
         j = 1
       bit = substr(dummy,j,1)
       while(bit != ':' & bit != '')
        EXPORT.k = EXPORT.k''bit
         j = j + 1
       bit = substr(dummy,j,1)
       endwhile

       if( bit != '' )
         m = m + 1
         j = j + 1
       GC.m = ''
         bit = substr(dummy,j,1)
         while(bit != ':' & bit != '')
       GC.m = GC.m''bit
         j = j + 1
         bit = substr(dummy,j,1)
       endwhile
       endif

       if( bit != '' )
           OPT.m = TRUE
       else
           OPT.m = FALSE
       endif

k = k + 1
endwhile

* Initialize
* ----------
'reinit'
'set display color white'
'set csmooth on'
'c'

'uppercase 'seasons
            seasons = result

* Set number of EXPORTS & GCs
* ---------------------------
if( n = m )
    numGCs = n
else
    say 'Number of EXPORTS does not equal number of GCs!'
    say 'Number of EXPORTS: 'n
    say '              GCS: 'm
    return
endif
say ' '
n = 1
while( n<=numGCs )
say 'n = 'n'  EXPORT: 'EXPORT.n'   GC: 'GC.n'  Optional: 'OPT.n
n = n + 1
endwhile


* Get Model Variables
* -------------------
      mexp = 0
        n  = 1
while ( n <= numGCs )
'run getvar 'EXPORT.n' 'GC.n
        qname.n = subwrd(result,1)
        qfile.n = subwrd(result,2)
       qscale.n = subwrd(result,3)
        qdesc.n = subwrd(result,4)
         qtag.n = subwrd(result,5)
    if( STAT = "STD" )
        qname.n = 'VAR_'qname.n
    endif
    if( STAT = "BIAS" )
              k = n + 1
        qname.k =  qname.n
        qfile.k =  qfile.n
       qscale.k = qscale.n
        qdesc.k =  qdesc.n
         qtag.k =   qtag.n
    endif
    if( STAT = "RMS" )
              k = n + 1
        qname.k = 'VAR_'qname.n
        qfile.k =       qfile.n
       qscale.k =      qscale.n
        qdesc.k =       qdesc.n
         qtag.k =        qtag.n
    endif
    if( qfile.n != 'NULL' )
            mexp = mexp + 1
    else
      if( OPT.n = 'FALSE' )
          return
      endif
    endif
         n  = n + 1
endwhile
if( STAT = "RMS" | STAT = "BIAS" )
    mexp = mexp + 1
endif


* Get Environment Variables
* -------------------------
'run getenv "GEOSUTIL"'
         geosutil = result

'run getenv "VERIFICATION"'
         verification = result

'run getenv "ANALYSIS"'
         analysis  = result

* Model Experiment Data
* ---------------------
'set dfile 'qfile.1
if( LEVEL = 0 )
   'set z 1'
else
   'set lev 'LEVEL
endif
'getinfo  level'
          modlev = result

'getinfo xdim'
         xdim  = result
'getinfo ydim'
         ydim  = result
'getinfo undef'
         undef = result

'setlons'
'getinfo lonmin'
         lonmin = result
'getinfo lonmax'
         lonmax = result
'setlats'

* Create Environment Variables for Seasonal Utility
* -------------------------------------------------
'setdates'
'run getenv "BEGDATE"'
             begdate.EXPIDa = result
'run getenv "ENDDATE"'
             enddate.EXPIDa = result
'sett'

* Ensure NAME has no underscores
* ------------------------------
        m  = 1
while ( m <= mexp )
'fixname 'qname.m
          alias.m = result
     say 'Alias #'m' = 'alias.m
      if( qname.m != alias.m )
         'set lon -180 360'
         'rename 'qname.m ' 'alias.m''qfile.m
         'setlons'
      endif
      m = m+1
endwhile

* Perform Model Formula Calculation
* ---------------------------------
 say ' '
'q dims'
 say 'Model Environment: '
 say '             mexp: 'mexp 
 say result

if( mexp = 1 )
      NAME = EXPORT.1
        GC =     GC.1
    EXPORT = EXPORT.1

    say '  NAME: 'NAME
    say '    GC: 'GC
    say 'EXPORT: 'EXPORT

    if( qname.1 != alias.1 )
       'seasonalf -FUNCTION 'alias.1''qfile.1'*'qscale.1' -NAME 'mod
    else
       'seasonalf -FUNCTION 'alias.1'.'qfile.1'*'qscale.1' -NAME 'mod
    endif
    climfile = result
else
    mstring = mod
    m  = 1
    while ( m <= mexp )
       if( qname.m != alias.m )
           mstring = mstring' 'alias.m''qfile.m'*'qscale.m
       else
           mstring = mstring' 'alias.m'.'qfile.m'*'qscale.m
       endif
           m  = m + 1
    endwhile
   'run 'geosutil'/plots/formulas/'NAME'.gs 'mstring
    climfile = result
    if( STAT = "RMS" | STAT = "BIAS" )
        EXPORT = EXPORT.1
            GC = GC.1
    else
        EXPORT = NAME
            GC = GC.1
    endif
endif

if( STAT = "STD" | STAT = "RMS" | STAT = "BIAS" )
            k = 1
     while( k > 0 )
       season = subwrd(seasons,k)
       if( season = '' )
                k = -1
       else
          'define mod'season' = sqrt( mod'season' )'
                k = k+1
       endif
     endwhile
endif

'run getenv "CLIMATE"'
             climate.EXPIDa = result

say ''
say '        EXPID = 'EXPID
say 'begdate.EXPID => begdate.'EXPID' = 'begdate.EXPIDa
say 'enddate.EXPID => enddate.'EXPID' = 'enddate.EXPIDa
say 'climate.EXPID => climate.'EXPID' = 'climate.EXPIDa
say ''

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
say 'Comparing with: 'exp

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

* Get CMPEXP Variables
* --------------------
     found = TRUE
      oexp = 0
        m  = 1
while ( m <= numGCs )
       'run getvar 'EXPORT.m' 'GC.m' 'exp
        oname.numexp.m = subwrd(result,1)
      obsfile.numexp.m = subwrd(result,2)
       oscale.numexp.m = subwrd(result,3)
       obsdsc.numexp.m = subwrd(result,4)
       obsnam.numexp.m = subwrd(result,5)

    say "Looping CMPEXPs, numexp = "numexp"  oname."numexp" = "oname.numexp.m"  obsnam."numexp" = "obsnam.numexp.m"  numGCS = "numGCs
                                                                                         cmpname = obsnam.numexp.m
                                                                           'run fixname 'cmpname
                                                                                         cmpnama = result
    say 
    if( STAT = "STD" )
        oname.numexp.m = 'VAR_'oname.numexp.m
    endif
    if( STAT = "BIAS" )
              k = m + 1
        oname.numexp.k =   oname.numexp.m
      obsfile.numexp.k = obsfile.numexp.m
       oscale.numexp.k =  oscale.numexp.m
       obsdsc.numexp.k =  obsdsc.numexp.m
       obsnam.numexp.k =  obsnam.numexp.m
    endif
    if( STAT = "RMS" )
              k = m + 1
        oname.numexp.k = 'VAR_'oname.numexp.m
      obsfile.numexp.k = obsfile.numexp.m
       oscale.numexp.k =  oscale.numexp.m
       obsdsc.numexp.k =  obsdsc.numexp.m
       obsnam.numexp.k =  obsnam.numexp.m
    endif
    if( obsfile.numexp.m != 'NULL' )
            oexp = oexp + 1
    else
           if( OPT.m = 'FALSE' )
               found =  FALSE
           endif
    endif
         m  = m + 1
endwhile

if( STAT = "RMS" | STAT = "BIAS" )
    oexp = oexp + 1
endif

* Continue if all EXPORT(s) are found
* -----------------------------------
if( found = "TRUE" )

           'set dfile 'obsfile.numexp.1
            if( LEVEL = 0 )
               'set z 1'
            else
               'set lev 'LEVEL
            endif
           'getinfo  level'
                     obslev = result

           'getdates'
            begdate.cmpnama = subwrd(result,1)
            enddate.cmpnama = subwrd(result,2)

            say 'begdate.cmpname: begdate.'cmpname' = 'begdate.cmpnama
            say 'enddate.cmpname: enddate.'cmpname' = 'enddate.cmpnama

*          'run setenv   "BEGDATEO" 'begdate.numexp
*          'run setenv   "ENDDATEO" 'enddate.numexp

* Ensure NAME has no underscores
* ------------------------------
        m  = 1
while ( m <= oexp )
'fixname 'oname.numexp.m
          olias.numexp.m = result
     say 'Olias #'m' = 'olias.numexp.m
      if( oname.numexp.m != olias.numexp.m )
         'set lon -180 360'
         'rename 'oname.numexp.m ' 'olias.numexp.m''obsfile.numexp.m
         'setlons'
      endif
      m = m+1
endwhile

* Perform Model Formula Calculation
* ---------------------------------
 say ' '
'q dims'
 say 'CMPEXP Environment:'
 say result

if( oexp = 1 )
      NAME = EXPORT.1
        GC =     GC.1
    EXPORT = EXPORT.1
    if( oname.numexp.1 != olias.numexp.1 )
       'seasonalf -FUNCTION 'olias.numexp.1''obsfile.numexp.1'*'oscale.numexp.1'  -NAME obs'numexp
    else
       'seasonalf -FUNCTION 'olias.numexp.1'.'obsfile.numexp.1'*'oscale.numexp.1' -NAME obs'numexp
    endif
    climfile = result
else
    mstring = obs''numexp
    m  = 1
    while ( m <= oexp )
       if( oname.numexp.m != olias.numexp.m )
           mstring = mstring' 'olias.numexp.m''obsfile.numexp.m'*'oscale.numexp.m
       else
           mstring = mstring' 'olias.numexp.m'.'obsfile.numexp.m'*'oscale.numexp.m
       endif
           m  = m + 1
    endwhile
   'run 'geosutil'/plots/formulas/'NAME'.gs 'mstring
    climfile = result
    if( STAT = "RMS" | STAT = "BIAS" )
        EXPORT = EXPORT.1
            GC = GC.1
    else
        EXPORT = NAME
            GC = GC.1
    endif
endif

* Compute CLIMATOLOGY Flag for Comparison Experiment
* --------------------------------------------------
               'run getenv "CLIMATE"'
                        climate.cmpnama = result
                        anafile = obsfile.numexp.1
                        anadsc  =  obsdsc.numexp.1
                        ananam  =  obsnam.numexp.1

                 k = 1
          while( k > 0 )
              season = subwrd(seasons,k)
          if( season = '' )
                   k = -1
          else
                   k = k+1

                  'set dfile 'qfile.1
             say  'count "'season'" 'begdate.EXPIDa' 'enddate.EXPIDa
                  'count "'season'" 'begdate.EXPIDa' 'enddate.EXPIDa
                   nmod = result
             say  'climate.EXPID = 'climate.EXPIDa

                  'set dfile 'anafile
             say  'count "'season'" 'begdate.cmpnama' 'enddate.cmpnama
                  'count "'season'" 'begdate.cmpnama' 'enddate.cmpnama
                   nobs.numexp = result
             say  'climate.cmpname = 'climate.cmpnama

                  if( STAT = "STD" | STAT = "RMS" | STAT = "BIAS" )
                     'define obs'numexp''season' = sqrt( obs'numexp''season' )'
                  endif
                 'define obs'season' = obs'numexp''season

                       flag = ""
               while ( flag = "" )
              'run genplt.gs -EXPID 'EXPID' -EXPORT 'EXPORT' -GC 'GC' -ALIAS 'alias.1' -SEASON 'season' -MBDATE 'begdate.EXPIDa' -MEDATE 'enddate.EXPIDa' -CLIMEXP 'climate.EXPIDa' -CBDATE 'begdate.cmpnama' -CEDATE 'enddate.cmpnama' -CLIMCMP 'climate.cmpnama' -OUTPUT 'OUTPUT' -LEVEL 'LEVEL' -NMOD 'nmod' -CMOD 'nobs.numexp' -MFILE 'qfile.1' -CFILE 'anafile' -CNAME 'ananam' -CDESC 'anadsc' -DEBUG 'DEBUG' -MDESC 'qdesc.1' -STAT 'STAT
                if( DEBUG = "debug" )
                    say "Hit  ENTER  to repeat plot"
                    say "Type 'next' for  next plot, 'done' for next field"
                    pull flag
                else
                    flag = "next"
                endif
               endwhile
              'c'
          endif
          endwhile

* End FOUND Check
* ---------------
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
  cname.k =  oname.k.1
   ctag.k = obsnam.k.1
say ' '
say 'Looping through experiments, k = 'k' CTAG = 'ctag.k' TYPE = 'type.k
say '--------------------------------------------------------------'
say ' '

if( ( ctag.k = "MERRA-2" | type.k = V ) & cname.k != 'NULL' )
     TAG   = k
     say 'Performing Closeness plots to: 'ctag.TAG' k = 'k
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
         say 'm = 'm'  Processing Season: 'season

'set dfile 'qfile.1
'set gxout shaded'
'rgbset'
'run getenv "DIFFTYPE"'
             DIFFTYPE = result
'run setenv "LEVTYPE" 'DIFFTYPE'LEVS'

* Horizontal Closeness Plot (Experiment_vs_Comparison to Verification)
* --------------------------------------------------------------------
            n  = 1
     while( n <= numexp )
     say 'n = 'n'  Testing 'qtag.1' and 'ctag.n' for closeness with 'ctag.TAG

     if( ctag.n != "merra" & ctag.n != "MERRA-2" & ctag.n != ctag.TAG & type.n != V & cname.n != 'NULL' )
         say 'Closeness plot between  exp: 'qtag.1
         say '                       cexp: 'ctag.n
         say '                        obs: 'ctag.TAG
         say '              Total  numexp: 'numexp
         say ''
                                cmpnam = ctag.n
                                obsnam = ctag.TAG
                  'run fixname 'cmpnam
                                cmpnamf = result
                  'run fixname 'obsnam
                                obsnamf = result

     say '                          cmpnam: 'cmpnam
     say '                          obsnam: 'obsnam
     say '                  climate.cmpnam: 'climate.cmpnamf
     say '                  climate.obsnam: 'climate.obsnamf

                 flag = ""
         while ( flag = "" )

             'define zobs'TAG''season' = regrid2( obs'TAG''season',0.25,0.25,bs_p1,0,-90 )'
             'define zobs'n''season'   = regrid2( obs'n''season'  ,0.25,0.25,bs_p1,0,-90 )'
             'define zmod'season'      = regrid2( mod'season'     ,0.25,0.25,bs_p1,0,-90 )'

             'closeness -CVAR 'zobs''n' -MVAR 'zmod' -OVAR 'zobs''TAG' -CNAME 'ctag.n' -MNAME 'EXPORT' -ALIAS 'alias.1' -ONAME 'ctag.TAG' -CDESC 'obsdsc.n.1' -MDESC 'qdesc.1' -ODESC 'obsdsc.TAG.1' -MFILE 'qfile.1' -MBEGDATE 'begdate.EXPIDa' -MENDDATE 'enddate.EXPIDa' -OFILE 'obsfile.TAG.1' -OBEGDATE 'begdate.obsnamf' -OENDDATE 'enddate.obsnamf' -EXPID 'EXPID' -PREFIX 'NULL' -SEASON 'season' -OUTPUT 'OUTPUT' -CLIMEXP 'climate.EXPIDa' -CLIMCMP 'climate.cmpnamf' -CLIMOBS 'climate.obsnamf' -GC 'GC.1' -MATH 'NULL' -LEVEL 'LEVEL

             'myprint -name 'OUTPUT'/hdiag_'ctag.n'_'NAME'.'GC.1'_'LEVEL'_closeness_'ctag.TAG'.'season

              if( DEBUG = "debug" )
                  say "Hit ENTER to repeat plot, or NON-BLANK to continue"
                  pull flag
              else
                  flag = "next"
              endif
             'c'
         endwhile ;* END While_FLAG Loop

     endif :* END CTAG Test

     n = n + 1
     endwhile ;* END While_N Loop

* ---------------
endif ;* End Season Test

* ---------------
endwhile ;* END SEASON Loop

endif ;* END Closeness If Test

k = k + 1
endwhile ;* END While_k Loop

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

