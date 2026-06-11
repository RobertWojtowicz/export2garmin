#!/usr/bin/python3

import os
import csv
from collections import defaultdict
from datetime import datetime as dt, timedelta
from garminconnect import Garmin

# Version info
print("""
==============================================
Export 2 Garmin Connect v3.7 (omron_export.py)
==============================================
""")

path = os.path.dirname(os.path.dirname(__file__))
backup_file = path + '/user/omron_backup.csv'

# Defaults
omron_export_category = "eu"
omron_daily_filter = "all"

# Importing user variables from a file
with open(path + '/user/export2garmin.cfg', 'r') as file:
    for line in file:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name in ["omron_export_category", "omron_daily_filter"]:
            globals()[name] = value


def bp_category(systolic, diastolic):
    category = "None"

    if str(omron_export_category) == "eu":
        if systolic < 130 and diastolic < 85:
            category = "Normal"
        elif (130 <= systolic <= 139 and diastolic < 85) or (systolic < 130 and 85 <= diastolic <= 89):
            category = "High-Normal"
        elif (140 <= systolic <= 159 and diastolic < 90) or (systolic < 140 and 90 <= diastolic <= 99):
            category = "Grade_1"
        elif (160 <= systolic <= 179 and diastolic < 100) or (systolic < 160 and 100 <= diastolic <= 109):
            category = "Grade_2"

    elif str(omron_export_category) == "us":
        if systolic < 120 and diastolic < 80:
            category = "Normal"
        elif (120 <= systolic <= 129) and diastolic < 80:
            category = "High-Normal"
        elif (130 <= systolic <= 139) or (80 <= diastolic <= 89):
            category = "Grade_1"
        elif (systolic >= 140) or (diastolic >= 90):
            category = "Grade_2"

    return category


def average_records(records):
    """Return one averaged record, using the latest timestamp as upload timestamp."""
    latest = max(records, key=lambda r: r["unixtime"])
    source_indices = []
    for record in records:
        source_indices.extend(record["source_indices"])

    return {
        **latest,
        "systolic": round(sum(r["systolic"] for r in records) / len(records)),
        "diastolic": round(sum(r["diastolic"] for r in records) / len(records)),
        "pulse": round(sum(r["pulse"] for r in records) / len(records)),
        "MOV": max(r["MOV"] for r in records),
        "IHB": max(r["IHB"] for r in records),
        "source_indices": sorted(set(source_indices)),
    }


def find_truread_sessions(records, max_minutes=15):
    """
    Find TruRead-like sessions: 3 consecutive readings within max_minutes.
    Returns averaged session records.
    """
    records = sorted(records, key=lambda r: r["unixtime"])
    sessions = []

    i = 0
    while i <= len(records) - 3:
        session = records[i:i + 3]
        t1 = dt.fromtimestamp(session[0]["unixtime"])
        t3 = dt.fromtimestamp(session[2]["unixtime"])

        if t3 - t1 <= timedelta(minutes=max_minutes):
            sessions.append(average_records(session))
            i += 3
        else:
            i += 1

    return sessions


def select_daily_record(records, mode):
    records = sorted(records, key=lambda r: r["unixtime"])

    if mode == "latest":
        selected = records[-1]
        return {**selected, "source_indices": sorted(set(r["row_index"] for r in records))}

    if mode == "avg_all_raw":
        return average_records(records)

    if mode in ["first_truread", "latest_truread"]:
        sessions = find_truread_sessions(records)

        if sessions:
            if mode == "first_truread":
                selected = sessions[0]
            else:
                selected = sessions[-1]

            # Mark all pending records for that day/user as imported, not only
            # the three rows used for the TruRead average. Otherwise the
            # remaining rows would be retried on the next run.
            selected["source_indices"] = sorted(set(r["row_index"] for r in records))
            return selected

        # Fallback if no TruRead-like 3-reading session exists.
        return average_records(records)

    # Safe fallback
    return average_records(records)


