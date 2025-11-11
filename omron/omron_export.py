#!/usr/bin/python3

import os
import csv
from datetime import datetime as dt
from garminconnect import Garmin

# Version info
print("""
==============================================
Export 2 Garmin Connect v3.0 (omron_export.py)
==============================================
""")

# Importing user variables from a file
path = os.path.dirname(os.path.dirname(__file__))
with open(path + '/user/export2garmin.cfg', 'r') as file:
    for line in file:
        line = line.strip()
        if line.startswith('omron_export_category'):
            name, value = line.split('=')
            globals()[name.strip()] = value.strip()

# Import data variables from a file
with open(path + '/user/omron_backup.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row in csv_reader:
        if str(row[0]) in ["failed", "to_import"]:
            unixtime = int(row[1])
            omrondate = str(row[2])
            omrontime = str(row[3])
            systolic = int(row[4])
            diastolic = int(row[5])
            pulse = int(row[6])
            MOV = int(row[7])
            IHB = int(row[8])
            emailuser = str(row[9])

            # Determine blood pressure category
            omron_export_category = str(omron_export_category)
            category = "None"
            if omron_export_category == 'eu':
                if systolic < 130 and diastolic < 85:
                    category = "Normal"
                elif (130 <= systolic <= 139 and diastolic < 85) or (systolic < 130 and 85 <= diastolic <= 89):
                    category = "High-Normal"
                elif (140 <= systolic <= 159 and diastolic < 90) or (systolic < 140 and 90 <= diastolic <= 99):
                    category = "Grade_1"
                elif (160 <= systolic <= 179 and diastolic < 100) or (systolic < 160 and 100 <= diastolic <= 109):
                    category = "Grade_2"                 
            elif omron_export_category == 'us':
                if systolic < 120 and diastolic < 80:
                    category = "Normal"
                elif (120 <= systolic <= 129) and diastolic < 80:
                    category = "High-Normal"
                elif (130 <= systolic <= 139) or (80 <= diastolic <= 89):
                    category = "Grade_1"
                elif (systolic >= 140) or (diastolic >= 90):
                    category = "Grade_2"

            # Print to temp.log file
            print(f"OMRON * Import data: {unixtime};{omrondate};{omrontime};{systolic:.0f};{diastolic:.0f};{pulse:.0f};{MOV:.0f};{IHB:.0f};{emailuser}")
            print(f"OMRON * Calculated data: {category};{MOV:.0f};{IHB:.0f};{emailuser};{dt.now().strftime('%d.%m.%Y;%H:%M')}")

            # Login to Garmin Connect
            with open(path + '/user/' + emailuser, 'r') as token_file:
                tokenstore = token_file.read()
                garmin = Garmin()
                garmin.login(tokenstore)

                # Upload data to Garmin Connect
                garmin.set_blood_pressure(timestamp=dt.fromtimestamp(unixtime).isoformat(),diastolic=diastolic,systolic=systolic,pulse=pulse)
                print("OMRON * Upload status: OK")
            break