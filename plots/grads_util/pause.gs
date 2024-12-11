function pause (args)
'numargs  'args
 numargs = result
if( numargs > 0 )
    string  = subwrd(args,1)
            num  = 2
    while ( num <= numargs )
            string = string' 'subwrd(args,num)
            num = num + 1
    endwhile
    say string
endif
say 'Paused, Hit ENTER to Continue (or c to Clear and Continue) ...'
     pull flag
    'run uppercase 'flag
                    flag = result
    if( flag = 'C' )
        'c'
    endif
    return
