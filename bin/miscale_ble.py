#!/usr/bin/python3

import os
import datetime
from datetime import datetime as dt
from bluepy import btle

# Version Info
print("Export 2 Garmin Connect v1.0 (miscale_ble.py)")
print("")

# Importing bluetooth variables from a file
path = os.path.dirname(os.path.dirname(__file__))
with open(path + '/user/export2garmin.cfg', 'r') as file:
    for line in file:
        line = line.strip()
        if line.startswith('miscale_ble'):
            name, value = line.split('=')
            globals()[name.strip()] = value.strip()
miscale_ble_time = int(miscale_ble_time)
unique_dev_addresses = []

# Reading data from a scale using a BLE scanner
class miScale(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.address = str(miscale_ble_mac)
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr == self.address:
            for (adType, desc, value) in dev.getScanData():
                if dev.addr not in unique_dev_addresses:
                    unique_dev_addresses.append(dev.addr)
                    print("  BLE device found with address: " + dev.addr + " <= target device")
                if adType == 22:
                    data = bytes.fromhex(value[4:])
                    ctrlByte1 = data[1]
                    hasImpedance = ctrlByte1 & (1<<1)
                    if value[4:6] == '03':
                        lb_weight = int((value[28:30] + value[26:28]), 16) * 0.01
                        Weight = round(lb_weight / 2.2046, 1)
                    else:
                        Weight = (((data[12] & 0xFF) << 8) | (data[11] & 0xFF)) * 0.005
                    Impedance = ((data[10] & 0xFF) << 8) | (data[9] & 0xFF)
                    if hasImpedance:
                        Unix_time = int(dt.timestamp(dt.strptime(f"{int((data[3] << 8) | data[2])},{int(data[4])},{int(data[5])},{int(data[6])},{int(data[7])},{int(data[8])}", "%Y,%m,%d,%H,%M,%S")))
                        print(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * Reading BLE data complete, finished BLE scan")
                        print(str(Unix_time) + ";{:.1f}".format(Weight) + ";{:.0f}".format(Impedance))
                    else:
                        print(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * Reading BLE data incomplete, finished BLE scan")
                    exit()
        else:
            if dev.addr not in unique_dev_addresses:
                unique_dev_addresses.append(dev.addr)
                print("  BLE device found with address: " + dev.addr + ", non-target device")
    def run(self):
        if len(os.popen(f"hcitool dev | awk '/hci{miscale_ble_hci}/ {{print $2}}'").read()) == 0:
            print(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * BLE scanner not detected")
        else: 
            scanner = btle.Scanner(miscale_ble_hci)
            scanner.withDelegate(self)
            scanner.start()
            print(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * Starting BLE scan:")
            scanner.process(miscale_ble_time)
            scanner.stop()
            print(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * Finished BLE scan")

# Main program loop
scale = miScale()
scale.run()
