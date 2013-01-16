#!/bin/bash

USERNAME=$1
HOST_NAME=$2
DAYS=$3
DATE=$(date +%Y%m%d)

cd ~/jobs

cat <<EOF > ${HOST_NAME}_${USERNAME}_${DATE}.pbs
#PBS -N ${HOST_NAME}_${USERNAME}
#PBS -q dispatch

IPMI_PASSFILE=/home/tfadmin/.ipmipass
nodes_dir=/home/tfadmin/nodes

# Date
date

# Sleep while it's reserved.
sleep ${DAYS}d

# Reboot the node.
ipmitool -I lanplus -U USERID -f \$IPMI_PASSFILE -E -H bmc-${HOST_NAME} power off
sleep 10
ipmitool -I lanplus -U USERID -f \$IPMI_PASSFILE -E -H bmc-${HOST_NAME} power on

# Update pxeconf to reset node.
cat \$nodes_dir/${HOST_NAME}/reset > \$nodes_dir/${HOST_NAME}/pxeconf

EOF

qsub ${HOST_NAME}_${USERNAME}_${DATE}.pbs
