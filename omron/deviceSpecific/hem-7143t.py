import datetime
import logging
import sys

logger = logging.getLogger("omblepy")

sys.path.append('..')
from sharedDriver import sharedDeviceDriverCode


class deviceSpecificDriver(sharedDeviceDriverCode):
    """
    Verified on a HEM-7143T2-ESL with firmware SI.S01.16.02 against the device display.
    Same memory layout as the HEM-7146T (X2 Smart+) profile in UBPM.
    Unread counter (-n) is not supported.
    """
    parentService_UUID         = "0000fe4a-0000-1000-8000-00805f9b34fb"
    deviceRxChannelUUIDs       = ["49123040-aee8-11e1-a74d-0002a5d5c51b"]
    deviceTxChannelUUIDs       = ["db5b55e0-aee7-11e1-965e-0002a5d5c51b"]
    requiresUnlock             = False
    supportsPairing            = False
    supportsOsBondingOnly      = True  #OS-managed BLE bond only, no unlock key.

    deviceEndianess            = "little"
    userStartAdressesList      = [0x2e8]
    perUserRecordsCountList    = [30]
    recordByteSize             = 0x0e
    transmissionBlockSize      = 0x2c

    settingsReadAddress        = 0x0260
    settingsWriteAddress       = 0x02a4
    settingsUnreadRecordsBytes = None
    settingsTimeSyncBytes      = None

    def deviceSpecific_ParseRecordFormat(self, singleRecordAsByteArray):
        checksum = sum(singleRecordAsByteArray[:12]) & 0xFF
        if singleRecordAsByteArray[12] != checksum or singleRecordAsByteArray[13] != checksum ^ 0xFF:
            raise ValueError("record checksum mismatch")
        recordDict = dict()
        recordDict["sys"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 104, 111) + 25
        recordDict["dia"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 96, 103)
        recordDict["bpm"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 88, 95)
        year                   = self._bytearrayBitsToInt(singleRecordAsByteArray, 82, 87) + 2000
        hour                   = self._bytearrayBitsToInt(singleRecordAsByteArray, 75, 79)
        day                    = self._bytearrayBitsToInt(singleRecordAsByteArray, 70, 74)
        month                  = self._bytearrayBitsToInt(singleRecordAsByteArray, 66, 69)
        recordDict["ihb"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 65, 65)
        recordDict["mov"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 64, 64)
        second                 = self._bytearrayBitsToInt(singleRecordAsByteArray, 58, 63)
        if second == 63: #A second field of 63 marks a reading taken while the device clock was not set. Records carry no usable time in this case.
            raise ValueError("clock not valid when the reading was taken")
        minute                 = self._bytearrayBitsToInt(singleRecordAsByteArray, 52, 57)
        _sequenceNum           = self._bytearrayBitsToInt(singleRecordAsByteArray, 16, 31)
        second                 = min([second, 59]) #for some reason the second value can range up to 63
        recordDict["datetime"] = datetime.datetime(year, month, day, hour, minute, second)
        return recordDict

    def deviceSpecific_syncWithSystemTime(self):
        raise ValueError("Not supported yet.")
