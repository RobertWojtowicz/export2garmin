## 4.1. ARM_BLE VERSION
### 4.1.1. Preparing operating system
- How to run USB bluetooth adapter on a Raspberry Pi Zero W? read section [4.1.3. How to increase BLE range](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/ARM_ble.md#413-how-to-increase-ble-range)
- Minimum hardware and software requirements are: 1CPU, 512MB RAM, 2GB disk space, network connection, Raspberry Pi OS | Debian 11 operating system;
- Update your system and then install following modules:
```
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install wget python3 bc bluetooth python3-pip libglib2.0-dev -y
sudo pip install bluepy
```
- Modify file ```sudo nano /etc/systemd/system/bluetooth.target.wants/bluetooth.service```:
```
ExecStart=/usr/lib/bluetooth/bluetoothd --noplugin=sap
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable, choose correct version of boodycomposition depending on your operating system:
  - Raspberry Pi OS | Debian 11 (32-bit) use _Linux_armv6.tar.gz
  - Raspberry Pi OS | Debian 11 (64-bit) use _Linux_arm64.tar.gz
```
wget https://github.com/RobertWojtowicz/miscale2garmin/archive/refs/tags/5.tar.gz -O - | tar -xz
cd miscale2garmin-5
wget https://github.com/davidkroell/bodycomposition/releases/download/v1.7.0/bodycomposition_1.7.0_Linux_x86_64.tar.gz -O - | tar -xz bodycomposition
sudo chmod 755 bodycomposition import_data.sh scanner_ble.py export_garmin.py
sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.9/dist-packages/bluepy/bluepy-helper
```

### 4.1.2. Configuring scripts
- First script is "scanner_ble.py", you need to complete data: "scale_mac_addr", which is related to MAC address of scale, if you don't know MAC address read section [2. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object](https://github.com/RobertWojtowicz/miscale2garmin/tree/master#2-getting-mac-address-of-mi-body-composition-scale-2--disable-weigh-small-object);
- If you have multiple BLE devices, check which device should scan scale with command ```sudo hcitool dev``` and set hci_num parameter in "scanner_ble.py" script;
- Script "scanner_ble.py" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ python3 /home/robert/miscale2garmin-5/scanner_ble.py
Mi Body Composition Scale 2 Garmin Connect v5.3 (scanner_ble.py)

* Starting BLE scan:
  BLE device found with address: 3f:f1:3e:a6:4d:00, non-target device
  BLE device found with address: 42:db:e4:c4:5c:d4, non-target device
  BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
  BLE device found with address: 00:00:00:00:00:00 <= target device
* Reading BLE data complete, finished BLE scan
1672412076;58.4;521
```
- Second script is "export_garmin.py", you must complete data in "users" section: sex, height in cm, birthdate in dd-mm-yyyy, email and password to Garmin Connect, max_weight in kg, min_weight in kg;
- Script "export_garmin.py" supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect;
- Script "import_data.sh" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/miscale2garmin-5/import_data.sh
Mi Body Composition Scale 2 Garmin Connect v5.5 (import_data.sh)

* backup.csv file exists, check if temp.log exists
* temp.log file exists, checking for new data
* Importing data from a BLE scanner
* Saving import 1672412076 to backup.csv file
* Calculating data from import 1672412076, upload to Garmin Connect
* Data upload to Garmin Connect is complete
* Saving calculated data from import 1672412076 to backup.csv file
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /home/robert/miscale2garmin-5/temp.log
... uploading weight

Mi Body Composition Scale 2 Garmin Connect v5.3 (export_garmin.py)

* Import data: 1672412076;58.1;526
* Calculated data: 07.01.2023;19:09;58.1;19.6;13.8;47.5;2.6;59.2;7;6;22;526;email@email.com;07.01.2023;19:21
```
- Finally, if everything works correctly add script import_ble.sh to CRON to run it every 1 minute ```sudo crontab -e```:
```
*/1 * * * * /home/robert/miscale2garmin-5/import_data.sh
```

### 4.1.3. How to increase BLE range
- Purchase a cheap USB bluetooth 5.0/5.1 adapter with external antenna (tested on RTL8761B chipset, manufacturer Zexmte);
- Purchase an OTG cable (micro USB male to USB Type-A female), connect bluetooth to Raspberry Pi Zero W;
- Bluetooth adapter should have a removable RP-SMA antenna;
- You will have option to change if standard RP-SMA antenna included with bluetooth adapter gives too little range;
- Sometimes if you increase antenna range, scan time is too short to find your scale (too many devices around), you should increase scan_time parameter in scanner_ble.py script;
- RTL8761B chipset has no native support in Raspberry Pi OS | Debian 11, driver needed, download from Realtek repository: https://github.com/Realtek-OpenSource:
```
wget https://github.com/Realtek-OpenSource/android_hardware_realtek/raw/rtk1395/bt/rtkbt/Firmware/BT/rtl8761b_fw
wget https://github.com/Realtek-OpenSource/android_hardware_realtek/raw/rtk1395/bt/rtkbt/Firmware/BT/rtl8761b_config
```
- Disable BLE internal module by adding a line in file ```sudo nano /boot/config.txt```:
```
dtoverlay=disable-bt
```
- Move to destination folder (add an extra letter "u" in driver name), restart Raspberry Pi Zero W:
```
sudo mv rtl8761b_config /lib/firmware/rtl_bt/rtl8761bu_config.bin
sudo mv rtl8761b_fw /lib/firmware/rtl_bt/rtl8761bu_fw.bin
sudo reboot
```
- Sample photo with test configuration, on left Raspberry Pi Zero W:

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/usb.jpg)

### If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>