#!/bin/bash

# Version Info
echo "Export 2 Garmin Connect v1.1 (omron_pairing.sh)"
echo ""

# Workaround for pairing
coproc bluetoothctl
path=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)
source <(grep omron_omblepy_ $path/user/export2garmin.cfg)
if [ $omron_omblepy_debug == "on" ] ; then
	python3 -B $path/omron/omblepy.py -p -d $omron_omblepy_model --loggerDebug
else
	python3 -B $path/omron/omblepy.py -p -d $omron_omblepy_model
fi