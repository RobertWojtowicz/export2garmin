import sys
import datetime
import logging
logger = logging.getLogger("omblepy")

sys.path.append('..')
from sharedDriver import sharedDeviceDriverCode

class deviceSpecificDriver(sharedDeviceDriverCode):
    deviceEndianess                 = "big"
    userStartAdressesList           = [0x2e8]
    perUserRecordsCountList         = [90]
    recordByteSize                  = 0x0e
    transmissionBlockSize           = 0x10
    
    settingsReadAddress             = 0x0260
    settingsWriteAddress            = 0x02a4

    #settingsUnreadRecordsBytes      = [0x00, 0x08]
    #settingsTimeSyncBytes           = [0x14, 0x1e]
    
    def deviceSpecific_ParseRecordFormat(self, singleRecordAsByteArray):
        recordDict             = dict()
        recordDict["dia"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 0,  7)
        recordDict["sys"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 8,  15) + 25
        year                   = self._bytearrayBitsToInt(singleRecordAsByteArray, 18, 23) + 2000
        recordDict["bpm"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 24, 31)
        recordDict["mov"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 32, 32)
        recordDict["ihb"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 33, 33)
        month                  = self._bytearrayBitsToInt(singleRecordAsByteArray, 34, 37)
        day                    = self._bytearrayBitsToInt(singleRecordAsByteArray, 38, 42)
        hour                   = self._bytearrayBitsToInt(singleRecordAsByteArray, 43, 47)
        minute                 = self._bytearrayBitsToInt(singleRecordAsByteArray, 52, 57)
        second                 = self._bytearrayBitsToInt(singleRecordAsByteArray, 58, 63)
        second                 = min([second, 59]) #for some reason the second value can range up to 63
        recordDict["datetime"] = datetime.datetime(year, month, day, hour, minute, second)
        return recordDict
    
    def deviceSpecific_syncWithSystemTime(self):
        raise ValueError("not supported")