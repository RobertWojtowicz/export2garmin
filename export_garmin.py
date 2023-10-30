#!/usr/bin/python3

import Xiaomi_Scale_Body_Metrics
import csv
import os
import glob
import datetime

# Version Info
print("")
print("Mi Body Composition Scale 2 Garmin Connect v5.9 (export_garmin.py)")
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
		if str(row[0]) in ["failed","to_import"]:
			mitdatetime = str(row[1])
			weight = float(row[2])
			miimpedance = float(row[3])
			break
selected_user = None
for user in users:
	if weight >= user.min_weight and weight <= user.max_weight:
		selected_user = user
		break

# Calcuating body metrics and send data to Garmin Connect
if selected_user is not None:
	lib = Xiaomi_Scale_Body_Metrics.bodyMetrics(weight, selected_user.height, selected_user.age, selected_user.sex, int(miimpedance))
	message = (path) + '/YAGCC uploadbodycomposition '
	message += '--password ' + selected_user.password + ' '
	message += '--weight ' + "{:.1f}".format(weight) + ' '
	message += '--unix-timestamp ' + mitdatetime + ' '
	message += '--email ' + selected_user.email + ' '
	message += '--bmi ' + "{:.1f}".format(lib.getBMI()) + ' '
	message += '--fat ' + "{:.1f}".format(lib.getFatPercentage()) + ' '
	message += '--muscle-mass ' + "{:.1f}".format(lib.getMuscleMass()) + ' '
	message += '--bone-mass ' + "{:.1f}".format(lib.getBoneMass()) + ' '
	message += '--hydration ' + "{:.1f}".format(lib.getWaterPercentage()) + ' '
	message += '--physique-rating ' + "{:.0f}".format(lib.getBodyType()) + ' '
	message += '--visceral-fat ' + "{:.0f}".format(lib.getVisceralFat()) + ' '
	message += '--metabolic-age ' + "{:.0f}".format(lib.getMetabolicAge()) + ' '
	os.system(message)

	# Print for log
	print("* Import data: " + mitdatetime + ";{:.1f}".format(weight) + ";{:.0f}".format(miimpedance))
	print("* Calculated data: " + datetime.datetime.fromtimestamp(int(mitdatetime)).strftime("%d.%m.%Y;%H:%M") + ";{:.1f}".format(weight) + ";{:.1f}".format(lib.getBMI()) + ";{:.1f}".format(lib.getFatPercentage()) + ";{:.1f}".format(lib.getMuscleMass()) + ";{:.1f}".format(lib.getBoneMass()) + ";{:.1f}".format(lib.getWaterPercentage()) + ";{:.0f}".format(lib.getBodyType()) + ";{:.0f}".format(lib.getVisceralFat()) + ";{:.0f}".format(lib.getMetabolicAge()) + ";{:.0f}".format(miimpedance) + ";" + selected_user.email + datetime.datetime.now().strftime(";%d.%m.%Y;%H:%M"))
else:
	print("* Import data: " + mitdatetime + ";{:.1f}".format(weight) + ";{:.0f}".format(miimpedance))
	print("* There is no user with given weight, check users section in export_garmin.py")