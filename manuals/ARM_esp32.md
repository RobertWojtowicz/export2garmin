## 4.2. ARM_ESP32 VERSION
### 4.2.1. ESP32 configuration (bluetooth gateway to WiFi/MQTT)
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
  - MAC address of scale read from Zepp Life App ("scale_mac_addr"), if you don't know MAC address read section [2. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object](https://github.com/RobertWojtowicz/miscale2garmin/tree/master#2-getting-mac-address-of-mi-body-composition-scale-2--disable-weigh-small-object);
  - parameters of your WiFi network ("ssid", "password");
  - other settings ("led_pin", "Battery18650Stats");
  - connection parameters MQTT ("mqtt_server", "mqtt_port", "mqtt_userName", "mqtt_userPass");
- Debug and comments:
  - Project is prepared to work with ESP32 board with charging module (red LED indicates charging). I based my version on Li-ion 18650 battery;
  - Program for ESP32 has implemented UART debug mode (baud rate must be set to 115200), you can verify if everything is working properly:
  ```
  Mi Body Composition Scale 2 Garmin Connect v5.3 (esp32.ino)
  
  * Starting BLE scan:
   BLE device found with address: 3f:f1:3e:a6:4d:00, non-target device
   BLE device found with address: 42:db:e4:c4:5c:d4, non-target device
   BLE device found with address: 24:fc:e5:8f:ce:bf, non-target device
   BLE device found with address: 00:00:00:00:00:00 <= target device
  * Reading BLE data complete, finished BLE scan
  * Connecting to WiFi: connected
   IP address: 192.168.4.18
  * Connecting to MQTT: connected
  * Publishing MQTT data: 1672412076;58.4;521;3.5;5
  * Waiting for next scan, going to sleep
  ```
  - After switching device on, blue LED will light up for a moment to indicate that module has started successfully;
  - If data are acquired correctly in next step, blue LED will flash for a moment 2 times;
  - If there is an error, e.g. data is incomplete, no connection to WiFi network or MQTT broker, blue LED will light up for 5 seconds;
  - Program implements voltage measurement and battery level, which are sent toger with scale data in topic MQTT;
  - Device has 2 buttons, first green is reset button (monostable), red is battery power switch (bistable);
- Sample photo of finished module with ESP32 (Wemos LOLIN D32 Pro) and Li-ion 18650 battery (LG 3600mAh, LGDBM361865):

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/esp32.jpg)

### 4.2.2. Preparing operating system
- Minimum hardware and software requirements are: 1CPU, 512MB RAM, 2GB disk space, network connection, Raspberry Pi OS | Debian 11 operating system;
- Update your system and then install following modules:
```
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install wget python3 bc mosquitto mosquitto-clients unzip -y
```
- You need to set up a password for MQTT (password must be same as in ESP32): ```sudo mosquitto_passwd -c /etc/mosquitto/passwd admin```;
- Create a configuration file for Mosquitto: ```sudo nano /etc/mosquitto/mosquitto.conf``` and enter following parameters:
```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable, choose correct version of YAGCC depending on your operating system:
  - Raspberry Pi OS | Debian 11 (32-bit) use linux-arm.zip
  - Raspberry Pi OS | Debian 11 (64-bit) use linux-arm64.zip
```
wget https://github.com/RobertWojtowicz/miscale2garmin/archive/refs/tags/5.tar.gz -O - | tar -xz
cd miscale2garmin-5
wget https://github.com/lswiderski/yet-another-garmin-connect-client/releases/download/cli-v0.0.1/linux-arm.zip
unzip -j linux-arm.zip linux-arm/YAGCC && rm linux-arm.zip
sudo chmod 755 YAGCC import_data.sh export_garmin.py
```

### 4.2.3. Configuring scripts
- First script is "import_data.sh", you need to complete data: "user", "password" which are related to MQTT broker, "mqtt" set to "on";
- Second script is "export_garmin.py", you must complete data in "users" section: "sex", "height" in cm, "birthdate" in dd-mm-yyyy, "email" and "password" to Garmin Connect, "max_weight" in kg, "min_weight" in kg;
- Script "export_garmin.py" supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect;
- Script "import_data.sh" has implemented debug mode, you can verify if everything is working properly, just execute it from console:
```
$ /home/robert/miscale2garmin-5/import_data.sh
Mi Body Composition Scale 2 Garmin Connect v5.9 (import_data.sh)

* backup.csv file exists, check if temp.log exists
* temp.log file exists, checking for new data
* Importing data from an MQTT broker
* Saving import 1672412076 to backup.csv file
* Calculating data from import 1672412076, upload to Garmin Connect
* Data upload to Garmin Connect is complete
* Saving calculated data from import 1672412076 to backup.csv file
```
- If there is an error upload to Garmin Connect, data will be sent again on next execution, upload errors and other operations are saved in temp.log file:
```
$ cat /home/robert/miscale2garmin-5/temp.log
Uploaded

Mi Body Composition Scale 2 Garmin Connect v5.9 (export_garmin.py)

* Import data: 1672412076;58.1;526
* Calculated data: 07.01.2023;19:09;58.1;19.6;13.8;47.5;2.6;59.2;7;6;22;526;email@email.com;07.01.2023;19:21
```
- Finally, if everything works correctly add script import_mqtt.sh to CRON to run it every 1 minute ```sudo crontab -e```:
```
*/1 * * * * /home/robert/miscale2garmin-5/import_data.sh
```

### If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>