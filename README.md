# Mi Body Composition Scale 2 Garmin Connect

## 1. Introduction
- This project works **only on Linux**, Windows is not supported;
- It is possible to run Linux as a virtual machine on Windows and use passthrough mechanism;
- This project is based on following projects:
  - https://github.com/lswiderski/yet-another-garmin-connect-client;
  - https://github.com/wiecosystem/Bluetooth;
  - https://github.com/lolouk44/xiaomi_mi_scale;
  - https://github.com/rando-calrissian/esp32_xiaomi_mi_2_hass;
- Allows fully automatic synchronization of Mi Body Composition Scale 2 (tested on XMTZC05HM) directly to Garmin Connect, with following parameters:
  - Time;
  - Weight (**_NOTE:_ kg units only**);
  - BMI;
  - Body Fat;
  - Skeletal Muscle Mass;
  - Bone Mass;
  - Body Water;
  - Physique Rating;
  - Visceral Fat;
  - Metabolic Age;
- Supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect.

## 2. Getting MAC address of Mi Body Composition Scale 2 / disable weigh small object
- Install Zepp Life App on your mobile device, user manual: https://files.xiaomi-mi.com/files/smart_scales/smart_scales-EN.pdf;
- Configure your scale with Zepp Life App on your mobile device (tested on Android 10-13);
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
- Processed data are sent by program YAGCC to Garmin Connect;
- Raw and calculated data from scale is backed up on server in backup.csv file;
- backup.csv file can be imported e.g. for analysis into Excel.

**Select your platform and go to instructions:**
- [x86 e.g. virtual machine (support for Debian 12)](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/x86_ble.md);
- [ARM e.g. Raspberry Pi Zero W (support for Debian 11)](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/ARM_ble.md).

### 4.2. ESP32 VERSION
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- ESP32 module operates in a deep sleep and wakes up every 7 minutes, scans for BLE device for 10 seconds and queries scale for data, process can be started immediately via reset button;
- ESP32 module sends acquired data via MQTT protocol to MQTT broker installed on server;
- Body weight and impedance data on server are appropriately processed by scripts;
- Processed data are sent by program YAGCC to Garmin Connect;
- Raw and calculated data from scale is backed up on server in backup.csv file;
- backup.csv file can be imported e.g. for analysis into Excel.

**Select your platform and go to instructions:**
- [x86 e.g. virtual machine (support for Debian 12)](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/x86_esp32.md);
- [ARM e.g. Raspberry Pi Zero W (support for Debian 11)](https://github.com/RobertWojtowicz/miscale2garmin/blob/master/manuals/ARM_esp32.md).

## 5. Mobile App
I don't plan to create a mobile app, but I encourage you to take advantage of another projects:
- Android: https://github.com/lswiderski/mi-scale-exporter;
- iOS | iPadOS: https://github.com/lswiderski/WebBodyComposition.

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>