# Mi Body Composition Scale 2 Garmin Connect

## 1. Introduction
- This project is based on the following projects:
  - https://github.com/davidkroell/bodycomposition;
  - https://github.com/wiecosystem/Bluetooth;
  - https://github.com/lolouk44/xiaomi_mi_scale;
  - https://github.com/rando-calrissian/esp32_xiaomi_mi_2_hass;
- It allows the Mi Body Composition Scale 2 (model: XMTZC05HM) to be fully automatically synchronized to Garmin Connect, the following parameters:
  - BMI;
  - Body Fat;
  - Body Water;
  - Bone Mass;
  - Metabolic Age;
  - Physique Rating;
  - Skeletal Muscle Mass;
  - Time;
  - Visceral Fat;
  - Weight **_(kg units only)_**;
- Synchronization diagram from Mi Body Composition Scale 2 to Garmin Connect:

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/pic/workflow.png)

## 2. Getting the MAC address of Mi Body Composition Scale 2
- Install Xiaomi Mi Fit App on your mobile device, user manual: https://files.xiaomi-mi.com/files/smart_scales/smart_scales-EN.pdf;
- Configure your scale with Xiaomi Mi Fit App on your mobile device (tested on Android 10 and 11);
- Retrieve scale's MAC Address from Xiaomi Mi Fit App (go to Profile > My devices > Mi Body Composition Scale 2):

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/pic/mac_addr.png)

## 3. BLE VERSION
### 3.1. How does this work ?
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- USB bluetooth device (or internal e.g. Raspberry Pi, tested with USB bluetooth versions 4.0 and 5.0) scans for BLE device every 1 minute for 20 seconds and queries scale for data;
- Body weight and impedance data on the server are appropriately processed by scripts;
- Processed data are sent by the program bodycomposition to Garmin Connect;
- Raw data from the scale is backed up on the server in backup.csv file;
- backup.csv file can be imported e.g. for analysis into Excel.

### 3.2. Preparing Linux system
- I based on a virtual machine with Debian (tested on 10 and 11). I prefer the minimal version with an ssh server (Net Install);
- Minimum hardware requirements are: 1 CPU, 512 MB RAM, 2 GB HDD, network connection;
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
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable (note: choose correct version of boodycomposition depending on your computer, e.g. "_Linux_x86_64.tar.gz"):
```
wget https://github.com/RobertWojtowicz/miscale2garmin/archive/refs/tags/3.0.tar.gz -O - | tar -xz
cd miscale2garmin-3.0
wget https://github.com/davidkroell/bodycomposition/releases/download/v1.6.2/bodycomposition_1.6.2_Linux_x86_64.tar.gz -O - | tar -xz bodycomposition
chmod +x bodycomposition import_ble.sh scanner_ble.py export_garmin.py
```

### 3.3. Configuring scripts
- First script is "scanner_ble.py", you need to complete data: "scale_mac_addr", which is related to the MAC address of the scale;
- Script "scanner_ble.py" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ python3 /home/robert/miscale2garmin-3.0/scanner_ble.py
Mi Body Composition Scale 2 Garmin Connect v3.0 (scanner_ble.py)

* Starting BLE scan:
   BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
   BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
   BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
   BLE device found with address: 00:00:00:00:00:00 <= target device
   BLE device found with address: 00:00:00:00:00:00 <= target device
   BLE device found with address: 00:00:00:00:00:00 <= target device
