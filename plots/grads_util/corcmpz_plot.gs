function corcmpz (args)

'numargs  'args
 numargs = result

'run getenv SOURCE'
        SOURCE = result

field = h
desc  = ''

       num = 0
while( num < numargs )
       num = num + 1
if( subwrd(args,num)='-field'  ) ; field  = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-numexp' ) ; numexp = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-desc'   ) ; desc   = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-debug'  ) ; debug  = subwrd(args,num+1) ; endif
if( subwrd(args,num)='-NOPLOT' ) ; PLOT   = FALSE              ; endif
endwhile
                                   mexps  = numexp-1
       num = 0
while( num < numargs )
       num = num + 1
       m = 0
       while( m<=mexps )
       if( subwrd(args,num)='-desc'm  ) ; expdsc.m = subwrd(args,num+1) ; endif
       m = m + 1
       endwhile
endwhile

***********************************************************
*****                                                 *****
*****  Note:  numexp is the Total Number of           *****
*****         Experiments (including the Control)     *****
*****         being compared.                         *****
*****                                                 *****
***********************************************************

'getinfo numfiles'
files_per_month = result/numexp

expcmp.0 = 1
expcol.0 = 1
       m = 1
while( m <= mexps )
expcmp.m = m+1
expcol.m = m+1
       m = m+1
endwhile


say '   Exp0: 'expcmp.0'  Color: 'expcol.0
       m = 1
while( m <= mexps )
say '   Exp'm': 'expcmp.m'  Color: 'expcol.m
       m = m+1
endwhile

say 'MEXPs = 'mexps
say 'FPM: 'files_per_month

'rgbset'
'run setenv "ANTIALIAS" NULL'


* Initialize Plot Values
* ----------------------
if( field = "h" )
    name  = "Heights"
    unit  = "(m)"
    label = "hght"
    cint  = 0.02
  rbrange = "0.70 1.0"
endif
if( field = "u" )
    name  = "U-Wind"
    unit  = "(m/sec)"
    label = "uwnd"
    cint  = 0.02
  rbrange = "0.70 1.0"
endif
if( field = "v" )
    name  = "V-Wind"
    unit  = "(m/sec)"
    label = "vwnd"
    cint  = 0.02
  rbrange = "0.70 1.0"
endif
if( field = "t" )
    name  = "Temperature"
    unit  = "(K)"
    label = "tmpu"
    cint  = 0.02
  rbrange = "0.70 1.0"
endif
if( field = "q" )
    name  = "Specific Humidity"
    unit  = "(g/g)"
    label = "sphu"
    cint  = 0.02
  rbrange = "0.70 1.0"
endif


'getinfo xpos'
         xpos  = result
'getinfo ypos'
         ypos  = result

if( xpos =  1 ) ; region = "Global"                                     ;  reg = "GLO"  ; endif
if( xpos =  2 ) ; region = "N.Hem. ExtraTropics (Lats: 20,80)"          ;  reg = "NHE"  ; endif
if( xpos =  3 ) ; region = "Tropics (Lats: -20,20)"                     ;  reg = "TRO"  ; endif
if( xpos =  4 ) ; region = "S.Hem. ExtraTropics (Lats: -20,-80)"        ;  reg = "SHE"  ; endif
if( xpos =  5 ) ; region = "N.W. Quadrant (Lons:-180,0  Lats: 0, 90)"   ;  reg = "NWQ"  ; endif
if( xpos =  6 ) ; region = "N.E. Quadrant (Lons: 0,180  Lats: 0, 90)"   ;  reg = "NEQ"  ; endif
if( xpos =  7 ) ; region = "S.W. Quadrant (Lons:-180,0  Lats: 0,-90)"   ;  reg = "SWQ"  ; endif
if( xpos =  8 ) ; region = "S.E. Quadrant (Lons: 0,180  Lats: 0,-90)"   ;  reg = "SEQ"  ; endif
if( xpos =  9 ) ; region = "North America (Lons:-140,-60  Lats: 20,60)" ;  reg = "NAM"  ; endif
if( xpos = 10 ) ; region = "Europe (Lons:-10,30  Lats: 30,60)"          ;  reg = "EUR"  ; endif
if( xpos = 11 ) ; region = "N.Polar (Lats: 60,90)"                      ;  reg = "NPO"  ; endif
if( xpos = 12 ) ; region = "S.Polar (Lats: -60,-90)"                    ;  reg = "SPO"  ; endif
if( xpos = 13 ) ; region = "X.Polar (Lats: -60,60)"                     ;  reg = "XPO"  ; endif


