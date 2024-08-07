#!/bin/bash

# Version Info
echo "Export 2 Garmin Connect v1.4 (import_data.sh)"
echo ""

# Blocking multiple instances of same script process
timenow() {
    date +%d.%m.%Y-%H:%M:%S
}
remove_lock() {
    rm -f "/dev/shm/export.lock"
}
another_instance() {
	echo "$(timenow) EXPORT * Another instance running"
	exit 1
}
lockfile -r 0 -l 60 "/dev/shm/export.lock" || another_instance
trap remove_lock EXIT

path=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
source <(grep switch_ $path/user/export2garmin.cfg)

# Create a loop, "-l" parameter executes loop indefinitely
loop_count=1
[[ "$1" == "-l" ]] && loop_count=0
i=0
while [[ $loop_count -eq 0 ]] || [[ $i -lt $loop_count ]] ; do
	((i++))

	# Cleaning temp.log file after last startup
    [[ -s /dev/shm/temp.log ]] && > /dev/shm/temp.log

	# Mi Body Composition Scale 2
	if [[ $switch_miscale == "on" ]] ; then
		miscale_backup=$path/user/miscale_backup.csv
		echo "$(timenow) MISCALE * Module is on"

		# Creating miscale_backup.csv and temp.log file
		if [[ ! -f $miscale_backup ]] ; then
			miscale_header="Data Status;Unix Time;Date [dd.mm.yyyy];Time [hh:mm:ss];Weight [kg];Change [kg];BMI;Body Fat [%];Skeletal Muscle Mass [kg];Bone Mass [kg];Body Water [%];Physique Rating;Visceral Fat;Metabolic Age [years];BMR [kCal];LBM [kg];Ideal Wieght [kg];Fat Mass To Ideal [type:mass kg];Protein [%];Impedance;Login e-mail;Upload Date [dd.mm.yyyy];Upload Time [hh:mm:ss];Difference Time [s]"
			[[ $switch_mqtt == "on" ]] && miscale_header="$miscale_header;Battery [V];Battery [%]"
			echo "$(timenow) MISCALE * Creating miscale_backup.csv file, check if temp.log exists"
			echo $miscale_header > $miscale_backup
		else echo "$(timenow) MISCALE * miscale_backup.csv file exists, check if temp.log exists"
		fi
		if [[ ! -f /dev/shm/temp.log ]] ; then
			echo "$(timenow) MISCALE * Creating temp.log file, checking for new data"
			echo > /dev/shm/temp.log
		else echo "$(timenow) MISCALE * temp.log file exists, checking for new data"
		fi

		# Importing raw data from source (BLE or MQTT)
		if [[ $switch_mqtt == "on" ]] ; then
  			source <(grep miscale_mqtt_ $path/user/export2garmin.cfg)
			echo "$(timenow) MISCALE * Importing data from an MQTT broker"
			miscale_read=$(mosquitto_sub -h localhost -t 'data' -u "$miscale_mqtt_user" -P "$miscale_mqtt_passwd" -C 1 -W 10)
		else echo "$(timenow) MISCALE * Importing data from a BLE scanner"
			miscale_read_all=$(python3 -B $path/miscale/miscale_ble.py)
			miscale_read=$(echo $miscale_read_all | awk '{sub(/.*BLE scan/, ""); print substr($1,1)}')
		fi

		# Checking if BLE scanner detects BLE devices, print to temp.log file, restart service, reimport
		miscale_unixtime=$(echo $miscale_read | awk -F ";" '{print $1}')
		if [[ -z $miscale_unixtime ]] ; then
			if [[ $switch_mqtt == "on" ]] ; then
				echo "$(timenow) MISCALE * No MQTT data, check connection to MQTT broker or ESP32"
			else
				if echo $miscale_read_all | grep -q "device" ; then
					echo "$(timenow) MISCALE * No BLE data from scale or incomplete, check BLE scanner"
					grep -q "bluetooth" /dev/shm/temp.log && sed -i "/bluetooth/d" /dev/shm/temp.log
				else
					if [[ ! -f /dev/shm/temp.log ]] ; then
						echo "$(timenow) MISCALE * No BLE devices found to scan, restarting bluetooth service" 2>&1 | tee /dev/shm/temp.log
						sudo systemctl restart bluetooth.service
						miscale_read=$(python3 -B $path/miscale/miscale_ble.py | awk 'END{print}')
						miscale_unixtime=$(echo $miscale_read | awk -F ";" '{print $1}')
					elif grep -q "bluetooth" /dev/shm/temp.log ; then
						echo "$(timenow) MISCALE * Again, no BLE devices found to scan"
					else echo "$(timenow) MISCALE * No BLE devices found to scan, restarting bluetooth service" 2>&1 | tee /dev/shm/temp.log
						sudo systemctl restart bluetooth.service
						miscale_read=$(python3 -B $path/miscale/miscale_ble.py | awk 'END{print}')
						miscale_unixtime=$(echo $miscale_read | awk -F ";" '{print $1}')
					fi
				fi
			fi
		fi

		# Checking raw data and time, save correct raw data to miscale_backup.csv file
		if [[ -n $miscale_unixtime ]] ; then
  			source <(grep miscale_offset $path/user/export2garmin.cfg)
			miscale_time_zone=$(date +%z | awk '{print substr($1,1,3)}')
			miscale_offset_unixtime=$(( $miscale_unixtime + $miscale_time_zone * 3600 + $miscale_offset ))
			miscale_offset=${miscale_read/${miscale_unixtime}/to_import;${miscale_offset_unixtime}}
			miscale_cut=$(echo $miscale_offset_unixtime | awk '{print substr($1,1,8)}')
			miscale_os_unixtime=$(date +%s)
			miscale_time_shift=$(( $miscale_os_unixtime - $miscale_offset_unixtime ))
			if grep -q $miscale_cut $miscale_backup ; then
				miscale_time_tag=$(grep -m 1 $miscale_cut $miscale_backup | awk -F ";" '{print $2}')
				miscale_time_dif=$(( $miscale_offset_unixtime - $miscale_time_tag ))
				miscale_absolute_dif=$(echo ${miscale_time_dif#-})
				if (( $miscale_absolute_dif < 30 )) ; then
					echo "$(timenow) MISCALE * $miscale_time_dif s time difference, same or similar data already exists in miscale_backup.csv file"
				else miscale_absolute_shift=$(echo ${miscale_time_shift#-})
					if (( $miscale_absolute_shift > 1200 )) ; then
						echo "$(timenow) MISCALE * $miscale_time_shift s time difference, synchronize date and time scale"
						echo "$(timenow) MISCALE * Time offset is set to $miscale_offset s"
						echo "$(timenow) MISCALE * Deleting import $miscale_offset_unixtime from miscale_backup.csv file"
						sed -i "/$miscale_offset_unixtime/d" $miscale_backup
					else echo "$(timenow) MISCALE * Saving import $miscale_offset_unixtime to miscale_backup.csv file"
						echo $miscale_offset >> $miscale_backup
					fi
				fi
			else miscale_absolute_shift=$(echo ${miscale_time_shift#-})
				if (( $miscale_absolute_shift > 1200 )) ; then
					echo "$(timenow) MISCALE * $miscale_time_shift s time difference, synchronize date and time scale"
					echo "$(timenow) MISCALE * Time offset is set to $miscale_offset s"
				else echo "$(timenow) MISCALE * Saving import $miscale_offset_unixtime to miscale_backup.csv file"
					echo $miscale_offset >> $miscale_backup
				fi
			fi
		fi

		# Calculating data and upload to Garmin Connect, print to temp.log file
		if grep -q "failed\|to_import" $miscale_backup ; then
			if grep -q "bluetooth" /dev/shm/temp.log ; then
				echo "$(timenow) MISCALE * No BLE devices found to scan, restarting bluetooth service" > /dev/shm/temp.log
				python3 -B $path/miscale/miscale_export.py >> /dev/shm/temp.log 2>&1
				miscale_import=$(awk -F ": " '/MISCALE /*/ Import data:/{print substr($2,1,10)}' /dev/shm/temp.log)
			else python3 -B $path/miscale/miscale_export.py > /dev/shm/temp.log 2>&1
				miscale_import=$(awk -F ": " '/MISCALE /*/ Import data:/{print substr($2,1,10)}' /dev/shm/temp.log)
			fi
		fi

		# Handling errors, save calculated data to miscale_backup.csv file
		if [[ -z $miscale_import ]] ; then
			echo "$(timenow) MISCALE * There is no new data to upload to Garmin Connect"
		else echo "$(timenow) MISCALE * Calculating data from import $miscale_import, upload to Garmin Connect"
			if grep -q "MISCALE \* There" /dev/shm/temp.log ; then
				echo "$(timenow) MISCALE * There is no user with given weight or undefined user email@email.com, check users section in export2garmin.cfg"
				echo "$(timenow) MISCALE * Deleting import $miscale_import from miscale_backup.csv file"
				sed -i "/$miscale_import/d" $miscale_backup
			elif grep -q "Err" /dev/shm/temp.log ; then
				echo "$(timenow) MISCALE * Upload to Garmin Connect has failed, check temp.log for error details"
				sed -i "s/to_import;$miscale_import/failed;$miscale_import/" $miscale_backup
			else echo "$(timenow) MISCALE * Data upload to Garmin Connect is complete"
				echo "$(timenow) MISCALE * Saving calculated data from import $miscale_import to miscale_backup.csv file"
				miscale_calc_data=$(awk -F ": " '/MISCALE /*/ Calculated data:/{print $2}' /dev/shm/temp.log)
				miscale_import_data=$(awk -F ": " '/MISCALE /*/ Import data:/{print $2}' /dev/shm/temp.log)
				sed -i "s/failed;$miscale_import_data/uploaded;$miscale_import;$miscale_calc_data;$miscale_time_shift/; s/to_import;$miscale_import_data/uploaded;$miscale_import;$miscale_calc_data;$miscale_time_shift/" $miscale_backup
				miscale_import_diff=$(echo $miscale_calc_data | awk -F ";" '{print $1 ";" $2 ";" $3}')
				miscale_check_line=$(wc -l < $miscale_backup)
				if [[ $miscale_check_line == "2" ]] ; then
					sed -i "s/$miscale_import;$miscale_import_diff/$miscale_import;$miscale_import_diff;0.0/" $miscale_backup
				else miscale_email_user=$(echo $miscale_calc_data | awk -F ";" '{print $18}')
					miscale_weight_last=$(grep $miscale_email_user $miscale_backup | sed -n 'x;$p' | awk -F ";" '{print $5}')
					miscale_weight_import=$(echo $miscale_calc_data | awk -F ";" '{print $3}')
					miscale_weight_diff=$(echo $miscale_weight_import - $miscale_weight_last | bc | sed "s/^-\./-0./; s/^\./0./")
					sed -i "s/$miscale_import;$miscale_import_diff/$miscale_import;$miscale_import_diff;$miscale_weight_diff/; s/;0;/;0.0;/" $miscale_backup
				fi
			fi
		fi
		unset $(compgen -v | grep '^miscale_')
	else echo "$(timenow) MISCALE * Module is off"
	fi

	# Omron blood pressure
	if [[ $switch_omron == "on" ]] ; then
		source <(grep omron_ $path/user/export2garmin.cfg)
		omron_backup=$path/user/omron_backup.csv
		echo "$(timenow) OMRON * Module is on"

		# Creating omron_backup.csv and temp.log file
		if [[ ! -f $omron_backup ]] ; then
			echo "Data Status;Unix Time;Email User;Date [dd.mm.yyyy];Time [hh:mm:ss];Systolic [mmHg];Diastolic [mmHg];Heart Rate [bpm];MOV;IHB;Upload Date [dd.mm.yyyy];Upload Time [hh:mm:ss];Difference Time [s]" > $omron_backup
			echo "$(timenow) OMRON * Creating omron_backup.csv file, check if temp.log exists"
		else echo "$(timenow) OMRON * omron_backup.csv file exists, check if temp.log exists"
		fi
		if [[ ! -f /dev/shm/temp.log ]] ; then
			echo "$(timenow) OMRON * Creating temp.log file, checking for new data"
			echo > /dev/shm/temp.log
		else echo "$(timenow) OMRON * temp.log file exists, checking for new data"
		fi
		if [[ -z $(hcitool dev | awk 'NR>1 {print $2}') ]] ; then
			echo "$(timenow) OMRON * No BLE device detected, skip scanning"

		# Importing raw data from source (BLE)
		else echo "$(timenow) OMRON * Importing data from a BLE scanner"
			coproc ble { bluetoothctl; }
			while true ; do
				timeout 10s python3 -B $path/omron/omblepy.py -p -d $omron_omblepy_model > /dev/shm/omron_users.csv 2>&1
				if grep -q $omron_omblepy_mac /dev/shm/omron_users.csv ; then
					if [[ $omron_omblepy_debug == "on" ]] ; then
						python3 -B $path/omron/omblepy.py -n -t -d $omron_omblepy_model --loggerDebug -m $omron_omblepy_mac
					elif [[ $omron_omblepy_all == "on" ]] ; then
						python3 -B $path/omron/omblepy.py -t -d $omron_omblepy_model -m $omron_omblepy_mac > /dev/null 2>&1
					else
						python3 -B $path/omron/omblepy.py -n -t -d $omron_omblepy_model -m $omron_omblepy_mac > /dev/null 2>&1
					fi
				else exec {ble[0]}>&-
					exec {ble[1]}>&-
					wait $ble_PID
					break
				fi
			done
			if [[ -f "/dev/shm/omron_user1.csv" ]] || [[ -f "/dev/shm/omron_user2.csv" ]] ; then
				echo "$(timenow) OMRON * Prepare data for omron_backup.csv file"
				awk -F ';' 'NR==FNR{a[$2];next}!($2 in a)' $omron_backup /dev/shm/omron_user1.csv > /dev/shm/omron_users.csv
				awk -F ';' 'NR==FNR{a[$2];next}!($2 in a)' $omron_backup /dev/shm/omron_user2.csv >> /dev/shm/omron_users.csv
				sed -i "s/ /;/g; s/user1/$omron_export_user1/; s/user2/$omron_export_user2/" /dev/shm/omron_users.csv
				grep -q "email@email.com" /dev/shm/omron_users.csv && echo "$(timenow) OMRON * Deleting records with undefined user email@email.com, check users section in export2garmin.cfg" && sed -i "/email@email\.com/d" /dev/shm/omron_users.csv
				cat /dev/shm/omron_users.csv >> $omron_backup
				rm /dev/shm/omron_user*.csv
			else echo "$(timenow) OMRON * No BLE data from Omron, check BLE scanner"
				rm /dev/shm/omron_users.csv
			fi
		fi

		# Upload to Garmin Connect, print to temp.log file
		if grep -q "failed\|to_import" $omron_backup ; then
			if [[ $switch_miscale == "on" ]] ; then
				python3 -B $path/omron/omron_export.py >> /dev/shm/temp.log 2>&1
				omron_import=$(awk -F ": " '/OMRON /*/ Import data:/{print substr($2,1,10)}' /dev/shm/temp.log)
			else python3 -B $path/omron/omron_export.py > /dev/shm/temp.log 2>&1
				if [[ $omron_omblepy_all == "on" ]] || [[ $switch_mqtt == "on" ]] ; then
					omron_import=$(awk -F ": " '/OMRON /*/ Import data:/{print substr($2,1,10)}' /dev/shm/temp.log)
					sleep 10
				else
					omron_import=$(awk -F ": " '/OMRON /*/ Import data:/{print substr($2,1,10)}' /dev/shm/temp.log)
				fi
			fi
		fi

		# Handling errors, save data to miscale_backup.csv file
		if [[ -z $omron_import ]] ; then
			echo "$(timenow) OMRON * There is no new data Omron to upload to Garmin Connect"
		else echo "$(timenow) OMRON * Data from import $omron_import upload to Garmin Connect"
			if grep -q "Err" /dev/shm/temp.log ; then
				if grep -q "MISCALE \* Upload" /dev/shm/temp.log ; then
					echo "$(timenow) OMRON * Upload to Garmin Connect has failed, check temp.log for error details"
					sed -i "s/to_import;$omron_import/failed;$omron_import/" $omron_backup
				elif grep -q "OMRON \* Upload" /dev/shm/temp.log ; then
					echo "$(timenow) OMRON * Data upload to Garmin Connect is complete"
					echo "$(timenow) OMRON * Saving calculated data from import $omron_import to omron_backup.csv file"
					omron_import_data=$(awk -F ": " '/OMRON /*/ Import data:/{print $2}' /dev/shm/temp.log)
					omron_date_time=$(awk -F ": " '/OMRON /*/ Export date time:/{print $2}' /dev/shm/temp.log)
					omron_os_unixtime=$(date +%s)
					omron_time_shift=$(( $omron_os_unixtime - $omron_import ))
					sed -i "s/failed;$omron_import_data/uploaded;omron_import_data;$omron_date_time;$omron_time_shift/; s/to_import;$omron_import_data/uploaded;$omron_import_data;$omron_date_time;$omron_time_shift/" $omron_backup
				else
					echo "$(timenow) OMRON * Upload to Garmin Connect has failed, check temp.log for error details"
					sed -i "s/to_import;$omron_import/failed;$omron_import/" $omron_backup
				fi
			else echo "$(timenow) OMRON * Data upload to Garmin Connect is complete"
				echo "$(timenow) OMRON * Saving calculated data from import $omron_import to omron_backup.csv file"
				omron_import_data=$(awk -F ": " '/OMRON /*/ Import data:/{print $2}' /dev/shm/temp.log)
				omron_date_time=$(awk -F ": " '/OMRON /*/ Export date time:/{print $2}' /dev/shm/temp.log)
				omron_os_unixtime=$(date +%s)
				omron_time_shift=$(( $omron_os_unixtime - $omron_import ))
				sed -i "s/failed;$omron_import_data/uploaded;omron_import_data;$omron_date_time;$omron_time_shift/; s/to_import;$omron_import_data/uploaded;$omron_import_data;$omron_date_time;$omron_time_shift/" $omron_backup
			fi
		fi
		unset $(compgen -v | grep '^omron_')
	else echo "$(timenow) OMRON * Module is off"
	fi
    [[ $loop_count -eq 1 ]] && break
done