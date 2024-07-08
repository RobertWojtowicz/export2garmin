#!/usr/bin/python3

import os
import datetime
import requests
from getpass import getpass
from garth.exc import GarthHTTPError
from garminconnect import Garmin, GarminConnectAuthenticationError

# Version Info
print("Export 2 Garmin Connect v1.0 (import_tokens.py)")
print("")

# Get user credentials
def get_credentials():
    email = input(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * Login e-mail: ")
    password = getpass(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * Enter password: ")
    return email, password

def get_mfa():
    return input(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * MFA/2FA one-time code: ")

def init_api():
# Initialize Garmin API with your credentials without/and MFA/2FA
    try:
        email, password = get_credentials()
        garmin = Garmin(email, password, is_cn=False, prompt_mfa=get_mfa)
        garmin.login()

# Create Oauth1 and Oauth2 tokens as base64 encoded string
        tokenstore_base64 = os.path.dirname(os.path.dirname(__file__))
        token_base64 = garmin.garth.dumps()
        dir_path = os.path.expanduser(tokenstore_base64 + email)
        with open(dir_path, "w") as token_file:
            token_file.write(token_base64)
        print(datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S") + " * Oauth tokens saved correctly")
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
        print(err)
        return None

# Main program loop
if __name__ == "__main__":
    init_api()