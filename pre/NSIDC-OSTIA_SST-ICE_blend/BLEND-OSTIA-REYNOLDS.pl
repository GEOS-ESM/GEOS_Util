#!/usr/bin/perl -w
# 
#########################################################################
# process_OSTIA_REYNOLDS                                                #
#                                                                       #
# This program has been developed to gather the SST data                #
#
# From OSTIA(ICE) and REYNOLDS (LAKE)                                   #
#                                                                       #
# Log:                                                                  #
# Nadeau Denis SSAI 2012/07/17   Modified from get_sst.pl               #
# Mark Solomon SSAI 2013/01/10   Modifications for year crossover       #
#                                                                       #
#########################################################################

use integer;

# **********************************************
#     BEGIN section ()
# **********************************************
BEGIN {
    
    print `date`;
#$DB::single = 1;
    
# Keep track of errors within BEGIN block.
    
    $die_away = 0;
    
# Initialize output listing location
    $opt_O = 0;

# This module contains the getopts() subroutine.
    use Getopt::Long; 
   
# Module contains "mkpath"
    use File::Path;
    
# Get options and arguments
    
#    getopts('E:F:I:P:O:B:T:D:H:L:R:C:Sp');

   GetOptions ('env=s',\$env,
               'E=s',\$opt_E,
               'P=s',\$opt_P,
               'R=s',\$opt_R,
               'O=s',\$opt_O,
               'L=s',\$opt_L,
               'F=s',\$opt_F,
               'I=s',\$opt_I,
               'force=s',\$force,
               'sched_cnfg=s',\$sched_cnfg,
               'sched_id=s',\$sched_id,
               'sched_synp=s',\$sched_synp,
               'sched_c_dt=s',\$sched_c_dt,
               'sched_dir=s',\$sched_dir,
               'sched_sts_fl=s',\$sched_sts_fl,
               'sched_hs=s',\$sched_hs );

# If do_wxmaps_ecmwf.pl is initiated by the scheduler, construct table
# info. for "task_state" table of scheduler

   if ( defined( $sched_id ) )
   {
      $tab_argv = "$sched_cnfg, $sched_id, $sched_synp, $sched_c_dt";
      $fl_name = "BLEND-OSTIA-REYNOLDS.pl";
   }
    
# The pre-processing configuration file.
    
    if ( defined( $opt_E ) ) {
	$PREP_CONFIG_FILE = $opt_E;
    } else {
	$PREP_CONFIG_FILE = "DEFAULT";
	print "INPUT PREP_CONFIG_FILE = $PREP_CONFIG_FILE\n";
    }

    
# The Run_Config file to use.
    
    if ( defined( $opt_R ) ) {
	$RUN_CONFIG_FILE = $opt_R;
    } else {
	$RUN_CONFIG_FILE = "DEFAULT";
    }
# The Proc_ID - default = "ops".
    
    if ( defined( $opt_I ) ) {
	$proc_id = $opt_I;
    } else {
	$proc_id = "ops";
    }
    
# The lag date command.
    
    if ( defined( $opt_L ) ) {
	$LAG_DATE = $opt_L;
    }
    else {
	$LAG_DATE = "DEFAULT";
	
    }

# Path to directory containing other GEOS DAS programs.
# Directory $GEOSDAS_PATH/bin will be searched for these
# programs.
    
    if ( defined( $opt_P ) ) {
	$GEOSDAS_PATH = $opt_P;
    } else {
	$GEOSDAS_PATH = "DEFAULT";
    }
    
# The value for debug information
    
#
    
    
# The log file to use.
    
    if ( defined( $opt_F ) ) {
	$logfile = $opt_F;
    }
    else {
	$logfile = "DEFAULT";
    }
    
    
# Location for output listings
    $listing_file = 0;
    
    if ( defined( $opt_O ) ) {
	$listing_file = 1;
	if ( ! -d "$opt_O" ) {
            mkpath( "$opt_O" ) or die "Can't make $opt_O: $!\n";
	}
	if ( -w "$opt_O" ) {
	    $listing = "$opt_O/BLEND-OSTIA-REYNOLDS.$$.listing";
	    print "Standard output redirecting to $listing\n";
            open (STDOUT, ">$listing");
            open (STDERR, ">&" . STDOUT);
	    
	} else {
            print "$0: WARNING: $listing is not writable for listing.\n";
	}
    }
    
    if ( $ARGV[0] eq 'help' || $ARGV[0] eq 'HELP' || $#ARGV < 0 ) {
	print STDERR <<'ENDOFHELP';
	
Usage:
	
	BLEND-OSTIA-REYNOLDS [-E Prep_Config] [-P GEOSDAS_Path] [-O output_location] 
            [-D SYN_date] [-I Proc_ID] [-R Run_Config] Prep_ID
	    
	    Normal options and arguments:
	    
	    -E Prep_Config
	    The full path to the preprocessing configuration file.  This file contains
	    parameters needed by the preprocessing control programs. If not given, a
	    file named $HOME/$prep_ID/Prep_Config is used.  get_map06_sst exits with an
	    error if neither of these files exist. See below...

	    -F Log_File
	    The full path to the ERROR_LOG file ( Default is \~$user/GEOS_EVENT_LOG)

	    -I Proc_ID
	    The processing identifier. The default is "ops".
	    
	    -R Run_Config
	    The full path and name of the Run_Config file to use. If not given,
	    the default will be GEOSDAS_PATH/bin/Run_Config
	    
	    -D SYN_date
	    The date for which the model is running for. FORMAT CCYYMMDD
	    
	    -P GEOSDAS_Path
	    Path to directory containing other GEOS DAS programs.  The path is
	    $GEOSDAS_PATH, where $GEOSDAS_PATH/bin is the directory containing these
	    programs.  If -P GEOSDAS_Path is given, then other required programs not
	    found in the directory where this program resides will be obtained from
	    subdirectories in GEOSDAS_Path - the subdirectory structure is assumed
	    to be the same as the operational subdirectory structure.  The default is
	    to use the path to the subdirectory containing this program, which is what
	    should be used in the operational environment.
	    
	    -O output_location
	    If this option is specified, output listings (both STDERR and STDOUT) will be
	    placed in the directory "output_location."

	    -p    Use persisted anomaly instead of anomaly persistence.  This is done for sea-ice only.
	    
	    Prep_ID
	    Identification tag for this run.
	    
	    
	    Prep_Config setttings
	    ---------------------
	    
	    The program will consult a Prep_Config file for configurable parameters.
	    Many of these parameters can use the GrADS-style date and time templates,
	    i.e., %y4, %y2, %m2, %d2.  The Prep_Config file is assumed to reside in
	    ~/Prep_ID/Prep_Config, but any other path can be specified by the -E option.	    
	    
	    
ENDOFHELP

	    $die_away = 1;
	exit 0;
    }
# This module gives the routine access to the environment
    
    use Env;
    
# This module locates the full path name to the location of this file.  Variable
# $FindBin::Bin will contain that value.
    
    use FindBin;
    
# This module contains the dirname() subroutine.
    
    use File::Basename;
    
# If default GEOS DAS path, set path to parent directory of directory where this
# script resides.
    
    if ( $GEOSDAS_PATH eq "DEFAULT" ) {
	$GEOSDAS_PATH = dirname( $FindBin::Bin );
    }
    
# Set name of the bin directory to search for other programs needed by this one.
    
    $BIN_DIR = "$GEOSDAS_PATH/bin";
    $CORE_BIN_DIR = "$GEOSDAS_PATH/geosdas/Core/bin";

    
# Get the name of the directory where this script resides.  If it is different
# than BIN_DIR, then this directory will also be included in the list of
# directories to search for modules and programs.
    
    $PROGRAM_PATH = $FindBin::Bin;
    
# Now allow use of any modules in the bin directory, and (if not the same) the
# directory where this program resides.  (The search order is set so that
# the program's directory is searched first, then the bin directory.)
    
    if ( $PROGRAM_PATH ne $BIN_DIR ) {
	@SEARCH_PATH = ( $PROGRAM_PATH, $BIN_DIR, $CORE_BIN_DIR );
    } else {
	@SEARCH_PATH = ( $BIN_DIR, $CORE_BIN_DIR );
    }
    print "bin dir is ${BIN_DIR}\n";
    print "source g5_modules.\n";
    local @ARGV = ("$BIN_DIR");
    do "${BIN_DIR}/g5_modules_perl_wrapper";
} # END 


