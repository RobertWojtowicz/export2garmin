## 2.6. about_BLE VERSION

### 2.6.1 BLE adapters support matrix
| BT version | Chipset/Brand | Alterative name/Model | Type | Range | External antenna | Mi Body Composition Scale 2 | Xiaomi Body Composition Scale S400 | Omron | Testers |
| ----- | ----- | ----- | ----- | -----  | ----- | ----- | ----- | ----- | ----- |
| 4.0 | CSR8510 A10/LogiLink | Cambridge Silicon Radio | USB | medium | ❌ | ✔️ | ✔️ | ✔️ | RobertWojtowicz |
| 4.1 | Broadcom/Raspberry Pi | Zero W | Internal | low | ❌ | ❌ | ❌ | ❌ | RobertWojtowicz |
| 4.2 | Broadcom/Raspberry Pi | Zero 2W | Internal | low | ❌ | ✔️ | ❌ | ✔️ | RobertWojtowicz |
| 5.0 | Broadcom/Raspberry Pi | 4B** | Internal | low | ❌ | ✔️ | ❌ | ✔️ | RobertWojtowicz |
| 5.0 | Broadcom/Raspberry Pi | 5**(*) | Internal | low | ❌ | ✔️ | ❌ | ✔️ | RobertWojtowicz |
| 5.1 | RTL8761B/Zexmte| Realtek | USB | high* | ✔️* | ✔️| ❌ | ✔️ | RobertWojtowicz |
| 5.3 | ATS2851/Zexmte | Actions | USB | high* | ✔️* | ✔️| ❓ | ❌ | RobertWojtowicz |
| 5.4 | RDK | X5 | Internal | low | ❌ | ❓ | ✔️ | ❓ | CoreJa |

✔️=tested working, ❓=not tested, ❌=not supported

### 2.6.2 Troubleshooting BLE adapters
- Bluetooth adapter should have a removable RP-SMA antenna if you want a long range*;
- ATS2851 chipset has native support in Debian 12 operating system | Raspberry Pi OS no additional driver needed;
- If you have a lot of bluetooth devices in area, it's a good idea to set an additional check, set ble_adapter_check parameter to "on" in `user/export2garmin.cfg`;
- Script `miscale/miscale_ble.py` has implemented debug mode and recovery mechanisms for bluetooth, you can verify if everything is working properly;
- If you are using a virtual machine, assign bluetooth adapter from tab Hardware > Add: USB device > Use USB Vendor/Device ID > Choose Device: > Passthrough a specific device (tested on Proxmox VE 8.3);
- RTL8761B chipset requires driver (for Raspberry Pi OS skip this step), install Realtek package and restart virtual machine:
```
sudo apt install -y firmware-realtek
sudo reboot
```
- In some cases of **Raspberry Pi** when using internal bluetooth and WiFi:
  - You should connect WiFi on 5GHz, because on 2,4GHz there may be a problem with connection stability (sharing same antenna)**;
  - WiFi may freeze in 5 version, set switch_wifi_watchdog parameter to "on" in `user/export2garmin.cfg`***;
  - If you only use an external BLE adapter, it is recommended to disable internal module `sudo nano /boot/firmware/config.txt` and restart:
  ```
  [all]
  dtoverlay=disable-bt
  ```
  ```
  sudo reboot
  ```

### 2.6.3 Using multiple BLE adapters
- If you are using multiple BLE adapters, select appropriate one by HCI number or MAC address (recommended) and set in `user/export2garmin.cfg` file;
- Use command `sudo hciconfig -a` to locate BLE adapter, and then select type of identification:
	- By HCI number, set parameter "ble_adapter_hci";
	- By MAC address, set parameter "ble_adapter_switch" to "on" and specify MAC addres in parameter "ble_adapter_mac".
- Go to next part of instructions, select module:
  - [Miscale | Mi Body Composition Scale 2 - Debian 12](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_BLE.md);
  - [Miscale | Xiaomi Body Composition Scale S400 - Debian 12](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/S400_BLE.md);
  - [Omron - Debian 12](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Omron_BLE.md);
  - Back to [README](https://github.com/RobertWojtowicz/export2garmin/blob/master/README.md).

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>