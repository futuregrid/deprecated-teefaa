#!/bin/bash

# Load Teefaa Torque configuration and functions.
source /home/tfadmin/teefaa/torque/torquerc
source /home/tfadmin/teefaa/torque/torque_functions

SetJobDispatch $@