filebeg  = 1
fileend  = filebeg + files_per_month - 1
numfiles = fileend-filebeg+1


* Compute Beginning Times Relative to Control (1st File) across ALL Experiments
* -----------------------------------------------------------------------------
       m = 0
while( m<=mexps )
'set dfile 1'
'set t 1'
            n   = filebeg
            n.m = n + m*numfiles
'set dfile 'n.m

'q dims'
   tline    = sublin(result,5)
   toff.m.n = subwrd(tline,9)
*say 'toffset:  m = 'm'  n = 'n'  toff = 'toff.m.n
m = m+1
endwhile

m = 0
while( m<=mexps )
        n   = filebeg
while ( n  <= fileend )
        n.m = n + m*numfiles
'set dfile 1'
'set t 1'
'set dfile 'n.m
'q dims'
tline       = sublin(result,5)
toffset.n.m = subwrd(tline,9)
*say 'toffset:  m: 'm'  n: 'n'  file(n.m) = 'n.m'  toffset = 'toffset.n.m
n = n + 1
endwhile
m = m + 1
endwhile

* Determine Months from Ensembles
* -------------------------------
month  = ''
months = ''
season = ''
        n   = filebeg
while ( n  <= fileend )
'set dfile 'n
'set t 1'
'getinfo date'
         date = result
        dummy = substr(date,6,3)
    if( dummy != month )
        month  = dummy

        if( months = '' )
            months = month
         else
            months = months'-'month
        endif

        if( months = 'DEC-JAN-FEB' )
            if( season = '' )
                season = 'DJF'
            else
                season = season'-DJF'
            endif
            months = ''
        endif

        if( months = 'MAR-APR-MAY' )
            if( season = '' )
                season = 'MAM'
            else
                season = season'-MAM'
            endif
            months = ''
        endif

        if( months = 'JUN-JUL-AUG' )
            if( season = '' )
                season = 'JJA'
            else
                season = season'-JJA'
            endif
            months = ''
        endif

        if( months = 'SEP-OCT-NOV' )
            if( season = '' )
                season = 'SON'
            else
                season = season'-SON'
            endif
            months = ''
        endif

    endif
n = n + 1
endwhile
if( season != '' )
    if( months != '' )
        months  = season'-'months
    else
        months  = season
    endif
endif
say 'Months Used in Forecasts: 'months


* Define TOPLEV, NDAY and NDAYMAX across ALL Experiments
* ------------------------------------------------------
 toplev  = 0
 ndaymax = 999
       m = 0
while( m<=mexps )
            n   = filebeg
            n.m = n + m*numfiles
'set dfile 'n.m

'getinfo zdim'
         zdim = result
        'set z 'zdim
        'getinfo level'
                 level = result
             if( level > toplev )
                 toplev = level
             endif

'run getinfo tinc'
             tinc = result
         if( tinc = "NULL" ) ; tinc = 6 ; endif

'run getinfo tdim'
             tdum = result - toff.m.n
             nday = tdum * tinc / 24
         if( nday < ndaymax ) ; ndaymax = nday ; endif
m = m+1
endwhile
if( toplev < 1 ) ; toplev = 1 ; endif

'run getenv "NDAY"'
             nday = result
         if( nday = "NULL" ) ; nday = ndaymax ; endif
         if( nday > ndaymax) ; nday = ndaymax ; endif
say 'NDAY: ' nday
say 'TOPLEV: 'toplev

* Determine TDIM based on TINC from Experiment Files for Diff Calculations
* ------------------------------------------------------------------------
   m = 0
while( m<=mexps )
            n   = filebeg
            n.m = n + m*numfiles
'set dfile 'n.m
'getinfo tdim'
         tdim = result
'getinfo tinc'
         tinc = result

         ndayloc = (tdim-toff.m.n) * tinc / 24
         tmax    = toff.m.n + ndayloc*(24/tinc)
         tbeg.m  = toff.m.n -(tmax-tdim)
         tdim.m  = tbeg.m   + nday*(24/tinc)

if( tdim.m < tdim.0 )
    tdif.m = tdim.m
    ddif.m = n.m
else
    tdif.m = tdim.0
    ddif.m = 1