* Reading BLE data complete, finished BLE scan
62.60;576;1643612352;2022-1-31 7:59:12
```
- Second script is "export_garmin.py", you must complete data in the "users" section: sex, height in cm, birthdate in dd-mm-yyyy, email and password to Garmin Connect, max_weight in kg, min_weight in kg;
- Script "export_garmin.py" supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect;
- Script "import_ble.sh" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/miscale2garmin-3.0/import_ble.sh
Mi Body Composition Scale 2 Garmin Connect v3.0 (import_ble.sh)

* Data backup file exists, checking for new data
* Importing and calculating data to upload
* Data upload to Garmin Connect is complete
```
- If there is an error upload to Garmin Connect, data will be sent again on the next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /home/robert/miscale2garmin-3.0/temp.log
... uploading weight
Mi Body Composition Scale 2 Garmin Connect v3.0 (export_garmin.py)
Processed file: 1641199035.tlog
```
- Finally, if everything works correctly add script import_ble.sh to CRON to run it every 1 minute ```sudo crontab -e```:
```
*/1 * * * * /home/robert/miscale2garmin-3.0/import_ble.sh
```

## 4. ESP32 VERSION
### 4.1. How does this work ?
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- ESP32 module operates in a deep sleep and wakes up every 7 minutes, scans for BLE device for 20 seconds and queries scale for data, process can be started immediately via the reset button;
- ESP32 module sends the acquired data via the MQTT protocol to the MQTT broker installed on the server;
- Body weight and impedance data on the server are appropriately processed by scripts;
- Processed data are sent by the program bodycomposition to Garmin Connect;
- Raw data from the scale is backed up on the server in backup.csv file;
- backup.csv file can be imported e.g. for analysis into Excel.

### 4.2. ESP32 configuration (bluetooth gateway to WiFi/MQTT)
- Use Arduino IDE to compile and upload software to ESP32, following board and libraries required:
  - Arduino ESP32: https://github.com/espressif/arduino-esp32;
  - Battery 18650 Stats: https://github.com/danilopinotti/Battery18650Stats;
  - PubSubClient: https://github.com/knolleary/pubsubclient;
  - Timestamps: https://github.com/alve89/Timestamps;
- How to install board and library in Arduino IDE?:
  - board **(_WARNING_, use version 1.0.4, newer is unstable)**: https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html;
  - libraries: https://www.arduino.cc/en/Guide/Libraries;
- Preparing Arduino IDE to upload the project to ESP32, go to Tools and select:
  - Board: > ESP32 Arduino > "WEMOS LOLIN32";
  - CPU Frequency: > "80MHz (WiFi / BT)" for better energy saving;
  - Partition Scheme: > "No OTA (Large APP)";
  - Port: > "COM" on which ESP32 board is detected;
- The following information must be entered before compiling code (esp32.ino) in Arduino IDE:
  - mac address of the scale read from Xiaomi Mi Fit App ("scale_mac_addr");
  - parameters of your WiFi network ("ssid", "password");
  - other settings ("led_pin", "Timestamps", "Battery18650Stats");
  - connection parameters MQTT ("mqtt_server", "mqtt_port", "mqtt_userName", "mqtt_userPass");
- Debug and other comments:
  - Project is prepared to work with the ESP32 board with the charging module (red LED indicates charging). I based my version on the Li-ion 18650 battery;
  - Program for ESP32 has implemented UART debug mode (baud rate must be set to 115200), you can verify if everything is working properly:
  ```
  Mi Body Composition Scale 2 Garmin Connect v3.0 (esp32.ino)
  
  * Starting BLE scan:
    BLE device found with address: 3f:f1:3e:a6:4d:00, non-target device
    BLE device found with address: 42:db:e4:c4:5c:d4, non-target device
    BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
    BLE device found with address: 00:00:00:00:00:00 <= target device
  * Reading BLE data complete, finished BLE scan
  * Connecting to WiFi: connected
    IP address: 192.168.4.18
  * Connecting to MQTT: connected
  * Publishing MQTT data: 63.85;583;1641241525;2022-1-3 21:25:25;3.48;5
  * Waiting for next scan, going to sleep
  ```
  - After switching the device on, blue LED will light up for a moment to indicate that the module has started successfully;
  - If the data are acquired correctly in the next step, blue LED will flash for a moment 2 times;
  - If there is an error, e.g. the data is incomplete, no connection to the WiFi network or the MQTT broker, blue LED will light up for 5 seconds;
  - Program implements voltage measurement and battery level, which are sent together with the scale data in topic MQTT;
  - Device has 2 buttons, the first green is the reset button (monostable), the red one is the battery power switch (bistable).

Sample photo of the finished module with ESP32 (Wemos LOLIN D32 Pro) and Li-ion 18650 battery (LG 3600mAh, LGDBM361865):

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/pic/esp32.jpg)

### 4.3. Preparing Linux system
- I based on a virtual machine with Debian (tested on 10 and 11). I prefer the minimal version with an ssh server (Net Install);
- Minimum hardware requirements are: 1 CPU, 512 MB RAM, 2 GB HDD, network connection;
- Update your system and then install following modules:
```
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install wget python3 mosquitto mosquitto-clients -y
```
- You need to set up a password for MQTT (password must be the same as in ESP32): ```sudo mosquitto_passwd -c /etc/mosquitto/passwd admin```;
- Create a configuration file for Mosquitto: ```sudo nano /etc/mosquitto/mosquitto.conf``` and enter the following parameters:
```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable (note: choose correct version of boodycomposition depending on your computer, e.g. "_Linux_x86_64.tar.gz"):
```
wget https://github.com/RobertWojtowicz/miscale2garmin/archive/refs/tags/3.0.tar.gz -O - | tar -xz
cd miscale2garmin-3.0
wget https://github.com/davidkroell/bodycomposition/releases/download/v1.6.2/bodycomposition_1.6.2_Linux_x86_64.tar.gz -O - | tar -xz bodycomposition
chmod +x bodycomposition import_mqtt.sh export_garmin.py
```

### 4.4. Configuring scripts
- First script is "import_mqtt.sh", you need to complete data: "user", "passwd", which are related to the MQTT broker;
- Second script is "export_garmin.py", you must complete data in the "users" section: sex, height in cm, birthdate in dd-mm-yyyy, email and password to Garmin Connect, max_weight in kg, min_weight in kg;
- Script "export_garmin.py" supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect;
- Script "import_mqtt.sh" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/miscale2garmin-3.0/import_mqtt.sh
Mi Body Composition Scale 2 Garmin Connect v3.0 (import_mqtt.sh)

* Data backup file exists, checking for new data
* Importing and calculating data to upload
* Data upload to Garmin Connect is complete
```
- If there is an error upload to Garmin Connect, data will be sent again on the next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /home/robert/miscale2garmin-3.0/temp.log
... uploading weight
Mi Body Composition Scale 2 Garmin Connect v3.0 (export_garmin.py)
Processed file: 1641199035.tlog
```
- Finally, if everything works correctly add script import_mqtt.sh to CRON to run it every 1 minute ```sudo crontab -e```:
```
*/1 * * * * /home/robert/miscale2garmin-3.0/import_mqtt.sh
```

<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