def select_records_for_upload(records):
    mode = str(omron_daily_filter).strip().lower()

    if mode == "all":
        return sorted(records, key=lambda r: r["unixtime"])

    allowed_modes = ["all", "latest", "avg_all_raw", "first_truread", "latest_truread"]
    if mode not in allowed_modes:
        print(f"OMRON * Unknown omron_daily_filter={mode}, falling back to all")
        mode = "all"

    grouped = defaultdict(list)
    for record in records:
        day = dt.fromtimestamp(record["unixtime"]).strftime("%Y-%m-%d")
        grouped[(record["emailuser"], day)].append(record)

    selected = []
    for (_emailuser, _day), day_records in grouped.items():
        selected.append(select_daily_record(day_records, mode))

    return sorted(selected, key=lambda r: r["unixtime"])


def ensure_row_length(row, length=13):
    while len(row) < length:
        row.append("")
    return row


def write_backup(rows):
    with open(backup_file, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerows(rows)


# Read backup data
all_rows = []
records = []

with open(backup_file, 'r', newline='', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    for row_index, row in enumerate(csv_reader):
        if not row:
            continue

        row = ensure_row_length(row)
        all_rows.append(row)

        if row_index == 0:
            continue

        if row[0] not in ["failed", "to_import"]:
            continue

        records.append({
            "row_index": row_index,
            "source_indices": [row_index],
            "status": str(row[0]),
            "unixtime": int(row[1]),
            "omrondate": str(row[2]),
            "omrontime": str(row[3]),
            "systolic": int(row[4]),
            "diastolic": int(row[5]),
            "pulse": int(row[6]),
            "MOV": int(row[7]),
            "IHB": int(row[8]),
            "emailuser": str(row[9]),
        })

records_to_upload = select_records_for_upload(records)

if not records_to_upload:
    print("OMRON * There is no new data to upload to Garmin Connect")

backup_changed = False

for record in records_to_upload:
    unixtime = record["unixtime"]
    omrondate = record["omrondate"]
    omrontime = record["omrontime"]
    systolic = record["systolic"]
    diastolic = record["diastolic"]
    pulse = record["pulse"]
    MOV = record["MOV"]
    IHB = record["IHB"]
    emailuser = record["emailuser"]
    source_indices = record["source_indices"]

    category = bp_category(systolic, diastolic)

    print(f"OMRON * Import data: {unixtime};{omrondate};{omrontime};{systolic:.0f};{diastolic:.0f};{pulse:.0f};{MOV:.0f};{IHB:.0f};{emailuser}")
    print(f"OMRON * Calculated data: {category};{MOV:.0f};{IHB:.0f};{emailuser};{dt.now().strftime('%d.%m.%Y;%H:%M')}")

    try:
        token_file = os.path.join(path, "user", emailuser)
        garmin = Garmin()
        garmin.login(token_file)

        garmin.set_blood_pressure(
            timestamp=dt.fromtimestamp(unixtime).isoformat(),
            diastolic=diastolic,
            systolic=systolic,
            pulse=pulse,
        )

        print("OMRON * Upload status: OK")

        upload_dt = dt.now()
        upload_date = upload_dt.strftime("%d.%m.%Y")
        upload_time = upload_dt.strftime("%H:%M")
        diff_time = str(round(upload_dt.timestamp() - unixtime))

        for idx in source_indices:
            all_rows[idx] = ensure_row_length(all_rows[idx])
            all_rows[idx][0] = "imported"
            all_rows[idx][10] = upload_date
            all_rows[idx][11] = upload_time
            all_rows[idx][12] = diff_time

        backup_changed = True

    except Exception as exc:
        print(f"OMRON * Upload status: FAILED - {exc}")

        for idx in source_indices:
            all_rows[idx] = ensure_row_length(all_rows[idx])
            all_rows[idx][0] = "failed"

        backup_changed = True

if backup_changed:
    write_backup(all_rows)
