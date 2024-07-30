function setup_wstar (args)

say ' '
say 'Inside setup_wstar'
say ' '
pause

* -------------------------------------------------
* Set TIME flag:  A => Common Times, B => All Times
* -------------------------------------------------
      TFLAG = A
* -------------------------------------------------
* -------------------------------------------------

source = subwrd(args,1)
expid  = subwrd(args,2)
output = subwrd(args,3)

say 'source: 'source
say ' expid: 'expid
pause

* Define Seasons to Process
* -------------------------
seasons  = ''
       k = 4
while( k > 0 )
    season = subwrd(args,k)
if( season = '' )
    k = -1
else
    seasons = seasons % ' ' % season
k = k+1
endif
endwhile
'uppercase 'seasons
            seasons = result

'getinfo numfiles'
         numfiles = result

if( numfiles = 'NULL' )

* Loop over Experiment Datasets
* -----------------------------
'getpwd'
    pwd = result

'getnumrc 'pwd
     rcinfo = result
     numrc  = subwrd( rcinfo,1 )
       num  = 1
       cnt  = 0
while( num <= numrc )
        loc = num + 1
     rcfile = subwrd( rcinfo,loc )
     say 'num = 'num'  rcfile = 'rcfile
   '!grep filename 'rcfile' | cut -d'"\' -f2 > CTLFILE.txt"
    'run getenv CTLFILE '
                CTLFILE.num = result

   '!basename 'rcfile' > BASENAME.txt'
    'run getenv BASENAME'
                basename = result
     length   = strlen(basename) - 3
     say 'original length = 'length
    '!echo 'basename' | cut -b1-'length' > CMPID.txt'
    'run getenv CMPID '
                CMPID.num = result

   say '  CMPID #'num' = 'CMPID.num
   say 'CTLFILE #'num' = 'CTLFILE.num

           '!remove TEM_NAME.txt.'
           '!basename 'CTLFILE.num' | cut -d. -f2 > TEM_NAME.txt'
       say 'run getenv "TEM_NAME"'
           'run getenv "TEM_NAME"'
                        TEM_NAME.num = result
            say 'TEM_Collection = 'TEM_NAME.num
            pause

   'xdfopen 'CTLFILE.num
   if( CMPID.num = 'VERIFICATION.'expid ) ; nexpid = num ; endif
   num = num + 1
endwhile

'getinfo numfiles'
         numfiles = result
endif


'!/bin/rm -f LOCKFILE'
'q files'
say ' Files: 'result
say 'nexpid: 'nexpid
pause

'set dfile 'nexpid
'getinfo dset'
         dset = result
'!fsource 'dset
'run getenv FSOURCE'
            fsource = result

'!remove NFILES.txt'
'!/bin/ls -1 'fsource'/'expid'.TEM_Diag.monthly.*.nc4 | wc -l > NFILES.txt'
'run getenv NFILES'
            nfiles = result

'getinfo tdim'
         tdim = result

say ''
say '    TDIM: 'tdim
say '  NFILES: 'nfiles
say ''

* Initialize BEGDATE and ENDATE for each Experiment
* -------------------------------------------------
say 'Initializing BEGDATE and ENDATE for each Experiment:'
say '----------------------------------------------------'
n = 1
while( n<=numfiles )
   'set dfile 'n
   'set t 1'
   'getinfo date'
         begdate.n = result
   'run setenv BEGDATE'n' 'begdate.n
   'getinfo tdim'
            tdim.n = result
   'set t ' tdim.n
   'getinfo date'
         enddate.n = result
   'run setenv ENDDATE'n' 'enddate.n
say 'begdate.'n': 'begdate.n'  enddate.'n': 'enddate.n
n = n + 1
endwhile
say ''

* -------------------------------------------
* Compute Seasonal Means for Common Times (A)
* -------------------------------------------
if( TFLAG = 'A' )
'run setenv TIME 'TFLAG

