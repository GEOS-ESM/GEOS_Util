function setup_epflx (args)

source = subwrd(args,1)
expid  = subwrd(args,2)
output = subwrd(args,3)
debug  = subwrd(args,4)

* Define Seasons to Process
* -------------------------
seasons  = ''
       k = 5
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

say 'Running:  setup_epflx 'source' 'expid' 'output' 'seasons
say '--------------------------------------------------------'
say ' '

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
   if( CMPID.num = expid ) ; nexpid = num ; endif
   num = num + 1
endwhile

'getinfo numfiles'
         numfiles = result
endif

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
     say 'CTLFILE.'num' = 'CTLFILE.num

   '!basename 'CTLFILE.num' > BASENAME.txt'
    'run getenv BASENAME'
                basename = result

           '!remove NODE.txt'
           '!echo 'basename' | cut -d. -f1 >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            cmpid = node

            say 'cmpid = 'cmpid
            TEM_Collection = TEM_NAME.num
            m = 2
           '!remove NODE.txt'
           '!echo 'basename' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            while( node != TEM_Collection )
                   cmpid =  cmpid'.'node
              say 'cmpid = 'cmpid
            m = m + 1
           '!remove NODE.txt'
           '!echo 'basename' | cut -d. -f'm' >> NODE.txt'
           'run getenv "NODE"'
                        node = result
            endwhile

                          CMPID.num = cmpid
   say '  CMPID #'num' = 'CMPID.num
   say 'CTLFILE #'num' = 'CTLFILE.num
   say ' '
*  'xdfopen 'CTLFILE.num
   if( CMPID.num = expid ) ; nexpid = num ; endif
   num = num + 1
endwhile

'getinfo numfiles'
         numfiles = result


'!/bin/rm -f LOCKFILE'
'q files'
   check = subwrd(result,1)

* Set MASKFILE to file which is not time-continuous (i.e., has UNDEF periods)
* ---------------------------------------------------------------------------
     maskfile = 'NULL'
*    maskfile = 2
    'run setenv MASKFILE ' maskfile
    'run setenv NUMFILES ' numfiles

say ''
say 'Files:'
'q files'
say result

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

* Hardwire begdate and enddate here
* ---------------------------------
*begdateA = 00z01jan2010
*enddateA = 00z01dec2014

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

say 'setdates'
    'setdates'
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

   if( maskfile != 0 & maskfile != NULL )
      'define epfy   = maskout(   epfy.'n',abs(   epfy.'maskfile') )'
      'define epfz   = maskout(   epfz.'n',abs(   epfz.'maskfile') )'
      'define epfdiv = maskout( epfdiv.'n',abs( epfdiv.'maskfile') )'
   endif

  'seasonal epfy   A'n
  'seasonal epfz   A'n
  'seasonal epfdiv A'n

n = n + 1
endwhile


'run setenv BEGDATE 'begdateA
'run setenv ENDDATE 'enddateA
'set display color white'
'rgbset'
'set gxout shaded'
'c'

'run getenv "GEOSUTIL"'
             geosutil = result

n = 1
while( n<=numfiles )
          k = 1
   while( k > 0 )
           season = subwrd(seasons,k)
       if( season != '' )
                k = k+1
           say 'Running: epflx.gs 'CMPID.n' 'season' A'n' 'output
           say '-------------------------------------------------'
           'set x 1'
           'sety'
           'setz'
                    flag = ""
            while ( flag = "" )
                   'run 'geosutil'/plots/res/epflx.gs 'CMPID.n' 'TEM_NAME.n' 'season' A'n' 'output
                    if( debug = "debug" )
                        say "Hit  ENTER  to repeat plot"
                        say "Type 'next' for  next plot, 'done' for next field"
                             pull flag
                    else
                             flag = "next"
                    endif
                   'c'
            endwhile

       else
                k = -1
       endif
   endwhile
n = n + 1
endwhile


n = 1
while( n<=numfiles )
if( CMPID.n != expid )
          k = 1
   while( k > 0 )
           season = subwrd(seasons,k)
       if( season != '' )
                k = k+1
           say 'Running:  epflx_diff.gs 'expid' 'CMPID.n' 'season' A'nexpid' A'n' 'output
           say '----------------------------------------------------'

               flag = ""
       while ( flag = "" )
          say 'run 'geosutil'/plots/res/epflx_diff.gs 'expid' 'CMPID.n' 'TEM_NAME.nexpid' 'TEM_NAME.n' 'season' A'nexpid' A'n' 'output
              'run 'geosutil'/plots/res/epflx_diff.gs 'expid' 'CMPID.n' 'TEM_NAME.nexpid' 'TEM_NAME.n' 'season' A'nexpid' A'n' 'output
               if( debug = "debug" )
                   say "Hit  ENTER  to repeat plot"
                   say "Type 'next' for  next plot, 'done' for next field"
                        pull flag
               else
                        flag = "next"
               endif
              'c'
       endwhile

               flag = ""
       while ( flag = "" )
          say 'run 'geosutil'/plots/res/epflx_diff.gs 'CMPID.n' 'expid' 'TEM_NAME.n' 'TEM_NAME.nexpid' 'season' A'n' A'nexpid' 'output
              'run 'geosutil'/plots/res/epflx_diff.gs 'CMPID.n' 'expid' 'TEM_NAME.n' 'TEM_NAME.nexpid' 'season' A'n' A'nexpid' 'output
               if( debug = "debug" )
                   say "Hit  ENTER  to repeat plot"
                   say "Type 'next' for  next plot, 'done' for next field"
                        pull flag
               else
                        flag = "next"
               endif
              'c'
       endwhile

       else
                k = -1
       endif
   endwhile
endif
n = n + 1
endwhile

* Move DATA for Archive
* ---------------------
*'!/bin/mv -f residual*ctl    ../'
*'!/bin/mv -f residual*data   ../'
*'!/bin/mv -f VERIFICATION*rc ../'
*'!/bin/cp -f ../residual.'expid'.* ../../'

return

