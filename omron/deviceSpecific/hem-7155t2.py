# Omron X4 Smart HEM-7155T-ESL with the newer firmware ("WLD3.0", parent service FE4A instead of ecbe3980).
# The device does OS-level BLE bonding (Just Works) and uses a stateless 0x11/0x91 token handshake
# instead of a programmed unlock key. Record format is the same as hem-7155t, the EEPROM layout is not.
# Protocol details from the eigger/hass-omron profile "HEM-7155T-MW3" (alias HEM-7155T_ESL1).
#
# Pairing: hold the bluetooth button until "P" is shown, then run omblepy with -p.
# The pairing session also writes the settings mirror the official app writes, without it the
# device forgets the bond after the first session (HCI "PIN or Key Missing").
import importlib
import logging
logger = logging.getLogger("omblepy")

_hem7155t = importlib.import_module("hem-7155t").deviceSpecificDriver

class deviceSpecificDriver(_hem7155t):
    parentService_UUID              = "0000fe4a-0000-1000-8000-00805f9b34fb"
    deviceRxChannelUUIDs            = ["49123040-aee8-11e1-a74d-0002a5d5c51b"]
    deviceTxChannelUUIDs            = ["db5b55e0-aee7-11e1-965e-0002a5d5c51b"]
    deviceUnlock_UUID               = "b305b680-aee7-11e1-a730-0002a5d5c51b"
    requiresUnlock                  = False
    supportsPairing                 = False
    supportsOsBondingOnly           = True
    requiresTokenUnlock             = True
    keepNotifySubscriptions         = True

    userStartAdressesList           = [0x02E8, 0x06A8]
    perUserRecordsCountList         = [60   , 60   ]

    settingsReadAddress             = 0x0260
    settingsWriteAddress            = 0x02A4
    settingsUnreadRecordsBytes      = [0x00, 0x10]
    settingsTimeSyncBytes           = [0x2C, 0x3C]

    #settings mirror written at the end of the pairing session
    pairingRegistrationSlotOffset   = 0x18
    pairingRegistrationSlotSize     = 10
    #(offset, width, idle value) of the unread record counters in the index region
    pairingRegistrationUnreadCounters = [(0x04, 2, 0x8000), (0x06, 2, 0x8000)]

    def deviceSpecific_ParseRecordFormat(self, singleRecordAsByteArray):
        record = super().deviceSpecific_ParseRecordFormat(singleRecordAsByteArray)
        #empty or corrupted slots decode to nonsense (e.g. year 2000, dia 0), skip them
        if not (record["datetime"].year >= 2020 and 60 <= record["sys"] <= 260 and 30 <= record["dia"] <= 160 and 30 <= record["bpm"] <= 220):
            raise ValueError(f"implausible record {record}")
        return record
