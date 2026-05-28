import datetime
import logging
import sys

logger = logging.getLogger("omblepy")

sys.path.append('..')
from sharedDriver import sharedDeviceDriverCode


class deviceSpecificDriver(sharedDeviceDriverCode):
    """Driver for Omron BP5360 (HEM-7377T1-ZAZ).

    Same Omron HEM-7361T-family record format and same vendor service UUIDs
    as HEM-7380T1, but with a different memory layout (record area starts
    8 bytes into the user data region — a header precedes the records).

    Authentication: OS-managed BLE bond only. The device does NOT respond to
    omblepy's 0x02/0x00/0x01 key programming flow at all (verified across 20+
    attempts with various orderings). Pair through the OS BLE stack first
    (bluetoothctl on Linux, Settings on Windows), then read with this driver.

    Time sync: requires a non-obvious byte-14 counter increment quirk at
    EEPROM 0x0088 (returning 0xe5 / "Err" otherwise). Not implemented in this
    driver yet — run without -t / --timeSync. See PR description for details.
    """
    parentService_UUID         = "0000fe4a-0000-1000-8000-00805f9b34fb"
    deviceRxChannelUUIDs       = ["49123040-aee8-11e1-a74d-0002a5d5c51b"]
    deviceTxChannelUUIDs       = ["db5b55e0-aee7-11e1-965e-0002a5d5c51b"]
    requiresUnlock             = False
    supportsPairing            = False
    supportsOsBondingOnly      = True

    deviceEndianess            = "little"
    # Two record slots; matches HEM-7380T1 layout. NOTE on user identification:
    # the cuff stores BOTH "User 1" and "User 2" measurements in slot index 1
    # (0x080C); they are distinguished by metadata bytes within the record
    # itself. byte 13 is consistently 0x01 for User 1 records, 0xFF for User 2
    # records. Bytes 8-15 hold structured metadata for User 1 (sequence
    # counter at byte 9, etc.) and are all-FF for User 2. Guest measurements
    # are not stored to EEPROM at all (verified empirically). The slot at
    # 0x01CC is reserved but appears unused on the BP5360 sample tested.
    userStartAdressesList      = [0x01CC, 0x080C]
    perUserRecordsCountList    = [100, 100]
    recordByteSize             = 0x10
    transmissionBlockSize      = 0x38

    # Settings region: time data lives in the first 16 bytes of a 0x18-byte
    # status block at 0x0040, and the time-sync write target is 0x0088.
    # (settingsUnreadRecordsBytes is set to a zero-length range because BP5360's
    # unread-record counter location isn't yet mapped — --newRecOnly will
    # behave as if no records are unread until that's investigated.)
    settingsReadAddress        = 0x0040
    settingsWriteAddress       = 0x0088
    settingsUnreadRecordsBytes = [0x00, 0x00]
    settingsTimeSyncBytes      = [0x00, 0x10]

    def deviceSpecific_ParseRecordFormat(self, singleRecordAsByteArray):
        # HEM-7361T-family bit layout (BP5360 uses the same record format).
        # Detect empty / non-record slots up front to keep omblepy's parse-error
        # warnings clean: BP5360's unused user slot contains daily-summary or
        # similar metadata that decodes to nonsense dates if pushed through the
        # full parser.
        year = self._bytearrayBitsToInt(singleRecordAsByteArray, 98, 103) + 2000
        if year < 2020:
            raise ValueError("record slot is empty")
        month = self._bytearrayBitsToInt(singleRecordAsByteArray, 82, 85)
        day = self._bytearrayBitsToInt(singleRecordAsByteArray, 86, 90)
        hour = self._bytearrayBitsToInt(singleRecordAsByteArray, 91, 95)
        minute = self._bytearrayBitsToInt(singleRecordAsByteArray, 68, 73)
        if not (1 <= month <= 12) or not (1 <= day <= 31) or hour > 23 or minute > 59:
            raise ValueError("record slot is empty")

        second = self._bytearrayBitsToInt(singleRecordAsByteArray, 74, 79)
        second = min([second, 59])  # field can range up to 63 in some records

        recordDict = dict()
        recordDict["mov"] = self._bytearrayBitsToInt(singleRecordAsByteArray, 80, 80)
        recordDict["ihb"] = self._bytearrayBitsToInt(singleRecordAsByteArray, 81, 81)
        recordDict["bpm"] = self._bytearrayBitsToInt(singleRecordAsByteArray, 104, 111)
        recordDict["dia"] = self._bytearrayBitsToInt(singleRecordAsByteArray, 112, 119)
        recordDict["sys"] = self._bytearrayBitsToInt(singleRecordAsByteArray, 120, 127) + 25

        # Range sanity (matches the standalone implementation; defends against
        # rare corruption of stored records).
        if not (60 <= recordDict["sys"] <= 250) or not (30 <= recordDict["dia"] <= 150) or not (30 <= recordDict["bpm"] <= 200):
            raise ValueError("record values out of physiological range")

        recordDict["datetime"] = datetime.datetime(year, month, day, hour, minute, second)
        return recordDict

    def deviceSpecific_syncWithSystemTime(self):
        # BP5360 byte-14 turns out to be a CHECKSUM of bytes 0-13 (sum & 0xff),
        # the same convention HEM-7361T uses. The "running counter" formula in
        # the original reverse engineering — old_byte14 + (new_sec - old_sec) + 1
        # — was a coincidence: when only the second byte changes by +N (and
        # byte 4 changes from 0x00 to 0x01), the checksum delta IS exactly
        # N + 1, so the additive formula matched in the common case. It breaks
        # when seconds wrap (negative delta) or when other date bytes change.
        # Computing the checksum directly works in all cases.
        timeSyncSettingsCopy = self.cachedSettingsBytes[slice(*self.settingsTimeSyncBytes)]
        old_byte14 = timeSyncSettingsCopy[14]

        currentTime = datetime.datetime.now()

        # Build the new time block. Bytes 0-7 are preserved from the device read;
        # byte 4 is forced to 0x01 (required by BP5360 firmware — purpose unclear
        # from reverse engineering, but consistently sent by the Android app).
        setNewTimeDataBytes = bytearray(timeSyncSettingsCopy[0:8])
        setNewTimeDataBytes[4] = 0x01
        setNewTimeDataBytes += bytes([
            currentTime.year - 2000,
            currentTime.month,
            currentTime.day,
            currentTime.hour,
            currentTime.minute,
            currentTime.second,
        ])
        # byte 14 = checksum over bytes 0-13; byte 15 = 0
        checksum = sum(setNewTimeDataBytes) & 0xFF
        setNewTimeDataBytes += bytes([checksum, 0x00])

        self.cachedSettingsBytes[slice(*self.settingsTimeSyncBytes)] = setNewTimeDataBytes
        logger.info(f"BP5360 time set to {currentTime.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"(byte14 checksum: 0x{old_byte14:02x} -> 0x{checksum:02x})")
