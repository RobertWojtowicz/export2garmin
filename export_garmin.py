#!/usr/bin/python

import Xiaomi_Scale_Body_Metrics
import csv
import os
import glob
import datetime

# Version Info
print("Mi Body Composition Scale 2 Garmin Connect v2.3")

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
users = [User("male", 172, '02-04-1984', "email", "password", 60, 55),
		 User("male", 188, '02-04-1984', "email", "password", 92, 85)]

# Import MQTT file as csv
path = os.path.dirname(__file__)
weight = 0
miimpedance = 0
mitdatetime = 0
for filename in glob.glob((path) + '/*.tlog'):
	with open(filename, 'r') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=';')
		for row in csv_reader:
			weight = float(row[0])
			miimpedance = float(row[1])
			mitdatetime = str(row[4])
			break

selected_user = None
for user in users:
	if weight >= user.min_weight and weight <= user.max_weight:
		selected_user = user
		break

# Calcuating body metrics and send data to Garmin Connect
if selected_user is not None:
	lib = Xiaomi_Scale_Body_Metrics.bodyMetrics(weight, selected_user.height, selected_user.age, selected_user.sex, int(miimpedance))
	bone_percentage = (lib.getBoneMass() / weight) * 100
	muscle_percentage = (lib.getMuscleMass() / weight) * 100
	message = (path) + '/bodycomposition upload '
	message += '--bone ' + "{:.2f}".format(bone_percentage) + ' '
	message += '--bmi ' + "{:.2f}".format(lib.getBMI()) + ' '
	message += '--email ' + selected_user.email + ' '
	message += '--fat ' + "{:.2f}".format(lib.getFatPercentage()) + ' '
	message += '--hydration ' + "{:.2f}".format(lib.getWaterPercentage()) + ' '
	message += '--metabolic-age ' + "{:.0f}".format(lib.getMetabolicAge()) + ' '
	message += '--muscle ' + "{:.2f}".format(muscle_percentage) + ' '
	message += '--password ' + selected_user.password + ' '
	message += '--physique-rating ' + "{:.2f}".format(lib.getBodyType()) + ' '
	message += '--unix-timestamp ' + mitdatetime + ' '
	message += '--visceral-fat ' + "{:.2f}".format(lib.getVisceralFat()) + ' '
	message += '--weight ' + "{:.2f}".format(weight) + ' '
	os.system(message)
	print("Processed file: " + (mitdatetime) + ".tlog")
else:
	print("There is no user with the given weight, skipping upload to Garmin Connect")