function setup_epflx (args)

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

'run getenv MASKFILE ' maskfile
            maskfile = result

'q files'
say result

'run getenv "GEOSUTIL"'
             geosutil = result

* Find time subset which includes all files
* -----------------------------------------
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

n = 1
while( n<=numfiles )
'run 'geosutil'/plots/res/epflx.gs 'CMPID.n' 'season' A'n' 'output
pause
'c'
n = n + 1
endwhile


n = 1
while( n<=numfiles )
if( CMPID.n != expid )

*           flag = ""
*   while ( flag = "" )
   'run 'geosutil'/plots/res/epflx_diff.gs 'expid' 'CMPID.n' 'season' A'nexpid' A'n' 'output
*   say "Hit  ENTER  to repeat plot"
*   say "Type 'next' for  next plot, 'done' for next field"
*   pull flag
*   endwhile
   'c'
*           flag = ""
*   while ( flag = "" )
   'run 'geosutil'/plots/res/epflx_diff.gs 'CMPID.n' 'expid' 'season' A'n' A'nexpid' 'output
*   say "Hit  ENTER  to repeat plot"
*   say "Type 'next' for  next plot, 'done' for next field"
*   pull flag
*   endwhile
   'c'

endif
n = n + 1
endwhile

* Move DATA for Archive
* ---------------------
'!/bin/mv -f residual*ctl    ../'
'!/bin/mv -f residual*data   ../'
'!/bin/mv -f VERIFICATION*rc ../'
'!/bin/cp -f ../residual.'expid'.* ../../'

return

