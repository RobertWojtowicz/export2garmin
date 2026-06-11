#!/usr/bin/python3

import os
import subprocess
import signal
import argparse
import asyncio
import time
import logging
from datetime import datetime
from bleak import BleakScanner
from xiaomi_ble.parser import XiaomiBluetoothDeviceData
from bluetooth_sensor_state_data import BluetoothServiceInfo

# Handling print function in BrokenPipeError exception
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
time_print = time.time()
def safe_print(*args, **kwargs):
    global time_print
    try:
        print(*args, **kwargs)
        time_print = time.time()
    except BrokenPipeError:
        signal.raise_signal(signal.SIGPIPE)

safe_print("""
==========================================
Export 2 Garmin Connect v3.6 (s400_ble.py)
==========================================
""")

# Importing bluetooth variables from a file
path = os.path.dirname(os.path.dirname(__file__))
with open(path + '/user/export2garmin.cfg', 'r') as file:
    for line in file:
        line = line.strip()
        if line.startswith('ble_miscale_') or line.startswith('ble_arg_hci'):
            name, value = line.split('=')
            globals()[name.strip()] = value.strip()

# Arguments to pass in script
parser = argparse.ArgumentParser()
parser.add_argument("-a", default=ble_arg_hci)
args = parser.parse_args()
ble_arg_hci = args.a
hci_out = subprocess.check_output(["hcitool", "dev"], stderr=subprocess.DEVNULL).decode()
ble_arg_mac = [line.split()[1] for line in hci_out.splitlines() if f"hci{ble_arg_hci}" in line][0]

# Counters for slow/fast iteration detection
time_slow = 0
time_fast = 0
def handle_timing(duration):
    global time_slow, time_fast
    if duration > 1:
        safe_print(f"   BLE scan iteration took {duration:.2f} s, too slow")
        time_slow += 1
        time_fast = 0
        if time_slow >= 5:
            safe_print(f"{datetime.now().strftime('%d.%m.%Y-%H:%M:%S')} S400 * Reading BLE data failed, finished BLE scan")
            stop_event.set()
    else:
        time_fast += 1
        if time_fast >= 5 and time_slow < 5:
            time_slow = 0
            time_fast = 0

# Detecting an incorrect BLE KEY
ble_key = bytes.fromhex(ble_miscale_key)
xiaomi_parser = XiaomiBluetoothDeviceData(bindkey=ble_key)
logger = logging.getLogger("xiaomi_ble.parser")
logger.setLevel(logging.DEBUG)
time_log = 0
stop_event = asyncio.Event()
class DecryptionFailedHandler(logging.Handler):
    def emit(self, record):
        global time_log
        msg = record.getMessage()
        if "Decryption failed" in msg:
            now = time.time()
            if now - time_log > 1:
                safe_print(f"{datetime.now().strftime('%d.%m.%Y-%H:%M:%S')} S400 * Decryption failed, finished BLE scan")
                time_log = now
            stop_event.set()
handler = DecryptionFailedHandler()
logger.addHandler(handler)

# Reading data from a scale using a BLE adapter
time_found = 0
mac_seen_event = asyncio.Event()
def detection_callback(device, advertisement_data):
    try:
        global time_found
        if device.address.upper() != ble_miscale_mac.upper():
            return
        safe_print(f"  BLE device found with address: {device.address.upper()}")
        now = time.monotonic()
        if time_found == 0:
            time_found = now
        else:
            duration = now - time_found
            handle_timing(duration)
            time_found = now
        mac_seen_event.set()
        service_info = BluetoothServiceInfo(name=device.name,address=device.address,rssi=advertisement_data.rssi,manufacturer_data=advertisement_data.manufacturer_data,service_data=advertisement_data.service_data,service_uuids=advertisement_data.service_uuids,source=device.address)
        if xiaomi_parser.supported(service_info):
            update = xiaomi_parser.update(service_info)
            if update and update.entity_values:
                fields = {'Mass','Impedance','Impedance Low','Heart Rate'}
                values = {v.name: v.native_value for v in update.entity_values.values() if v.name in fields}
                if fields <= values.keys():
                    safe_print(f"{datetime.now().strftime('%d.%m.%Y-%H:%M:%S')} S400 * Reading BLE data complete, finished BLE scan")
                    safe_print(f"to_import;{int(time.time())};{values['Mass']};{values['Impedance']:.0f};{values['Impedance Low']:.0f};{values['Heart Rate']}")
                    stop_event.set()
    except Exception:
        pass

# Watchdog for entire loop
async def watchdog(timeout=30):
    while not stop_event.is_set():
        await asyncio.sleep(1)
        if time.time() - time_print > timeout:
            safe_print(f"{datetime.now().strftime('%d.%m.%Y-%H:%M:%S')} S400 * Reading BLE data failed, finished BLE scan")
            stop_event.set()

# Searching for scale, 5 attempts
time_not_found = 0
async def main():
    global time_not_found
    asyncio.create_task(watchdog(30))
    safe_print(f"{datetime.now().strftime('%d.%m.%Y-%H:%M:%S')} * Starting scan with BLE adapter hci{ble_arg_hci}({ble_arg_mac}):")
    attempts = 0
    while attempts < 5 and not stop_event.is_set():
        mac_seen_event.clear()
        scanner = BleakScanner(detection_callback=detection_callback)
        scan_started = False
        try:
            await scanner.start()
            scan_started = True
            await asyncio.wait_for(mac_seen_event.wait(), timeout=0.5)
            await stop_event.wait()
            break
        except asyncio.TimeoutError:
            safe_print(f"  BLE device not found with address: {ble_miscale_mac.upper()}")
            now = time.monotonic()
            if time_not_found == 0:
                time_not_found = now
            else:
                duration = now - time_not_found
                handle_timing(duration)
                time_not_found = now
            attempts += 1
        finally:
            if scan_started:
                try:
                    await scanner.stop()
                except Exception:
                    pass
    if not stop_event.is_set():
        safe_print(f"{datetime.now().strftime('%d.%m.%Y-%H:%M:%S')} S400 * Reading BLE data failed, finished BLE scan")

# Main program loop
if __name__ == "__main__":
    asyncio.run(main())