endif
say '  m: 'm'  tbeg: 'tbeg.m'  tdim: 'tdim.m'  tinc: 'tinc'  tdif: 'tdif.m'  ddif: 'ddif.m

m = m+1
endwhile

* Find LCD for TDIM among all Experiment Files for Synoptic Average Stats
* -----------------------------------------------------------------------
 tmin = tdim.0
dfile = 1
    m = 1
while( m<=mexps )
            n   = filebeg
            n.m = n + m*numfiles
            d.m = 1 + m*numfiles
if( tdim.m < tmin )
    tmin   = tdim.m
    dfile  = d.m
endif
m = m+1
endwhile

'set dfile 1'
'getinfo undef'
         undef = result
'    set undef ' undef

* Initialize Variables to Zero
* ----------------------------
'set dfile '1
'set lev 1000 'toplev
'set t  'tbeg.0' 'tdim.0
'define  zero = 0.0'

say 'TBEG: 'tbeg.0'  TEND: 'tdim.0
say 'XPOS: 'xpos  '  YPOS: 'ypos
say ' '
say 'Initialize zave and zvar ...'
   m = 0
while( m<=mexps )
            n   = filebeg
            n.m = n + m*numfiles
            d.m = 1 + m*numfiles
'set dfile 'd.m
'set lev 1000 'toplev
'set t  'tbeg.m' 'tdim.m
say '  m: 'm'  dfile: 'd.m'  tbeg: 'tbeg.m'  tdim: 'tdim.m
'define  zave'm' = 0.0'
'define  zvar'm' = 0.0'
m = m+1
endwhile


say 'Initialize zaved and zvard ...'
   m = 0
while( m<=mexps )
            n   = filebeg
            n.m = n + m*numfiles
'set dfile 'ddif.m
'set lev 1000 'toplev
'set t  'tbeg.m' 'tdif.m
say '  m: 'm'  ddfile: 'ddif.m'  tbeg: 'tbeg.m'  tdif: 'tdif.m
'define zaved'm' = 0.0'
'define zvard'm' = 0.0'
m = m+1
endwhile

* Plot each individual forecast while computing mean and Fisher Transform (to force Gaussian Distribution)
* --------------------------------------------------------------------------------------------------------

*say 'Redfine field'
m = 0
while( m<=mexps )
        n   = filebeg
while ( n  <= fileend )
        n.m = n + m*numfiles
        d.m = 1 + m*numfiles
'set dfile 'd.m
'set lev 1000 'toplev
'set t  'tbeg.m' 'tdim.m
 toffset = 1-toffset.n.m
*say 'dfile 'd.m'  tbeg: 'tbeg.m'  tend: 'tdim.m'  toffset: 'toffset'  'field'cor'n.m' = 'field'cor.'n.m'(t+'toffset')'

'define 'field'cor'n.m' = 'field'cor.'n.m'(t+'toffset')'
n = n + 1
endwhile
m = m + 1
endwhile

* Define New Fisher Transform Variable (to force Gaussian Distribution)
* ---------------------------------------------------------------------
say ' Define New Fisher Transform Variable znem ...'
m = 0
while( m<=mexps )
        n   = filebeg
while ( n  <= fileend )
        n.m = n + m*numfiles
        d.m = 1 + m*numfiles
'set dfile 'd.m
'set lev 1000 'toplev
'set t  'tbeg.m' 'tdim.m
'define     q'm' = 'field'cor'n.m
'define z'n'e'm' = 0.5*log( (1+ q'm')/(1- q'm'+5.0e-6) )'
*say '   DFILE: 'n.m'   Defined q'm' and z'n'e'm
n = n + 1
endwhile
m = m + 1
endwhile

say ' Define New Fisher Transform Variable zdnem ...'
m = 0
while( m<=mexps )
        n   = filebeg
while ( n  <= fileend )
        n.m = n + m*numfiles
        d.m = 1 + m*numfiles

* Set Proper Time Domain
* ----------------------
'set dfile 'm
'sett -q'
'getinfo tinc'
         tinc1  = result
        'getinfo tmin'
                 tmin1 = result
        'getinfo tmax'
                 tmax1 = result
     tdim1 = tmax1 - tmin1 + 1
    'set t 'tmin1
    'getinfo date'
             datemin1 = result
    'set t 'tmax1
    'getinfo date'
             datemax1 = result

