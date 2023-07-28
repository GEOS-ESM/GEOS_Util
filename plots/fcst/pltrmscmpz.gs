function pltcorcmpz (args)

*******************************************************
****                 INPUT Variables               ****
*******************************************************

'numargs  'args
 numargs = result

SOURCE = NULL
DESC   = ''
rcfile = 'stats.rc'
fields = 'p u v t q h'
rms    = 0
regions = 'GLO NHE TRO SHE'
xregions = 'GLO NHE TRO SHE NWQ NEQ SWQ SEQ NAM EUR NPO SPO XPO'

        num = 0
while ( num < numargs )
        num = num + 1

if( subwrd(args,num) = '-source' ) ; SOURCE = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-desc'   ) ; DESC   = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-rc'     ) ; rcfile = subwrd(args,num+1) ; endif
if( subwrd(args,num) = '-rms'    ) ; rms    = subwrd(args,num+1) ; endif

if( subwrd(args,num) = '-fields' )
     fields = ''
           k = 1
    while( k > 0 )
           L = num + k
        field  = subwrd(args,L)
    if( field  = '' )
        k = -1
    else
        bit = substr(field,1,1)
        if( bit = '-' )
              k = -1
        else
              fields = fields % ' ' % field
              k = k+1
        endif
    endif
    endwhile
endif

if( subwrd(args,num) = '-regions' )
     regions = ''
           k = 1
    while( k > 0 )
           L = num + k
        region  = subwrd(args,L)
    if( region  = '' )
        k = -1
    else
        bit = substr(region,1,1)
        if( bit = '-' )
              k = -1
        else
              regions = regions % ' ' % region
              k = k+1
        endif
    endif
    endwhile
endif

endwhile

'numargs 'fields
 numfields = result

'numargs 'regions
 numregions = result

if( SOURCE != NULL ) 
   'run setenv "SOURCE" 'SOURCE
else
   'run getenv "PWD"'
            PWD = result
   'run setenv "SOURCE" 'PWD
endif
   'run getenv "SOURCE"'
            SOURCE = result

   'run getenv "GEOSUTIL"'
            geosutil = result

if( DESC = '' )
   'getresource 'rcfile' DESC'
                         DESC = result
   if( DESC = "NULL" ) ; DESC = 'Forecast_Statisitcs' ; endif
endif

*******************************************************
****            Open Control Experiment            ****
*******************************************************

n = 0

'run getenv SOURCE'
        SOURCE = result

if( SOURCE = "NULL" )
   'run getenv "PWD"'
    SOURCE = result
   'run setenv "SOURCE" 'SOURCE
endif

'getresource 'rcfile' EXP'n ;  exp.n = result
'getresource 'rcfile' DSC'n ; desc.n = result
 if( exp.n != NULL | desc.n  != NULL )
     n = n+1
 else
     say 'You must supply a CONTROL and COMPARISON experiment list'
     say 'in the file:  stats.rc'
     return
 endif

while( n >= 0 )
'getresource 'rcfile' EXP'n ;  exp.n = result
'getresource 'rcfile' DSC'n ; desc.n = result
 if( exp.n != NULL | desc.n  != NULL )
     n = n+1
 else
     ntot = n
        n = -999
 endif
endwhile

'corcmp_open.gs 'exp.0' 'desc.0

*******************************************************
****      Determine Number of Fields in File       ****
*******************************************************

'set dfile 1'
'run getenv SYSCMP_XDIM'
            xdim = result
'q ctlinfo'
say 'ctlinfo 'result
'getinfo nvars'
         nvars = result
m=0
n=1
while(n<=nvars)

  string = 'cor'
 lstring = strlen(string)
'run getvarz 'n
    var  = result
   name  = subwrd(result,1)
   levs  = subwrd(result,2)
   len   = strlen(name)
   root  = substr(name,1,len-lstring)
 suffix  = substr(name,len-lstring+1,len)
 if( suffix = string )
          m =  m + 1
    field.m = root
     levs.m = levs
 endif
n = n + 1
endwhile
numflds = m

'reinit'

*******************************************************
****             Make Zonal Mean Plots             ****
*******************************************************

say 'XDIM = 'xdim
n = 1
while ( n<=numflds )

   field = field.n
       j = 1
while( j<=numfields )
if( field = subwrd(fields,j) & field != p )

* Run Script to Produce PLOTS
* ---------------------------
    x = 1
    while ( x<=xdim )
       r = 1
       while ( r<=numregions )
         if( subwrd(regions,r) = subwrd(xregions,x) )
           'run 'geosutil'/plots/grads_util/rmscmpz -x 'x' -field 'field' -rc 'rcfile' -rms 'rms' -desc 'DESC' -debug FALSE'
           'c'
         endif
         r = r + 1
       endwhile
       x = x + 1
    endwhile

    j = numfields + 1
else
    j = j + 1
endif
endwhile

n = n + 1
endwhile

return
