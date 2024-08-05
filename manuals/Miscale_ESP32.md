## 2.2. Miscale_ESP32 VERSION

### 2.2.1. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object
- Install Zepp Life App on your mobile device from Play Store;
- Configure your scale with Zepp Life App on your mobile device (tested on Android 10-14);
- Retrieve scale's MAC address from Zepp Life App (Profile > My devices > Mi Body Composition Scale 2);
- Turn off weigh small object in Zepp Life App (Profile > My devices > Mi Body Composition Scale 2) for better measurement quality.

### 2.2.2. Setting correct date and time in Mi Body Composition Scale 2
- Launch Zepp Life App, go to scale (Profile > My devices > Mi Body Composition Scale 2);
- Start scale and select Clear data in App;
- Take a new weight measurement with App, App should synchronize date and time (UTC);
- Script import_data.sh detects time zone and includes this as a time offset;
- If time is still not synchronized correctly, check NTP synchronization on server or change time offset in user/export2garmin.cfg file ("miscale_offset" parameter);
- You should also synchronize scale after replacing batteries;
- Script import_data.sh detects same weighing done in less than 30 seconds (protection against duplicates);
- Script import_data.sh have time difference detection of more than 20 minutes (between scale data and os).

### 2.2.3. ESP32 configuration (bluetooth gateway to WiFi/MQTT)
- Use Arduino IDE to compile and upload software to ESP32, following board and libraries required:
  - Arduino ESP32: https://github.com/espressif/arduino-esp32;
  - Battery 18650 Stats: https://github.com/danilopinotti/Battery18650Stats;
  - PubSubClient: https://github.com/knolleary/pubsubclient;
  - Timestamps: https://github.com/alve89/Timestamps.
- How to install board and library in Arduino IDE?:
  - board (**_NOTE:_ use version 1.0.4, newer is unstable**): https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html;
  - libraries: https://www.arduino.cc/en/Guide/Libraries.
- Preparing Arduino IDE to upload project to ESP32, go to Tools and select:
  - Board: > ESP32 Arduino > "WEMOS LOLIN32";
  - Upload Speed: "921600";
  - CPU Frequency: > "80MHz (WiFi / BT)" for better energy saving;
  - Flash Frequency: "80Mhz";
  - Partition Scheme: > "No OTA (Large APP)";
  - Port: > "COM" on which ESP32 board is detected.
- Following information must be entered before compiling code (esp32.ino) in Arduino IDE:
  - MAC address of scale read from Zepp Life App ("scale_mac_addr"), if you don't know MAC address read section [2.2.1.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_ESP32.md#221-getting-mac-address-of-mi-body-composition-scale-2--disable-weigh-small-object);
  - Parameters of your WiFi network ("ssid", "password");
  - Other settings ("led_pin", "Battery18650Stats");
  - Connection parameters MQTT ("mqtt_server", "mqtt_port", "mqtt_userName", "mqtt_userPass");
  - If you want to speed up download process, you can minimize ESP32 sleep time in "esp_sleep_enable_timer_wakeup" parameter (at expense of battery life).
- Debug and comments:
  - Project is prepared to work with ESP32 board with charging module (red LED indicates charging). I based my version on Li-ion 18650 battery;
  - Program for ESP32 has implemented UART debug mode (baud rate must be set to 115200), you can verify if everything is working properly:
  ```
  Export 2 Garmin Connect v1.0 (miscale_esp32.ino)
  
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
  - Device has 2 buttons, first green is reset button (monostable), red is battery power switch (bistable).
- Sample photo of finished module with ESP32 (Wemos LOLIN D32 Pro) and Li-ion 18650 battery (LG 3600mAh, LGDBM361865):

![alt text](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_ESP32.jpg)

### 2.2.4. Preparing operating system
- Minimum hardware and software requirements are:
  - x86: 1vCPU, 1024MB RAM, 8GB disk space, network connection, Debian 12 operating system;
  - ARM: 1CPU, 512MB RAM, 8GB disk space, network connection, Raspberry Pi OS | Debian 12 operating system.
- Update your system and then install following modules:
```
$ sudo apt update && sudo apt full-upgrade -y && sudo apt install -y wget python3 bc mosquitto mosquitto-clients python3-pip procmail
$ sudo pip3 install --upgrade garminconnect --break-system-packages
```
- You need to set up a password for MQTT (password must be same as in ESP32): `sudo mosquitto_passwd -c /etc/mosquitto/passwd admin`;
- Create a configuration file for Mosquitto: `sudo nano /etc/mosquitto/mosquitto.conf` and enter following parameters:
```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```
- Download and extract to your home directory (e.g. "/home/robert/"), make a files executable:
```
$ wget https://github.com/RobertWojtowicz/export2garmin/archive/refs/heads/master.tar.gz -O - | tar -xz
$ cd export2garmin-master && sudo chmod 755 import_data.sh
```

### 2.2.5. Configuring scripts
- Configuration is stored in `user/export2garmin.cfg` file (make changes e.g. via `sudo nano`):
  - To enable Miscale module, set "on" in "switch_miscale" parameter;
  - You need to complete data: "miscale_mqtt_user", "miscale_mqtt_passwd" which are related to MQTT broker, "switch_mqtt" set to "on";
  - Additionally, you must complete data in "miscale_export_user*" section: sex, height in cm, birthdate in dd-mm-yyyy and login e-mail to Garmin Connect, max_weight in kg, min_weight in kg.
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
15.07.2024-23:00:11 MISCALE * Importing data from an MQTT broker
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
$# find / -name import_data.sh
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
- You can check if export2garmin service works `sudo systemctl status export2garmin.service` or temporarily stop it with command `sudo systemctl stop export2garmin.service`;
- Back to [README](https://github.com/RobertWojtowicz/export2garmin/blob/master/README.md).

## 3. Mobile App
I don't plan to create a mobile app, but I encourage you to take advantage of another projects:
- Android: https://github.com/lswiderski/mi-scale-exporter;
- iOS | iPadOS: https://github.com/lswiderski/WebBodyComposition.

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>