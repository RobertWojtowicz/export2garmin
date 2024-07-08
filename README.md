# Mi Body Composition Scale & Omron blood pressure 2 Garmin Connect

## 1. Introduction
- This project is based on following projects:
  - https://github.com/cyberjunky/python-garminconnect;
  - https://github.com/wiecosystem/Bluetooth;
  - https://github.com/userx14/omblepy;
  - https://github.com/lolouk44/xiaomi_mi_scale;
  - https://github.com/dorssel/usbipd-win;
  - https://github.com/rando-calrissian/esp32_xiaomi_mi_2_hass;
### 1.1. Miscale module:
- Allows fully automatic synchronization of Mi Body Composition Scale 2 (tested on XMTZC05HM) directly to Garmin Connect, with following parameters:
  - Date and Time;
  - Weight (**_NOTE:_ kg units only**);
  - BMI (Body Mass Index);
  - Body Fat;
  - Skeletal Muscle Mass;
  - Bone Mass;
  - Body Water;
  - Physique Rating;
  - Visceral Fat;
  - Metabolic Age;
- Miscale_backup.csv file also contains other calculated parameters (can be imported e.g. for analysis into Excel):
  - BMR (Basal Metabolic Rate);
  - LBM (Lean Body Mass);
  - Ideal Weight;
  - Fat Mass To Ideal;
  - Protein;
- Supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect;
### 1.2. Omron module: 
- Allows fully automatic synchronization of Omron blood pressure (tested on HEM-7322T/M700 Intelli IT) directly to Garmin Connect, with following parameters:
  - Date and Time;
  - DIA (Diastolic Blood Pressure);
  - SYS (Systolic Blood Pressure);
  - BPM (Beats Per Minute);
- Omron_backup.csv file also contains other parameters (can be imported e.g. for analysis into Excel):
  - MOV;
  - IHB (Irregular Heart Beat).

## 2. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object
- Install Zepp Life App on your mobile device from Play Store;
- Configure your scale with Zepp Life App on your mobile device (tested on Android 10-14);
- Retrieve scale's MAC address from Zepp Life App (Profile > My devices > Mi Body Composition Scale 2);
- Turn off weigh small object in Zepp Life App (Profile > My devices > Mi Body Composition Scale 2) for better measurement quality:

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/settings.png)

## 3. Setting correct date and time in Mi Body Composition Scale 2
- Launch Zepp Life App, go to scale (Profile > My devices > Mi Body Composition Scale 2);
- Start scale and select Clear data in App;
- Take a new weight measurement with App, App should synchronize date and time (UTC);
- Script import_data.sh detects time zone and includes this as a time offset;
- If time is still not synchronized correctly, check NTP synchronization on server or change time offset in import_data.sh file (offset parameter);
- You should also synchronize scale after replacing batteries;
- Script import_data.sh detects same weighing done in less than 30 seconds (protection against duplicates);
- Script import_data.sh have time difference detection of more than 20 minutes (between scale data and os).

## 4. How does this work
- Synchronization diagram from Mi Body Composition Scale 2 to Garmin Connect:

![alt text](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/workflow.png)

### 4.1. BLE VERSION
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- USB bluetooth adapter or internal module (tested with bluetooth versions 4.0/4.1 and 5.0/5.1/5.3) scans for BLE device every 1 minute for 10 seconds and queries scale for data;
- Body weight and impedance data on server are appropriately processed by scripts;
- Processed data are sent to Garmin Connect (MFA/2FA support);
- Raw and calculated data from scale is backed up on server in backup.csv file.

**Select your platform and go to instructions:**
- [x86 - Debian 12](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/x86_ble.md);
- [x86 - Windows 11](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/x86_ble_win.md);
- [ARM - Raspberry Pi OS | Debian 12](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/ARM_ble.md).

### 4.2. ESP32 VERSION
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- ESP32 module operates in a deep sleep and wakes up every 7 minutes, scans for BLE device for 10 seconds and queries scale for data, process can be started immediately via reset button;
- ESP32 module sends acquired data via MQTT protocol to MQTT broker installed on server;
- Body weight and impedance data on server are appropriately processed by scripts;
- Processed data are sent to Garmin Connect (MFA/2FA support);
- Raw and calculated data from scale is backed up on server in backup.csv file.

**Select your platform and go to instructions:**
- [x86 - Debian 12](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/x86_esp32.md);
- [x86 - Windows 11](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/x86_esp32_win.md);
- [ARM - Raspberry Pi OS | Debian 12](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/ARM_esp32.md).

## 5. Mobile App
I don't plan to create a mobile app, but I encourage you to take advantage of another projects:
- Android: https://github.com/lswiderski/mi-scale-exporter;
- iOS | iPadOS: https://github.com/lswiderski/WebBodyComposition.

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
