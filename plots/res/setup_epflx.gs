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

           '!remove EXPID.txt.'
           '!echo 'CMPID.num' | cut -d. -f2 > EXPID.txt'
       say 'run getenv "EXPID"'
           'run getenv "EXPID"'
                        expid.num = result


           'run setenv  DFILE DFILE.'num
           'run getenv  DFILE'
                        DFILE = result
           'run setenv 'DFILE' 'num


            say 'EXPID.'num' = 'expid.num
            say 'DFILE.'num' = 'num
            pause

   'xdfopen 'CTLFILE.num
   if( CMPID.num = 'VERIFICATION.'expid ) ; nexpid = num ; endif
   num = num + 1
endwhile

'getinfo numfiles'
         numfiles = result
endif


'!/bin/rm -f LOCKFILE'
say ''
say 'Files:'
'q files'
say  result
say 'nexpid: 'nexpid
pause

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

       say 'Computing seasonal epfy, epfz, and epfdiv using file: 'n' and maskfile: 'maskfile
       say '-----------------------------------------------------'
       pause
       'makezdif4 -q1 epfy.'n' -q2 zeromask -file1 'n' -file2 'maskfile
       'run getenv "ZDIFILE" '
                    zdifile = result
       'set dfile ' zdifile

           'run setenv  DFILE DFILE.'n
           'run getenv  DFILE'
                        DFILE = result
           'run setenv 'DFILE' 'zdifile

       'getdates'
       'set x 1'
       'sety'
       'setz'
       'define epfy'n' = qz'
       'seasonal epfy'n' A'
       'set dfile 'n
       'q files'
        say 'FILES: 'result
        pause

       'getdates'
       'set x 1'
       'sety'
       'setz'
       'makezdif4 -q1 epfz.'n' -q2 zeromask -file1 'n' -file2 'maskfile
       'run getenv "ZDIFILE" '
                    zdifile = result
       'set dfile ' zdifile
       'getdates'
       'set x 1'
       'sety'
       'setz'
       'define epfz'n' = qz'
       'seasonal epfz'n' A'
       'set dfile 'n
       'q files'
        say 'FILES: 'result
        pause

       'getdates'
       'set x 1'
       'sety'
       'setz'
       'makezdif4 -q1 epfdiv.'n' -q2 zeromask -file1 'n' -file2 'maskfile
       'run getenv "ZDIFILE" '
                    zdifile = result
       'set dfile ' zdifile
       'getdates'
       'set x 1'
       'sety'
       'setz'
       'define epfdiv'n' = qz'
       'seasonal epfdiv'n' A'
       'set dfile 'n
       'q files'
        say 'FILES: 'result
        pause

   else

       say 'Computing seasonal epfy, epfz, and epfdiv using file 'n' and NO maskfile'
       say '------------------------------------------------------------------------'
       pause
      'define     epfy'n' =   epfy.'n
      'define     epfz'n' =   epfz.'n
      'define   epfdiv'n' = epfdiv.'n
      'seasonal   epfy'n' A'
      'seasonal   epfz'n' A'
      'seasonal epfdiv'n' A'
       pause

   endif

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
           say 'Running: epflx.gs 'expid.n' 'season' 'n'A 'output
           say '-------------------------------------------------'
           'set x 1'
           'sety'
           'setz'
                    flag = ""
            while ( flag = "" )
                   'run 'geosutil'/plots/res/epflx.gs 'expid.n' 'TEM_NAME.n' 'season' 'n'A 'output
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
if( CMPID.n != 'VERIFICATION.'expid )
          k = 1
   while( k > 0 )
           season = subwrd(seasons,k)
       if( season != '' )
                k = k+1
           say 'Running:  epflx_diff.gs 'expid' 'expid.n' 'season' 'nexpid'A 'output
           say '----------------------------------------------------'

               flag = ""
       while ( flag = "" )
          say 'run 'geosutil'/plots/res/epflx_diff.gs 'expid' 'expid.n' 'TEM_NAME.nexpid' 'TEM_NAME.n' 'season' 'nexpid'A 'n'A 'output
              'run 'geosutil'/plots/res/epflx_diff.gs 'expid' 'expid.n' 'TEM_NAME.nexpid' 'TEM_NAME.n' 'season' 'nexpid'A 'n'A 'output
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
          say 'run 'geosutil'/plots/res/epflx_diff.gs 'expid.n' 'expid' 'TEM_NAME.n' 'TEM_NAME.nexpid' 'season' 'n'A 'nexpid'A 'output
              'run 'geosutil'/plots/res/epflx_diff.gs 'expid.n' 'expid' 'TEM_NAME.n' 'TEM_NAME.nexpid' 'season' 'n'A 'nexpid'A 'output
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