# =================================================================
#
#
# =================================================================

# Any reason to exit found during the BEGIN block?

if ( $die_away == 1 ) {
    exit 1;
}

# Include the directories to be searched for required modules.

use lib ( @SEARCH_PATH );

# Set the path to be searched for required programs.

$ENV{'PATH'} = join( ':', @SEARCH_PATH, $ENV{'PATH'} );

# This module contains the extract_config() subroutine.

use Extract_config;

# Archive utilities: gen_archive

use Arch_utils;

# This module contains the z_time(), dec_time() and date8() subroutines.

use Manipulate_time;

# This module contains the mkpath() subroutine.

use File::Path;

use Conv_utils;

use Net::FTP;
use Remote_utils;

# Error logging utilities.
use Err_Log;

# Record FAILED to schedule status file.
use Recd_State;

# ID for the preprocessing run.
$prep_ID = $ARGV[0];

# The synoptic date to run.
    
# If date given, use that, 
# otherwise use today's date (GMT).
if ( $#ARGV > 0 ) {
    $SYN_DATE = date8( $ARGV[1] );

} 
else {
    $SYN_DATE = ( z_time() )[0];
}
print "SYN_DATE=$SYN_DATE\n";
$process_date = $SYN_DATE;
($end_date, $dummy) = inc_time($process_date, 0, 1 ,0);
$current_time = ( z_time() )[1];
print "current_time=$current_time\n";
print "argv0 = $ARGV[0] , argv1 = $ARGV[1] \n";

