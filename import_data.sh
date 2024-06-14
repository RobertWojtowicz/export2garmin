#!/bin/bash

# Version Info
echo "Export 2 Garmin Connect v1.0 (import_data.sh)"
echo ""

# Creating miscale_backup.csv and temp.log file
path=`cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd`
source $path/user/export2garmin.cfg
timenow="date +%d.%m.%Y-%H:%M:%S"
if [ ! -f $path/user/miscale_backup.csv ] ; then
	header="Data Status;Unix Time;Date;Time;Weight [kg];Change [kg];BMI;Body Fat [%];Skeletal Muscle Mass [kg];Bone Mass [kg];Body Water [%];Physique Rating;Visceral Fat;Metabolic Age [years];BMR [kCal];LBM [kg];Ideal Wieght [kg];Fat Mass To Ideal [type:mass kg];Protein [%];Impedance;Login e-mail;Upload Date;Upload Time;Difference Time [s]"
	echo "$($timenow) * Creating miscale_backup.csv file, check if temp.log exists"
	if [ $miscale_mqtt == "off" ] ; then
		echo "$header" > $path/user/miscale_backup.csv
	else echo "$header;Battery [V];Battery [%]" > $path/user/miscale_backup.csv
	fi
else echo "$($timenow) * miscale_backup.csv file exists, check if temp.log exists"
fi
if [ ! -f $path/temp.log ] ; then
	echo "$($timenow) * Creating temp.log file, checking for new data"
	echo > $path/temp.log
else echo "$($timenow) * temp.log file exists, checking for new data"
fi

# Importing raw data from source (BLE or MQTT)
if [ $miscale_mqtt == "off" ] ; then
	echo "$($timenow) * Importing data from a BLE scanner"
	read_all=`python3 -B $path/bin/miscale_ble.py`
	read_scale=`echo $read_all | awk '{sub(/.*BLE scan/, ""); print substr($1,1)}'`
else echo "$($timenow) * Importing data from an MQTT broker"
	read_scale=`mosquitto_sub -h localhost -t 'data' -u $miscale_mqtt_user -P $miscale_mqtt_passwd -C 1 -W 10`
fi

# Checking if BLE scanner detects BLE devices, print to temp.log file, restart service, reimport
unixtime_scale=`echo $read_scale | awk -F ";" '{print $1}'`
if [ -z $unixtime_scale ] ; then
	if [ $miscale_mqtt == "off" ] ; then
		if echo $read_all | grep -q "device" ; then
			echo "$($timenow) * No BLE data from scale or incomplete, check BLE scanner"
			if grep -q "bluetooth" $path/temp.log ; then
				sed -i "/bluetooth/d" $path/temp.log
			fi
		else
			if [ ! -f $path/temp.log ] ; then
				echo "$($timenow) * No BLE devices found to scan, restarting bluetooth service" 2>&1 | tee $path/temp.log
				sudo systemctl restart bluetooth
				read_scale=`python3 -B $path/bin/miscale_ble.py | awk 'END{print}'`
				unixtime_scale=`echo $read_scale | awk -F ";" '{print $1}'`
			elif grep -q "bluetooth" $path/temp.log ; then
				echo "$($timenow) * Again, no BLE devices found to scan"
			else
				echo "$($timenow) * No BLE devices found to scan, restarting bluetooth service" 2>&1 | tee $path/temp.log
				sudo systemctl restart bluetooth
				read_scale=`python3 -B $path/bin/miscale_ble.py | awk 'END{print}'`
				unixtime_scale=`echo $read_scale | awk -F ";" '{print $1}'`
			fi
		fi
	else echo "$($timenow) * No MQTT data, check connection to MQTT broker or ESP32"
	fi
fi

