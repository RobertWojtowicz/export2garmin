import datetime
import logging
import sys

logger = logging.getLogger("omblepy")

sys.path.append('..')
from sharedDriver import sharedDeviceDriverCode


class deviceSpecificDriver(sharedDeviceDriverCode):
    parentService_UUID    = "0000fe4a-0000-1000-8000-00805f9b34fb"
    deviceRxChannelUUIDs  = ["49123040-aee8-11e1-a74d-0002a5d5c51b"]
    deviceTxChannelUUIDs  = ["db5b55e0-aee7-11e1-965e-0002a5d5c51b"]

    requiresUnlock        = False
    supportsPairing       = False
    supportsOsBondingOnly = True

    deviceEndianess       = "little"
    userStartAdressesList = [0x01C8]
    perUserRecordsCountList = [100]
    recordByteSize        = 0x10
    transmissionBlockSize = 0x10

    settingsReadAddress = None
    settingsWriteAddress = None
    settingsUnreadRecordsBytes = None
    settingsTimeSyncBytes = None

    def deviceSpecific_ParseRecordFormat(self, b):
        recordDict = {}

        flags1 = b[0] | (b[1] << 8)
        flags2 = b[2] | (b[3] << 8)

        hour = flags1 & 0x1F
        day = (flags1 >> 5) & 0x1F
        month = (flags1 >> 10) & 0x0F

        second = min(flags2 & 0x3F, 59)
        minute = (flags2 >> 6) & 0x3F

        recordDict["sys"] = b[12] + 25
        recordDict["dia"] = b[13]
        recordDict["bpm"] = b[14]
        year = 2000 + b[15]

        recordDict["datetime"] = datetime.datetime(year, month, day, hour, minute, second)
        recordDict["mov"] = 0
        recordDict["ihb"] = 0

        return recordDict

    def deviceSpecific_syncWithSystemTime(self):
        raise ValueError("not supported")
