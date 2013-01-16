#!/usr/bin/env bash
# ``bootstrap.sh`` - install and configure Linux from scratch or backup onto a 
# local hard disk, such as ``/dev/sda``, ``/dev/sdb`` and ``/dev/vda``. The 
# default is set as ``/dev/sda``, and you can change it on your ``$TOP_DIR/localrc`` 
# file if you need.

# Keep track of the top directory.
TOP_DIR=$(cd $(dirname "$0") && pwd)

# Load local configuration.
source $TOP_DIR/localrc

# Load bootstrap configuration.
source $TOP_DIR/snapshotrc

# Import common functions.
source $TOP_DIR/functions

# Prepare log file.
if [[ -n "$LOGFILE" ]]; then
    LOGDIR=$(dirname "$LOGFILE")
    LOGNAME=$(basename "$LOGFILE")
    mkdir -p $LOGDIR
    #if [[ -f "$LOGFILE" ]]; then
         #mv $LOGFILE ${LOGFILE}.$(date +%Y%m%d-%H%M)
    #fi
    exec > >(tee -a "${LOGFILE}") 2>&1
fi

# Print Date.
echo $(date):  "Starting snapshot.sh"

# Check required software
CheckReq

# Call MakeSnapshot function.
MakeSnapshot
