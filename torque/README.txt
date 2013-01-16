# teefaa/torque - Scripts and examples for Torque.

# These scripts and examples are used for setting up Teefaa
# with Torque Resource Manager so that users can get compute 
# nodes with their own images.

# rc.local - needs to be placed in your messenger(netboot image.)
teefaa=/path/to/teefaa
cp $teefaa/trque/rc.local /etc/rc.local

# epilogue - needs to be placed in your torque_mom nodes.
torque=/var/spool/torque
cp $teefaa/torque/epilogue $torque/mom_priv/epilogue
