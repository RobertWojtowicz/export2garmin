#!/usr/bin/python3

# Version info
# ================================================
# Export 2 Garmin Connect v3.6 (omblepy.py)
# ================================================

import asyncio                                                      #avoid wait on bluetooth stack stalling the application
import terminaltables                                               #for pretty selection table for ble devices
import bleak                                                        #bluetooth low energy package for python
import re                                                           #regex to match bt mac address
import argparse                                                     #to process command line arguments
import datetime
import time
import sys
import pathlib
import logging
import csv
import os

#global constants
parentService_UUID        = "ecbe3980-c9a2-11e1-b1bd-0002a5d5c51b"

#global variables
bleClient           = None
examplePairingKey   = bytearray.fromhex("deadbeaf12341234deadbeaf12341234") #arbitrary choise
deviceSpecific      = None                            #imported module for each device
logger              = logging.getLogger("omblepy")

# Code change for Export2Garmin
path = os.path.dirname(os.path.dirname(__file__))
with open(path + '/user/export2garmin.cfg', 'r') as file:
    for line in file:
        line = line.strip()
        if line.startswith('switch_temp_path'):
            name, value = line.split('=')
            globals()[name.strip()] = value.strip()

def convertByteArrayToHexString(array):
    return (bytes(array).hex())

