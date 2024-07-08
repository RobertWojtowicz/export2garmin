#!/bin/bash

# Version Info
echo "Export 2 Garmin Connect v1.0 (omron_pairing.sh)"
echo ""

# Workaround for pairing and data transfer
coproc bluetoothctl
path=`cd "$(dirname "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd`
export $(grep omron_omblepy $path/user/export2garmin.cfg)
python3 -B $path/omron/omblepy.py -p -d $omron_omblepy_model
