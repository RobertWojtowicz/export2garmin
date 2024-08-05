## 2.1. Miscale_BLE VERSION

### 2.1.1. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object
- Install Zepp Life App on your mobile device from Play Store;
- Configure your scale with Zepp Life App on your mobile device (tested on Android 10-14);
- Retrieve scale's MAC address from Zepp Life App (Profile > My devices > Mi Body Composition Scale 2);
- Turn off weigh small object in Zepp Life App (Profile > My devices > Mi Body Composition Scale 2) for better measurement quality.

### 2.1.2. Setting correct date and time in Mi Body Composition Scale 2
- Launch Zepp Life App, go to scale (Profile > My devices > Mi Body Composition Scale 2);
- Start scale and select Clear data in App;
- Take a new weight measurement with App, App should synchronize date and time (UTC);
- Script import_data.sh detects time zone and includes this as a time offset;
- If time is still not synchronized correctly, check NTP synchronization on server or change time offset in `user/export2garmin.cfg` file ("miscale_offset" parameter);
- You should also synchronize scale after replacing batteries;
- Script import_data.sh detects same weighing done in less than 30 seconds (protection against duplicates);
- Script import_data.sh have time difference detection of more than 20 minutes (between scale data and os).

### 2.1.3. Preparing operating system
- Minimum hardware and software requirements are:
  - x86: 1vCPU, 1024MB RAM, 8GB disk space, network connection, Debian 12 operating system;
  - ARM: 1CPU, 512MB RAM, 8GB disk space, network connection, Raspberry Pi OS | Debian 12 operating system.
- Update your system and then install following modules:
```
$ sudo apt update && sudo apt full-upgrade -y && sudo apt install -y wget python3 bc bluetooth python3-pip libglib2.0-dev procmail
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
$ sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.11/dist-packages/bluepy/bluepy-helper
```

### 2.1.4. Configuring scripts
- Configuration is stored in `user/export2garmin.cfg` file (make changes e.g. via `sudo nano`):
  - To enable Miscale module, set "on" in "switch_miscale" parameter;
  - Fill in "miscale_ble_mac" parameter, which is related to MAC address of scale, if you don't know MAC address read section [2.1.1.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_BLE.md#211-getting-mac-address-of-mi-body-composition-scale-2--disable-weigh-small-object);
  - If you have multiple BLE devices, check which device should scan scale with command `sudo hcitool dev` and set "miscale_ble_hci" parameter;
  - Additionally, you must complete data in "miscale_export_user*" section: sex, height in cm, birthdate in dd-mm-yyyy and login e-mail to Garmin Connect, max_weight in kg, min_weight in kg.
- Script `miscale/miscale_ble.py` has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ python3 /home/robert/export2garmin-master/miscale/miscale_ble.py
Export 2 Garmin Connect v1.0 (miscale_ble.py)

18.11.2023-23:23:30 * Starting BLE scan:
  BLE device found with address: 3f:f1:3e:a6:4d:00, non-target device
  BLE device found with address: 42:db:e4:c4:5c:d4, non-target device
  BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
  BLE device found with address: 00:00:00:00:00:00 <= target device
18.11.2023-23:23:34 * Reading BLE data complete, finished BLE scan
1672412076;58.4;521
```
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

15.07.2024-23:00:11 MISCALE * Module is on
15.07.2024-23:00:11 MISCALE * miscale_backup.csv file exists, check if temp.log exists
15.07.2024-23:00:11 MISCALE * temp.log file exists, checking for new data
15.07.2024-23:00:11 MISCALE * Importing data from a BLE scanner
15.07.2024-23:00:12 MISCALE * Saving import 1721076654 to miscale_backup.csv file
15.07.2024-23:00:16 MISCALE * Calculating data from import 1721076654, upload to Garmin Connect
15.07.2024-23:00:16 MISCALE * Data upload to Garmin Connect is complete
15.07.2024-23:00:16 MISCALE * Saving calculated data from import 1721076654 to miscale_backup.csv file
15.07.2024-23:00:16 OMRON * Module is off
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /dev/shm/temp.log
Export 2 Garmin Connect v1.3 (miscale_export.py)

MISCALE * Import data: 1721076654;55.2;508
MISCALE * Calculated data: 15.07.2024;22:50;55.2;18.7;10.8;46.7;2.6;61.2;7;4;19;1217;51.1;64.4;to_gain:6.8;23.4;508;email@email.com;15.07.2024;23:00
MISCALE * Upload status: OK
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
sudo systemctl enable export2garmin.service && sudo systemctl start export2garmin.service
```
- You can check if export2garmin service works `sudo systemctl status export2garmin.service` or temporarily stop it with command `sudo systemctl stop export2garmin.service`.

### 2.1.5. How to increase BLE range
- Purchase a cheap USB bluetooth:
  - 5.0/5.1 (tested on RTL8761B chipset, manufacturer Zexmte, works with Miscale and Omron module);
  - 5.3 (tested on ATS2851 chipset, manufacturer Zexmte, works only with Miscale module).
- Bluetooth adapter should have a removable RP-SMA antenna;
- You will have option to change if standard RP-SMA antenna included with bluetooth adapter gives too little range;
- Sometimes if you increase antenna range, scan time is too short to find your scale (too many devices around), you should increase scan_time parameter in scanner_ble.py script;
- ATS2851 chipset has native support in Debian 12 operating system no additional driver needed;
- RTL8761B chipset requires driver download from Realtek repository: https://github.com/Realtek-OpenSource:
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

## 3. Mobile App
I don't plan to create a mobile app, but I encourage you to take advantage of another projects:
- Android: https://github.com/lswiderski/mi-scale-exporter;
- iOS | iPadOS: https://github.com/lswiderski/WebBodyComposition.

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>