# Use Prep_Config file under the preprocessing run's directory in the user's home directory
# as the default.

if ( "$PREP_CONFIG_FILE" eq "DEFAULT" ) {
    $PREP_CONFIG_FILE = "$ENV{'HOME'}/$prep_ID/Prep_Config";
}

# Does the Prep_Config file exist?  If not, fatal_error.
  if ( ! -e "$PREP_CONFIG_FILE" ) {
    fatal_error("error $PREP_CONFIG_FILE not found.");
  }

if ( "$RUN_CONFIG_FILE" eq "DEFAULT" ) {
    $RUN_CONFIG_FILE = "$BIN_DIR/Run_Config";
}
# Write start message to Event Log

err_log (0, "BLEND-OSTIA-REYNOLDS", "$prep_ID","$proc_id","-1",
	 {'log_name' => "$logfile",
	  'err_desc' => "$prep_ID process_OSTIA job has started - Standard output redirecting to $listing"});

#********#
# Set up #
#********#

# First find the correct date based on the run time (corrects FLK 18Z run)

print "SYN_DATE=$SYN_DATE\n";
print "lag_date=${LAG_DATE}\n";
if ( ${LAG_DATE} ne "DEFAULT" ) {
    $NEW_LAG = ${LAG_DATE} ;
    ( ${SYN_DATE}, $current_time ) = dec_time (${SYN_DATE}, $current_time, ${NEW_LAG}, 0);
}
($previousDate, $current_time) = dec_time ($SYN_DATE, $SYN_DATE, 1, 0);
print "previousDate=$previousDate\n";

# Defining an array which I will fill with found file names and fix some variables.

$SYN_DATE = substr(date8(${SYN_DATE}),0,8);
$YEAR = substr(date8(${SYN_DATE}),0,4);
my $nextyear = $YEAR + 1;
my $lastyear = $YEAR - 1;

# Define job_id
$job_id = ${SYN_DATE};

# Extract working directory, staging, and working locations and the archive flag.

