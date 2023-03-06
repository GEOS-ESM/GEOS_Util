#!/bin/csh -f

unsetenv LD_LIBRARY_PATH

setenv  ARCH `uname`
setenv  GEOSBIN @BINARY_INSTALL_DIR@
source $GEOSBIN/g5_modules
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${BASEDIR}/${ARCH}/lib

setenv RUN_CMD "$GEOSBIN/esma_mpirun -np "

if ($?SLURM_NTASKS) then
        set NCPUS = $SLURM_NTASKS
        set   RUN = "$RUN_CMD $NCPUS $GEOSBIN/3CH_mpi.x "
else
        set NCPUS = 1
        set   RUN = "$GEOSBIN/3CH.x "
endif

# ----------------------------------------------------
# Define Experiment IDs, Locations, and Relevant Files
# ----------------------------------------------------

set nymdb = `cat 3CH.rc | grep -v \# | grep nymdb: | cut -d: -f2`
set nhmsb = `cat 3CH.rc | grep -v \# | grep nhmsb: | cut -d: -f2`
set nymde = `cat 3CH.rc | grep -v \# | grep nymde: | cut -d: -f2`
set nhmse = `cat 3CH.rc | grep -v \# | grep nhmse: | cut -d: -f2`
set ndt   = `cat 3CH.rc | grep -v \# | grep   ndt: | cut -d: -f2`

if( $ndt == '' ) set ndt = 21600

@ numexps = `cat 3CH.rc | grep -v \# | grep expid_ | wc -l`
set command_line = " "

@ n = 1
while( $n <= $numexps )
   set expid = `cat 3CH.rc | grep -v \# | grep expid_$n | cut -d: -f2`
   set files = `cat 3CH.rc | grep -v \# | grep files_$n | cut -d: -f2`

   echo "Corner $n  EXPID: $expid"

   # Check for Time template
   # -----------------------
   set  hourly = `echo $files | grep %h2`
   set   daily = `echo $files | grep %d2`

   if( $hourly == $files ) then
       set nsecs = $ndt
   else if( $daily == $files ) then
       set nsecs = 86400
   else
       set nsecs = -999
   endif

   set command_line = "$command_line -exp"$n" $expid $files "
@  n = $n + 1
end

set im     = `cat 3CH.rc | grep -v \# | grep  im:     | cut -d: -f2` ; if( "$im"     != '' ) set im     = "-im     $im"
set jm     = `cat 3CH.rc | grep -v \# | grep  jm:     | cut -d: -f2` ; if( "$jm"     != '' ) set jm     = "-jm     $jm"
set levs   = `cat 3CH.rc | grep -v \# | grep  levs:   | cut -d: -f2` ; if( "$levs"   != '' ) set levs   = "-levs   $levs"
set fields = `cat 3CH.rc | grep -v \# | grep  fields: | cut -d: -f2` ; if( "$fields" != '' ) set fields = "-fields $fields"

set method = `cat 3CH.rc | grep -v \# | grep  interpolation_method: | cut -d: -f2`

if($method != '' ) then
   if( $method == 'BL' ) then
        set method = "-method 1"
   else if( $method == 'BC' ) then
        set method = "-method 2"
   else if( $method == 'BA' ) then
        set method = "-method 3"
   endif
endif

# ----------------------------------------------------
# Perform 3CH Calculation
# ----------------------------------------------------


 $RUN $command_line $im $jm $levs $fields $method \
      -nymdb $nymdb -nhmsb $nhmsb -nymde $nymde -nhmse $nhmse -ndt $ndt  

# ----------------------------------------------------
# Convert grads to nc4 file
# ----------------------------------------------------

set ctl_files = `/bin/ls -1t *ctl`
set ctl_file  = $ctl_files[1]
set length    = `echo $ctl_file | awk '{print length($0)}'`
@ loc = $length - 4
set  newfile = `echo $ctl_file | cut -b1-$loc`
echo Newfile = $newfile

$GEOSBIN/flat2hdf.x -flat $newfile.data -ctl $newfile.ctl -nymd $nymdb -nhms $nhmsb -ndt $ndt

