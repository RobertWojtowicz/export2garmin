import datetime
import logging
import sys

logger = logging.getLogger("omblepy")

sys.path.append('..')
from sharedDriver import sharedDeviceDriverCode


class deviceSpecificDriver(sharedDeviceDriverCode):
    parentService_UUID         = "0000fe4a-0000-1000-8000-00805f9b34fb"
    deviceRxChannelUUIDs       = ["49123040-aee8-11e1-a74d-0002a5d5c51b"]
    deviceTxChannelUUIDs       = ["db5b55e0-aee7-11e1-965e-0002a5d5c51b"]
    requiresUnlock             = False
    supportsPairing            = False
    supportsOsBondingOnly      = True

    deviceEndianess            = "little"
    userStartAdressesList      = [0x01C4, 0x0804]
    perUserRecordsCountList    = [100, 100]
    recordByteSize             = 0x10
    transmissionBlockSize      = 0x10

    settingsReadAddress        = None
    settingsWriteAddress       = None
    settingsUnreadRecordsBytes = None
    settingsTimeSyncBytes      = None

    def deviceSpecific_ParseRecordFormat(self, singleRecordAsByteArray):
        recordDict             = dict()
        minute                 = self._bytearrayBitsToInt(singleRecordAsByteArray, 68, 73)
        second                 = self._bytearrayBitsToInt(singleRecordAsByteArray, 74, 79)
        second                 = min([second, 59]) #for some reason the second value can range up to 63
        recordDict["mov"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 80, 80)
        recordDict["ihb"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 81, 81)
        month                  = self._bytearrayBitsToInt(singleRecordAsByteArray, 82, 85)
        day                    = self._bytearrayBitsToInt(singleRecordAsByteArray, 86, 90)
        hour                   = self._bytearrayBitsToInt(singleRecordAsByteArray, 91, 95)
        year                   = self._bytearrayBitsToInt(singleRecordAsByteArray, 98, 103) + 2000
        recordDict["bpm"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 104, 111)
        recordDict["dia"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 112, 119)
        recordDict["sys"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 120,  127) + 25
        if recordDict["sys"] > 0xFA:
            raise ValueError("record slot is empty")
        recordDict["datetime"] = datetime.datetime(year, month, day, hour, minute, second)
        return recordDict

    def deviceSpecific_syncWithSystemTime(self):
        raise ValueError("not supported")
