function writegrads(args)

*****************************************************************************************
*
*       args:  -vars  list of variables to write (Default: all variables)  
*              -levs  list of levels    to write (Default: all levels)  
*              -time  all  (all times to single file, Default)  
*                     one  (one time  per file)  
*              -name  name of binary name.data and name.ctl file (Default: name = grads)
*
* Note: To Write Data in Reverse Order
*       run setenv ZFLIP ON
*
*****************************************************************************************

'numargs  'args
 numargs = result

'getinfo xdim'
         xdim = result
'getinfo ydim'
         ydim = result
'getinfo zdim'
         zdim = result
'getinfo edim'
         edim = result
'getinfo tdim'
         tdim = result

'getinfo nvars'
         nvars = result

'getinfo dlon'
         dlon = result
'getinfo dlat'
         dlat = result

if( xdim = 1 ) ; dlon = 1 ; endif

*****************************************************************************************

VARS = 'ALL'
LEVS = 'ALL'
TIME = 'ALL'
NAME = 'grads'

        n   = 0
        num = 0
while ( num < numargs )
        num = num + 1
        if( subwrd(args,num) = '-name' ) ; NAME = subwrd(args,num+1) ; endif
        if( subwrd(args,num) = '-time' ) ; TIME = subwrd(args,num+1) ; endif

* Read VARS
* ---------
    if( subwrd(args,num) = '-vars' )
            VARS = ''
               k = 1
        while( k > 0 )
               L = num + k
             VAR = subwrd(args,L)
         if( VAR  = '' )
             k = -1
         else
            bit = substr(VAR,1,1)
            if( bit = '-' )
                  k = -1
            else
                  VARS = VARS % ' ' % VAR
                  k = k+1
            endif
         endif
        endwhile
    endif

* Read LEVS
* ---------
    if( subwrd(args,num) = '-levs' )
            LEVS = ''
               k = 1
        while( k > 0 )
               L = num + k
             LEV = subwrd(args,L)
         if( LEV  = '' )
             k = -1
         else
            bit = substr(LEV,1,1)
            if( bit = '-' )
                  k = -1
            else
                  LEVS = LEVS % ' ' % LEV
                  k = k+1
            endif
         endif
        endwhile
    endif

endwhile
* ------

if( LEVS = 'ALL' )
       z = 1
    LEVS = ''
    while( z<=zdim )
      'set z 'z
      'getinfo level'
               LEV  = result
               LEVS = LEVS' 'LEV
       z = z + 1
    endwhile
endif

if( VARS = 'ALL' )
       n = 1
    VARS = ''
    while( n<=nvars )
      'run getvarz 'n' noprint'
              VAR  = subwrd(result,1)
              VARS = VARS' 'VAR
       n = n + 1
    endwhile
endif

'numargs  'LEVS
 numlevs = result
    zdim = numlevs

'numargs  'VARS
 numvars = result

'run uppercase 'TIME
                TIME = result

*******************************************

'q gxout'
   gxout = sublin(result,4)
   gxout = subwrd(gxout,6)

'run getenv ZFLIP'
            zflip = result
'setx'
'sety'
'setz'

'set x 1'
'set y 1'
'getinfo lon'
         lonbeg = result
'getinfo lat'
         latbeg = result
'getinfo tinc'
         tinc = result
'getinfo tunit'
         tunit = result
'getinfo label'
         label = result

if( tunit = 'year'  ) ; tunit = yr ; endif
if( tunit = 'month' ) ; tunit = mo ; endif
if( tunit = 'day'   ) ; tunit = dy ; endif
if( tunit = 'hour'  ) ; tunit = hr ; endif

'setx'
'sety'

* --------------------------------

* --------------------------------------------------------------------

t=1
while(t<=tdim)

  'set t 't

'getinfo date'
         date = result
         year = substr( date,9,4 )
         day  = substr( date,4,2 )
        month = get_month()
     yyyymmdd = year''month''day

if( t = 1 | TIME = 'ONE' ) 

* Write 'NAME'.ctl
* ----------------
'!remove 'NAME'.'yyyymmdd'.ctl'
'!touch  'NAME'.'yyyymmdd'.ctl'
'!echo dset ^'NAME'.'yyyymmdd'.data            >> 'NAME'.'yyyymmdd'.ctl'
'!echo title 'label'                           >> 'NAME'.'yyyymmdd'.ctl'
'!echo undef 1e15                              >> 'NAME'.'yyyymmdd'.ctl'
'!echo xdef 'xdim' linear 'lonbeg' 'dlon'      >> 'NAME'.'yyyymmdd'.ctl'
'!echo ydef 'ydim' linear 'latbeg' 'dlat'      >> 'NAME'.'yyyymmdd'.ctl'
'!echo zdef 'zdim' levels 'LEVS'               >> 'NAME'.'yyyymmdd'.ctl'
if( TIME = 'ALL' )
'!echo tdef 'tdim' linear 'date' 'tinc''tunit' >> 'NAME'.'yyyymmdd'.ctl'
else
'!echo tdef   1    linear 'date' 'tinc''tunit' >> 'NAME'.'yyyymmdd'.ctl'
endif
'!echo vars 'numvars'                          >> 'NAME'.'yyyymmdd'.ctl'

