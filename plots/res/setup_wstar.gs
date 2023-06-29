function setup_wstar (args)

source = subwrd(args,1)
expid  = subwrd(args,2)
output = subwrd(args,3)
season = subwrd(args,4)

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
   '!grep filename 'rcfile' | cut -d'"\' -f2 > CTLFILE.txt"
    'run getenv CTLFILE '
                CTLFILE.num = result

    '!echo `basename 'rcfile' | cut -d. -f2 > CMPID.txt`'
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


'run 'geosutil'/plots/res/turn_around_lats.gs 'season' 'output
'c'

'run 'geosutil'/plots/res/plot_season.gs avrg 'output
'c'
'run 'geosutil'/plots/res/plot_season.gs indv 'output
'c'