'set dfile 'n
'sett -q'
'getinfo tinc'
         tinc2  = result
        'getinfo tmin'
                 tmin2 = result
        'getinfo tmax'
                 tmax2 = result
     tdim2 = tmax2 - tmin2 + 1
    'set t 'tmin2
    'getinfo date'
             datemin2 = result
    'set t 'tmax2
    'getinfo date'
             datemax2 = result

if( tinc1 >= tinc2 )
    timefile.m = m
else
    timefile.m = n
endif

if( datemin1 <= datemin2 )
    tmin.m = tmin2
else
    tmin.m = tmin1
endif

if( datemax1 >= datemax2 )
    tmax.m = tmax2
else
    tmax.m = tmax1
endif
     tdim.m = tmax - tmin + 1

*say 'm: 'm'  tmin1: 'tmin1'  tmin2: 'tmin2'  tmin.m: 'tmin.m
*say 'm: 'm'  tmax1: 'tmax1'  tmax2: 'tmax2'  tmax.m: 'tmax.m
*say 'm: 'm'  tdim.m: 'tdim.m

* ----------------------

'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev
'define ctl = 'field'cor'n
*say '   DFILE: 'n'  CTL defined for TBEG = 'tbeg.0' to TEND: 'tdif.0

'define dum  = 'field'cor'n.m
*say   '   DFILE: 'n.m'  DUM defined for TBEG = 'tbeg.0' to TEND: 'tdif.0

if( m = 0 )
*   say 'Computing DumDiff for EXP: 'm'   File: 'ddif.m' for TBEG = 'tbeg.0' to TEND: 'tdif.0
   'define dumdiff = dum'
else
    say 'Computing DumDiff in makezdif2 for EXP: 'm'   File: 'n.m' for TBEG = 'tbeg.0' to TEND: 'tdif.0
   'makezdif2 -q1 dum -file1 'd.m' -q2 zero    -file2   1 -ptop 'toplev' -name dum'
endif

'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev
'define     dq'm' = 0.5*(ctl-dumdiff)'
'define zd'n'e'm' = 0.5*log( (1+dq'm')/(1-dq'm') )'
n = n + 1
endwhile
m = m + 1
endwhile

* Compute Mean
* ------------
say ' Compute mean zave ...'
m = 0
while( m<=mexps )
        n  = filebeg
while ( n <= fileend )
        n.m = n + m*numfiles
        d.m = 1 + m*numfiles
'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev
'define  zave'm' =  zave'm' +  z'n'e'm
n = n + 1
endwhile
'define  zave'm' =  zave'm'/'numfiles
m = m + 1
endwhile
*say 'Hit Enter to continue ...'
*pull flag

say ' Compute mean zdave ...'
m = 0
while( m<=mexps )
        n  = filebeg
while ( n <= fileend )
'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev
'define zaved'm' = zaved'm' + zd'n'e'm
n = n + 1
endwhile
'define zaved'm' = zaved'm'/'numfiles
m = m + 1
endwhile
*say 'Hit Enter to continue ...'
*pull flag


* Compute Variance and Standard Deviations
* ----------------------------------------
say ' Compute variance zvar and zstd ...'
m = 0
while( m<=mexps )
        n  = filebeg
while ( n <= fileend )
        n.m = n + m*numfiles
        d.m = 1 + m*numfiles
'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev
'define  zvar'm' =  zvar'm' + pow(  z'n'e'm'- zave'm',2 )'
n = n + 1
endwhile
'define  zvar'm' =  zvar'm'/('numfiles'-1)'
'define  zstd'm' = sqrt(  zvar'm' )'
m = m + 1
endwhile
*pull flag

say ' Compute variance zdvar and zdstd ...'
m = 0
while( m<=mexps )
        n  = filebeg
while ( n <= fileend )
'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev
'define zvard'm' = zvard'm' + pow( zd'n'e'm'-zaved'm',2 )'
n = n + 1
endwhile
'define zvard'm' = zvard'm'/('numfiles'-1)'
'define zstdd'm' = sqrt( zvard'm' )'
m = m + 1
endwhile
*pull flag


* Compute Fisher Mean
* -------------------
say ' Compute Fisher Mean rave ...'
m = 0
while( m<=mexps )
        n  = filebeg
        n.m = n + m*numfiles
        d.m = 1 + m*numfiles
'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev
'define rave'm' = (exp(2*zave'm')-1) / (exp(2*zave'm')+1)'
m = m + 1
endwhile
*pull flag


