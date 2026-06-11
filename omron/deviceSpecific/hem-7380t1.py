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
    transmissionBlockSize      = 0x38

    settingsReadAddress        = None
    settingsWriteAddress       = None
    settingsUnreadRecordsBytes = None
    settingsTimeSyncBytes      = None

    def deviceSpecific_ParseRecordFormat(self, singleRecordAsByteArray):
        rawSys = singleRecordAsByteArray[0]
        if rawSys > 0xE1:
            raise ValueError("record slot is empty")

        recordDict = dict()
        recordDict["sys"] = rawSys + 25
        recordDict["dia"] = singleRecordAsByteArray[1]
        recordDict["bpm"] = singleRecordAsByteArray[2]

        year   = 2000 + (singleRecordAsByteArray[3] & 0x3F)
        flags1 = singleRecordAsByteArray[4] | (singleRecordAsByteArray[5] << 8)
        flags2 = singleRecordAsByteArray[6] | (singleRecordAsByteArray[7] << 8)

        recordDict["hour"] = flags1 & 0x1F
        day                = (flags1 >> 5) & 0x1F
        month              = (flags1 >> 10) & 0x0F
        recordDict["ihb"]  = (flags1 >> 14) & 0x01
        recordDict["mov"]  = (flags1 >> 15) & 0x01
        second             = min(flags2 & 0x3F, 59)
        minute             = (flags2 >> 6) & 0x3F

        recordDict["datetime"] = datetime.datetime(
            year,
            month,
            day,
            recordDict["hour"],
            minute,
            second,
        )
        del recordDict["hour"]
        return recordDict

    def deviceSpecific_syncWithSystemTime(self):
        raise ValueError("not supported")
