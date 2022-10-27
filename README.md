# Mi Body Composition Scale 2 Garmin Connect

## 1. Introduction
- This project works only on Linux operating system, Windows is not supported;
- It is possible to run Linux operating system as a virtual machine on Windows;
- This project is based on following projects:
  - https://github.com/davidkroell/bodycomposition;
  - https://github.com/wiecosystem/Bluetooth;
  - https://github.com/lolouk44/xiaomi_mi_scale;
  - https://github.com/rando-calrissian/esp32_xiaomi_mi_2_hass;
- It allows Mi Body Composition Scale 2 (model: XMTZC05HM) to be fully automatically synchronized to Garmin Connect, following parameters:
  - BMI;
  - Body Fat;
  - Body Water;
  - Bone Mass;
  - Metabolic Age;
  - Physique Rating;
  - Skeletal Muscle Mass;
  - Time;
  - Visceral Fat;
  - Weight (**_NOTE:_ kg units only**);
- Synchronization diagram from Mi Body Composition Scale 2 to Garmin Connect:

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/pic/workflow.png)

## 2. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object
- Install Zepp Life App on your mobile device, user manual: https://files.xiaomi-mi.com/files/smart_scales/smart_scales-EN.pdf;
- Configure your scale with Zepp Life App on your mobile device (tested on Android 10/11/12);
- Retrieve scale's MAC Address from Zepp Life App (Profile > My devices > Mi Body Composition Scale 2);
- Turn off weigh small object in Zepp Life App (Profile > My devices > Mi Body Composition Scale 2) for better measurement quality:

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/pic/settings.png)

## 3. Setting correct date and time in Mi Body Composition Scale 2
- Launch Zepp Life App, go to scale (Profile > My devices > Mi Body Composition Scale 2);
- Start scale and select Clear data in App;
- Take a new weight measurement with App, App should synchronize date and time;
- 2 times a year it is necessary to perform synchronization due to change from winter to summer time and then vice versa. Another way is to change time offset in import_data.sh file (offset parameter);
- You should also synchronize scale after replacing batteries;
- Script import_data.sh detects same weighing done in less than 30 seconds (protection against duplicates);
- Script import_data.sh have time difference detection of more than 20 minutes (between scale data and os);
- If time is still not synchronized correctly, check NTP synchronization on server or change time offset in import_data.sh file (offset parameter).

## 4. BLE VERSION
### 4.1. How does this work?
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- USB bluetooth adapter or internal module (tested with bluetooth versions 4.0/4.1 and 5.0/5.1) scans for BLE device every 1 minute for 10 seconds and queries scale for data;
- Body weight and impedance data on server are appropriately processed by scripts;
- Processed data are sent by program bodycomposition to Garmin Connect;
- Raw and calculated data from scale is backed up on server in backup.csv file;
- backup.csv file can be imported e.g. for analysis into Excel.

