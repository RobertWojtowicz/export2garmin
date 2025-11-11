#!/usr/bin/python3

import os
import subprocess
import argparse
import time
from datetime import datetime as dt
from bluepy import btle

# Version info
print("""
=============================================
Export 2 Garmin Connect v3.6 (miscale_ble.py)
=============================================
""")

# Importing bluetooth variables from a file
path = os.path.dirname(os.path.dirname(__file__))
with open(path + '/user/export2garmin.cfg', 'r') as file:
    for line in file:
        line = line.strip()
        if line.startswith('ble_') or line.startswith('switch_'):
            name, value = line.split('=')
            globals()[name.strip()] = value.strip()

# Arguments to pass in script
parser = argparse.ArgumentParser()
parser.add_argument("-a", default=ble_arg_hci)
parser.add_argument("-bt", default=ble_arg_hci2mac)
parser.add_argument("-mac", default=ble_arg_mac)
args = parser.parse_args()
ble_arg_hci = args.a
ble_arg_hci2mac = args.bt
ble_arg_mac = args.mac

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
            if switch_miscale == 'off' and (switch_s400 == 'on' or switch_omron == 'on'):
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} S400|OMRON * BLE scan test completed successfully")
                exit()
            if switch_miscale == 'on' and (switch_s400 == 'off' or switch_omron == 'on'):
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
                            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} MISCALE|OMRON * Reading BLE data complete, finished BLE scan")
                            print(f"{unix_time};{weight:.1f};{impedance:.0f}")
                        else:
                            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} MISCALE|OMRON * Reading BLE data incomplete, finished BLE scan")
                        exit()
            else:
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} MISCALE|S400|OMRON * Incorrect configuration in export2garmin.cfg file, finished BLE scan")
                exit()

    # Verifying correct working of BLE adapter, max 3 times
    def restart_bluetooth(self):
        subprocess.run(["rfkill", "unblock", "bluetooth"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        subprocess.run(["modprobe", "btusb"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        subprocess.run(["systemctl", "restart", "bluetooth.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    def run(self):
        print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Checking if a BLE adapter is detected")
        ble_error = 0
        ble_success = False
        while ble_error < 3:
            ble_error += 1
            hci_out = subprocess.check_output(["hcitool", "dev"], stderr=subprocess.DEVNULL).decode()
            if ble_arg_hci2mac == "on":
                if ble_arg_mac not in hci_out:
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter {ble_arg_mac} not detected, restarting bluetooth service")
                else:
                    ble_arg_hci_read = [line.split()[0][-1] for line in hci_out.splitlines() if ble_arg_mac in line][0]
                    ble_arg_mac_read = ble_arg_mac
                    ble_success = True
            else:
                if f"hci{ble_arg_hci}" not in hci_out:
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter hci{ble_arg_hci} not detected, restarting bluetooth service")
                else:
                    ble_arg_hci_read = ble_arg_hci
                    ble_arg_mac_read = [line.split()[1] for line in hci_out.splitlines() if f"hci{ble_arg_hci}" in line][0]
                    ble_success = True
            if ble_success is False:
                self.restart_bluetooth()
            else:
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter hci{ble_arg_hci_read}({ble_arg_mac_read}) detected, check BLE adapter connection")
                break
        if ble_error == 3 and not ble_success:
            if ble_arg_hci2mac == "on":
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter {ble_arg_mac} failed to be found, not detected by {ble_error} attempts")
            else:
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE adapter hci{ble_arg_hci} failed to be found, not detected by {ble_error} attempts")
            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Finished BLE scan")
            return

        # Verifying correct working of BLE adapter connection, max 3 times
        con_error = 0
        con_success = False
        while con_error < 3 and ble_success:
            con_error += 1
            try:
                scanner = btle.Scanner(ble_arg_hci_read)
                scanner.withDelegate(self)
                scanner.start()
                scanner.stop()
                con_success = True
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Connection to BLE adapter hci{ble_arg_hci_read}({ble_arg_mac_read}) works, starting BLE scan:")
                break
            except btle.BTLEManagementError:
                print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Connection error, restarting BLE adapter hci{ble_arg_hci_read}({ble_arg_mac_read})")
                subprocess.run(["hciconfig", f"hci{ble_arg_hci_read}", "down"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                subprocess.run(["hciconfig", f"hci{ble_arg_hci_read}", "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
        if con_error == 3 and not con_success:
            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Failed to connect to BLE adapter hci{ble_arg_hci_read}({ble_arg_mac_read}) by {con_error} attempts")
            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Finished BLE scan")
            return

        # Scanning for BLE devices in range, default 7 times
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
                    self.restart_bluetooth()
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