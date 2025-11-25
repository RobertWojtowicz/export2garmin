## 2.1. Miscale_BLE VERSION
- This module is based on following projects:
  - https://github.com/cyberjunky/python-garminconnect;
  - https://github.com/wiecosystem/Bluetooth;
  - https://github.com/lolouk44/xiaomi_mi_scale.

### 2.1.1. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object
- Install Zepp Life App on your mobile device from Play Store;
- Configure your scale with Zepp Life App on your mobile device (tested on Android 10-15);
- Retrieve scale's MAC address from Zepp Life App (Profile > My devices > Mi Body Composition Scale 2);
- Turn off weigh small object in Zepp Life App (Profile > My devices > Mi Body Composition Scale 2) for better measurement quality.

### 2.1.2. Setting correct date and time in Mi Body Composition Scale 2
- Launch Zepp Life App, go to scale (Profile > My devices > Mi Body Composition Scale 2);
- Start scale and select Clear data in App;
- Take a new weight measurement with App, App should synchronize date and time (UTC);
- You should also synchronize scale after replacing batteries.

### 2.1.3. Preparing operating system
- Minimum hardware and software requirements are:
  - x86: 1vCPU, 1024MB RAM, 8GB disk space, network connection, Debian 13 operating system;
  - ARM: Minimum is Raspberry Pi Zero 2 W, 8GB disk space, Raspberry Pi operating system;
- Check bluetooth adapter from support matrix [2.6.1.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/about_BLE.md#261-ble-adapters-support-matrix);
- Update your system and then install following packages:
```
$ sudo apt update && sudo apt full-upgrade -y && sudo apt install -y wget python3 bc bluetooth python3-pip libglib2.0-dev procmail libssl-dev rfkill
$ sudo pip3 install --upgrade bluepy garminconnect --break-system-packages
```
- Modify file `sudo nano /etc/systemd/system/bluetooth.target.wants/bluetooth.service`:
```
ExecStart=/usr/libexec/bluetooth/bluetoothd --experimental
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable:
```
$ wget https://github.com/RobertWojtowicz/export2garmin/archive/refs/heads/master.tar.gz -O - | tar -xz
$ cd export2garmin-master && sudo chmod 755 import_data.sh && sudo chmod 555 /etc/bluetooth
$ sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.13/dist-packages/bluepy/bluepy-helper
```

### 2.1.4. Configuring scripts
- First script is `user/import_tokens.py` is used to export Oauth1 and Oauth2 tokens of your account from Garmin Connect:
  - Script has support for login with or without MFA;
  - Once a year, tokens must be exported again, due to their expiration;
  - Repeat tokens export process for each user (if we have multiple users);
  - When you run `user/import_tokens.py`, you need to provide a login and password and possibly a code from MFA:
	```
	$ python3 /home/robert/export2garmin-master/user/import_tokens.py

	===============================================
	Export 2 Garmin Connect v3.0 (import_tokens.py)
	===============================================

	28.04.2024-11:58:44 * Login e-mail: email@email.com
	28.04.2024-11:58:50 * Enter password:
	28.04.2024-11:58:57 * MFA/2FA one-time code: 000000
	28.04.2024-11:59:17 * Oauth tokens saved correctly
	```
- Configuration is stored in `user/export2garmin.cfg` file (make changes e.g. via `sudo nano`):
  - Complete data in "miscale_export_user*" parameter sex, height in cm, birthdate in dd-mm-yyyy, Login e-mail, max_weight in kg, min_weight in kg;
  - To enable scale in Miscale module, set "on" in "switch_miscale" parameter;
  - Complete data in "ble_miscale_mac" parameter, which is related to MAC address of scale, if you don't know MAC address read section [2.1.1.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_BLE.md#211-getting-mac-address-of-mi-body-composition-scale-2--disable-weigh-small-object);
  - Configuration file contains many **other options**, check descriptions and use for your configuration.
- Second script `miscale/miscale_ble.py` has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ python3 /home/robert/export2garmin-master/miscale/miscale_ble.py

=============================================
Export 2 Garmin Connect v3.6 (miscale_ble.py)
=============================================

18.11.2023-23:23:30 * Checking if a BLE adapter is detected
18.11.2023-23:23:30 * BLE adapter hci0(00:00:00:00:00:00) detected, check BLE adapter connection
18.11.2023-23:23:30 * Connection to BLE adapter hci0(00:00:00:00:00:00) works, starting BLE scan:
  BLE device found with address: 00:00:00:00:00:00 <= target device
18.11.2023-23:23:34 MISCALE|OMRON * Reading BLE data complete, finished BLE scan
1672412076;58.4;521
```
- Third script `import_data.sh` has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/export2garmin-master/import_data.sh

=============================================
Export 2 Garmin Connect v3.6 (import_data.sh)
=============================================

18.07.2024-16:56:01 SYSTEM * Main process runs on PID: 000
18.07.2024-16:56:01 SYSTEM * Path to temp files: /dev/shm/
18.07.2024-16:56:01 SYSTEM * Path to user files: /home/robert/export2garmin-master/user/
18.07.2024-16:56:01 SYSTEM * BLE adapter is ON in export2garmin.cfg file, check if available
18.07.2024-16:56:01 SYSTEM * BLE adapter hci0(00:00:00:00:00:00) working, check if temp.log file exists
18.07.2024-16:56:01 SYSTEM * temp.log file exists, go to modules
18.07.2024-16:56:07 MISCALE|S400 * Module is ON in export2garmin.cfg file
18.07.2024-16:56:07 MISCALE|S400 * miscale_backup.csv file exists, checking for new data
18.07.2024-16:56:07 MISCALE|S400 * Importing data from a BLE adapter
18.07.2024-16:56:39 MISCALE|S400 * Saving import 1721076654 to miscale_backup.csv file
18.07.2024-16:56:40 MISCALE|S400 * Calculating data from import 1721314552, upload to Garmin Connect
18.07.2024-16:56:40 MISCALE|S400 * Data upload to Garmin Connect is complete
18.07.2024-16:56:40 MISCALE|S400 * Saving calculated data from import 1721314552 to miscale_backup.csv file
18.07.2024-16:56:40 OMRON * Module is OFF in export2garmin.cfg file
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /dev/shm/temp.log

================================================
Export 2 Garmin Connect v3.5 (miscale_export.py)
================================================

MISCALE * Import data: 1721076654;55.2;508
MISCALE * Calculated data: 15.07.2024;22:50;55.2;18.7;10.8;46.7;2.6;61.2;7;4;19;1217;51.1;64.4;to_gain:6.8;23.4;508;email@email.com;15.07.2024;23:00
MISCALE * Upload status: OK
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
sudo systemctl enable export2garmin.service && sudo systemctl start export2garmin.service
```
- You can check if export2garmin service works `sudo systemctl status export2garmin.service` or temporarily stop it with command `sudo systemctl stop export2garmin.service`;
- Checking running export2garmin service in a continuous loop: `sudo journalctl -u export2garmin.service -f` (process exit is Ctrl+C);
- Troubleshooting BLE adapters [2.6.2.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/about_BLE.md#262-troubleshooting-ble-adapters);
- Back to [README](https://github.com/RobertWojtowicz/export2garmin/blob/master/README.md).

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>