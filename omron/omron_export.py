#!/usr/bin/python3

import os
import datetime
import csv
from datetime import datetime as dt
from garminconnect import Garmin

# Version Info
print("Export 2 Garmin Connect v1.3 (omron_export.py)")
print("")

# Import data from a file
path = os.path.dirname(os.path.dirname(__file__))
unixtime = 0
emailuser = ""
diastolic = 0
systolic = 0
pulse = 0

with open(path + '/user/omron_backup.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        if str(row[0]) in ["failed", "to_import"]:
            unixtime = int(row[1])
            emailuser = str(row[2])
            omrondate = str(row[3])
            omrontime = str(row[4])
            diastolic = int(row[5])
            systolic = int(row[6])
            pulse = int(row[7])
            MOV = int(row[8])
            IHB = int(row[9])

            # Print to temp.log file
            print(f"OMRON * Import data: {unixtime};{emailuser};{omrondate};{omrontime};{diastolic:.0f};{systolic:.0f};{pulse:.0f};{MOV:.0f};{IHB:.0f}")
            print(f"OMRON * Export date time: {datetime.datetime.now().strftime('%d.%m.%Y;%H:%M')}")

            # Login to Garmin Connect
            dir_path = os.path.expanduser(path + '/user/' + emailuser)
            with open(dir_path, "r") as token_file:
                tokenstore = token_file.read()
                garmin = Garmin()
                garmin.login(tokenstore)

                # Upload data to Garmin Connect
                garmin.set_blood_pressure(timestamp=dt.fromtimestamp(unixtime).isoformat(),diastolic=diastolic,systolic=systolic,pulse=pulse)
                print("OMRON * Upload status: OK")
            break