* Copmute Confidence Intervals for Two-Tailed Students T-Test Distribution
* ------------------------------------------------------------------------
 dof = numfiles-1    ;* Degrees of Freedom (dof)

'astudt 'dof' 0.0001';* 99.99% Confidence
'q defval astudtout 1 1'
critval99p99=subwrd(result,3)

'astudt 'dof' 0.01'  ;* 99% Confidence
'q defval astudtout 1 1'
critval99=subwrd(result,3)

'astudt 'dof' 0.05'  ;* 95% Confidence
'q defval astudtout 1 1'
critval95=subwrd(result,3)

'astudt 'dof' 0.10'  ;* 90% Confidence
'q defval astudtout 1 1'
critval90=subwrd(result,3)

'astudt 'dof' 0.20'  ;* 80% Confidence
'q defval astudtout 1 1'
critval80=subwrd(result,3)

* Estimate Statistically Significant Range for Zero-Mean Hypothesis in a Paired t-Test)
* -------------------------------------------------------------------------------------
say ' Estimate T-Test Range rUpm rLpm ...'
m = 1
while( m<=mexps )
'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev
'define se  = sqrt( zvard'm'/'numfiles' )'

'define dx = se*'critval99p99
'define rUp99p99'm' = 2*(exp( 2*dx)-1)/(exp( 2*dx)+1)'
'define rLp99p99'm' = 2*(exp(-2*dx)-1)/(exp(-2*dx)+1)'

'define dx = se*'critval99
'define rUp99'm' = 2*(exp( 2*dx)-1)/(exp( 2*dx)+1)'
'define rLp99'm' = 2*(exp(-2*dx)-1)/(exp(-2*dx)+1)'

'define dx = se*'critval95
'define rUp95'm' = 2*(exp( 2*dx)-1)/(exp( 2*dx)+1)'
'define rLp95'm' = 2*(exp(-2*dx)-1)/(exp(-2*dx)+1)'

'define dx = se*'critval90
'define rUp90'm' = 2*(exp( 2*dx)-1)/(exp( 2*dx)+1)'
'define rLp90'm' = 2*(exp(-2*dx)-1)/(exp(-2*dx)+1)'

'define dx = se*'critval80
'define rUp80'm' = 2*(exp( 2*dx)-1)/(exp( 2*dx)+1)'
'define rLp80'm' = 2*(exp(-2*dx)-1)/(exp(-2*dx)+1)'

m = m + 1
endwhile


************************************************************************
if (1 = 0)
* Plot Fisher Mean for Experiments
* --------------------------------
say '  Plot Fisher Mean for Experiments'
'getinfo year'
         year = result
'getinfo date'
         date = result

        m  = 0
while( m<=mexps )
        n  = filebeg
        n.m = n + m*numfiles
        d.m = 1 + m*numfiles
'set dfile 'timefile.m
*'set t 'tmin.m' 'tmax.m
'set t 'tbeg.m' 'tdif.m
'set lev 1000 'toplev

'set vpage off'
'set grads off'
'set gxout contour'
'set parea 2.25 9.75 1.0 7.5'
if( toplev < 100 )
    'set zlog on'
    'setlevs'
else
    'set zlog off'
endif
'set clab  on'
'set xaxis 0 'nday' .5'
'set cmark  0'
'set cthick 8'
'set cstyle 1'
'set ccolor rainbow'
'set cint 'cint
'set rbrange 'rbrange
'd rave'm

'draw ylab Pressure (hPa)'
'set  string 1 c 6 0'
'set  strsiz .17'
'draw string 6.0 8.15 'expdsc.m' ('numfiles')   Anomaly Correlation (CINT: 'cint')'
'draw string 6.0 7.8  'name'  'region
'set  strsiz .12'
'draw string 6.0 0.72 Forecast Day'

'set  string 1 c 6 90'
'set  strsiz .18'
'draw string 0.80 4.25 'months' 'year

say 'EXP'm'  Field: 'name'  Region: 'region

'!/bin/mkdir -p 'SOURCE'/corcmp'
if( nday = ndaymax )
   'myprint2 -name 'SOURCE'/corcmp/'expdsc.m'_'expdsc.m'_stats_'label'_corcmp_'reg'_z_'months' -rotate 90 -density 100x100'
else
   'myprint2 -name 'SOURCE'/corcmp/'expdsc.m'_'expdsc.m'_stats_'label'_corcmp_'reg'_z_'months'_'nday'DAY -rotate 90 -density 100x100'
