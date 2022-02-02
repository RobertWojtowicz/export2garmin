#!/usr/bin/python

import datetime
from bluepy import btle
import os

# Version Info
print("Mi Body Composition Scale 2 Garmin Connect v3.0 (scanner_ble.py)")
print("")

# Scale Mac Address, please use lowercase letters
scale_mac_addr = "00:00:00:00:00:00"

# Reading data from the scale using Bluetooth
class miScale(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.address = scale_mac_addr

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr == self.address:
            for (adType, desc, value) in dev.getScanData():
                print("  BLE device found with address: " + (dev.addr) + " <= target device")
                if adType == 22:
                    data = bytes.fromhex(value[4:])
                    ctrlByte1 = data[1]
                    hasImpedance = ctrlByte1 & (1<<1)
                    Weight = (((data[12] & 0xFF) << 8) | (data[11] & 0xFF)) * 0.005
                    Impedance = ((data[10] & 0xFF) << 8) | (data[9] & 0xFF)
                    if hasImpedance:
                        Readable_time = "{}-{}-{} {}:{}:{}".format(int((data[3] << 8) | data[2]), int(data[4]), int(data[5]), int(data[6]), int(data[7]), int(data[8]))
                        Unix_time = int(datetime.datetime.timestamp(datetime.datetime.strptime((Readable_time), "%Y-%m-%d %H:%M:%S")))
                        print("* Reading BLE data complete, finished BLE scan")
                        print("{:.2f}".format(Weight) + ";" + str(Impedance) + ";" + str(Unix_time) + ";" + str(Readable_time))
                    else:
                        print("* Reading BLE data incomplete, finished BLE scan")
                    exit()
        else:
            print("  BLE device found with address: " + (dev.addr) + ", non-target device")

    def run(self):
        if len(os.popen("hcitool dev | awk 'NR>1 {print $2}'").read()) != 0:
            scanner = btle.Scanner()
            scanner.withDelegate(self)
            scanner.start()
            print("* Starting BLE scan:")
        
            # Scan for 10 seconds
            scanner.process(10)
            scanner.stop()
            print("* Finished BLE scan")
        else:
            print("* No BLE device detected")        

scale = miScale()
scale.run()