class bluetoothTxRxHandler:
    #BTLE Characteristic IDs
    deviceRxChannelUUIDs  = [
                                "49123040-aee8-11e1-a74d-0002a5d5c51b",
                                "4d0bf320-aee8-11e1-a0d9-0002a5d5c51b",
                                "5128ce60-aee8-11e1-b84b-0002a5d5c51b",
                                "560f1420-aee8-11e1-8184-0002a5d5c51b"
                            ]
    deviceTxChannelUUIDs  = [
                                "db5b55e0-aee7-11e1-965e-0002a5d5c51b",
                                "e0b8a060-aee7-11e1-92f4-0002a5d5c51b",
                                "0ae12b00-aee8-11e1-a192-0002a5d5c51b",
                                "10e1ba60-aee8-11e1-89e5-0002a5d5c51b"
                            ]
    deviceDataRxChannelIntHandles = [0x360, 0x370, 0x380, 0x390]
    deviceUnlock_UUID         = "b305b680-aee7-11e1-a730-0002a5d5c51b"

    def __init__(self, pairing = False):
        self.currentRxNotifyStateFlag   = False
        self.rxPacketType               = None
        self.rxEepromAddress            = None
        self.rxDataBytes                = None
        self.rxFinishedFlag             = False
        self.rxRawChannelBuffer         = [None] * 4 #a buffer for each channel

    async def _enableRxChannelNotifyAndCallback(self):
        if(self.currentRxNotifyStateFlag != True):
            for rxChannelUUID in self.deviceRxChannelUUIDs:
                await bleClient.start_notify(rxChannelUUID, self._callbackForRxChannels)
            self.currentRxNotifyStateFlag = True

    async def _disableRxChannelNotifyAndCallback(self):
        if(self.currentRxNotifyStateFlag != False):
            for rxChannelUUID in self.deviceRxChannelUUIDs:
                await bleClient.stop_notify(rxChannelUUID)
            self.currentRxNotifyStateFlag = False

    def _callbackForRxChannels(self, BleakGATTChar, rxBytes):
        if type(BleakGATTChar) is int:
            rxChannelId = self.deviceDataRxChannelIntHandles.index(BleakGATTChar)
        else:
            rxChannelId = self.deviceDataRxChannelIntHandles.index(BleakGATTChar.handle)
        self.rxRawChannelBuffer[rxChannelId] = rxBytes

        logger.debug(f"rx ch{rxChannelId} < {convertByteArrayToHexString(rxBytes)}")
        if self.rxRawChannelBuffer[0]:                               #if there is data present in the first rx buffer
            packetSize       = self.rxRawChannelBuffer[0][0]
            requiredChannels = range((packetSize + 15) // 16)
            #are all required channels already recieved
            for channelIdx in requiredChannels:
                if self.rxRawChannelBuffer[channelIdx] is None:         #if one of the required channels is empty wait for more packets to arrive
                    return

            #check crc
            combinedRawRx = bytearray()
            for channelIdx in requiredChannels:
                combinedRawRx += self.rxRawChannelBuffer[channelIdx]
            combinedRawRx = combinedRawRx[:packetSize]          #cut extra bytes from the end
            xorCrc = 0
            for byte in combinedRawRx:
                xorCrc ^= byte
            if(xorCrc):
                raise ValueError(f"data corruption in rx\ncrc: {xorCrc}\ncombniedBuffer: {convertByteArrayToHexString(combinedRawRx)}")
                return
            #extract information
            self.rxPacketType       = combinedRawRx[1:3]
            self.rxEepromAddress    = combinedRawRx[3:5]
            expectedNumDataBytes    = combinedRawRx[5]
            if(expectedNumDataBytes > (len(combinedRawRx) - 8)):
                self.rxDataBytes    = bytes(b'\xff') * expectedNumDataBytes
            else:
                if(self.rxPacketType) == bytearray.fromhex("8f00"): #need special case for end of transmission packet, otherwise transmission error code is not accessible
                    self.rxDataBytes = combinedRawRx[6:7]
                else:
                    self.rxDataBytes    = combinedRawRx[6: 6 + expectedNumDataBytes]
            self.rxRawChannelBuffer = [None] * 4 #clear channel buffers
            self.rxFinishedFlag     = True
            return
        return

    async def _waitForRxOrRetry(self, command, timeoutS = 1.0):
        self.rxFinishedFlag = False
        retries = 0
        while True:
            commandCopy = command
            requiredTxChannels = range((len(command) + 15) // 16)
            for channelIdx in requiredTxChannels:
                logger.debug(f"tx ch{channelIdx} > {convertByteArrayToHexString(commandCopy[:16])}")
                await bleClient.write_gatt_char(self.deviceTxChannelUUIDs[channelIdx], commandCopy[:16])
                commandCopy = commandCopy[16:]

            currentTimeout = timeoutS
            while(self.rxFinishedFlag == False):
                await asyncio.sleep(0.1)
                currentTimeout -= 0.1
                if(currentTimeout < 0):
                    break
            if(currentTimeout >= 0):
                break
            retries += 1
            logger.warning(f"Transmission failed, count of retries: {retries} / 5")
            if(retries >= 5):
                ValueError("Same transmission failed 5 times, abort")
                return

    async def startTransmission(self):
        await self._enableRxChannelNotifyAndCallback()
        startDataReadout    = bytearray.fromhex("0800000000100018")
        await self._waitForRxOrRetry(startDataReadout)
        if(self.rxPacketType != bytearray.fromhex("8000")):
            raise ValueError("invalid response to data readout start")

    async def endTransmission(self):
        stopDataReadout         = bytearray.fromhex("080f000000000007")
        await self._waitForRxOrRetry(stopDataReadout)
        if(self.rxPacketType != bytearray.fromhex("8f00")):
            raise ValueError("invlid response to data readout end")
            return
        if(self.rxDataBytes[0]):
            raise ValueError(f"Device reported error status code {self.rxDataBytes[0]} while sending endTransmission command.")
            return
        await self._disableRxChannelNotifyAndCallback()

    async def _writeBlockEeprom(self, address, dataByteArray):
        dataWriteCommand = bytearray()
        dataWriteCommand += (len(dataByteArray) + 8).to_bytes(1, 'big') #total packet size with 6byte header and 2byte crc
        dataWriteCommand += bytearray.fromhex("01c0")
        dataWriteCommand += address.to_bytes(2, 'big')
        dataWriteCommand += len(dataByteArray).to_bytes(1, 'big')
        dataWriteCommand += dataByteArray
        #calculate and append crc
        xorCrc = 0
        for byte in dataWriteCommand:
            xorCrc ^= byte
        dataWriteCommand += b'\x00'
        dataWriteCommand.append(xorCrc)
        await self._waitForRxOrRetry(dataWriteCommand)
        if(self.rxEepromAddress != address.to_bytes(2, 'big')):
            raise ValueError(f"recieved packet address {self.rxEepromAddress} does not match the written address {address.to_bytes(2, 'big')}")
        if(self.rxPacketType != bytearray.fromhex("81c0")):
            raise ValueError("Invalid packet type in eeprom write")
        return

    async def _readBlockEeprom(self, address, blocksize):
        dataReadCommand = bytearray.fromhex("080100")
        dataReadCommand += address.to_bytes(2, 'big')
        dataReadCommand += blocksize.to_bytes(1, 'big')
        #calculate and append crc
        xorCrc = 0
        for byte in dataReadCommand:
            xorCrc ^= byte
        dataReadCommand += b'\x00'
        dataReadCommand.append(xorCrc)
        await self._waitForRxOrRetry(dataReadCommand)
        if(self.rxEepromAddress != address.to_bytes(2, 'big')):
            raise ValueError(f"revieved packet address {self.rxEepromAddress} does not match requested address {address.to_bytes(2, 'big')}")
        if(self.rxPacketType != bytearray.fromhex("8100")):
            raise ValueError("Invalid packet type in eeprom read")
        return self.rxDataBytes

    async def writeContinuousEepromData(self, startAddress, bytesArrayToWrite, btBlockSize = 0x08):
        while(len(bytesArrayToWrite) != 0):
            nextSubblockSize = min(len(bytesArrayToWrite), btBlockSize)
            logger.debug(f"write to {hex(startAddress)} size {hex(nextSubblockSize)}")
            await self._writeBlockEeprom(startAddress, bytesArrayToWrite[:nextSubblockSize])
            bytesArrayToWrite = bytesArrayToWrite[nextSubblockSize:]
            startAddress += nextSubblockSize
        return

    async def readContinuousEepromData(self, startAddress, bytesToRead, btBlockSize = 0x10):
        eepromBytesData = bytearray()
        while(bytesToRead != 0):
            nextSubblockSize = min(bytesToRead, btBlockSize)
            logger.debug(f"read from {hex(startAddress)} size {hex(nextSubblockSize)}")
            eepromBytesData += await self._readBlockEeprom(startAddress, nextSubblockSize)
            startAddress    += nextSubblockSize
            bytesToRead     -= nextSubblockSize
        return eepromBytesData

    def _callbackForUnlockChannel(self, UUID_or_intHandle, rxBytes):
        self.rxDataBytes = rxBytes
        self.rxFinishedFlag = True
        return

    async def writeNewUnlockKey(self, newKeyByteArray = examplePairingKey):
        if(len(newKeyByteArray) != 16):
            raise ValueError(f"key has to be 16 bytes long, is {len(newKeyByteArray)}")
            return
        #enable key programming mode
        await bleClient.start_notify(self.deviceUnlock_UUID, self._callbackForUnlockChannel)
        self.rxFinishedFlag = False
        await bleClient.write_gatt_char(self.deviceUnlock_UUID, b'\x02' + b'\x00'*16, response=True)
        while(self.rxFinishedFlag == False):
            await asyncio.sleep(0.1)
        deviceResponse = self.rxDataBytes
        if(deviceResponse[:2] != bytearray.fromhex("8200")):
            raise ValueError(f"Could not enter key programming mode. Has the device been started in pairing mode? Got response: {deviceResponse}")
            return
        #program new key
        self.rxFinishedFlag = False
        await bleClient.write_gatt_char(self.deviceUnlock_UUID, b'\x00' + newKeyByteArray, response=True)
        while(self.rxFinishedFlag == False):
            await asyncio.sleep(0.1)
        deviceResponse = self.rxDataBytes
        if(deviceResponse[:2] != bytearray.fromhex("8000")):
            raise ValueError(f"Failure to program new key. Response: {deviceResponse}")
            return
        await bleClient.stop_notify(self.deviceUnlock_UUID)
        logger.info(f"Paired device successfully with new key {newKeyByteArray}.")
        logger.info("From now on you can connect omit the -p flag, even on other PCs with different bluetooth-mac-addresses.")
        return

    async def unlockWithUnlockKey(self, keyByteArray = examplePairingKey):
        await bleClient.start_notify(self.deviceUnlock_UUID, self._callbackForUnlockChannel)
        self.rxFinishedFlag = False
        await bleClient.write_gatt_char(self.deviceUnlock_UUID, b'\x01' + keyByteArray, response=True)
        while(self.rxFinishedFlag == False):
            await asyncio.sleep(0.1)
        deviceResponse = self.rxDataBytes
        if(deviceResponse[:2] !=  bytearray.fromhex("8100")):
            raise ValueError(f"entered pairing key does not match stored one.")
            return
        await bleClient.stop_notify(self.deviceUnlock_UUID)
        return

# Code change for Export2Garmin
def readCsv(filename):
    records = []
    with open(filename, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile, delimiter=';')
        for oldRecordDict in reader:
            oldRecordDict["datetime"] = datetime.datetime.strptime(oldRecordDict["datetime"], "%d.%m.%Y %H:%M")
            records.append(oldRecordDict)
    return records
def appendCsv(allRecords):
    for userIdx in range(len(allRecords)):
        oldCsvFile = pathlib.Path(f"{switch_temp_path}/omron_user{userIdx+1}.csv")
        datesOfNewRecords = [record["datetime"] for record in allRecords[userIdx]]
        if(oldCsvFile.is_file()):
            records = readCsv(f"{switch_temp_path}/omron_user{userIdx+1}.csv")
            allRecords[userIdx].extend(filter(lambda x: x["datetime"] not in datesOfNewRecords,records))
        allRecords[userIdx] = sorted(allRecords[userIdx], key = lambda x: x["datetime"])
        logger.info(f"writing data to omron_user{userIdx+1}.csv")
        with open(f"{switch_temp_path}/omron_user{userIdx+1}.csv", mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, delimiter=';', fieldnames = ["Data Status", "Unix Time", "datetime", "sys", "dia", "bpm", "mov", "ihb", "User"])
            writer.writeheader()
            for recordDict in allRecords[userIdx]:
                recordDict["Data Status"] = "to_import"
                recordDict["Unix Time"] = int(time.mktime(recordDict["datetime"].timetuple()))
                recordDict["datetime"] = recordDict["datetime"].strftime("%d.%m.%Y %H:%M")
                recordDict["User"] = (f"user{userIdx+1}")
                writer.writerow(recordDict)

# Code change for Export2Garmin
async def selectBLEdevices(adapter):
    print("Select your Omron device from the list below...")
    while(True):
        devices = await bleak.BleakScanner.discover(adapter=adapter, return_adv=True)
        devices = list(sorted(devices.items(), key = lambda x: x[1][1].rssi, reverse=True))
        tableEntries = []
        tableEntries.append(["ID", "MAC", "NAME", "RSSI"])
        for deviceIdx, (macAddr, (bleDev, advData)) in enumerate(devices):
            tableEntries.append([deviceIdx, macAddr, bleDev.name, advData.rssi])
        print(terminaltables.AsciiTable(tableEntries).table)
        res = input("Enter ID or just press Enter to rescan.\n")
        if(res.isdigit() and int(res) in range(len(devices))):
            break
    return devices[int(res)][0]

async def main():
    global bleClient
    global deviceSpecific
    parser = argparse.ArgumentParser(description="python tool to read the records of omron blood pressure instruments")
    parser.add_argument('-d', "--device",     required="true", type=ascii,  help="Device name (e.g. HEM-7322T-D).")
    parser.add_argument("--loggerDebug",      action="store_true",          help="Enable verbose logger output")
    parser.add_argument("-p", "--pair",       action="store_true",          help="Programm the pairing key into the device. Needs to be done only once.")
    parser.add_argument("-m", "--mac",                          type=ascii, help="Bluetooth Mac address of the device (e.g. 00:1b:63:84:45:e6). If not specified, will scan for devices and display a selection dialog.")
    parser.add_argument('-n', "--newRecOnly", action="store_true",          help="Considers the unread records counter and only reads new records. Resets these counters afterwards. If not enabled, all records are read and the unread counters are not cleared.")
    parser.add_argument('-t', "--timeSync",   action="store_true",          help="Update the time on the omron device by using the current system time.")

    # Code change for Export2Garmin
    parser.add_argument('-a', "--adapter", required="true", type=str,       help="Choose which HCI adapter you want to scan with (e.g. hci0).")
    args = parser.parse_args()

    #setup logging
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if(args.loggerDebug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    #import device specific module
    if(not args.pair and not args.device):
        raise ValueError("When not in pairing mode, please specify your device type name with -d or --device")
        return
    if(args.device):
        deviceName = args.device.strip("'").strip('\"') #strip quotes around arg

        # Code change for Export2Garmin
        sys.path.insert(0, path + "/omron/deviceSpecific")
        try:
            logger.info(f"Attempt to import module for device {deviceName.lower()}")
            deviceSpecific = __import__(deviceName.lower())
        except ImportError:
            raise ValueError("the device is no supported yet, you can help by contributing :)")
            return

    #select device mac address
    validMacRegex = re.compile(r"^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$")
    if(args.mac is not None):
        btmac = args.mac.strip("'").strip('\"') #strip quotes around arg
        if(validMacRegex.match(btmac) is None):
            raise ValueError(f"argument after -m or --mac {btmac} is not a valid mac address")
            return
        bleAddr = btmac
    else:
        print("To improve your chance of a successful connection please do the following:")
        print(" -remove previous device pairings in your OS's bluetooth dialog")
        print(" -enable bluetooth on you omron device and use the specified mode (pairing or normal)")
        print(" -do not accept any pairing dialog until you selected your device in the following list\n")
        
        # Code change for Export2Garmin
        bleAddr = await selectBLEdevices(adapter=args.adapter)
    bleClient = bleak.BleakClient(bleAddr, adapter=args.adapter)
    try:
        logger.info(f"Attempt connecting to {bleAddr}.")
        await bleClient.connect()
        await asyncio.sleep(10)   #time delay for user to accept os pairing dialog on win11
        await bleClient.pair(protection_level = 2)
        #verify that the device is an omron device by checking presence of certain bluetooth services
        if parentService_UUID not in [service.uuid for service in bleClient.services]:
            raise OSError("""Some required bluetooth attributes not found on this ble device.
                             This means that either, you connected to a wrong device,
                             or that your OS has a bug when reading BT LE device attributes (certain linux versions).""")
            return
        bluetoothTxRxObj = bluetoothTxRxHandler()
        if(args.pair):
            await bluetoothTxRxObj.writeNewUnlockKey()
            #this seems to be necessary when the device has not been paired to any device
            await bluetoothTxRxObj.startTransmission()
            await bluetoothTxRxObj.endTransmission()
        else:
            logger.info("communication started")
            devSpecificDriver = deviceSpecific.deviceSpecificDriver()
            allRecs = await devSpecificDriver.getRecords(btobj = bluetoothTxRxObj, useUnreadCounter = args.newRecOnly, syncTime = args.timeSync)
            logger.info("communication finished")
            appendCsv(allRecs)
    finally:
        logger.info("unpair and disconnect")
        if bleClient.is_connected:
            await bleClient.unpair()
            try:
                await bleClient.disconnect()
            except AssertionError as e:
                logger.error("Bleak AssertionError during disconnect. This usually happens when using the bluezdbus adapter.")
                logger.error("You can find the upstream issue at: https://github.com/hbldh/bleak/issues/641")
                logger.error(f"AssertionError details: {e}")

asyncio.run(main())