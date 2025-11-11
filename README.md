# Export 2 to Garmin Connect

## 1. Introduction
### 1.1. Miscale module (once known as miscale2garmin):
- Allows fully automatic synchronization of Mi Body Composition Scale 2 (tested on XMTZC05HM) or Xiaomi Body Composition Scale S400 (tested on MJTZC01YM) directly to Garmin Connect, with following parameters:
  - Date and Time (measurement, from device);
  - Weight (**_NOTE:_ lbs is automatically converted to kg**, applies to Mi Body Composition Scale 2);
  - BMI (Body Mass Index);
  - Body Fat;
  - Skeletal Muscle Mass;
  - Bone Mass;
  - Body Water;
  - Physique Rating;
  - Visceral Fat;
  - Metabolic Age;
  - Heart rate (Xiaomi Body Composition Scale S400 only, optional upload to blood pressure section).
- Miscale_backup.csv file also contains other parameters (can be imported e.g. for analysis into Excel):
  - BMR (Basal Metabolic Rate);
  - LBM (Lean Body Mass);
  - Ideal Weight;
  - Fat Mass To Ideal;
  - Protein;
  - Data Status (to_import, failed, uploaded);
  - Unix Time (based on Date and Time);
  - Email User (used account for Garmin Connect);
  - Upload Date and Upload Time (to Garmin Connect);
  - Difference Time (between measuring and uploading);
  - Battery status in V and % (ESP32 - Mi Body Composition Scale 2 only);
  - Impedance;
  - Impedance Low (Xiaomi Body Composition Scale S400 only).
- Supports multiple users with individual weights ranges, we can link multiple accounts with Garmin Connect.

### 1.2. Omron module: 
- Allows fully automatic synchronization of Omron blood pressure (tested on M4/HEM-7155T and M7/HEM-7322T Intelli IT) directly to Garmin Connect, with following parameters:
  - Date and Time (measurement, from device);
  - DIAstolic blood pressure;
  - SYStolic blood pressure;
  - Heart rate.
- Omron_backup.csv file also contains other parameters (can be imported e.g. for analysis into Excel):
  - Category (**_NOTE:_ EU and US classification only**);
  - MOV (Movement detection);
  - IHB (Irregular Heart Beat);
  - Data Status (to_import, failed, uploaded);
  - Unix Time (based on Date and Time);
  - Email User (used account for Garmin Connect);
  - Upload Date and Upload Time (to Garmin Connect);
  - Difference Time (between measuring and uploading).
-  Supports 2 users from Omron device, we can connect 2 accounts with Garmin Connect.

### 1.3. User module:
- Enables configuration of all parameters related to integration Miscale and Omron;
- Provides export Oauth1 and Oauth2 tokens of your account from Garmin Connect (MFA/2FA support).

## 2. How does this work
- Miscale and Omron modules can be activated individually or run together:
	- Devices can run together (Mi Body Composition Scale 2 and Omron);
	- Devices can run together but there must be a sequence, first measuring blood pressure and then weighing (Xiaomi Body Composition Scale S400 and Omron);<br>
	  This is because Xiaomi Body Composition Scale S400 requires continuous scanning, importing data from scale will allow you to go to Omron module.
	- Devices can run together in parallel but two USB Bluetooth adapters are required, one for scanning Xiaomi Body Composition Scale S400 and other for Omron;<br>
	  This is an using separate processes, view section [2.6.4.](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/about_BLE.md#264-using-two-ble-adapters-in-parallel)
- Synchronization diagram from Export 2 to Garmin Connect:

![alt text](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/workflow.png)

### 2.1. Miscale module | Mi Body Composition Scale 2 | BLE VERSION
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- USB Bluetooth adapter or internal module scans BLE devices for 10 seconds to acquire data from scale;
- Body weight and impedance data on server are appropriately processed by scripts;
- Processed data are sent to Garmin Connect;
- Raw and calculated data from scale is backed up on server in miscale_backup.csv file;
- This part of project is **no longer being developed**, but it still works.

**Select your platform and go to instructions:**
- [Debian 13 | Raspberry Pi OS (based on Debian 13)](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_BLE.md);
- [Windows 11](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/all_BLE_win.md).

### 2.2. Miscale module | Mi Body Composition Scale 2 | ESP32 VERSION
- After weighing, Mi Body Composition Scale 2 is active for 15 minutes on bluetooth transmission;
- ESP32 module operates in a deep sleep and wakes up every 7 minutes, scans BLE devices for 10 seconds to acquire data from scale, process can be started immediately via reset button;
- ESP32 module sends acquired data via MQTT protocol to MQTT broker installed on server;
- Body weight and impedance data on server are appropriately processed by scripts;
- Processed data are sent to Garmin Connect;
- Raw and calculated data from scale is backed up on server in miscale_backup.csv file;
- This part of project is **no longer being developed**, but it still works.

**Select your platform and go to instructions:**
- [Debian 13 | Raspberry Pi OS (based on Debian 13)](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_ESP32.md);
- [Windows 11](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_ESP32_win.md).

### 2.3. Miscale module | Xiaomi Body Composition Scale S400 | BLE VERSION
- After weighing, Xiaomi Body Composition Scale S400 transmits weight data for a short while on bluetooth transmission;
- A USB Bluetooth adapter scans BLE devices continuously to acquire data from scale;
- Data from scale is decrypted and parsed into a readable form;
- Body weight and impedance data on server are appropriately processed by scripts;
- Processed data are sent to Garmin Connect;
- Raw and calculated data from scale is backed up on server in miscale_backup.csv file.

**Select your platform and go to instructions:**
- [Debian 13 | Raspberry Pi OS (based on Debian 13)](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/S400_BLE.md);
- [Windows 11](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/all_BLE_win.md).

### 2.4. Omron module | BLE VERSION
- After measuring blood pressure, Omron allows you to download measurement data once;
- USB bluetooth adapter or internal module scans BLE devices for 10 seconds to acquire data from blood pressure device (downloading data can take about 1 minute);
- Pressure measurement data are appropriately processed by scripts on server;
- Processed data are sent to Garmin Connect;
- Raw and calculated data from device is backed up on server in omron_backup.csv file.

**Select your platform and go to instructions:**
- [Debian 13 | Raspberry Pi OS (based on Debian 13)](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Omron_BLE.md);
- [Windows 11](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/all_BLE_win.md).

## 3. Mobile App
I don't plan to create a mobile app, but I encourage you to take advantage of another projects (applies to Mi Body Composition Scale / Mi Scale / S400):
- Android: https://github.com/lswiderski/mi-scale-exporter;
- iOS | iPadOS: https://github.com/lswiderski/WebBodyComposition.

## 4. Synchronizing data between different ecosystems
A very interesting project called SmartScaleConnect synchronizes scale data (applies to Mi Body Composition Scale 2 / S400) from Xiaomi cloud to Garmin:
- Linux | MacOS | Windows: https://github.com/AlexxIT/SmartScaleConnect.

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>