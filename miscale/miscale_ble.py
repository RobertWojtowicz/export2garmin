#!/usr/bin/python3

import os
import time
from datetime import datetime as dt
from bluepy import btle

# Version info
print("""
=============================================
Export 2 Garmin Connect v2.2 (miscale_ble.py)
=============================================
""")

# Importing bluetooth variables from a file
path = os.path.dirname(os.path.dirname(__file__))
with open(path + '/user/export2garmin.cfg', 'r') as file:
    for line in file:
        line = line.strip()
        if line.startswith('ble_'):
            name, value = line.split('=')
            globals()[name.strip()] = value.strip()

# Reading data from a scale using a BLE adapter
class miScale(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.address = ble_miscale_mac.lower()
        self.unique_dev_addresses = []
        self.ble_adapter_time = int(ble_adapter_time)
        self.ble_adapter_repeat = int(ble_adapter_repeat)
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr not in self.unique_dev_addresses:
            self.unique_dev_addresses.append(dev.addr)
            print(f"  BLE device found with address: {dev.addr}" + (" <= target device" if dev.addr == self.address else ", non-target device"))
        if dev.addr == self.address:
            for (adType, desc, value) in dev.getScanData():
                if adType == 22:
                    data = bytes.fromhex(value[4:])
                    ctrlByte1 = data[1]
                    hasImpedance = ctrlByte1 & (1<<1)
                    if hasImpedance:

                        # lbs to kg unit conversion
                        if value[4:6] == '03':
                            lb_weight = int((value[28:30] + value[26:28]), 16) * 0.01
                            weight = round(lb_weight / 2.2046, 1)
                        else:
                            weight = (((data[12] & 0xFF) << 8) | (data[11] & 0xFF)) * 0.005
                        impedance = ((data[10] & 0xFF) << 8) | (data[9] & 0xFF)
                        unix_time = int(dt.timestamp(dt.strptime(f"{int((data[3] << 8) | data[2])},{int(data[4])},{int(data[5])},{int(data[6])},{int(data[7])},{int(data[8])}","%Y,%m,%d,%H,%M,%S")))
                        print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Reading BLE data complete, finished BLE scan")
                        print(f"{unix_time};{weight:.1f};{impedance:.0f}")
                    else:
                        print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Reading BLE data incomplete, finished BLE scan")
                    exit()
    def run(self):

        # Verifying correct working of BLE adapter, max 3 times
        print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Checking if a BLE adapter is detected")
        ble_error = 0
        ble_success = False
        while ble_error < 3:
            ble_error += 1
            if ble_adapter_switch == "on":
                if not os.popen(f"hcitool dev | awk '/{ble_adapter_mac}/ {{print $1}}'").read():
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter {ble_adapter_mac} not detected, restarting bluetooth service")
                else:
                    ble_adapter_hci_read = os.popen(f"hcitool dev | awk '/{ble_adapter_mac}/ {{print $1}}' | cut -c4").read().strip()
                    ble_adapter_mac_read = ble_adapter_mac
                    ble_success = True
            else:
                if not os.popen(f"hcitool dev | awk '/hci{ble_adapter_hci}/ {{print $2}}'").read():
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter hci{ble_adapter_hci} not detected, restarting bluetooth service")
                else:
                    ble_adapter_hci_read = ble_adapter_hci
                    ble_adapter_mac_read = os.popen(f"hcitool dev | awk '/hci{ble_adapter_hci}/ {{print $2}}'").read().strip()
                    ble_success = True

            if ble_success == False:
                os.system("sudo modprobe btusb >/dev/null 2>&1")
                time.sleep(1)
                os.system("sudo systemctl restart bluetooth.service >/dev/null 2>&1")
                time.sleep(1)
            else:
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter hci{ble_adapter_hci_read}({ble_adapter_mac_read}) detected, check BLE adapter connection")
                break

        if ble_error == 3 and not ble_success:
            if ble_adapter_switch == "on":
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter {ble_adapter_mac} failed to be found, not detected by {ble_error} attempts")
            else:
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter hci{ble_adapter_hci} failed to be found, not detected by {ble_error} attempts")
            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Finished BLE scan")
            return

        # Verifying correct working of BLE adapter connection, max 3 times
        con_error = 0
        con_success = False
        while con_error < 3 and ble_success:
            con_error += 1
            try:
                scanner = btle.Scanner(ble_adapter_hci_read)
                scanner.withDelegate(self)
                scanner.start()
                scanner.stop()
                con_success = True
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Connection to BLE adapter hci{ble_adapter_hci_read}({ble_adapter_mac_read}) works, starting BLE scan:")
                break
            except btle.BTLEManagementError:
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Connection error, restarting BLE adapter hci{ble_adapter_hci_read}({ble_adapter_mac_read})")
                os.system(f"sudo hciconfig hci{ble_adapter_hci_read} down >/dev/null 2>&1")
                time.sleep(1)
                os.system(f"sudo hciconfig hci{ble_adapter_hci_read} up >/dev/null 2>&1")
                time.sleep(1)
        if con_error == 3 and not con_success:
            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Failed to connect to BLE adapter hci{ble_adapter_hci_read}({ble_adapter_mac_read}) by {con_error} attempts")
            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Finished BLE scan")
            return

        # Scanning for BLE devices in range
        dev_around = 0
        while ble_success and con_success:
            scanner.start()
            scanner.process(self.ble_adapter_time)
            scanner.stop()
            if ble_adapter_check == "on" and not self.unique_dev_addresses:
                dev_around += 1
                if dev_around < self.ble_adapter_repeat:
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * No devices around")
                elif dev_around == self.ble_adapter_repeat:
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * No devices around, restarting bluetooth service")
                    os.system("sudo modprobe btusb >/dev/null 2>&1")
                    time.sleep(1)
                    os.system("sudo systemctl restart bluetooth.service >/dev/null 2>&1")
                    time.sleep(1)
                else:
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * No devices around, failed {dev_around} attempts")
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Finished BLE scan")
                    break
            else:
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Finished BLE scan")
                break

# Main program loop
if __name__ == "__main__":
    scale = miScale()
    scale.run()