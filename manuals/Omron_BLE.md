## Omron_BLE VERSION

### 2.3.1. Preparing operating system
- Minimum hardware and software requirements are:
  - x86: 1vCPU, 1024MB RAM, 8GB disk space, network connection, Debian 12 operating system;
  - ARM: 1CPU, 512MB RAM, 8GB disk space, network connection, Raspberry Pi OS (based on Debian 12) | Debian 12 operating system;
  - In some cases of Raspberry Pi when using internal WiFi and bluetooth, you should connect internal WiFi on **_5GHz_**, because on 2,4GHz there may be a problem with connection stability (sharing same antenna).
- Update your system and then install following packages:
```
$ sudo apt update && sudo apt full-upgrade -y && sudo apt install -y wget python3 bc bluetooth python3-pip libglib2.0-dev procmail
$ sudo pip3 install --upgrade bluepy garminconnect bleak terminaltables --break-system-packages
```
- Modify file `sudo nano /etc/systemd/system/bluetooth.target.wants/bluetooth.service`:
```
ExecStart=/usr/libexec/bluetooth/bluetoothd --experimental
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable:
```
$ wget https://github.com/RobertWojtowicz/export2garmin/archive/refs/heads/master.tar.gz -O - | tar -xz
$ cd export2garmin-master && sudo chmod 755 import_data.sh omron/omron_pairing.sh && sudo chmod 555 /etc/bluetooth
```
### 2.3.2. Disabling Auto Sync of Omron device
- After measuring blood pressure, Omron allows you to download measurement data once;
- If you have OMRON connect app, you must disable Auto Sync;
- Because measurement data will be captured by app and integration will not be able to download data;
- In app, go to three dots (More) > Profile > Connected devices and set Auto sync to Off.

### 2.3.3. Configuring scripts
- First script is `user/import_tokens.py` is used to export Oauth1 and Oauth2 tokens of your account from Garmin Connect:
  - Script has support for login with or without MFA;
  - Once a year, tokens must be exported again, due to their expiration;
  - Repeat tokens export process for each user (if we have multiple users);
  - When you run `user/import_tokens.py`, you need to provide a login and password and possibly a code from MFA:
	```
	$ python3 /home/robert/export2garmin-master/user/import_tokens.py

	===============================================
	Export 2 Garmin Connect v2.6 (import_tokens.py)
	===============================================

	28.04.2024-11:58:44 * Login e-mail: email@email.com
	28.04.2024-11:58:50 * Enter password:
	28.04.2024-11:58:57 * MFA/2FA one-time code: 000000
	28.04.2024-11:59:17 * Oauth tokens saved correctly
	```
- Configuration is stored in `user/export2garmin.cfg` file (make changes e.g. via `sudo nano`):
  - Complete data in "omron_export_user*" parameter by inserting your Login e-mail (same as `user/import_tokens.py`);
  - To enable Omron module, set "on" in "switch_omron" parameter;
  - Complete device model in "omron_omblepy_model" parameter, check out [Omron device support matrix](https://github.com/userx14/omblepy?tab=readme-ov-file#omron-device-support-matrix);
  - Put blood pressure monitor in pairing mode by pressing Bluetooth button for 3-5 seconds, You will see a flashing "P" on monitor;
  - Run second script`omron/omron_pairing.sh` find device starting with “BLEsmart_”, select ID and press Enter, wait for pairing:
    ```
	$ /home/robert/export2garmin-master/omron/omron_pairing.sh

	===============================================
	Export 2 Garmin Connect v2.2 (omron_pairing.sh)
	===============================================

	27.11.2024-12:56:16 SYSTEM * BLE adapter check if available
	27.11.2024-12:56:38 SYSTEM * BLE adapter hci0(00:00:00:00:00:00) working, go to pairing
	2024-11-27 12:56:38,688 - omblepy - INFO - Attempt to import module for device hem-7361t
	To improve your chance of a successful connection please do the following:
	 -remove previous device pairings in your OS's bluetooth dialog
	 -enable bluetooth on you omron device and use the specified mode (pairing or normal)
	 -do not accept any pairing dialog until you selected your device in the following list

	Select your Omron device from the list below...
	+----+-------------------+-------------------------------+------+
	| ID | MAC               | NAME                          | RSSI |
	+----+-------------------+-------------------------------+------+
	| 0  | 00:00:00:00:00:00 | BLESmart_0000025828FFB232E019 | -74  |
	+----+-------------------+-------------------------------+------+
	Enter ID or just press Enter to rescan.
	```
  - Complete data in "omron_omblepy_mac" parameter which is related to MAC address of Omron device (read during pairing, MAC column);
  - Configuration file contains many **other options**, check descriptions and use for your configuration.
- Third script is `import_data.sh` has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/export2garmin-master/import_data.sh

=============================================
Export 2 Garmin Connect v2.5 (import_data.sh)
=============================================

18.07.2024-16:56:01 SYSTEM * Path to temp files: /dev/shm/
18.07.2024-16:56:01 SYSTEM * Path to user files: /home/robert/export2garmin-master/user/
18.07.2024-16:56:01 SYSTEM * BLE adapter is ON in export2garmin.cfg file, check if available
18.07.2024-16:56:01 SYSTEM * BLE adapter hci0(00:00:00:00:00:00) working, check if temp.log file exists
18.07.2024-16:56:01 SYSTEM * temp.log file exists, go to modules
18.07.2024-16:56:07 MISCALE * Module is OFF in export2garmin.cfg file
18.07.2024-16:56:07 OMRON * Module is ON in export2garmin.cfg file
18.07.2024-16:56:07 OMRON * omron_backup.csv file exists, checking for new data
18.07.2024-16:56:07 OMRON * Importing data from a BLE adapter
18.07.2024-16:56:39 OMRON * Prepare data for omron_backup.csv file
18.07.2024-16:56:40 OMRON * Calculating data from import 1721314552, upload to Garmin Connect
18.07.2024-16:56:40 OMRON * Data upload to Garmin Connect is complete
18.07.2024-16:56:40 OMRON * Saving calculated data from import 1721314552 to omron_backup.csv file
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /dev/shm/temp.log

=============================================
Export 2 Garmin Connect v2.0 (omron_export.py
=============================================

OMRON * Import data: 1721231144;17.07.2024;17:45;82;118;65;0;0;email@email.com
OMRON * Calculated data: Normal;0;0;email@email.com;17.07.2024;17:47
OMRON * Upload status: OK
```
- Finally, if everything works correctly add script import_data.sh as a service, make sure about path:
```
$ find / -name import_data.sh
/home/robert/export2garmin-master/import_data.sh
```
- To run it at system startup in an infinite loop, create a file `sudo nano /etc/systemd/system/export2garmin.service` enter previously searched path to import_data.sh and include "User" name:
```
[Unit]
Description=Export2Garmin service
After=network.target

[Service]
Type=simple
User=robert
ExecStart=/home/robert/export2garmin-master/import_data.sh -l
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
- Activate Export2Garmin service and run it:
```
$ sudo systemctl enable export2garmin.service && sudo systemctl start export2garmin.service
```
- You can check if export2garmin service works `sudo systemctl status export2garmin.service` or temporarily stop it with command `sudo systemctl stop export2garmin.service`.

### 2.3.4. How to increase BLE range
- Purchase a cheap USB bluetooth adapter:
  - 5.0/5.1 (tested on RTL8761B chipset, manufacturer Zexmte, works with Miscale and Omron module);
  - 5.3 (tested on ATS2851 chipset, manufacturer Zexmte, works with Miscale module, **does not work with Omron module**).
- Bluetooth adapter should have a removable RP-SMA antenna;
- You will have option to change if standard RP-SMA antenna included with bluetooth adapter gives too little range;
- If you are using a virtual machine, assign bluetooth adapter from tab Hardware > Add: USB device > Use USB Vendor/Device ID > Choose Device: > Passthrough a specific device (tested on Proxmox VE 8.3);
- RTL8761B chipset requires driver (for Raspberry Pi OS skip this step), install Realtek package and restart virtual machine:
```
sudo apt install -y firmware-realtek
sudo reboot
```
- If you are using multiple BLE adapters, select appropriate one by HCI number or MAC address (recommended) and set in `user/export2garmin.cfg` file;
- Use command `sudo hciconfig -a` to locate BLE adapter, and then select type of identification:
  - By HCI number, set parameter "ble_adapter_hci";
  - By MAC address, set parameter "ble_adapter_switch" to "on" and specify MAC addres in parameter "ble_adapter_mac".
- Sample photo with test configuration, on left Raspberry Pi 0W, on right server with virtual machine (stronger antenna added):

![alt text](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/usb.jpg)
- Back to [README](https://github.com/RobertWojtowicz/export2garmin/blob/master/README.md).

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>