#!/usr/bin/python3

import datetime
import os
from bluepy import btle

# Version Info
print("Mi Body Composition Scale 2 Garmin Connect v4.8 (scanner_ble.py)")
print("")

# Scale Mac Address, please use lowercase letters
scale_mac_addr = "00:00:00:00:00:00"
unique_dev_addresses = []

# Scanning time, in seconds
scan_time = 10

# Reading data from the scale using Bluetooth
class miScale(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.address = scale_mac_addr
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr == self.address:
            for (adType, desc, value) in dev.getScanData():
                if dev.addr not in unique_dev_addresses:
                    unique_dev_addresses.append(dev.addr)
                    print("  BLE device found with address: " + (dev.addr) + " <= target device")
                if adType == 22:
                    data = bytes.fromhex(value[4:])
                    ctrlByte1 = data[1]
                    hasImpedance = ctrlByte1 & (1<<1)
                    Weight = (((data[12] & 0xFF) << 8) | (data[11] & 0xFF)) * 0.005
                    Impedance = ((data[10] & 0xFF) << 8) | (data[9] & 0xFF)
                    if hasImpedance:
                        Unix_time = int(datetime.datetime.timestamp(datetime.datetime.strptime("{},{},{},{},{},{}".format(int((data[3] << 8) | data[2]), int(data[4]), int(data[5]), int(data[6]), int(data[7]), int(data[8])), "%Y,%m,%d,%H,%M,%S")))
                        print("* Reading BLE data complete, finished BLE scan")
                        print("{:.2f}".format(Weight) + ";" + str(Impedance) + ";" + str(Unix_time))
                    else:
                        print("* Reading BLE data incomplete, finished BLE scan")
                    exit()
        else:
            if dev.addr not in unique_dev_addresses:
                unique_dev_addresses.append(dev.addr)
                print("  BLE device found with address: " + (dev.addr) + ", non-target device")
    def run(self):
        if len(os.popen("hcitool dev | awk 'NR>1 {print $2}'").read()) == 0:
            print("* No BLE device detected")
        else:
            scanner = btle.Scanner()
            scanner.withDelegate(self)
            scanner.start()
            print("* Starting BLE scan:")
            scanner.process(scan_time)
            scanner.stop()
            print("* Finished BLE scan")

scale = miScale()
scale.run()