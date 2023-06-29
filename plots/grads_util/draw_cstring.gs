function draw_cstring (args)

'numargs  'args
 numargs = result

if( numargs = 0 )
    say '  Syntax:  draw_cstring XPOS YPOS JUSTIFICATION THICKNESS D(elimiter) C(olor)D(elimiter)STRING C(olor)D(elimiter)STRING etc. ... '
    say ' Example:  draw_cstring 4.0 6.0 L 2 : 1:String1 3:String2 1:String3 4:String4'
    say '    Note:  Color must be single integer (0-9)'
    return
endif

* -----------------------------------------------------------------------------------------------------------------------

xpos = subwrd(args,1)
ypos = subwrd(args,2)
just = subwrd(args,3)
thck = subwrd(args,4)
deli = subwrd(args,5)

'run uppercase 'just
                just = result

verbose = 1

length = strlen(args)
  xlen = strlen(xpos)
  ylen = strlen(ypos)
  jlen = strlen(just)
  tlen = strlen(thck)
  dlen = strlen(deli)

if( verbose = 1 )
 say 'Total len: 'length
 say '     xlen: 'xlen
 say '     ylen: 'ylen
 say '     jlen: 'jlen
 say '     tlen: 'tlen
 say '     dlen: 'dlen
endif

xbeg = xlen + 1 + ylen + 1 + jlen + 1 + tlen + 1 + dlen + 2
xend = length-xbeg+1
tstring = substr(args,xbeg,xend)
tlength = strlen(tstring)

if( verbose = 1 )
 say '        xbeg: 'xbeg
 say '        xend: 'xend
 say 'Total String:'tstring
 say '      Length:'tlength
endif


* Find First Color
* ----------------
        n = 1
        k = 1
        bit = substr(tstring,k,1)
  color.n = bit
        k = k + 1
        bit = substr(tstring,k,1)
 while( bit != deli & k < tlength )
  color.n = color.n''bit
        k = k + 1
        bit = substr(tstring,k,1)
 endwhile

* Find next delimiter
* -------------------
        k = k + 1
   bitbeg = k
        bit = substr(tstring,k,1)
 while( bit != deli & k < tlength )
        k = k + 1
      bit = substr(tstring,k,1)
 endwhile
   if( k = tlength )
       bitend = k
   else
       bitend = k-2
   endif
 string.n = substr(tstring,bitbeg,bitend-bitbeg+1)
if( verbose = 1 )
 say 'n: 'n'  Color.'n': 'color.n'  String.'n': 'string.n
endif

* Find next color and string
* --------------------------
 while( k < tlength )
        n = n + 1
        k = bitend + 1
      bit = substr(tstring,k,1)
  color.n = bit
    if( color.n = 7 ) ; color.n = 50 ; endif
        k = k + 2
   bitbeg = k
        bit = substr(tstring,k,1)
 while( bit != deli & k < tlength )
        k = k + 1
      bit = substr(tstring,k,1)
* say 'k: 'k'  bit: 'bit
 endwhile
   if( k = tlength )
       bitend = k
   else
       bitend = k-2
   endif
* say 'bitbeg: 'bitbeg'  bitend: 'bitend'   tlength: 'tlength'   string.'n' = substr(tstring,'bitbeg','bitend-bitbeg+1')'
 string.n = substr(tstring,bitbeg,bitend-bitbeg+1)

if( verbose = 1 )
 say 'n: 'n'  Color.'n': 'color.n'  String.'n': 'string.n
endif
 endwhile

if( verbose = 1 )
 say ' '
 say ' '
endif

* Define number of string segments
* --------------------------------
     num = n

* -----------------------------------------------------------------------------------------------------------------------

if( just = L )
    n = num
    strings.n = ''
    m = 1
    while( m<=n )
    strings.n = strings.n''string.m
    m = m + 1
    endwhile
    k = n
 'set  string 'color.k' 'just' 'thck
 'draw string 'xpos' 'ypos' 'strings.n

         n  = num-1
  while( n >= 1)
    strings.n = ''
    m = 1
    while( m<=n )
    strings.n = strings.n''string.m
    m = m + 1
    endwhile
    k = n
 'set  string 0 'just' 'thck
 'draw string 'xpos' 'ypos' 'strings.n
 'set  string 'color.k' 'just' 'thck
 'draw string 'xpos' 'ypos' 'strings.n
  n = n - 1
  endwhile
endif

* -----------------------------------------------------------------------------------------------------------------------

if( just = R )
    string = ''
    m = 1
    while( m<=num )
    string = string''string.m
    m = m + 1
    endwhile
    k = 1
 'set  string 'color.k' 'just' 'thck
 'draw string 'xpos' 'ypos' 'string

         n =2
  while( n<=num )
    string = ''
           m = n
    while( m<=num )
    string = string''string.m
    m = m + 1
    endwhile
    k = n
 'set  string 0 'just' 'thck
 'draw string 'xpos' 'ypos' 'string
 'set  string 'color.k' 'just' 'thck
 'draw string 'xpos' 'ypos' 'string
  n = n + 1
  endwhile
endif

* -----------------------------------------------------------------------------------------------------------------------

return
