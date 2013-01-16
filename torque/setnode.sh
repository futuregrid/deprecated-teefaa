#!/bin/bash

nodes_dir="/home/tfadmin/nodes"

cat $nodes_dir/$1/messenger > $nodes_dir/$1/pxeconf