* Find time subset which includes all files
* -----------------------------------------
'set dfile 1'
say 'Calling SETDATES for File1'
say '--------------------------'
'setdates'
say 'Calling GETDATES for File1'
say '--------------------------'
'getdates'

'run getenv BEGDATE'
            BEGDATE = result
'run getenv ENDDATE'
            ENDDATE = result
say ' '


say 'Finding Common Times between Experiments'
say '----------------------------------------'
begtimeA = 1
endtimeA = tdim.1

begdateA = begdate.1
enddateA = enddate.1
n = 2
while( n<=numfiles )
    'set time 'begdate.n
    'getinfo time'
             time = result
    if( time > begtimeA )
        say begdate.n' > 'begdateA
            begdateA = begdate.n
            begtimeA = time
    endif
    'set time 'enddate.n
    'getinfo time'
             time = result
    if( time < endtimeA )
        say enddate.n' < 'enddateA
            enddateA =  enddate.n
            endtimeA = time
    endif
n = n + 1
endwhile
pause

* Hardwire Beginning and Ending Dates
* -----------------------------------
say ' '
say 'Pre-Set Environment Variable BEGDATE: 'BEGDATE
say 'Pre-Set Environment Variable ENDDATE: 'ENDDATE
say '     Computed Common Dates  begdateA: 'begdateA
say '     Computed Common Dates  enddateA: 'enddateA
say ' '
pause

* Compare with Pre-Set Environment Variables
* ------------------------------------------
  'set time 'BEGDATE
    'getinfo time'
             begtime = result
  'set time 'ENDDATE
    'getinfo time'
             endtime = result
  
  if( begtime >= begtimeA & endtime <= endtimeA )
      begdateA = BEGDATE
      enddateA = ENDDATE
  endif

* Compute Seasonal Means for Subset Times (A)
* -------------------------------------------
say 'run setenv BEGDATE 'begdateA
    'run setenv BEGDATE 'begdateA
say ' '

say 'run setenv ENDDATE 'enddateA
    'run setenv ENDDATE 'enddateA
say ' '

say 'set time 'begdateA' 'enddateA
    'set time 'begdateA' 'enddateA
say ' '


* Check to see if expid files are time-continuous (i.e., no UNDEF periods)
* ---------------------------------------------------------------------------------
'set dfile 'nexpid
 say 'getdates'
     'getdates'
 say ' '
'set z 1'

maskfile = 'NULL'
       k = 1
  season = subwrd(seasons,k)
while( k > 0 )
       'run count.gs "'season'" 'begdateA' 'enddateA
        countnomask = result
       'run count.gs "'season'" 'begdateA' 'enddateA' -field str'
        countmask = result
        say 'COUNT 'season' without MASK: 'countnomask
        say      '          with    MASK: 'countmask

        if( countnomask != countmask )
           maskfile = nexpid
        endif

             k = k+1
        season = subwrd(seasons,k)
    if( season = '' )
             k = -1
    endif
say ' '
endwhile

     say       'MASKFILE: 'maskfile
    'run setenv MASKFILE ' maskfile
    'run setenv NUMFILES ' numfiles

     pause

if( maskfile != 'NULL' ) 
  'set dfile 'maskfile
  'getdates'
  'set x 1'
  'sety'
  'setz'
  'define zeromask = wstar-wstar + lon-lon'
endif

