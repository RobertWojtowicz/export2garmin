## 4.1. x86_BLE VERSION
### 4.1.1. Preparing operating system
- Minimum hardware and software requirements are: 1vCPU, 1024MB RAM, 8GB disk space, network connection, Debian 12 operating system;
- Update your system and then install following modules:
```
$ sudo apt-get update && sudo apt-get upgrade -y
$ sudo apt-get install wget python3 bc bluetooth python3-pip libglib2.0-dev -y
$ sudo pip3 install --upgrade bluepy garminconnect --break-system-packages
```
- Modify file ```sudo nano /etc/systemd/system/bluetooth.target.wants/bluetooth.service```:
```
ExecStart=/usr/lib/bluetooth/bluetoothd --noplugin=sap --experimental
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable:
```
$ wget https://github.com/RobertWojtowicz/miscale2garmin/archive/refs/tags/7.tar.gz -O - | tar -xz
$ cd miscale2garmin-7
$ sudo chmod 755 import_tokens.py import_data.sh scanner_ble.py export_garmin.py
$ sudo chmod 555 /etc/bluetooth
$ sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.11/dist-packages/bluepy/bluepy-helper
```

### 4.1.2. Configuring scripts
- First script is "scanner_ble.py", you need to complete data: "scale_mac_addr", which is related to MAC address of scale, if you don't know MAC address read section [2. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object](https://github.com/RobertWojtowicz/miscale2garmin/tree/master#2-getting-mac-address-of-mi-body-composition-scale-2--disable-weigh-small-object);
- If you have multiple BLE devices, check which device should scan scale with command ```sudo hcitool dev``` and set hci_num parameter in "scanner_ble.py" script;
- Script "scanner_ble.py" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ python3 /home/robert/miscale2garmin-7/scanner_ble.py
Mi Body Composition Scale 2 Garmin Connect v7.2 (scanner_ble.py)

18.11.2023-23:23:30 * Starting BLE scan:
  BLE device found with address: 3f:f1:3e:a6:4d:00, non-target device
  BLE device found with address: 42:db:e4:c4:5c:d4, non-target device
  BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
  BLE device found with address: 00:00:00:00:00:00 <= target device
18.11.2023-23:23:34 * Reading BLE data complete, finished BLE scan
1672412076;58.4;521
```
- Second script is "import_tokens.py" is used to export Oauth1 and Oauth2 tokens of your account from Garmin Connect;
- Script "import_tokens.py" has support for login with or without MFA/2FA;
- Once a year, tokens must be exported again, due to their expiration;
- When you run "import_tokens.py" script, you need to provide a login and password and possibly a code from MFA/2FA:
```
$ python3 /home/robert/miscale2garmin-7/import_tokens.py
Mi Body Composition Scale 2 Garmin Connect v7.2 (import_tokens.py)

28.04.2024-11:58:44 * Login e-mail: email@email.com
28.04.2024-11:58:50 * Enter password:
28.04.2024-11:58:57 * MFA/2FA one-time code: 000000
28.04.2024-11:59:17 * Oauth tokens saved correctly
```
- Third script is "export_garmin.py", you must complete data in "users" section: sex, height in cm, birthdate in dd-mm-yyyy and login e-mail to Garmin Connect, max_weight in kg, min_weight in kg;
- Script "export_garmin.py" supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect;
- Script "import_data.sh" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/miscale2garmin-7/import_data.sh
Mi Body Composition Scale 2 Garmin Connect v7.4 (import_data.sh)

18.11.2023-22:49:58 * backup.csv file exists, check if temp.log exists
18.11.2023-22:49:58 * temp.log file exists, checking for new data
18.11.2023-22:49:58 * Importing data from a BLE scanner
18.11.2023-22:50:01 * Saving import 1700344090 to backup.csv file
18.11.2023-22:50:06 * Calculating data from import 1700344090, upload to Garmin Connect
18.11.2023-22:50:06 * Data upload to Garmin Connect is complete
18.11.2023-22:50:06 * Saving calculated data from import 1700344090 to backup.csv file
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /home/robert/miscale2garmin-7/temp.log
Mi Body Composition Scale 2 Garmin Connect v7.4 (export_garmin.py)

* Import data: 1672412076;58.1;526
* Calculated data: 09.05.2024;12:29;55.9;18.9;12.5;46.4;2.5;60.1;7;5;24;1228;50.7;64.4;to_gain:5.9;23.0;589;email@email.com;09.05.2024;12:31
```
- Finally, if everything works correctly add script import_ble.sh to CRON to run it every 1 minute ```sudo crontab -e```:
```
*/1 * * * * /home/robert/miscale2garmin-7/import_data.sh
```

### 4.1.3. How to increase BLE range
- Purchase a cheap USB bluetooth 5.3 adapter with external antenna (tested on ATS2851 chipset, manufacturer Zexmte);
- Bluetooth adapter should have a removable RP-SMA antenna;
- You will have option to change if standard RP-SMA antenna included with bluetooth adapter gives too little range;
- Sometimes if you increase antenna range, scan time is too short to find your scale (too many devices around), you should increase scan_time parameter in scanner_ble.py script;
- ATS2851 chipset has native support in Debian 12 operating system no additional driver needed;
- Add USB chipset using passthrough mechanism (for performance and stability), connect USB bluetooth adapter;
- Assign USB chipset to virtual machine from hypevisor (tested on VMware ESXi 7/8);
- Sample photo with test configuration, on right server with virtual machine (stronger antenna added):

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/usb.jpg)

### If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>