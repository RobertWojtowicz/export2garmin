#!/bin/bash

# Version info
echo -e "\n==============================================="
echo -e "Export 2 Garmin Connect v3.0 (omron_pairing.sh)"
echo -e "===============================================\n"

# Verifying correct working of BLE, restart bluetooth service and device via miscale_ble.py
path=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)
timenow() { date +%d.%m.%Y-%H:%M:%S; }
echo "$(timenow) SYSTEM * BLE adapter check if available"
ble_check=$(python3 -B $path/miscale/miscale_ble.py)
if echo $ble_check | grep -q "failed" ; then
	echo "$(timenow) SYSTEM * BLE adapter not working, skip pairing"
else ble_status=ok
	hci_mac=$(echo $ble_check | grep -o 'h.\{21\})' | head -n 1)
	echo "$(timenow) SYSTEM * BLE adapter $hci_mac working, go to pairing"
fi

# Workaround for pairing
if [[ $ble_status == "ok" ]] ; then
	source <(grep omron_omblepy_ $path/user/export2garmin.cfg)
	omron_hci=$(echo $ble_check | grep -o 'hci.' | head -n 1)
	coproc bluetoothctl
	if [ $omron_omblepy_debug == "on" ] ; then
        python3 -B $path/omron/omblepy.py -a $omron_hci -p -d $omron_omblepy_model --loggerDebug
	else
        python3 -B $path/omron/omblepy.py -a $omron_hci -p -d $omron_omblepy_model
	fi
fi