endif
if( debug = "TRUE" )
    say "Hit ENTER for next plot"
    pull flag
endif
'c'

m = m + 1
endwhile
endif

************************************************************************


* Plot Difference plus Significance
* ---------------------------------
m = 1
while( m<=mexps )
       n  = filebeg
       d.m = 1 + m*numfiles

mfile = 1 + m*files_per_month

say 'Computing makezdif3 data for EXP: 'm'   File: 'mfile'  xpos: 'xpos'  Region: 'region

* Compute RMS difference between ravem and rave0: ravediff
* --------------------------------------------------------
'makezdif3 -q1  rave'm' -file1 'mfile' -q2 rave0  -file2 1  -ptop 'toplev' -name rave'
'getinfo numfiles'
         newfile = result
'close ' newfile

* Compute difference between 99% Confidence and zero: rUp99diff
* -------------------------------------------------------------
'makezdif3 -q1   rUp99'm' -file1 'mfile' -q2  zero  -file2 1  -ptop 'toplev' -name  rUp99'
'getinfo numfiles'
         newfile = result
'close ' newfile

* Compute difference between 95% Confidence and zero: rUp95diff
* -------------------------------------------------------------
'makezdif3 -q1   rUp95'm' -file1 'mfile' -q2  zero  -file2 1  -ptop 'toplev' -name  rUp95'
'getinfo numfiles'
         newfile = result
'close ' newfile

* Compute difference between 90% Confidence and zero: rUp90diff
* -------------------------------------------------------------
'makezdif3 -q1   rUp90'm' -file1 'mfile' -q2  zero  -file2 1  -ptop 'toplev' -name  rUp90'
'getinfo numfiles'
         newfile = result
'close ' newfile

* Compute difference between 80% Confidence and zero: rUp80diff
* -------------------------------------------------------------
'makezdif3 -q1   rUp80'm' -file1 'mfile' -q2  zero  -file2 1  -ptop 'toplev' -name  rUp80'
'getinfo numfiles'
         newfile = result
'close ' newfile

'set gxout grfill'
'rgbset'

* Define New Variables for Montage Plots
* -------------------------------------
'set dfile 'timefile.m
'set t 'tmin.m' 'tmax.m
'set lev 1000 'toplev

* For ravediff > 0
* ----------------
'define sigdiffp90   = 1000 * ( ravediff-rUp90diff )'
'define sigdiffp95   = 1000 * ( ravediff-rUp95diff )'
'define sigdiffp99   = 1000 * ( ravediff-rUp99diff )'
'define sigdiffp99p99= 1000 * ( ravediff-rUp99p99diff )'

* For ravediff < 0
* ----------------
'define sigdiffm90 = 1000 * ( ravediff+rUp90diff )'
'define sigdiffm95 = 1000 * ( ravediff+rUp95diff )'
'define sigdiffm99 = 1000 * ( ravediff+rUp99diff )'
'define sigdiffm99p99 = 1000 * ( ravediff+rUp99p99diff )'

'define maskm90 = ( sigdiffm90 - abs(sigdiffm90) )/2'
'define maskm95 = ( sigdiffm95 - abs(sigdiffm95) )/2'
'define maskm99 = ( sigdiffm99 - abs(sigdiffm99) )/2'
'define maskm99p99 = ( sigdiffm99p99 - abs(sigdiffm99p99) )/2'

'define maskp90 = ( sigdiffp90 + abs(sigdiffp90) )/2'
'define maskp95 = ( sigdiffp95 + abs(sigdiffp95) )/2'
'define maskp99 = ( sigdiffp99 + abs(sigdiffp99) )/2'
'define maskp99p99 = ( sigdiffp99p99 + abs(sigdiffp99p99) )/2'

'define sigdiff90 = maskm90 + maskp90'
'define sigdiff95 = maskm95 + maskp95'
'define sigdiff99 = maskm99 + maskp99'
'define sigdiff99p99 = maskm99p99 + maskp99p99'


* Find maximum value of critical sigdiff across all levels and times
* ------------------------------------------------------------------
if( toplev <= 1 )
    loopdim = 3
    levmin  = 1
endif
if( toplev > 1 & toplev < 100 )
    loopdim = 2
    levmin  = 10
endif
if( toplev >= 100 )
    loopdim = 1
    levmin  = 100
endif