( $OSTIA_REYNOLDS_ARCHIVE_FLAG = extract_config( "OSTIA_REYNOLDS_ARCHIVE_FLAG", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - can not set OSTIA_REYNOLDS_ARCHIVE_FLAG configuration value");

( $OSTIA_DIR = extract_config( "OSTIA_DIR", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_DIR configuration value missing in Prep_Config file.");

( $OSTIA_REYNOLDS_OUTPUT_STAGE_DIR = extract_config( "OSTIA_REYNOLDS_OUTPUT_STAGE_DIR", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_REYNOLDS_OUTPUT_STAGE_DIR configuration value missing in Prep_Config file.");

( $OSTIA_REYNOLDS_WORK_DIR = extract_config( "OSTIA_REYNOLDS_WORK_DIR", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_REYNOLDS_WORK_DIR configuration value missing in Prep_Config file.");

( $OSTIA_REYNOLDS_NLAT = extract_config( "OSTIA_REYNOLDS_NLAT", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_REYNOLDS_NLAT configuration value missing in Prep_Config file.");

( $OSTIA_REYNOLDS_NLON = extract_config( "OSTIA_REYNOLDS_NLON", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_REYNOLDS_NLON configuration value missing in Prep_Config file.");

( $OSTIA_REYNOLDS_PERSIST_NBDAY = extract_config( "OSTIA_REYNOLDS_PERSIST_NBDAY", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_REYNOLDS_PERSIST_NBDAY configuration value missing in Prep_Config file.");

( $OSTIA_REYNOLDS_DAYS_FORWARD = extract_config( "OSTIA_REYNOLDS_DAYS_FORWARD", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_REYNOLDS_DAYS_FORWARD configuration value missing in Prep_Config file.");

( $OSTIA_REYNOLDS_DAYS_BACKWARD = extract_config( "OSTIA_REYNOLDS_DAYS_BACKWARD", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_REYNOLDS_DAYS_BACKWARD configuration value missing in Prep_Config file.");

( $OSTIA_REYNOLDS_FILENAME = extract_config( "OSTIA_REYNOLDS_FILENAME", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_REYNOLDS_FILENAME configuration value missing in Prep_Config file.");

( $OSTIA_FILE = extract_config( "OSTIA_FILE", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - OSTIA_FILE configuration value missing in Prep_Config file.");
( $SST_THR = extract_config( "SST_THR", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
    or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - SST_THR configuration value missing in Prep_Config file.");

# If the user wants to archive get location.

if ($OSTIA_REYNOLDS_ARCHIVE_FLAG != "0") {    
    ( $OSTIA_REYNOLDS_ARCHIVE_LOC = extract_config( "OSTIA_REYNOLDS_ARCHIVE_LOC", $PREP_CONFIG_FILE, "NONE" ) ) ne "NONE"
	or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - can not set OSTIA_REYNOLDS_ARCHIVE_LOC configuration value");
}

# Make the paths in the stage directory
$locdir = ${OSTIA_REYNOLDS_WORK_DIR};

# Make the paths in the stage directory

if ( ! -d "$locdir" ) {
    mkpath( "$locdir" ) or fatal_error( "Can't make $locdir: $!");
}

chdir "$locdir";
print "changing dir: $locdir\n";
$persist=0;
# Changed from getting the value from the input variables to using
# the value from the Config file
$persist = $OSTIA_REYNOLDS_PERSIST_NBDAY;

# ---------------------------------------------
#  Look for date that matches SST and  OSTIA.
# ---------------------------------------------
@files = () ;
($find_date, $dummy) = inc_time($SYN_DATE, 0, 0, 0);
$start_date=$find_date;
$ostiaFile = token_resolve($OSTIA_FILE,  $find_date);
$ostiaDir = token_resolve($OSTIA_DIR,  $find_date);
	print "find $ostiaDir -name ${ostiaFile}*\n";
	@files = `find $ostiaDir -name "${ostiaFile}*"`;
        if( $#files == -1 ) {
           fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - Cannot find todays OSTIA data".
           " $start_date $end_date $process_date $OSTIA_REYNOLDS_WORK_DIR ... $persist ");
        }

# =================================================================
# Cat weekly data into a yearly file.
# ostia_bcs.csh ostia_data_path beg_date end_date nlat nlon outdir 
# =================================================================
 
my $prefix = $OSTIA_REYNOLDS_FILENAME;

$filenameSST  = "${prefix}SST.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${YEAR}_current.data";
$filenameICE  = "${prefix}ICE.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${YEAR}_current.data";
my @typeList = ('SST', 'ICE');
my %files = ('SST' => "$filenameSST",
             'ICE' => "$filenameICE"); 
foreach $type (@typeList) {
   my $file = $files{$type};
   $cmd="/usr/bin/sh $PROGRAM_PATH/sst_scan_last $file \n";
   print "$cmd\n";
   $result = system($cmd);
   if( $result ) {
       fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - can not run /usr/bin/sh $PROGRAM_PATH/sst_scan_last".
    " $start_date $end_date $process_date $OSTIA_REYNOLDS_WORK_DIR ... $persist ");
   }
   open (DATEFILE, '<', "$locdir/fort.40") or fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - can not open $locdir/fort.40\n");
   my $dateInFile = <DATEFILE>;
   close(DATEFILE);
   print "dateInFile = $dateInFile";
   unlink "$locdir/fort.10";
   unlink "$locdir/fort.40";
   if($dateInFile > $previousDate) {
      $file  = "${prefix}${type}.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${YEAR}.data.${previousDate}";
      $newfile  = "${prefix}${type}.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${nextyear}.data.${previousDate}";
      $oldfile  = "${prefix}${type}.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${lastyear}.data.${previousDate}";
      if($type eq 'SST') {
          $filenameSST = $file;
      } elsif ($type eq 'ICE') {
          $filenameICE = $file;
      }
      print "Using previousDate $file";
      $cmd="/usr/bin/sh $PROGRAM_PATH/sst_scan_last $file \n";
      $result = system($cmd);
      if( $result ) {
          fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - can not run /usr/bin/sh $PROGRAM_PATH/sst_scan_last".
       " $start_date $end_date $process_date $OSTIA_REYNOLDS_WORK_DIR ... $persist ");
      }
      open (DATEFILE2,"$locdir/fort.40");
      my $dateInFile = <DATEFILE2>;
      close(DATEFILE2);
      unlink "$locdir/fort.10";
      unlink "$locdir/fort.40";
      if($dateInFile > $previousDate) {
         fatal_error ("BLEND-OSTIA-REYNOLDS ERROR Looks like $type 
           already ran -  dateInFile = $dateInFile file = $file
           previousDate = $previousDate ");
      } elsif ($dateInFile < $previousDate) {
         fatal_error ("BLEND-OSTIA-REYNOLDS ERROR Looks like missing 
          $type day(s)-  dateInFile = $dateInFile
          file = $file previousDate = $previousDate ");
      }
      system("cp -f ${locdir}/${file} ${locdir}/${prefix}${type}.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${YEAR}_current.data");
      if(-s "$locdir/$newfile") {
         system("cp -f ${locdir}/${newfile} ${locdir}/${prefix}${type}.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${nextyear}_current.data");
      }
      if(-s "$locdir/$oldfile") {
         system("cp -f ${locdir}/${oldfile} ${locdir}/${prefix}${type}.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${lastyear}_current.data");
      }
   } elsif ($dateInFile < $previousDate) {
      if($force) {
         print "Running $type with missing days";
      } else {
         fatal_error ("BLEND-OSTIA-REYNOLDS ERROR Looks like missing $type day(s)-  dateInFile = $dateInFile ");
      }
   }
}

# =================================================================
# We do one day at a time, so date range is set to $start_date
# start_date correspond to the OSTIA/REYNOLDS file.
# process_date is the date written in the header of the bin file.
# =================================================================
$cmd="/usr/bin/sh $PROGRAM_PATH/make_ostia_sst_blend.sh ".
    "$start_date ".
    "$start_date ".
    "$process_date ".
    "$OSTIA_REYNOLDS_WORK_DIR ".
    "$ostiaDir ".
    "$OSTIA_REYNOLDS_NLON ".
    "$OSTIA_REYNOLDS_NLAT ".
    "$persist ".
    "$OSTIA_REYNOLDS_DAYS_FORWARD ".
    "$OSTIA_REYNOLDS_DAYS_BACKWARD ".
    "$prefix ".
    "$ostiaFile ".
    "$SST_THR \n";

print "$cmd \n";
print "persist = $persist forward = $OSTIA_REYNOLDS_DAYS_FORWARD and \n";
print "backward = $OSTIA_REYNOLDS_DAYS_BACKWARD and prefix = $prefix \n";
$result = system($cmd);
if( $result ) {
    fatal_error ("BLEND-OSTIA-REYNOLDS ERROR - can not run /usr/bin/sh $PROGRAM_PATH/make_ostia_sst_blend.sh".
		 " $start_date $end_date $process_date $OSTIA_REYNOLDS_WORK_DIR ... $persist ");

}

$filenameSSTp = "${prefix}SST.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${YEAR}.data";
$filenameICEp = "${prefix}ICE.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${YEAR}.data";
$filenameSSTnp = "${prefix}SST.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${nextyear}.data";
$filenameICEnp = "${prefix}ICE.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${nextyear}.data";
$filenameSSTpp = "${prefix}SST.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${lastyear}.data";
$filenameICEpp = "${prefix}ICE.${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}.${lastyear}.data";
# ----------------------------------
# Make sure Stage directories exist.
# ----------------------------------
if ( ! -d "$OSTIA_REYNOLDS_OUTPUT_STAGE_DIR" ) {
    mkpath( "$OSTIA_REYNOLDS_OUTPUT_STAGE_DIR" ) or fatal_error( "Can't make $OSTIA_REYNOLDS_OUTPUT_STAGE_DIR: $!");
}
$FVINPUTDIR = "${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/${OSTIA_REYNOLDS_NLON}x${OSTIA_REYNOLDS_NLAT}";

if (! -d "$FVINPUTDIR" ) {
    mkpath( "$FVINPUTDIR" ) or fatal_error( "Can't make $locdir: $!");
}
#$DB::single = 1;

# ----------------------------------
# Copy all persistent files
# ----------------------------------
if ( $persist ) {
    system("cp -f ${locdir}/${filenameSSTp}    ${FVINPUTDIR}/${filenameSSTp}");
    system("cp -f ${locdir}/${filenameICEp}    ${FVINPUTDIR}/${filenameICEp}");

    $cmd="cube_BCs.pl -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/720x4320/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea1 ${YEAR} all c720";
    print "$cmd\n";
    my $rc=system("$cmd");
    if ($rc != 0) {
       fatal_error ("cube_BCs.pl invocation 01 failed. Contact OC/check listing."); 
    }

    $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/360x2160/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea2 ${YEAR} all c360";
    print "$cmd\n";
    my $rc=system("$cmd");
    if ($rc != 0) {
       fatal_error ("cube_BCs.pl invocation 02 failed. Contact OC/check listing."); 
    }

    $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/180x1080/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea3 ${YEAR} all c180";
    print "$cmd\n";
    my $rc=system("$cmd");
    if ($rc != 0) {
       fatal_error ("cube_BCs.pl invocation 03 failed. Contact OC/check listing."); 
    }

    $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/90x540/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea4 ${YEAR} all c90";
    print "$cmd\n";
    my $rc=system("$cmd");
    if ($rc != 0) {
       fatal_error ("cube_BCs.pl invocation 04 failed. Contact OC/check listing."); 
    }

    # np is next year's files

    if(-s "$locdir/$filenameSSTnp") {
       system("cp -f ${locdir}/${filenameSSTnp} ${FVINPUTDIR}/${filenameSSTnp}");
       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/720x4320/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea5 ${nextyear} sst c720";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 05 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/360x2160/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea6 ${nextyear} sst c360";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 06 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/180x1080/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea7 ${nextyear} sst c180";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 07 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/90x540/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea8 ${nextyear} sst c90";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 08 failed. Contact OC/check listing."); 
       }
    }
    if(-s "$locdir/$filenameICEnp") {
       system("cp -f ${locdir}/${filenameICEnp} ${FVINPUTDIR}/${filenameICEnp}");
       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/720x4320/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea9 ${nextyear} ice c720";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 09 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/360x2160/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea10 ${nextyear} ice c360";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 10 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/180x1080/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea11 ${nextyear} ice c180";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 11 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/90x540/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea12 ${nextyear} ice c90";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 12 failed. Contact OC/check listing."); 
       }

    }
    # pp is last year's files
    if(-s "$locdir/$filenameSSTpp") {
       system("cp -f ${locdir}/${filenameSSTpp} ${FVINPUTDIR}/${filenameSSTpp}");
       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/720x4320/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea13 ${lastyear} sst c720";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 13 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/360x2160/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea14 ${lastyear} sst c360";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 14 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/180x1080/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea15 ${lastyear} sst c180";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 15 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/90x540/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea16 ${lastyear} sst c90";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 16 failed. Contact OC/check listing."); 
       }

    }

    if(-s "$locdir/$filenameICEpp") {
       system("cp -f ${locdir}/${filenameICEpp} ${FVINPUTDIR}/${filenameICEpp}");

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/720x4320/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea17 ${lastyear} ice c720";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 17 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/360x2160/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea18 ${lastyear} ice c360";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 18 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/180x1080/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea19 ${lastyear} ice c180";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 19 failed. Contact OC/check listing."); 
       }

       $cmd="cube_BCs.pl -partition gmaodev -w -d ${OSTIA_REYNOLDS_OUTPUT_STAGE_DIR}/90x540/ -gid g2538 -wa /discover/nobackup/dao_ops/SSTworkareaTEST/workarea20 ${lastyear} ice c90";
       print "$cmd\n";
       my $rc=system("$cmd");
       if ($rc != 0) {
          fatal_error ("cube_BCs.pl invocation 20 failed. Contact OC/check listing."); 
       }
    }
}

##################
## Archive Time ##
##################
   if ($OSTIA_REYNOLDS_ARCHIVE_FLAG != "0") {

       if ( $persist ) {
	   $rc=gen_archive ( $proc_id, $prep_ID,'ostia-reynolds', 'weekly', "$YEAR", "$OSTIA_REYNOLDS_ARCHIVE_LOC",
			     "${locdir}/${filenameSSTp}",  
			     { 'run_config' => "$RUN_CONFIG_FILE", 'verbose' => "1", 'y4only' => "1" } );
	   if ($rc!=1) {
	       err_log (4, "BLEND-OSTIA-REYNOLDS", "$job_id","$prep_ID","-1",
		{'log_name' => "$logfile",
			 'err_desc' => "could not archive ${filenameSSTp}"});
	   }

	   $rc=gen_archive ( $proc_id, $prep_ID,'ostia-reynolds', 'weekly', "$YEAR", "$OSTIA_REYNOLDS_ARCHIVE_LOC",
			     "${locdir}/${filenameICEp}",  
			     { 'run_config' => "$RUN_CONFIG_FILE", 'verbose' => "1", 'y4only' => "1" } );
	   if ($rc!=1) {
	       err_log (4, "BLEND-OSTIA-REYNOLDS", "$job_id","$prep_ID","-1",
			{'log_name' => "$logfile",
			 'err_desc' => "could not archive ${filenameICEp}"});
	   }
       } 
       # Archive files for next year
       if ( $persist && -e $filenameSSTnp ) {
	   $rc=gen_archive ( $proc_id, $prep_ID,'ostia-reynolds', 'weekly', "$nextyear", "$OSTIA_REYNOLDS_ARCHIVE_LOC",
			     "${locdir}/${filenameSSTnp}",  
			     { 'run_config' => "$RUN_CONFIG_FILE", 'verbose' => "1", 'y4only' => "1" } );
	   if ($rc!=1) {
	       err_log (4, "BLEND-OSTIA-REYNOLDS", "$job_id","$prep_ID","-1",
		{'log_name' => "$logfile",
			 'err_desc' => "could not archive ${filenameSSTnp}"});
	   }

           if(-e $filenameICEnp) {
	      $rc=gen_archive ( $proc_id, $prep_ID,'ostia-reynolds', 'weekly',
                 "$nextyear", "$OSTIA_REYNOLDS_ARCHIVE_LOC", 
                 "${locdir}/${filenameICEnp}",  
                 { 'run_config' => "$RUN_CONFIG_FILE", 'verbose' => "1", 
                 'y4only' => "1" } );
           }
	   if ($rc!=1) {
	       err_log (4, "BLEND-OSTIA-REYNOLDS", "$job_id","$prep_ID","-1",
			{'log_name' => "$logfile",
			 'err_desc' => "could not archive ${filenameICEnp}"});
	   }
       } 
       # Archive files for previous year
       if ( $persist && -e $filenameSSTpp ) {
	   $rc=gen_archive ( $proc_id, $prep_ID,'ostia-reynolds', 'weekly', "$lastyear", "$OSTIA_REYNOLDS_ARCHIVE_LOC",
			     "${locdir}/${filenameSSTpp}",  
			     { 'run_config' => "$RUN_CONFIG_FILE", 'verbose' => "1", 'y4only' => "1" } );
	   if ($rc!=1) {
	       err_log (4, "BLEND-OSTIA-REYNOLDS", "$job_id","$prep_ID","-1",
		{'log_name' => "$logfile",
			 'err_desc' => "could not archive ${filenameSSTpp}"});
	   }

           if(-e $filenameICEpp) {
	      $rc=gen_archive ( $proc_id, $prep_ID,'ostia-reynolds', 'weekly',
                 "$lastyear", "$OSTIA_REYNOLDS_ARCHIVE_LOC", 
                 "${locdir}/${filenameICEpp}",  
                 { 'run_config' => "$RUN_CONFIG_FILE", 'verbose' => "1", 
                 'y4only' => "1" } );
           }
	   if ($rc!=1) {
	       err_log (4, "BLEND-OSTIA-REYNOLDS", "$job_id","$prep_ID","-1",
			{'log_name' => "$logfile",
			 'err_desc' => "could not archive ${filenameICEpp}"});
	   }
       } 
}

## Archive the listings file if one existed.
 
   if ( $listing_file ) {
       $out_listing = "$opt_O/BLEND-OSTIA-REYNOLDS.${job_id}.listing";
       system ("mv $listing $out_listing");
}

 
print `date`;
 
err_log (0, "BLEND-OSTIA-REYNOLDS", "$job_id","$prep_ID","-1",
	 {'log_name' => "$logfile",
	  'err_desc' => "BLEND-OSTIA-REYNOLDS: successfully finished "});

# Report success to D_BOSS Scheduler if run by scheduler
if ( defined( $sched_id ) ){ recd_state( $fl_name, "COMPLETE", $tab_argv, $sched_dir, $sched_sts_fl );}

#----------------------------------------------------------------------------
sub fatal_error{
    my ($message) = @_;

# Report failure to D_BOSS Scheduler if run by scheduler
    if ( defined( $sched_id ) ) { 
	recd_state($fl_name, FAILED, $tab_argv, $sched_dir, $sched_sts_fl);
        err_log (4, "$sched_id", "$process_date", "$prep_ID", "-1",
	     {'err_desc' => "FATAL ERROR: $message"});
    }
    else {
       err_log (4, "BLEND-OSTIA-REYNOLDS", "$process_date", "$prep_ID", "-1",
	     {'err_desc' => "FATAL ERROR: $message"});
    }
    die "FATAL ERROR: $message \n";
} 

