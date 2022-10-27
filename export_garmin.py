#!/usr/bin/python3

import Xiaomi_Scale_Body_Metrics
import csv
import os
import glob
import datetime

# Version Info
print("")
print("Mi Body Composition Scale 2 Garmin Connect v4.6 (export_garmin.py)")
print("")

class User():
	def __init__(self, sex, height, birthdate, email, password, max_weight, min_weight):
		self.sex = sex
		self.height = height
		self.birthdate = birthdate
		self.email = email
		self.password = password
		self.max_weight = max_weight
		self.min_weight = min_weight

	# Calculating age
	@property
	def age(self):
		today = datetime.date.today()
		calc_date = datetime.datetime.strptime(self.birthdate, "%d-%m-%Y")
		return today.year - calc_date.year

# Adding all the users (sex, height in cm, birthdate in dd-mm-yyyy, email and password to Garmin Connect, max_weight in kg, min_weight in kg)
users = [User("male", 172, '02-04-1984', "email", "password", 65, 55),
		 User("male", 188, '02-04-1984', "email", "password", 92, 85)]

# Import file as csv
path = os.path.dirname(__file__)
weight = 0
miimpedance = 0
mitdatetime = 0
with open(path + '/backup.csv', 'r') as csv_file:
	csv_reader = csv.reader(csv_file, delimiter=';')
	for row in csv_reader:
		if str(row[3]) in ["failed","to_import"]:
			weight = float(row[0])
			miimpedance = float(row[1])
			mitdatetime = str(row[2])
			break
selected_user = None
for user in users:
	if weight >= user.min_weight and weight <= user.max_weight:
		selected_user = user
		break

# Calcuating body metrics and send data to Garmin Connect
if selected_user is not None:
	lib = Xiaomi_Scale_Body_Metrics.bodyMetrics(weight, selected_user.height, selected_user.age, selected_user.sex, int(miimpedance))
	message = (path) + '/bodycomposition upload '
	message += '--bone-mass ' + "{:.2f}".format(lib.getBoneMass()) + ' '
	message += '--bmi ' + "{:.2f}".format(lib.getBMI()) + ' '
	message += '--email ' + selected_user.email + ' '
	message += '--fat ' + "{:.2f}".format(lib.getFatPercentage()) + ' '
	message += '--hydration ' + "{:.2f}".format(lib.getWaterPercentage()) + ' '
	message += '--metabolic-age ' + "{:.0f}".format(lib.getMetabolicAge()) + ' '
	message += '--muscle-mass ' + "{:.2f}".format(lib.getMuscleMass()) + ' '
	message += '--password ' + selected_user.password + ' '
	message += '--physique-rating ' + "{:.2f}".format(lib.getBodyType()) + ' '
	message += '--unix-timestamp ' + mitdatetime + ' '
	message += '--visceral-fat ' + "{:.2f}".format(lib.getVisceralFat()) + ' '
	message += '--weight ' + "{:.2f}".format(weight) + ' '
	os.system(message)

	# Print for log
	print("* Import number: " + (mitdatetime))
	print("* Calculated data: " + selected_user.email + ";{:.2f}".format(lib.getBoneMass()) + ";{:.2f}".format(lib.getBMI()) + ";{:.2f}".format(lib.getFatPercentage()) + ";{:.2f}".format(lib.getWaterPercentage()) + ";{:.0f}".format(lib.getMetabolicAge()) + ";{:.2f}".format(lib.getMuscleMass()) + ";{:.2f}".format(lib.getBodyType()) + ";{:.2f}".format(lib.getVisceralFat()) + datetime.datetime.now().strftime(";%Y-%m-%d %H:%M:%S"))
else:
	print("* Import number: " + (mitdatetime))
	print("* There is no user with given weight, check users section in export_garmin.py")