loop = 1
while( loop <= loopdim )
           if( loop = 1 ) ; levmin = 100 ; loopflag = ""  ; endif
           if( loop = 2 ) ; levmin = 10  ; loopflag = "2" ; endif
           if( loop = 3 ) ; levmin = 1   ; loopflag = "3" ; endif

'set dfile 'timefile.m
'set t 'tbeg.m' 'tdif.m
'set lev 1000 'levmin

         critvalue   = 95
' define sigdiffcrit = sigdiff'critvalue

' minmax sigdiffcrit'

    qmax = subwrd(result,1)
    qmin = subwrd(result,2)

    xmax = subwrd(result,3)
    ymax = subwrd(result,4)
    zmax = subwrd(result,7)
    tmax = subwrd(result,9)

    xmin = subwrd(result,5)
    ymin = subwrd(result,6)
    zmin = subwrd(result,8)
    tmin = subwrd(result,10)

    qmax = math_abs(qmax)
    qmin = math_abs(qmin)

if( qmin > qmax )
    qmax = qmin
    xmax = xmin
    ymax = ymin
    zmax = zmin
    tmax = tmin
endif

* To eliminate shading that is insignificant in a practical sense, 
* compare the shading scale based on the maximum value of sigdiffcrit ( ravediff - rUp90diff)
*                                 to the maximum value of sigdiffmax  (rUp99diff - rUp80diff)
* -------------------------------------------------------------------------------------------
           maxvalue  = 80
' define sigdiffmax  = 1000 * ( rUp99diff-rUp'maxvalue'diff )'

' minmax sigdiffmax'

    cmax = subwrd(result,1)
    cmin = subwrd(result,2)

    cmax = math_abs(cmax)
    cmin = math_abs(cmin)

if( cmin > cmax )
    cmax = cmin
endif

say ' '
say 'qmax based on critvalue ( ravediff-rUp'critvalue'diff) = 'qmax
say 'qmax based on  maxvalue (rUp99diff-rUp'maxvalue'diff) = 'cmax
say ' '
if(  cmax > qmax )
     qmax = cmax
endif
say '                final qmax = 'qmax

* Finally, only perform shading when the significant difference 
* is greater than the magnitude of the thickness of a standard RMS line
* (i.e., we need to see a gap between RMS lines)
* ---------------------------------------------------------------------
'set vpage off'
'set parea off'
'set grads off'

'getinfo zdim'
         zdim = result
zsum = 0.0
zmin =  1e15
zmax = -1e15

zcnt = 0
z = 1
while( z<=zdim )
   'set z 'z
'getinfo level'
         level  = result
if( level >= levmin ) 
zcnt = zcnt + 1

'minmax rave0'
if( subwrd(result,1) != 1e+15 )
    maxval = subwrd(result,1)
minval = subwrd(result,2)

    axmax  =   1.08 * maxval
axmin  = 0.92 * minval

    'set vpage off'
    'set parea off'
    'set grads off'
    'set parea 2.25 9.75 4.0 7.5'
    'set axlim 'axmin' 'axmax
    'd rave0'
    'd rave1'
'q gr2xy 1 1'
     xval = subwrd(result,3)
     yval = subwrd(result,6)
    
      if( xval != environment )
        say 'xval = 'xval
        say 'yval = 'yval
        say 'GR2XY Result, xval:yval = 'result
       'set line 2 1 3'
       'draw line 'xval' 'yval' 4 'yval
    yval = yval - 0.03
        say 'New yval = 'yval
       'q xy2gr 'xval' 'yval
        say 'XY2GR Result: 'result
    thickness.xpos.z = 1.0 - subwrd(result,6)
        thickness.xpos.z = thickness.xpos.z * 1000
        zsum = zsum + thickness.xpos.z
        if( thickness.xpos.z > zmax ) ; zmax = thickness.xpos.z ; endif
        if( thickness.xpos.z < zmin ) ; zmin = thickness.xpos.z ; endif
       'set line 3 1 3'
       'draw line 3.5 'yval' 7.5 'yval
        say ' '
        say 'z = 'z'  Level: 'level'  LEVMIN: 'levmin'  LINE_THICKNESS x 1000 = 'thickness.xpos.z
        say 'zmin = 'zmin'  zmax = 'zmax'  zsum = 'zsum
        say ' '
        say 'Hit Enter to Continue ...'
        pull flag
       'c'
      else
        zsum = 0
        zmin = 0
      endif

