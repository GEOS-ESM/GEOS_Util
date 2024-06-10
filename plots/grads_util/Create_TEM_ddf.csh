#!/bin/csh -fx

setenv ARCH `uname`

# NOTE The script below requires GEOSBIN. Usually this should be set in scripts calling
# this but if not, you should set it to the install/bin directory of your model

source $GEOSBIN/g5_modules
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${BASEDIR}/${ARCH}/lib

set EXPID          = $1
set TEM_Collection = $2

# Count Number of "Dots" in EXPID
# -------------------------------
set expdots = ''
      @ n = 0
      @ b = 1
      set bit = `echo ${EXPID} | cut -b $b`
      while( "${bit}" != '' )
         if( "${bit}" == '.' ) then
                  @ n = $n + 1
         endif
                  @ b = $b + 1
         set bit = `echo ${EXPID} | cut -b $b`
      end
      set expdots = `echo $expdots $n`
      @ date_node = $expdots + 4
echo Date_Node: $date_node

/bin/rm -f                                                                     grads.commands
touch                                                                          grads.commands
echo \'open residual.$EXPID.ctl\'                                           >> grads.commands
echo \'run writegrads.gs -name $EXPID.${TEM_Collection}.monthly -time one\' >> grads.commands
echo \'quit\'                                                               >> grads.commands
grads -b -l -c "run grads.commands"

set files = `/bin/ls -1 $EXPID.${TEM_Collection}.monthly.*.data`
foreach file ($files)
set date = `echo $file | cut -d. -f${date_node}`
$GEOSBIN/flat2hdf.x -flat $file -ctl $EXPID.${TEM_Collection}.monthly.$date.ctl -nymd $date -nhms 0 -ndt 21600
end

stripname data.nc4 nc4
/bin/rm $EXPID.*.data
/bin/rm $EXPID.*.ctl

# Create DDF File
# ---------------
set monthlies = `/bin/ls -1 $EXPID.${TEM_Collection}.monthly.*.nc4`
set       num = `/bin/ls -1 $monthlies | wc -l`
echo num = $num

    set edate  = `echo $monthlies[$num] | cut -d "." -f${date_node}`
    set eyear  = `echo $edate           | cut -c1-4`
    set emonth = `echo $edate           | cut -c5-6`

    set date  = `echo $monthlies[1] | cut -d "." -f${date_node}`
    set year  = `echo $date         | cut -c1-4`
    set month = `echo $date         | cut -c5-6`

echo edate  = $edate
echo eyear  = $eyear
echo emonth = $emonth

#   set expdsc = `grep EXPDSC: $HISTORYRC | cut -d" " -f2`
    set timinc = "mo"

    if( $month == "01" ) set MON = JAN
    if( $month == "02" ) set MON = FEB
    if( $month == "03" ) set MON = MAR
    if( $month == "04" ) set MON = APR
    if( $month == "05" ) set MON = MAY
    if( $month == "06" ) set MON = JUN
    if( $month == "07" ) set MON = JUL
    if( $month == "08" ) set MON = AUG
    if( $month == "09" ) set MON = SEP
    if( $month == "10" ) set MON = OCT
    if( $month == "11" ) set MON = NOV
    if( $month == "12" ) set MON = DEC

@   nmonths = ( $eyear - $year ) * 12 + ( $emonth - $month ) + 1

   /bin/rm -f  $EXPID.${TEM_Collection}.monthly.ddf
    echo DSET ^$EXPID.${TEM_Collection}.monthly.%y4%m201.nc4        > $EXPID.${TEM_Collection}.monthly.ddf
    echo TITLE Dummy Experiment Description                        >> $EXPID.${TEM_Collection}.monthly.ddf
    echo OPTIONS template                                          >> $EXPID.${TEM_Collection}.monthly.ddf
    echo TDEF time $nmonths  LINEAR  00:00Z01$MON$year 1$timinc    >> $EXPID.${TEM_Collection}.monthly.ddf





