## 2.3. S400_BLE VERSION
- This module is based on following projects:
  - https://github.com/cyberjunky/python-garminconnect;
  - https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor;
  - https://github.com/Bluetooth-Devices/xiaomi-ble.

### 2.3.1. Getting MAC address and BLE KEY of Xiaomi Body Composition Scale S400
- Install Xiaomi Home App on your mobile device from Play Store;
- Create an account and register your scale in app (tested on Android 15);
- Take a measurement with scale using app (scale starts sending requested BLE advertisements);
- You should also synchronize scale using app after **replacing batteries**;
- Don't turn off heart rate measurement in app, otherwise scale will **not send data**;
- In order for export2garmin to successfully download data from scale, **app must be closed**, bluetooth icon should blink;
- A full measurement (weighing and heart rate) is required, otherwise scale will **not send data**;
- For Windows download latest version and run: https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/releases/latest/download/token_extractor.exe
- For Linux update your system and then install following packages:
```
$ sudo apt update && sudo apt full-upgrade -y && sudo apt install -y wget python3 bc bluetooth python3-pip libglib2.0-dev procmail libssl-dev libjpeg-dev
$ sudo pip3 install --upgrade bluepy garminconnect bleak xiaomi-ble requests pycryptodome charset-normalizer pillow --break-system-packages
```
- Download and extract to your home directory and run token_extractor.py (e.g. "/home/robert/"):
```
$ wget https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/releases/latest/download/token_extractor.zip
$ unzip token_extractor.zip && rm token_extractor.zip
$ cd token_extractor
$ python3 /home/robert/token_extractor/token_extractor.py
```
- Complete data according to script, use email address and password from your registered account in Xiaomi Home app, get BLE KEY and MAC:
```
Username (email or user ID):
email@email.com
Password:

Server (one of: cn, de, us, ru, tw, sg, in, i2) Leave empty to check all available:
de

Logging in...
Logged in.

Devices found for server "de" @ home "000000000000":
   ---------
   NAME:     Xiaomi Body Composition Scale S400
   ID:       000.0.0000000090000
   BLE KEY:  00000000000000000000000000000000
   MAC:      00:00:00:00:00:00
   TOKEN:    000000000000000000000000
   MODEL:    yunmai.scales.ms104
   ---------
```
- In some cases Xiaomi Cloud Tokens Extractor may ask you to enter a captcha code, **requires a graphical interface and a web browser**;
- BLE KEY is updated when a new profile in Xiaomi Home is connected to scale (they are replaced).

### 2.3.2. Preparing operating system
- Minimum hardware and software requirements are:
  - x86: 1vCPU, 1024MB RAM, 8GB disk space, network connection, Debian 12 operating system;
  - ARM: Minimum is Raspberry Pi Zero 2 W, 8GB disk space, Raspberry Pi OS operating system;
- Purchase a low-cost USB bluetooth adapter, **currently required** for synchronization to work, check from support matrix [2.6.1.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/about_BLE.md#261-ble-adapters-support-matrix);
- Update your system and then install following packages (if you have not done so in section [2.3.1.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/S400_BLE.md#231-getting-mac-address-and-ble-key-of-xiaomi-body-composition-scale-s400));
```
$ sudo apt update && sudo apt full-upgrade -y && sudo apt install -y wget python3 bc bluetooth python3-pip libglib2.0-dev procmail libssl-dev
$ sudo pip3 install --upgrade bluepy garminconnect bleak xiaomi-ble --break-system-packages
```
- Modify file `sudo nano /etc/systemd/system/bluetooth.target.wants/bluetooth.service`:
```
ExecStart=/usr/libexec/bluetooth/bluetoothd --experimental
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable:
```
$ wget https://github.com/RobertWojtowicz/export2garmin/archive/refs/heads/master.tar.gz -O - | tar -xz
$ cd export2garmin-master && sudo chmod 755 import_data.sh && sudo chmod 555 /etc/bluetooth
$ sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.11/dist-packages/bluepy/bluepy-helper
```

### 2.3.3. Configuring scripts
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
  - To enable scale in Miscale module, set "on" in "switch_s400" parameter;
  - Complete data in "ble_miscale_mac" and "ble_miscale_key" parameter, which is related to MAC address and BLE KEY of scale, if you don't know MAC address or BLE KEY read section [2.3.1.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/S400_BLE.md#231-getting-mac-address-and-ble-key-of-xiaomi-body-composition-scale-s400);
  - Configuration file contains many **other options**, check descriptions and use for your configuration.
- Second script `miscale/s400_ble.py` has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ python3 /home/robert/export2garmin-master/miscale/s400_ble.py

==========================================
Export 2 Garmin Connect v3.5 (s400_ble.py)
==========================================

28.06.2025-12:56:31 * Starting scan with BLE adapter hci0(00:1A:7D:DA:71:13):
  BLE device found with address: 1C:EA:AC:5D:A7:B0
28.06.2025-12:57:01 S400 * Reading BLE data complete, finished BLE scan
to_import;1751108221;58.1;509;468;79
```
- Third script `import_data.sh` has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/export2garmin-master/import_data.sh

=============================================
Export 2 Garmin Connect v3.5 (import_data.sh)
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
- If there is an error upload to Garmin Connect, data will be sent again on next execution (required disable BLE scanning, set switch_bt=off parameter in ```user/export2garmin.cfg file```)
- Upload errors and other operations are saved in temp.log file:
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
- Back to [README](https://github.com/RobertWojtowicz/export2garmin/blob/master/README.md).

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>