endif
endif
z = z + 1
endwhile

   zsum = zsum / zcnt
   say 'Average zthick = 'zsum

'set t 'tbeg.m' 'tdif.m
'set lev 1000 'levmin

           dcint = qmax / 9
  mean_thickness = zsum
   min_thickness = zmin

************************************************************************
'c'
************************************************************************

if( mean_thickness > dcint ) ; dcint = mean_thickness ; endif

* Hardwire values for correlation plots
dcint = 2.0
min_thickness = 1.0

say '        DCINT for plots: 'dcint
say 'MIN_THICKNESS for plots: 'min_thickness

flag = ''
while( flag = '' )
'set vpage off'
'set grads off'
'set grid  off'
'set parea 2.25 9.75 1.0 7.5'
if( levmin < 100 )
    'set zlog on'
    'setlevs'
else
    'set zlog off'
endif
'set xaxis 0 'nday' .5'
'set string 1 c 6 0'

'set datawarn off'

* Shade where sigdiff > critvalue confidence error bar (color shaded)
* -------------------------------------------------------------------
 ' rgbset'
 ' set csmooth off'

 clevs = ''
 n = -10
 while ( n <= 9 )
   val = n * dcint + min_thickness 
   clevs = clevs' 'val
   n = n + 1
 endwhile

 clevm = -1 * dcint + min_thickness
 clevp = min_thickness

* Fill 95% confidence
* -------------------------------
 'set gxout grfill'
 'set clevs 'clevs
*'set ccols 159 157 155 147 144 137 136 134 132 130 -1 120 121 122 123 124 125 126 127 128 129'
 'set ccols 59 57 55 47 44 37 36 34 32 30 -1 20 21 22 23 24 25 26 27 28 29'
 ' d sigdiff95 '
 ' cbarn -xmid 6 -snum 0.70 -ndot 1'

* Fill 99% dotted
* -------------------------------
 'set csmooth on'
 'set gxout shade2'
 'set clevs 'clevm
 'set ccols 200 -1'
 ' d sigdiff99 '
 'set clevs 'clevp
 'set ccols -1 200' 
 ' d sigdiff99 '
 ' set csmooth off'

* Fill 99.99% dotted
* -------------------------------
 'set csmooth on'
 'set gxout shade2'
 'set clevs 'clevm
 'set ccols 100 -1'
 ' d sigdiff99p99 '
 'set clevs 'clevp
 'set ccols -1 100'
 ' d sigdiff99p99 '
 ' set csmooth off'

* reset some background values
* ----------------------------
'set datawarn on'
'set clab on'

* Draw Labels
* -----------
'draw ylab Pressure (hPa)'
'set  string 1 c 6 0'

dcintx = dcint * 100
'getint 'dcintx
         dcintx = result / 100

'set  strsiz .132'
'draw string 6.0 8.15 'expdsc.m' - 'expdsc.0' ('numfiles')'
'draw string 6.0 7.90 ACORR Difference (x10`a-3`n) >95% (Filled) >99% (Dotted) >99.99% (Hatched)'
'set  strsiz .125'
'draw string 6.0 7.65 'name' 'region
'set  strsiz .12'
'draw string 6.0 0.72 Forecast Day'

'run uppercase 'field
                FIELD = result

'set  string 1 l 8 0'
'set  strsiz .32'
'draw string 0.70 7.38 'reg
'draw string 0.70 7.01 'FIELD

'set  string 1 c 6 90'
'set  strsiz .18'
'draw string 0.80 4.25 'months' 'year

say 'EXP'm'  Field: 'name'  Region: 'region

'!/bin/mkdir -p 'SOURCE'/corcmp'
if( nday = ndaymax )
   'myprint2 -name 'SOURCE'/corcmp/'expdsc.0'_'expdsc.m'_stats'loopflag'_'label'_corcmp_'reg'_z_'months' -rotate 90 -density 100x100'
else
   'myprint2 -name 'SOURCE'/corcmp/'expdsc.0'_'expdsc.m'_stats'loopflag'_'label'_corcmp_'reg'_z_'months'_'nday'DAY -rotate 90 -density 100x100'
endif

if( debug = "TRUE" )
    say "Hit ENTER for next plot"
    pull flag
else
    flag = 'c'
endif
'c'

endwhile

************************************************************************
'set dfile 'ddif.m
************************************************************************

loop = loop + 1
endwhile

m = m + 1
endwhile

return

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

