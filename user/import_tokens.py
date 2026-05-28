#!/usr/bin/python3

import os
import datetime
from getpass import getpass
from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError

# Version info
print("""
===============================================
Export 2 Garmin Connect v3.7 (import_tokens.py)
===============================================
""")

# Importing tokens variables from a file
path = os.path.dirname(os.path.dirname(__file__))
config_path = os.path.join(path, "user", "export2garmin.cfg")
with open(config_path, "r") as file:
    for line in file:
        line = line.strip()
        if line.startswith("tokens_is_cn"):
            name, value = line.split("=", 1)
            tokens_is_cn = value.strip() == "True"

# Get user credentials
def ts():
    return datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")

def get_credentials():
    email = input(f"{ts()} * Login e-mail: ").strip()
    password = getpass(f"{ts()} * Enter password: ")
    return email, password

# Initialize Garmin API with your credentials without/and MFA/2FA
def get_mfa():
    return input(f"{ts()} * MFA/2FA one-time code: ").strip()

def init_api():
    try:
        email, password = get_credentials()
        token_file = os.path.join(path, "user", f"{email}")
        garmin = Garmin(email, password, is_cn=tokens_is_cn, prompt_mfa=get_mfa)
        garmin.login(token_file)
        print(f"{ts()} * OAuth tokens saved correctly in folder: {token_file}")
    except (FileNotFoundError, GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError) as err:
        print(f"{ts()} * ERROR: {err}")
        return None

# Main program loop
if __name__ == "__main__":
    init_api()