## Omron_BLE VERSION

### 2.3.1. Preparing operating system
- Minimum hardware and software requirements are:
  - x86: 1vCPU, 1024MB RAM, 8GB disk space, network connection, Debian 12 operating system;
  - ARM: 1CPU, 512MB RAM, 8GB disk space, network connection, Raspberry Pi OS | Debian 12 operating system.
- Update your system and then install following modules:
```
$ sudo apt update && sudo apt full-upgrade -y && sudo apt install -y wget python3 bc bluetooth python3-pip libglib2.0-dev procmail
$ sudo pip3 install --upgrade garminconnect bleak terminaltables --break-system-packages
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
- Configuration is stored in `user/export2garmin.cfg` file (make changes e.g. via `sudo nano`):
  - To enable Omron module, set "on" in "switch_omron" parameter;
  - You need to complete device model in "omron_omblepy_model" section, check out [Omron device support matrix](https://github.com/userx14/omblepy?tab=readme-ov-file#omron-device-support-matrix);
  - Put blood pressure monitor in pairing mode by pressing Bluetooth button for 3-5 seconds, You will see a flashing "P" on monitor;
  - Run `omron/omron_pairing.sh` find device starting with “BLEsmart_”, select ID and wait for pairing;
  - Fill in "omron_omblepy_mac" parameter in `user/export2garmin.cfg`, which is related to MAC address of Omron device (read during pairing, MAC column);
  - Additionally, you must complete data in "import_data_user*" section: login e-mail to Garmin Connect;
  - Optional one-time import of all Omron records, set "omron_omblepy_all" parameter to "on" (reads record by record every minute to prevent getting a temporary Garmin ban);
  - Optional omblepy debug mode for import_data.sh script, set "omron_omblepy_debug" parameter to "on".
- Second script is `user/import_tokens.py` is used to export Oauth1 and Oauth2 tokens of your account from Garmin Connect;
- Script `user/import_tokens.py` has support for login with or without MFA;
- Once a year, tokens must be exported again, due to their expiration;
- When you run `user/import_tokens.py` script, you need to provide a login and password and possibly a code from MFA:
```
$ python3 /home/robert/export2garmin-master/user/import_tokens.py
Export 2 Garmin Connect v1.0 (import_tokens.py)

28.04.2024-11:58:44 * Login e-mail: email@email.com
28.04.2024-11:58:50 * Enter password:
28.04.2024-11:58:57 * MFA/2FA one-time code: 000000
28.04.2024-11:59:17 * Oauth tokens saved correctly
```
- Script "import_data.sh" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/export2garmin-master/import_data.sh
Export 2 Garmin Connect v1.4 (import_data.sh)

17.07.2024-17:47:36 MISCALE * Module is off
17.07.2024-17:47:36 OMRON * Module is on
17.07.2024-17:47:36 OMRON * omron_backup.csv file exists, check if temp.log exists
17.07.2024-17:47:36 OMRON * temp.log file exists, checking for new data
17.07.2024-17:47:36 OMRON * Importing data from a BLE scanner
17.07.2024-17:47:48 OMRON * Prepare data for omron_backup.csv file
17.07.2024-17:47:49 OMRON * Data from import 1721231144 upload to Garmin Connect
17.07.2024-17:47:49 OMRON * Data upload to Garmin Connect is complete
17.07.2024-17:47:49 OMRON * Saving calculated data from import 1721231144 to omron_backup.csv file
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /dev/shm/temp.log
Export 2 Garmin Connect v1.0 (omron_export.py)

OMRON * Import data: 1721231144;email@email.com;17.07.2024;17:45;82;118;65;0;0
OMRON * Export date time: 17.07.2024;17:47
OMRON * Upload status: OK
```
- Finally, if everything works correctly add script import_data.sh as a service, make sure about path:
```
$ find / -name import_data.sh
/home/robert/export2garmin-master/import_data.sh
```
- To run it at system startup in an infinite loop, `sudo nano /etc/systemd/system/export2garmin.service` enter previously searched path to import_data.sh:
```
[Unit]
Description=Export2Garmin service
After=network.target

[Service]
Type=simple
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
- Purchase a cheap USB bluetooth 5.0/5.1 (tested on RTL8761B chipset, manufacturer Zexmte, works with Miscale and Omron module);
- Does not work with USB bluetooth 5.3 based on ATS2851 chipset;
- Bluetooth adapter should have a removable RP-SMA antenna;
- You will have option to change if standard RP-SMA antenna included with bluetooth adapter gives too little range;
- Download driver from Realtek repository https://github.com/Realtek-OpenSource:
```
wget https://github.com/Realtek-OpenSource/android_hardware_realtek/raw/rtk1395/bt/rtkbt/Firmware/BT/rtl8761b_fw
wget https://github.com/Realtek-OpenSource/android_hardware_realtek/raw/rtk1395/bt/rtkbt/Firmware/BT/rtl8761b_config
```
- Add USB chipset using passthrough mechanism (for performance and stability), connect USB bluetooth adapter;
- Assign USB chipset to virtual machine from hypevisor (tested on VMware ESXi 7/8);
- Create a folder and move driver to destination folder, restart virtual machine:
```
sudo mkdir /lib/firmware/rtl_bt
sudo mv rtl8761b_config /lib/firmware/rtl_bt/rtl8761bu_config.bin
sudo mv rtl8761b_fw /lib/firmware/rtl_bt/rtl8761bu_fw.bin
sudo reboot
```
- If you are using a Raspberry Pi, disable BLE internal module by adding a line in file `sudo nano /boot/config.txt`:
```
dtoverlay=disable-bt
```
- Sample photo with test configuration, on left Raspberry Pi 0W, on right server with virtual machine (stronger antenna added):

![alt text](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/usb.jpg)
- Back to [README](https://github.com/RobertWojtowicz/export2garmin/blob/master/README.md).

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>