n = 1
while( n<=numfiles )
  'set dfile 'n
  'getdates'
  'set x 1'
  'sety'
  'setz'

   if( maskfile != 'NULL' & maskfile != n ) 

       say 'Computing zdiff and seasonal wstar and res using file: 'n' and maskfile: 'maskfile
       say '-----------------------------------------------------'
       pause
       'makezdif4 -q1 wstar.'n' -q2 zeromask -file1 'n' -file2 'maskfile
       'run getenv "ZDIFILE" '
                    zdifile = result
       'set dfile ' zdifile
       'getdates'
       'set x 1'
       'sety'
       'setz'
       'define wstar'n' = qz'
       'seasonal wstar'n' A'
       'close 'zdifile
       'set dfile 'n
       'q files'
        say 'FILES: 'result
        pause

       'getdates'
       'set x 1'
       'sety'
       'setz'
       'makezdif4 -q1 res.'n' -q2 zeromask -file1 'n' -file2 'maskfile
       'run getenv "ZDIFILE" '
                    zdifile = result
       'set dfile ' zdifile
       'getdates'
       'set x 1'
       'sety'
       'setz'
       'define res'n' = qz'
       'seasonal res'n' A'
       'close 'zdifile
       'set dfile 'n
       'q files'
        say 'FILES: 'result
        pause

   else

       say 'Computing seasonal wstar and res using file: 'n' and maskfile: 'maskfile
       say '-------------------------------------------'
       pause
      'define wstar'n' = wstar.'n
      'define   res'n' =   res.'n
      'seasonal wstar'n' A'
      'seasonal res'n'   A'
       pause

   endif

n = n + 1
endwhile
endif

* -------------------------------------------

* -------------------------------------------------------------
* Compute Seasonal Means for ALL Times (B)  (Not fully tested)
* -------------------------------------------------------------
if( TFLAG = 'B' )
   'run setenv TIME 'TFLAG
   '!remove BEGDATE.txt'
   '!remove ENDDATE.txt'
   n = 1
   while( n<=numfiles )
     'set dfile 'n
     'set x 1'
     'sety'
     'setz'
     'sett'
     'define wstar'n' = wstar.'n
     'seasonal wstar  B'n
     'seasonal res    B'n
   n = n + 1
   endwhile
   pause
endif
* ----------------------------------------


'set display color white'
'rgbset'
'set gxout shaded'
'c'

'run getenv "GEOSUTIL"'
             geosutil = result

       k = 1
while( k > 0 )
        season = subwrd(seasons,k)
    if( season != '' )
             k = k+1

*  Plot turn-around-latitudes
* ---------------------------
   'run 'geosutil'/plots/res/turn_around_lats.gs 'season' 'output
    pause
   'c'

*  Plot wstar profiles for ALL experiments
* ----------------------------------------
   'run 'geosutil'/plots/res/plot_season.gs levl 'output
    pause
   'c'
   'run 'geosutil'/plots/res/plot_season.gs avrg 'output
    pause
   'c'
   'run 'geosutil'/plots/res/plot_season.gs indv 'output
    pause
   'c'

*  Plot wstar profiles for Individual experiments
* -----------------------------------------------
    say ' '
   'q files'
    say result
    say ' '

    n = 1
    while( n<=numfiles )
           CMPID = CMPID.n
           TEM_Collection = TEM_NAME.n

           'set dfile 'n
           'getinfo desc'
                    desc = result
            node = ''
            m = 1
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
            while( node != TEM_Collection )
            EXP.n = EXP.n'.'node
            say 'EXP'n' = 'EXP.n
            m = m + 1
           '!remove NODE.txt'
           '!basename 'desc' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            endwhile
        if( EXP.n  = expid )
            nexpid = n
        endif
        n = n + 1
    endwhile

    alfbet = 'abcdefghijklmnopqrstuvwxyz'
    alfexp = substr(alfbet,nexpid,1)
    say 'alfexp = 'alfexp
    pause

    n = 1
    while( n<=numfiles )
    if( n != nexpid )
        string = substr(alfbet,n,1)
       'run 'geosutil'/plots/res/plot_season.gs levl 'output' 'alfexp' 'string 
        pause
       'c'
       'run 'geosutil'/plots/res/plot_season.gs avrg 'output' 'alfexp' 'string
        pause
       'c'
       'run 'geosutil'/plots/res/plot_season.gs indv 'output' 'alfexp' 'string
        pause
       'c'
    endif
    n = n + 1
    endwhile

    else
             k = -1
    endif
endwhile