### 4.2. Preparing Linux system
- How to run USB bluetooth adapter? read section [5. How to increase BLE range?](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/README.md#5-how-to-increase-ble-range-)
- Minimum hardware and software requirements are: 1CPU, 512MB RAM, 2GB disk space, network connection, Raspberry Pi OS or Debian operating system;
- Update your system and then install following modules:
```
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install wget python3 bluetooth python3-pip libglib2.0-dev -y
sudo pip install bluepy
```
- Modify file ```sudo nano /etc/systemd/system/bluetooth.target.wants/bluetooth.service```:
```
ExecStart=/usr/lib/bluetooth/bluetoothd --noplugin=sap
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable, choose correct version of boodycomposition depending on your operating system:
  - Raspberry Pi OS (ARM, 32-bit) use _Linux_armv6.tar.gz
  - Raspberry Pi OS (ARM, 64-bit) use _Linux_arm64.tar.gz
  - Debian (x86, 32-bit) use _Linux_i386.tar.gz
  - Debian (x86, 64-bit) use _Linux_x86_64.tar.gz
```
wget https://github.com/RobertWojtowicz/miscale2garmin/archive/refs/tags/4.tar.gz -O - | tar -xz
cd miscale2garmin-4
wget https://github.com/davidkroell/bodycomposition/releases/download/v1.7.0/bodycomposition_1.7.0_Linux_x86_64.tar.gz -O - | tar -xz bodycomposition
sudo chmod +x bodycomposition import_data.sh scanner_ble.py export_garmin.py
sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.9/dist-packages/bluepy/bluepy-helper
```

### 4.3. Configuring scripts
- First script is "scanner_ble.py", you need to complete data: "scale_mac_addr", which is related to MAC address of scale;
- Script "scanner_ble.py" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ python3 /home/robert/miscale2garmin-4/scanner_ble.py
Mi Body Composition Scale 2 Garmin Connect v4.8 (scanner_ble.py)

* Starting BLE scan:
  BLE device found with address: 3f:f1:3e:a6:4d:00, non-target device
  BLE device found with address: 42:db:e4:c4:5c:d4, non-target device
  BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
  BLE device found with address: 00:00:00:00:00:00 <= target device
* Reading BLE data complete, finished BLE scan
59.35;511;1654529140
```
- Second script is "export_garmin.py", you must complete data in "users" section: sex, height in cm, birthdate in dd-mm-yyyy, email and password to Garmin Connect, max_weight in kg, min_weight in kg;
- Script "export_garmin.py" supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect;
- Script "import_data.sh" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/miscale2garmin-4/import_data.sh
Mi Body Composition Scale 2 Garmin Connect v4.7 (import_data.sh)

* Backup.csv file exists, checking for new data
* Importing data from BLE device
* Saving import 1654529140 to backup.csv file
* Calculating data from import 1654529140, upload to Garmin Connect
* Data upload to Garmin Connect is complete
* Saving calculated data from import 1654529140 to backup.csv file
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /home/robert/miscale2garmin-4/temp.log
... uploading weight

Mi Body Composition Scale 2 Garmin Connect v4.6 (export_garmin.py)

* Import number: 1654529140
* Calculated data: email@email.com;2.63;20.06;14.66;58.54;22;48.02;6.00;6.19;2022-06-06 17:25:15
```
- Finally, if everything works correctly add script import_ble.sh to CRON to run it every 1 minute ```sudo crontab -e```:
```
*/1 * * * * /home/robert/miscale2garmin-4/import_data.sh
```

## 5. How to increase BLE range?
### 5.1. Common part for x86 and ARM architectures
- This section is an expansion of section [4. BLE VERSION](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/README.md#4-ble-version);
- Purchase a cheap USB bluetooth 5.0/5.1 adapter with external antenna (tested on RTL8761B chipset);
- Bluetooth adapter should have a removable RP-SMA antenna;
- You will have option to change if standard RP-SMA antenna included with bluetooth adapter gives too little range;
- Sometimes if you increase antenna range, scan time is too short to find your scale (too many devices around), you should increase scan_time parameter in scanner_ble.py script;
- Download driver from Realtek repository https://github.com/Realtek-OpenSource:
```
wget https://github.com/Realtek-OpenSource/android_hardware_realtek/raw/rtk1395/bt/rtkbt/Firmware/BT/rtl8761b_fw
wget https://github.com/Realtek-OpenSource/android_hardware_realtek/raw/rtk1395/bt/rtkbt/Firmware/BT/rtl8761b_config
```

### 5.2. Virtual machine
- Add USB chipset using passthrough mechanism (for performance and stability), connect USB bluetooth adapter;
- Assign USB chipset to virtual machine from hypevisor (tested on VMware ESXi 7/8);
- Create a folder and move driver to destination folder, restart virtual machine:
```
sudo mkdir /lib/firmware/rtl_bt
sudo mv rtl8761b_config /lib/firmware/rtl_bt/rtl8761b_config.bin
sudo mv rtl8761b_fw /lib/firmware/rtl_bt/rtl8761b_fw.bin
sudo reboot
```

### 5.3. Raspberry Pi Zero W
- Purchase an OTG cable (micro USB male to USB Type-A female), connect bluetooth to Raspberry Pi Zero W;
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
- Sample photo with test configuration, on left Raspberry Pi Zero W, on right server with virtual machine (stronger antenna added):

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/pic/rtl8761b.jpg)

## 6. ESP32 VERSION
### 6.1. How does this work?
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- ESP32 module operates in a deep sleep and wakes up every 7 minutes, scans for BLE device for 10 seconds and queries scale for data, process can be started immediately via reset button;
- ESP32 module sends acquired data via MQTT protocol to MQTT broker installed on server;
- Body weight and impedance data on server are appropriately processed by scripts;
- Processed data are sent by program bodycomposition to Garmin Connect;
- Raw and calculated data from scale is backed up on server in backup.csv file;
- backup.csv file can be imported e.g. for analysis into Excel.

### 6.2. ESP32 configuration (bluetooth gateway to WiFi/MQTT)
- Use Arduino IDE to compile and upload software to ESP32, following board and libraries required:
  - Arduino ESP32: https://github.com/espressif/arduino-esp32;
  - Battery 18650 Stats: https://github.com/danilopinotti/Battery18650Stats;
  - PubSubClient: https://github.com/knolleary/pubsubclient;
  - Timestamps: https://github.com/alve89/Timestamps;
- How to install board and library in Arduino IDE?:
  - board (**_NOTE:_ use version 1.0.4, newer is unstable**): https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html;
  - libraries: https://www.arduino.cc/en/Guide/Libraries;
- Preparing Arduino IDE to upload project to ESP32, go to Tools and select:
  - Board: > ESP32 Arduino > "WEMOS LOLIN32";
  - Upload Speed: "921600";
  - CPU Frequency: > "80MHz (WiFi / BT)" for better energy saving;
  - Flash Frequency: "80Mhz";
  - Partition Scheme: > "No OTA (Large APP)";
  - Port: > "COM" on which ESP32 board is detected;
- Following information must be entered before compiling code (esp32.ino) in Arduino IDE:
  - mac address of scale read from Zepp Life App ("scale_mac_addr");
  - parameters of your WiFi network ("ssid", "password");
  - other settings ("led_pin", "Battery18650Stats");
  - connection parameters MQTT ("mqtt_server", "mqtt_port", "mqtt_userName", "mqtt_userPass");
- Debug and or comments:
  - Project is prepared to work with ESP32 board with charging module (red LED indicates charging). I based my version on Li-ion 18650 battery;
  - Program for ESP32 has implemented UART debug mode (baud rate must be set to 115200), you can verify if everything is working properly:
  ```
  Mi Body Composition Scale 2 Garmin Connect v4.4 (esp32.ino)
  
  * Starting BLE scan:
   BLE device found with address: 3f:f1:3e:a6:4d:00, non-target device
   BLE device found with address: 42:db:e4:c4:5c:d4, non-target device
   BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
   BLE device found with address: 00:00:00:00:00:00 <= target device
  * Reading BLE data complete, finished BLE scan
  * Connecting to WiFi: connected
   IP address: 192.168.4.18
  * Connecting to MQTT: connected
  * Publishing MQTT data: 59.35;511;1654529140
  * Waiting for next scan, going to sleep
  ```
  - After switching device on, blue LED will light up for a moment to indicate that module has started successfully;
  - If data are acquired correctly in next step, blue LED will flash for a moment 2 times;
  - If there is an error, e.g. data is incomplete, no connection to WiFi network or MQTT broker, blue LED will light up for 5 seconds;
  - Program implements voltage measurement and battery level, which are sent toger with scale data in topic MQTT;
  - Device has 2 buttons, first green is reset button (monostable), red is battery power switch (bistable);
- Sample photo of finished module with ESP32 (Wemos LOLIN D32 Pro) and Li-ion 18650 battery (LG 3600mAh, LGDBM361865):

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/pic/esp32.jpg)

### 6.3. Preparing Linux system
- Minimum hardware and software requirements are: 1CPU, 512MB RAM, 2GB disk space, network connection, Raspberry Pi OS or Debian operating system;
- Update your system and then install following modules:
```
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install wget python3 mosquitto mosquitto-clients -y
```
- You need to set up a password for MQTT (password must be same as in ESP32): ```sudo mosquitto_passwd -c /etc/mosquitto/passwd admin```;
- Create a configuration file for Mosquitto: ```sudo nano /etc/mosquitto/mosquitto.conf``` and enter following parameters:
```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable, choose correct version of boodycomposition depending on your operating system:
  - Raspberry Pi OS (ARM, 32-bit) use _Linux_armv6.tar.gz
  - Raspberry Pi OS (ARM, 64-bit) use _Linux_arm64.tar.gz
  - Debian (x86, 32-bit) use _Linux_i386.tar.gz
  - Debian (x86, 64-bit) use _Linux_x86_64.tar.gz
```
wget https://github.com/RobertWojtowicz/miscale2garmin/archive/refs/tags/4.tar.gz -O - | tar -xz
cd miscale2garmin-4
wget https://github.com/davidkroell/bodycomposition/releases/download/v1.7.0/bodycomposition_1.7.0_Linux_x86_64.tar.gz -O - | tar -xz bodycomposition
sudo chmod +x bodycomposition import_data.sh export_garmin.py
```

### 6.4. Configuring scripts
- First script is "import_data.sh", you need to complete data: "user", "password" which are related to MQTT broker, "mqtt" set to "on";
- Second script is "export_garmin.py", you must complete data in "users" section: "sex", "height" in cm, "birthdate" in dd-mm-yyyy, "email" and "password" to Garmin Connect, "max_weight" in kg, "min_weight" in kg;
- Script "export_garmin.py" supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect;
- Script "import_data.sh" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/miscale2garmin-4/import_data.sh
Mi Body Composition Scale 2 Garmin Connect v4.7 (import_data.sh)

* Backup.csv file exists, checking for new data
* Importing data from MQTT broker
* Saving import 1654529140 to backup.csv file
* Calculating data from import 1654529140, upload to Garmin Connect
* Data upload to Garmin Connect is complete
* Saving calculated data from import 1654529140 to backup.csv file
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /home/robert/miscale2garmin-4/temp.log
... uploading weight

Mi Body Composition Scale 2 Garmin Connect v4.6 (export_garmin.py)

* Import number: 1654529140
* Calculated data: email@email.com;2.63;20.06;14.66;58.54;22;48.02;6.00;6.19;2022-06-06 17:25:15
```
- Finally, if everything works correctly add script import_mqtt.sh to CRON to run it every 1 minute ```sudo crontab -e```:
```
*/1 * * * * /home/robert/miscale2garmin-4/import_data.sh
```

## 7. Mobile App
I don't plan to create a mobile app, but I encourage you to take advantage of another project: https://github.com/lswiderski/mi-scale-exporter

<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
