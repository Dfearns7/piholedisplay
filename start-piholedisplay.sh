#!/bin/bash

sleep 15s

echo "Starting pihole stats display"

cd $(dirname $0)/python

python3 piholedisplay.py