#!/bin/bash

# Data acquisition from MQTT broker
user=admin
passwd=password

# Version Info
echo 'Mi Body Composition Scale 2 Garmin Connect v3.0 (import_mqtt.sh)'
echo ''

# Create a data backup file
path=`cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd`
if [ ! -f $path/backup.csv ] ; then
	echo '* Create a data backup file, checking for new data'
	echo 'Weight;Impedance;Unix_time;Readable_time;Bat_in_V;Bat_in_%' > $path/backup.csv
else echo '* Data backup file exists, checking for new data'
fi

# Create file with import data
read_all=`mosquitto_sub -h localhost -t 'data' -u $user -P $passwd -C 1 -W 10`
read_unixtime=`echo $read_all | awk -F "\"*;\"*" 'END{print $3}'`
if [ -z $read_unixtime ] ; then
	echo '* No MQTT data, check connection to MQTT broker or ESP32'
elif grep -q $read_unixtime $path/backup.csv ; then
	echo '* There is no new data to upload to Garmin Connect'
elif [ -f $path/$read_unixtime.tlog ] ; then
	echo '* Import file already exists, calculating data to upload'
else echo $read_all > $path/$read_unixtime.tlog
	echo '* Importing and calculating data to upload'
fi

# Calculate data and export to Garmin Connect, logging, handling errors, backup file
if [ -f $path/*.tlog ] ; then
	python3 -B $path/export_garmin.py > $path/temp.log 2>&1
	move=`awk -F ": " '/Processed file:/{print $2}' $path/temp.log`
	if grep -q 'Error' $path/temp.log ; then
		echo '* Upload to Garmin Connect has failed, check temp.log for error details'
	elif grep -q 'panic' $path/temp.log ; then
		echo '* Upload to Garmin Connect has failed, check temp.log for error details'
	elif grep -q 'denied' $path/temp.log ; then
		echo '* Upload to Garmin Connect has failed, check temp.log for error details'
	elif grep -q 'There' $path/temp.log ; then
		echo '* Upload to Garmin Connect has failed, check temp.log for error details'
	elif grep -q 'Exec' $path/temp.log ; then
		echo '* Upload to Garmin Connect has failed, check temp.log for error details'
	else cat $path/$move >> $path/backup.csv
		rm $path/$move
		echo '* Data upload to Garmin Connect is complete'
	fi
fi