# Checking raw data and time, save correct raw data to miscale_backup.csv file
if [ ! -z $unixtime_scale ] ; then
	time_zone=`date +%z | awk '{print substr($1,1,3)}'`
	offset_unixtime=$(( $unixtime_scale + $time_zone * 3600 + $offset ))
	offset_scale=${read_scale/${unixtime_scale}/to_import;${offset_unixtime}}
	cut_scale=`echo $offset_unixtime | awk '{print substr($1,1,8)}'`
	unixtime_os=`date +%s`
	time_shift=$(( $unixtime_os - $offset_unixtime ))
	if grep -q $cut_scale $path/user/miscale_backup.csv ; then
		time_tag=`grep -m 1 $cut_scale $path/user/miscale_backup.csv | awk -F ";" '{print $2}'`
		time_dif=$(( $offset_unixtime - $time_tag ))
		absolute_dif=`echo ${time_dif#-}`
		if (( $absolute_dif < 30 )) ; then
			echo "$($timenow) * $time_dif s time difference, same or similar data already exists in miscale_backup.csv file"
		else absolute_shift=`echo ${time_shift#-}`
			if (( $absolute_shift > 1200 )) ; then
				echo "$($timenow) * $time_shift s time difference, synchronize date and time scale"
				echo "$($timenow) * Time offset is set to $offset s"
				echo "$($timenow) * Deleting import $offset_unixtime from miscale_backup.csv file"
				sed -i "/$offset_unixtime/d" $path/user/miscale_backup.csv
			else echo "$($timenow) * Saving import $offset_unixtime to miscale_backup.csv file"
				echo $offset_scale >> $path/user/miscale_backup.csv
			fi
		fi
	else absolute_shift=`echo ${time_shift#-}`
		if (( $absolute_shift > 1200 )) ; then
			echo "$($timenow) * $time_shift s time difference, synchronize date and time scale"
			echo "$($timenow) * Time offset is set to $offset s"
		else echo "$($timenow) * Saving import $offset_unixtime to miscale_backup.csv file"
			echo $offset_scale >> $path/user/miscale_backup.csv
		fi
	fi
fi

# Calculating data and upload to Garmin Connect, print to temp.log file
if grep -q "failed\|to_import" $path/user/miscale_backup.csv ; then
	if grep -q "bluetooth" $path/temp.log ; then
		echo "$($timenow) * No BLE devices found to scan, restarting bluetooth service" > $path/temp.log
		python3 -B $path/bin/miscale_export.py >> $path/temp.log 2>&1
		import_no=`awk -F ": " '/Import data:/{print substr($2,1,10)}' $path/temp.log`
	else
		python3 -B $path/bin/miscale_export.py > $path/temp.log 2>&1
		import_no=`awk -F ": " '/Import data:/{print substr($2,1,10)}' $path/temp.log`
	fi
fi

# Handling errors, save calculated data to miscale_backup.csv file
if [ -z $import_no ] ; then
	echo "$($timenow) * There is no new data to upload to Garmin Connect"
else echo "$($timenow) * Calculating data from import $import_no, upload to Garmin Connect"
	if grep -q "There" $path/temp.log ; then
		echo "$($timenow) * There is no user with given weight, check users section in miscale_export.py"
		echo "$($timenow) * Deleting import $import_no from miscale_backup.csv file"
		sed -i "/$import_no/d" $path/user/miscale_backup.csv
	elif grep -q "Err" $path/temp.log ; then
		echo "$($timenow) * Upload to Garmin Connect has failed, check temp.log for error details"
		sed -i "s/to_import;$import_no/failed;$import_no/" $path/user/miscale_backup.csv
	else echo "$($timenow) * Data upload to Garmin Connect is complete"
		echo "$($timenow) * Saving calculated data from import $import_no to miscale_backup.csv file"
		calc_data=`awk -F ": " '/Calculated data:/{print $2}' $path/temp.log`
		import_data=`awk -F ": " '/Import data:/{print $2}' $path/temp.log`
		sed -i "s/failed;$import_data/uploaded;$import_no;$calc_data;$time_shift/; s/to_import;$import_data/uploaded;$import_no;$calc_data;$time_shift/" $path/user/miscale_backup.csv
		import_diff=`echo $calc_data | awk -F ";" '{print $1 ";" $2 ";" $3}'`
		check_line=`wc -l < $path/user/miscale_backup.csv`
			if [ $check_line == "2" ] ; then
				sed -i "s/$import_no;$import_diff/$import_no;$import_diff;0.0/" $path/user/miscale_backup.csv
			else
				email_user=`echo $calc_data | awk -F ";" '{print $18}'`
				weight_last=`grep $email_user $path/user/miscale_backup.csv | sed -n 'x;$p' | awk -F ";" '{print $5}'`
				weight_import=`echo $calc_data | awk -F ";" '{print $3}'`
				weight_diff=`echo $weight_import - $weight_last | bc | sed "s/^-\./-0./; s/^\./0./"`
				sed -i "s/$import_no;$import_diff/$import_no;$import_diff;$weight_diff/; s/;0;/;0.0;/" $path/user/miscale_backup.csv
			fi
	fi
fi