* --------------------------------------------------------------------

'set gxout fwrite'
'set fwrite 'NAME'.'yyyymmdd'.data'

endif


'set undef 1e15'

n=1
while(n<=nvars)

'run getvarz 'n' noprint'
     name = subwrd(result,1)
     zref = subwrd(result,2)

     found = true
     if( numvars != nvars )
         found = false
         k=1
         while( k<=nvars ) 
           if( subwrd(args,k) = name ) ; found = true ; endif
         k=k+1
         endwhile
     endif

 if( found = true )

  'q file'
   loc = 6 + n 
   varinfo = sublin(result,loc)
  '!remove DESC.txt'
  '!echo "'varinfo'" > DESC.txt'
  'run getenv "DESC"'
    desc = result
  '!remove DESC.txt'
  'numargs 'desc
   numdesc = result
     field = subwrd(desc,1)
     nlev  = subwrd(desc,2)
   if( nlev = 0 )
       newdesc = subwrd(desc,1)' 'nlev
   else
       newdesc = subwrd(desc,1)' 'zdim
   endif
          count  = 3
   while( count <= numdesc )
         adddesc = subwrd(desc,count)
         newdesc = newdesc' 'adddesc
          count  = count + 1
   endwhile
   desc = newdesc

   say 'Writing Time: 't'  Desc: 'desc

   if( name = slp ) ; zref = 0 ; endif

   if( zref = 0 )
       if( ( t=1 & TIME = 'ALL' ) | TIME = 'ONE' ) ; '!echo "'desc'" >> 'NAME'.'yyyymmdd'.ctl' ; endif
*      say 'Writing Variable: 'name
      'set z 1'
       e = 1
       while( e<=edim )
      'set e 'e
      'd 'name
       e = e + 1
       endwhile
   else
      if( ( t=1 & TIME = 'ALL' ) | TIME = 'ONE' ) ; '!echo "'desc'" >> 'NAME'.'yyyymmdd'.ctl' ; endif

      if(zflip != 'ON' )
         z=1
         while(z<=zdim)
             level = subwrd(LEVS,z)  
            'set lev 'level
*           'set z 'z
            'getinfo level'
             lev = result
*            say 'Writing Variable: 'name' for Level: 'lev
             e = 1
             while( e<=edim )
            'set e 'e
            'd 'name
             e = e + 1
             endwhile
         z=z+1
         endwhile
      else
         z=zdim
         while(z>=1)
             level = subwrd(LEVS,z)  
            'set lev 'level
*           'set z 'z
            'getinfo level'
             lev = result
*            say 'Writing Variable: 'name' for Level: 'lev
             e = 1
             while( e<=edim )
            'set e 'e
            'd 'name
             e = e + 1
             endwhile
         z=z-1
         endwhile
      endif

   endif
*      say '  '
 endif

n=n+1
endwhile

if( ( t=1 & TIME = 'ALL' ) | TIME = 'ONE' ) ; '!echo endvars >> 'NAME'.'yyyymmdd'.ctl' ; endif
                         if( TIME = 'ONE' ) ; 'disable fwrite' ; 'set gxout 'gxout ; endif

say ' '
t=t+1
endwhile

if( TIME = 'ALL' ) ; 'disable fwrite' ; endif
'set gxout 'gxout
return

function get_month(args)
'getinfo month'
         month = result
      if(month="JAN") ; monthnum = 01 ; endif
      if(month="FEB") ; monthnum = 02 ; endif
      if(month="MAR") ; monthnum = 03 ; endif
      if(month="APR") ; monthnum = 04 ; endif
      if(month="MAY") ; monthnum = 05 ; endif
      if(month="JUN") ; monthnum = 06 ; endif
      if(month="JUL") ; monthnum = 07 ; endif
      if(month="AUG") ; monthnum = 08 ; endif
      if(month="SEP") ; monthnum = 09 ; endif
      if(month="OCT") ; monthnum = 10 ; endif
      if(month="NOV") ; monthnum = 11 ; endif
      if(month="DEC") ; monthnum = 12 ; endif
return monthnum

