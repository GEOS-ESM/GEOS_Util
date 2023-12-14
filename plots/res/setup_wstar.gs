function setup_wstar (args)

say ' '
say 'Inside setup_wstar'
say ' '
*pause

source = subwrd(args,1)
expid  = subwrd(args,2)
output = subwrd(args,3)

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
   'open 'CTLFILE.num
   if( CMPID.num = expid ) ; nexpid = num ; endif
   num = num + 1
endwhile

'getinfo numfiles'
         numfiles = result
endif

* Set TIME flag:  A => Common Times, B => All Times
* -------------------------------------------------
time = A


'!/bin/rm -f LOCKFILE'
'q files'
   check = subwrd(result,1)

* Set MASKFILE to file which is not time-continuous (i.e., has UNDEF periods)
* ---------------------------------------------------------------------------
     maskfile = 'NULL'
*    maskfile = 2
    'run setenv MASKFILE ' maskfile
    'run setenv NUMFILES ' numfiles

say 'Files:'
'q files'
say result
say 'MASKFILE: 'maskfile

* Initialize BEGDATE and ENDATE for each Experiment
* -------------------------------------------------
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

'run setenv TIME A'

* Find time subset which includes all files
* -----------------------------------------
'set dfile 1'
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
            begdateA   =  begdate.n
            begtimeA   = time
    endif
    'set time 'enddate.n
    'getinfo time'
             time = result
    if( time < endtimeA )
        say enddate.n' < 'enddateA
            enddateA   =  enddate.n
            endtimeA   = time
    endif
n = n + 1
endwhile

* Hardwire Beginning and Ending Dates
* -----------------------------------
say ' '
say 'begdateA = 'begdateA
say 'enddateA = 'enddateA

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

say 'getdates'
    'getdates'
say ' '

n = 1
while( n<=numfiles )
  'set dfile 'n
  'getdates'
  'set x 1'
  'sety'
  'setz'

   if( maskfile != 'NULL' ) 
      'define wstar'n' = maskout( wstar.'n',abs(wstar.'maskfile') )'
      'define wstar    = maskout( wstar.'n',abs(wstar.'maskfile') )'
      'define res      = maskout( res.'n'  ,abs(  res.'maskfile') )'
*     'define epfy     = maskout( epfy.'n' ,abs( epfy.'maskfile') )'
*     'define epfz     = maskout( epfz.'n' ,abs( epfz.'maskfile') )'
*     'define wmean    = maskout( wmean.'n',abs(wmean.'maskfile') )'
*     'define weddy    = maskout( weddy.'n',abs(weddy.'maskfile') )'
*     'define vstar    = maskout( vstar.'n',abs(vstar.'maskfile') )'
   else
      'define wstar'n' = wstar.'n
   endif

  'seasonal wstar  A'n
  'seasonal res    A'n
* 'seasonal epfy   A'n
* 'seasonal epfz   A'n
* 'seasonal epfdiv A'n
* 'seasonal wmean  A'n
* 'seasonal weddy  A'n
* 'seasonal vstar  A'n
n = n + 1
endwhile



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
           'set dfile 'n
           'getinfo desc'
                    desc = result
            node = ''
            m = 2
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
            while( node != 'ctl' & node != 'data' )
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

