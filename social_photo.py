from pyfcm import FCMNotification
from flask import Flask, request, jsonify, json
from flask_api import status
from jinja2._compat import izip
from datetime import datetime,timedelta,date
import pymysql
from flask_cors import CORS, cross_origin
from flask import Blueprint
from flask_restplus import Api, Resource, fields
from werkzeug.utils import cached_property
from werkzeug.datastructures import FileStorage
import requests
import calendar
import json
import string
import random
import math

app = Flask(__name__)
cors = CORS(app)

#----------------------database-connection---------------------#
'''def mysql_connection():
	connection = pymysql.connect(host='creamsonservices.com',
	                             user='creamson_langlab',
	                             password='Langlab@123',
	                             db='social_photo',
	                             charset='utf8mb4',
	                             cursorclass=pymysql.cursors.DictCursor)
	return connection'''

def mysql_connection():
	connection = pymysql.connect(host='socialphoto.cdcuaa7mp0jm.us-east-2.rds.amazonaws.com',
	                             user='admin',
	                             password='O17oxJe3rWVXHPtvM2ug',
	                             db='social_photo',
	                             charset='utf8mb4',
	                             cursorclass=pymysql.cursors.DictCursor)
	return connection

#----------------------database-connection---------------------#


social_photo = Blueprint('social_photo_api', __name__)
api = Api(social_photo,  title='Social Photo API',description='Social Photo')

name_space = api.namespace('SocialPhoto',description='Social Photo')
name_space_event = api.namespace('SocialPhotoEvent',description='Social Photo Event')


user_postmodel = api.model('SelectUser', {
	"email":fields.String,	
	"phoneno":fields.String(required=True),	
	"event_code":fields.String(required=True),
	"registration_role":fields.Integer(required=True),
	"password":fields.String,
	"registration_type":fields.Integer(required=True)
})

user_signup_postmodel = api.model('user_signup_postmodel', {
	"phoneno":fields.String(required=True),	
	"registration_role":fields.Integer(required=True),
	"password":fields.String,
	"registration_type":fields.Integer(required=True)
})

otp_postmodel = api.model('SelectOtp', {
	"PHONE_NUMBER":fields.String(required=True)	
})

check_user_postmodel = api.model('check_user_postmodel', {
	"phoneno":fields.String(required=True)	
})

login_postmodel = api.model('login_postmodel', {
	"phoneno":fields.String(required=True),
	"password":fields.String
})

check_otp_postmodel = api.model('SelectCheckOtp', {
	"PHONE_NUMBER":fields.String(required=True)	,
	"otp":fields.String(required=True)	
})

update_user_model = api.model('updateUser', {
	"name":fields.String,
	"profile_image":fields.String,
	"password":fields.String,
})

update_user_info_model = api.model('update_user_info_model', {
	"password":fields.String,
})


event_postmodel = api.model('addEvent', {
	"event_name":fields.String,
	"event_date":fields.String,
	"event_time":fields.String,
	"event_end_date":fields.String,
	"event_end_time":fields.String,
	"location":fields.String,
	"event_manager_id":fields.Integer(required=True),
	"user_id":fields.Integer(required=True)
})

check_event_postmodel = api.model('SelectCheckEvent', {	
	"event_code":fields.String(required=True)	
})

check_event_postmodel_for_guest = api.model('SelectCheckEventForGuest', {	
	"event_code":fields.String(required=True),
	"user_id":fields.Integer(required=True)	
})

event_photo_postmodel = api.model('EventPhoto', {
	"image":fields.String(required=True),
	"text":fields.String,
	"event_id":fields.Integer(required=True),	
	"event_manager_id":fields.Integer(required=True),
	"user_id":fields.Integer(required=True),
})

like_photo_postmodel = api.model('LikePhoto', {
	"event_photo_id":fields.Integer(required=True),
	"user_id":fields.Integer(required=True),
	"is_like":fields.Integer(required=True)
})

tag_photo_postmodel = api.model('TagPhoto', {
	"event_photo_id":fields.Integer(required=True),
	"user_id":fields.List(fields.Integer),
	"tagged_by_user_id":fields.Integer(required=True),
	"is_tagged":fields.Integer(required=True)
})

devicetoken_postmodel = api.model('deviceToken',{
	"user_id":fields.Integer(required=True),	
	"device_type":fields.Integer(required=True),
	"device_token":fields.String(required=True)
})

notification_model = api.model('notification_model', {	
	"user_id":fields.Integer(required=True),
	"text":fields.String(),	
	"image":fields.String(),
	"title": fields.String(required=True)
})

comments_on_event_photo_post_model = api.model('comments_on_event_photo_post_model',{
	"user_id":fields.Integer(required=True),
	"event_photo_id":fields.Integer(required=True),
	"comments":fields.String()
})

common_photo_model =  api.model('common_photo_model',{
	"is_common":fields.Integer(required=True)
})


BASE_URL = 'http://ec2-18-221-89-14.us-east-2.compute.amazonaws.com/flaskapp/'

#-----------------------Generate-Otp-------------------------------#

@name_space.route("/GenerateOTP")
class GenerateOTP(Resource):
	@api.expect(otp_postmodel)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()
		details = request.get_json()

		PHONE_NUMBER = details['PHONE_NUMBER']
		
		def get_random_digits(stringLength=6):
		    Digits = string.digits
		    return ''.join((random.choice(Digits) for i in range(stringLength)))
		
		otp = get_random_digits()
		details['OTP'] = otp

		insert_query = ("""INSERT INTO `user_otp`(`OTP`,`GENERATED_BY`,`PHONE_NUMBER`) 
							VALUES(%s,%s,%s)""")
		data = (otp,'System',PHONE_NUMBER)
		cursor.execute(insert_query,data)

		connection.commit()
		cursor.close()

		return ({"attributes": {"status_desc": "Social Photo OTP",
	                                "status": "success"
	                                },
				"responseList":details}), status.HTTP_200_OK

		
#-----------------------Generate-Otp-------------------------------#

#-----------------------Check-Otp-------------------------------#

@name_space.route("/CheckOTP")
class CheckOTP(Resource):
	@api.expect(check_otp_postmodel)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()
		details = request.get_json()

		get_otp_query = ("""SELECT *
					FROM `user_otp` WHERE `PHONE_NUMBER` = %s ORDER BY ID DESC LIMIT 1""")
		get_otp_data = (details['PHONE_NUMBER'])
		count_otp = cursor.execute(get_otp_query,get_otp_data)		

		if count_otp > 0:
			otp_data = cursor.fetchone()

			print(otp_data)

			if otp_data['OTP'] == int(details['otp']):
				
				otpjson = otp_data['OTP']
				PHONE_NUMBER = otp_data['PHONE_NUMBER']

				if otpjson :
					return ({"attributes": {"status_desc": "Check Otp",
										"status": "success",
										"message":"Outhenticate Successfully"
											},
						"responseList":{"otp":otpjson,"phoneno":PHONE_NUMBER}}), status.HTTP_200_OK
			else:
				return ({"attributes": {"status_desc": "Check Otp",
									"status": "error",
									"message":"Otp Not Validated"
										},
					"responseList":{}}), status.HTTP_200_OK
		else:
			return ({"attributes": {"status_desc": "Check Otp",
									"status": "error",
									"message":"Otp Not Validated"
										},
					"responseList":{}}), status.HTTP_200_OK	


#----------------------Add-User---------------------#

@name_space.route("/AddUser")
class AddCustomer(Resource):
	@api.expect(user_postmodel)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		email = details['email']	
		phoneno = 	details['phoneno']	
		registration_type = details['registration_type']
		event_code = details['event_code']
		registration_role = details['registration_role']

		if details and "password" in details:
			password = details['password']
		else:
			password = ''

		if registration_role == 1:
			if registration_type == 4:
				get_query = ("""SELECT *
						FROM `user`			
						WHERE `phone` = %s and `registration_role` = 1""")
				get_data = (phoneno)
				count_data = cursor.execute(get_query,get_data)

				if count_data > 0:
					user_data = cursor.fetchone()	
					if user_data['event_manager_id'] == 0:
						user_data['last_update_ts'] = str(user_data['last_update_ts'])	
						user_data['event_code'] = event_code
						user_data['registration_role'] = registration_role		
						return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "success"
							},
							"responseList":user_data}), status.HTTP_200_OK
					else:
						return ({"attributes": {
								    "status_desc": "Already Exsits As A User",
								    "status": "error"
								},
								"responseList":{}}), status.HTTP_200_OK

				else:
					insert_query = ("""INSERT INTO `user`(`email`,`phone`,`password`,`registration_role`,`registration_type`) 
									VALUES(%s,%s,%s,%s,%s)""")
					data = (email,phoneno,password,registration_role,registration_type)
					cursor.execute(insert_query,data)

					user_id = cursor.lastrowid

					get_query = ("""SELECT *
							FROM `user`			
							WHERE `user_id` = %s""")
					get_data = (user_id)
					cursor.execute(get_query,get_data)

					user_data = cursor.fetchone()	
					user_data['last_update_ts'] = str(user_data['last_update_ts'])	
					user_data['event_code'] = event_code
					user_data['registration_role'] = registration_role			

					connection.commit()
					cursor.close()

					return ({"attributes": {
								    "status_desc": "user_details",
								    "status": "success"
							},
							"responseList":user_data}), status.HTTP_200_OK
			else:
				get_email_query = ("""SELECT *
							FROM `user` WHERE `email` = %s""")
				get_email_data = (email)

				count_email_data = cursor.execute(get_email_query,get_email_data)

				if count_email_data > 0:
					return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "error"
							},
							"responseList":"Already Exsits"}), status.HTTP_200_OK
				else:
					insert_query = ("""INSERT INTO `user`(`email`,`phone`,`password`,`registration_role`,`registration_type`) 
								VALUES(%s,%s,%s,%s,%s)""")
					data = (email,phoneno,password,registration_role,registration_type)
					cursor.execute(insert_query,data)

					event_manager_id = cursor.lastrowid

					get_query = ("""SELECT *
							FROM `user`			
							WHERE `user_id` = %s""")
					get_data = (event_manager_id)
					cursor.execute(get_query,get_data)

					get_event_manager_query = ("""SELECT *
					FROM `event`			
					WHERE `event_code` = %s""")
					get_event_manager_data = (event_code)
					count_event_manager = cursor.execute(get_event_manager_query,get_event_manager_data)
					event_manager_data = cursor.fetchone()

					user_data = cursor.fetchone()
					user_data['last_update_ts'] = str(user_data['last_update_ts'])
					user_data['event_code'] = event_code
					user_data['event_id'] = event_manager_data['event_id']
					user_data['event_name'] = event_manager_data['event_name']
					user_data['registration_role'] = registration_role		

					connection.commit()
					cursor.close()

					return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "success"
						},
						"responseList":user_data}), status.HTTP_200_OK

		else:

			get_event_manager_query = ("""SELECT e.*,u.`phone`
					FROM `event` e		
					INNER JOIN `user` u on u.`user_id` = e.`event_manager_id`	
					WHERE `event_code` = %s""")
			get_event_manager_data = (event_code)
			count_event_manager = cursor.execute(get_event_manager_query,get_event_manager_data)

			if count_event_manager > 0:
				event_manager_data = cursor.fetchone()
				event_manager_id = event_manager_data['event_manager_id']

				if registration_type == 4:
					get_query = ("""SELECT *
						FROM `user`			
						WHERE `phone` = %s""")
					get_data = (phoneno)
					count_data = cursor.execute(get_query,get_data)

					if count_data > 0:						
						user_data = cursor.fetchone()	
						
						if user_data['event_manager_id'] == event_manager_id and user_data['registration_role'] == 2:								
							user_data['last_update_ts'] = str(user_data['last_update_ts'])	
							user_data['event_code'] = event_code
							user_data['registration_role'] = registration_role	
							user_data['event_id'] = event_manager_data['event_id']	
							user_data['event_name'] = event_manager_data['event_name']	

							
							return ({"attributes": {
									    "status_desc": "user_details",
									    "status": "success"
								},
								"responseList":user_data}), status.HTTP_200_OK
						else:
							if user_data['phone'] == event_manager_data['phone']:
								return ({"attributes": {
							    "status_desc": "Already Exsits As a Event Manager",
							    "status": "error"
								},
								"responseList":{}}), status.HTTP_200_OK
							else:
								insert_query = ("""INSERT INTO `user`(`email`,`phone`,`registration_role`,`registration_type`,`event_manager_id`) 
									VALUES(%s,%s,%s,%s,%s)""")
								data = (email,phoneno,registration_role,registration_type,event_manager_id)
								cursor.execute(insert_query,data)

								user_id = cursor.lastrowid

								get_query = ("""SELECT *
									FROM `user`			
									WHERE `user_id` = %s""")
								get_data = (user_id)
								cursor.execute(get_query,get_data)

								user_data = cursor.fetchone()	
								user_data['last_update_ts'] = str(user_data['last_update_ts'])	
								user_data['event_code'] = event_code
								user_data['registration_role'] = registration_role	
								user_data['event_id'] = event_manager_data['event_id']	
								user_data['event_name'] = event_manager_data['event_name']	

								connection.commit()
								cursor.close()

								return ({"attributes": {
										    "status_desc": "user_details",
										    "status": "success"
									},
									"responseList":user_data}), status.HTTP_200_OK
														
					else:
						
						insert_query = ("""INSERT INTO `user`(`email`,`phone`,`registration_role`,`registration_type`,`event_manager_id`) 
									VALUES(%s,%s,%s,%s,%s)""")
						data = (email,phoneno,registration_role,registration_type,event_manager_id)
						cursor.execute(insert_query,data)

						user_id = cursor.lastrowid

						get_query = ("""SELECT *
							FROM `user`			
							WHERE `user_id` = %s""")
						get_data = (user_id)
						cursor.execute(get_query,get_data)

						user_data = cursor.fetchone()	
						user_data['last_update_ts'] = str(user_data['last_update_ts'])	
						user_data['event_code'] = event_code
						user_data['registration_role'] = registration_role	
						user_data['event_id'] = event_manager_data['event_id']	
						user_data['event_name'] = event_manager_data['event_name']	

						connection.commit()
						cursor.close()

						return ({"attributes": {
								    "status_desc": "user_details",
								    "status": "success"
							},
							"responseList":user_data}), status.HTTP_200_OK	
				else:
					get_email_query = ("""SELECT *
							FROM `user` WHERE `email` = %s and  `event_manager_id` = %s""")
					get_email_data = (email,event_manager_id)

					count_email_data = cursor.execute(get_email_query,get_email_data)

					if count_email_data > 0:
						return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "error"
							},
							"responseList":"Already Exsits"}), status.HTTP_200_OK
					else:
						insert_query = ("""INSERT INTO `user`(`email`,`phone`,`registration_role`,`registration_type`,`event_manager_id`) 
								VALUES(%s,%s,%s,%s,%s)""")
						data = (email,phoneno,registration_role,registration_type,event_manager_id)
						cursor.execute(insert_query,data)

						user_id = cursor.lastrowid

						get_query = ("""SELECT *
							FROM `user`			
							WHERE `user_id` = %s""")
						get_data = (user_id)
						cursor.execute(get_query,get_data)

						user_data = cursor.fetchone()
						user_data['last_update_ts'] = str(user_data['last_update_ts'])	
						user_data['event_code'] = event_code
						user_data['registration_role'] = registration_role	

						connection.commit()
						cursor.close()

						return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "success"
						},
						"responseList":user_data}), status.HTTP_200_OK
			else:
				return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "error"
							},
							"responseList":"Event Manager does not Exsits"}), status.HTTP_200_OK
		

#----------------------Add-User---------------------#

#----------------------User-SignUp--------------------#

@name_space.route("/UserSignUp")
class UserSignUp(Resource):
	@api.expect(user_signup_postmodel)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		phoneno = 	details['phoneno']	
		registration_type = details['registration_type']		
		registration_role = details['registration_role']
		password =  details['password']

		get_query = ("""SELECT *
						FROM `user`			
						WHERE `phone` = %s""")
		get_data = (phoneno)
		count_data = cursor.execute(get_query,get_data)

		if count_data > 0:
			return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "error"
							},
							"responseList":"Already Exsits"}), status.HTTP_200_OK
		else:
			insert_query = ("""INSERT INTO `user`(`phone`,`registration_role`,`registration_type`) 
								VALUES(%s,%s,%s)""")
			data = (phoneno,registration_role,registration_type)
			cursor.execute(insert_query,data)

			user_id = cursor.lastrowid

			connection.commit()
			cursor.close()

			return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "success"
						},
						"responseList":details}), status.HTTP_200_OK

#----------------------User-SignUp--------------------#

#----------------------Login-User---------------------#

@name_space.route("/LoginUser")
class LoginUser(Resource):
	@api.expect(login_postmodel)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		phoneno = 	details['phoneno']		

		if details and "password" in details:
			password = details['password']
		else:
			password = ''

		get_query = ("""SELECT *
							FROM `user`			
							WHERE `phone` = %s and `password` = %s""")
		get_data = (phoneno,password)
		user_count = cursor.execute(get_query,get_data)
		if user_count > 0:
			user_data = cursor.fetchone()
			if user_data['event_id'] == 0:
				user_data['event_code'] = ''
				user_data['event_id'] = 0
				user_data['event_name'] = ''
			else:
				get_event_query = ("""SELECT *
								FROM `event`			
								WHERE `event_id` = %s""")
				get_event_data = (user_data['event_id'])
				event_count = cursor.execute(get_event_query,get_event_data)
				if event_count > 0:
					event_data = cursor.fetchone()
					user_data['event_code'] = event_data['event_code']
					user_data['event_id'] = event_data['event_id']
					user_data['event_name'] = event_data['event_name']
			user_data['last_update_ts'] = str(user_data['last_update_ts'])

			return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "success"
						},
						"responseList":user_data}), status.HTTP_200_OK
		else:
			return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "error"
							},
							"responseList":"Username Password Does Not Match"}), status.HTTP_200_OK

#----------------------Login-User---------------------#

#----------------------Check-User---------------------#

@name_space.route("/CheckUser")
class CheckUser(Resource):
	@api.expect(check_user_postmodel)
	def post(self):

		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		phoneno = details['phoneno']

		get_query = ("""SELECT *
							FROM `user`			
							WHERE `phone` = %s""")
		get_data = (phoneno)
		user_count = cursor.execute(get_query,get_data)
		if user_count > 0:
			user_data = cursor.fetchone()
			if user_data['event_id'] == 0:
				user_data['event_code'] = ''
				user_data['event_id'] = 0
				user_data['event_name'] = ''
			else:
				get_event_query = ("""SELECT *
								FROM `event`			
								WHERE `event_id` = %s""")
				get_event_data = (user_data['event_id'])
				event_count = cursor.execute(get_event_query,get_event_data)
				if event_count > 0:
					event_data = cursor.fetchone()
					user_data['event_code'] = event_data['event_code']
					user_data['event_id'] = event_data['event_id']
					user_data['event_name'] = event_data['event_name']
			user_data['last_update_ts'] = str(user_data['last_update_ts'])

			return ({"attributes": {
							    "status_desc": "user_details",
							    "status": "success"
						},
						"responseList":user_data}), status.HTTP_200_OK

		else:
			return ({"attributes": {
					    "status_desc": "user_details",
					    "status": "error"
				},
				"responseList":"Invalid User"}), status.HTTP_200_OK

#----------------------Check-User---------------------#

#----------------------Update-User---------------------#

@name_space.route("/ChangeUserInfomation/<int:user_id>")
class ChangeUserInfomation(Resource):
	@api.expect(update_user_info_model)
	def put(self,user_id):

		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()	

		if details and "password" in details:
			password = details['password']

			update_query = ("""UPDATE `user` SET `password` = %s
						WHERE `user_id` = %s """)
			update_data = (password,user_id)
			cursor.execute(update_query,update_data)

		connection.commit()
		cursor.close()

		return ({"attributes": {"status_desc": "Update User",
								"status": "success"},
				"responseList": 'Updated Successfully'}), status.HTTP_200_OK

#----------------------Update-User---------------------#


#----------------------Update-User---------------------#

@name_space.route("/UpdateUser/<int:user_id>")
class UpdateUser(Resource):
	@api.expect(update_user_model)
	def put(self,user_id):

		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		if details and "name" in details:
			name = details['name']

			update_query = ("""UPDATE `user` SET `name` = %s
						WHERE `user_id` = %s """)
			update_data = (name,user_id)
			cursor.execute(update_query,update_data)

		if details and "profile_image" in details:
			profile_image = details['profile_image']

			update_query = ("""UPDATE `user` SET `profile_image` = %s
						WHERE `user_id` = %s """)
			update_data = (profile_image,user_id)
			cursor.execute(update_query,update_data)

		connection.commit()
		cursor.close()

		return ({"attributes": {"status_desc": "Update User",
								"status": "success"},
				"responseList": 'Updated Successfully'}), status.HTTP_200_OK

#----------------------Update-User---------------------#

#----------------------Add-Event---------------------#

@name_space_event.route("/AddEvent")
class AddEvent(Resource):
	@api.expect(event_postmodel)
	def post(self):

		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		event_name = details['event_name']
		event_date = details['event_date']
		event_time = details['event_time']
		event_end_date = details['event_end_date']
		event_end_time = details['event_end_time']
		location = details['location']
		user_id = details['user_id']
		event_manager_id = details['event_manager_id']

		event_code = random_string(2,2)

		insert_query = ("""INSERT INTO `event`(`event_name`,`date`,`time`,`end_date`,`end_time`,`location`,`event_code`,`user_id`,`event_manager_id`) 
						VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""")
		data = (event_name,event_date,event_time,event_end_date,event_end_time,location,event_code,user_id,event_manager_id)
		cursor.execute(insert_query,data)

		event_id = cursor.lastrowid


		details['event_code'] = event_code
		details['event_id'] = event_id

		connection.commit()
		cursor.close()

		return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success"
				},
				"responseList":details}), status.HTTP_200_OK

#----------------------Add-Event---------------------#

#----------------------Get-Event-List---------------------#

@name_space_event.route("/getEventList/<int:user_id>/<string:event_code>/<int:role>")	
class getEventList(Resource):
	def get(self,user_id,event_code,role):
		connection = mysql_connection()
		cursor = connection.cursor()

		if event_code == 'NA' and role == 1:
			get_query = ("""SELECT * FROM `event` where `event_manager_id` = %s order by event_id desc""")
			get_data = (user_id)
		else:
			get_query = ("""SELECT * FROM `event` where `event_code` = %s""")
			get_data = (event_code)
		cursor.execute(get_query,get_data)
		event_data = cursor.fetchall()

		for key,data in enumerate(event_data):
			event_data[key]['last_update_ts'] = str(data['last_update_ts'])
			event_data[key]['date'] = str(data['date'])			
			event_data[key]['end_date'] = str(data['end_date'])			

		return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success"
				},
				"responseList":event_data}), status.HTTP_200_OK

#----------------------Get-Event-List---------------------#

#----------------------Check-Event---------------------#

@name_space_event.route("/CheckEvent")
class CheckEvent(Resource):
	@api.expect(check_event_postmodel)
	def post(self):

		connection = mysql_connection()
		cursor = connection.cursor()
		details = request.get_json()
		
		event_code = details['event_code']

		get_query = ("""SELECT * FROM `event` where `event_code` = %s""")
		get_data = (event_code)
		count_event = cursor.execute(get_query,get_data)

		if count_event > 0:
			event_data = cursor.fetchone()
			event_data['last_update_ts'] = str(event_data['last_update_ts'])
			event_data['date'] = str(event_data['date'])
			event_data['end_date'] = str(event_data['end_date'])

			return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success"
				},
				"responseList":event_data}), status.HTTP_200_OK
		else:

			return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "error"
				},
				"responseList":"Wrong Code Given"}), status.HTTP_200_OK
		

#----------------------Check-Event---------------------#

#----------------------Check-Event---------------------#

@name_space_event.route("/CheckEventForUser")
class CheckEventForUser(Resource):
	@api.expect(check_event_postmodel_for_guest)
	def post(self):

		connection = mysql_connection()
		cursor = connection.cursor()
		details = request.get_json()
		
		event_code = details['event_code']
		user_id = details['user_id']

		get_query = ("""SELECT * FROM `event` where `event_code` = %s""")
		get_data = (event_code)
		count_event = cursor.execute(get_query,get_data)

		if count_event > 0:
			event_data = cursor.fetchone()
			event_data['last_update_ts'] = str(event_data['last_update_ts'])
			event_data['date'] = str(event_data['date'])
			event_data['end_date'] = str(event_data['end_date'])
			registration_role = 2

			update_query = ("""UPDATE `user` SET `event_manager_id` = %s,`registration_role` = %s,`event_id` = %s
				WHERE `user_id` = %s """)
			update_data = (event_data['event_manager_id'],registration_role,event_data['event_id'],user_id)
			cursor.execute(update_query,update_data)

			return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success"
				},
				"responseList":event_data}), status.HTTP_200_OK
		else:

			return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "error"
				},
				"responseList":"Wrong Code Given"}), status.HTTP_200_OK
		

#----------------------Check-Event---------------------#

#----------------------Add-Event-Photo--------------------#

@name_space_event.route("/AddEventPhoto")
class AddEventPhoto(Resource):
	@api.expect(event_photo_postmodel)
	def post(self):

		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		image = details['image']
		text = details['text']
		event_id = details['event_id']
		event_manager_id = details['event_manager_id']
		user_id = details['user_id']		

		insert_query = ("""INSERT INTO `event_photos`(`image`,`text`,`event_id`,`event_manager_id`,`user_id`) 
						VALUES(%s,%s,%s,%s,%s)""")
		data = (image,text,event_id,event_manager_id,user_id)
		cursor.execute(insert_query,data)

		event_photo_id = cursor.lastrowid
		
		details['event_photo_id'] = event_photo_id

		connection.commit()
		cursor.close()

		return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success"
				},
				"responseList":details}), status.HTTP_200_OK

#----------------------Add-Event-Photo--------------------#

#----------------------Comments-On-Event-Photo--------------------#

@name_space_event.route("/CommentsOnEventPhoto")
class CommentsOnEventPhoto(Resource):
	@api.expect(comments_on_event_photo_post_model)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		user_id = details['user_id']
		event_photo_id = details['event_photo_id']
		comments = details['comments']

		insert_query = ("""INSERT INTO `event_photo_comments`(`event_photo_id`,`user_id`,`comments`) 
						VALUES(%s,%s,%s)""")
		data = (event_photo_id,user_id,comments)
		cursor.execute(insert_query,data)

		event_photo_comments_id = cursor.lastrowid

		return ({"attributes": {
					    "status_desc": "event_comment_details",
					    "status": "success"
				},
				"responseList":details}), status.HTTP_200_OK

#----------------------Comments-On-Event-Photo--------------------#

#----------------------Comment-List-By-Event-Photo-Id---------------------#

@name_space_event.route("/commentListByEventPhotoId/<int:event_photo_id>")	
class commentListByEventPhotoId(Resource):
	def get(self,event_photo_id):
		connection = mysql_connection()
		cursor = connection.cursor()

		get_query = ("""SELECT epc.*, u.`profile_image`,u.`name`
							FROM `event_photo_comments` epc							
							INNER JOIN `user` u ON u.`user_id` = epc.`user_id`
							where epc.`event_photo_id` = %s order by event_photo_id desc""")
		get_data = (event_photo_id)
		cursor.execute(get_query,get_data)

		comment_data = cursor.fetchall()

		for key,data in enumerate(comment_data):
			comment_data[key]['last_update_ts'] = str(data['last_update_ts'])	

		return ({"attributes": {
					    "status_desc": "event_comment_details",
					    "status": "success"
				},
				"responseList":comment_data}), status.HTTP_200_OK
		

#----------------------Comment-List-By-Event-Photo-Id---------------------#

#----------------------Update-User---------------------#

@name_space_event.route("/setCommonPhoto/<int:event_photo_id>")
class setCommonPhoto(Resource):
	@api.expect(common_photo_model)
	def put(self,event_photo_id):

		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		if details and "is_common" in details:
			is_common = details['is_common']

			update_query = ("""UPDATE `event_photos` SET `is_common` = %s
						WHERE `event_photo_id` = %s """)
			update_data = (is_common,event_photo_id)
			cursor.execute(update_query,update_data)		

		connection.commit()
		cursor.close()

		return ({"attributes": {"status_desc": "Update Event Photo",
								"status": "success"},
				"responseList": 'Updated Successfully'}), status.HTTP_200_OK

#----------------------Update-User---------------------#

#----------------------Get-Event-Photo-List---------------------#

@name_space_event.route("/EventPhotoList/<int:user_id>/<int:role>/<int:event_id>")	
class EventPhotoList(Resource):
	def get(self,user_id,role,event_id):
		connection = mysql_connection()
		cursor = connection.cursor()

		if role == 1:
			get_query = ("""SELECT ep.*, e.`event_name`,u.`profile_image`,u.`name`
							FROM `event_photos` ep
							INNER JOIN `event` e ON e.`event_id` = ep.`event_id`
							INNER JOIN `user` u ON u.`user_id` = ep.`user_id`
							where ep.`event_manager_id` = %s and ep.`event_id` = %s order by event_photo_id desc""")
			get_data = (user_id,event_id)
			cursor.execute(get_query,get_data)
		else:
			get_query = ("""SELECT ep.*, e.`event_name`,u.`profile_image`,u.`name`
							FROM `event_photos` ep
							INNER JOIN `event` e ON e.`event_id` = ep.`event_id`
							INNER JOIN `user` u ON u.`user_id` = ep.`user_id`
							where ep.`user_id` = %s and ep.`event_id` = %s and ep.`is_common` = 0 order by event_photo_id desc""")
			get_data = (user_id,event_id)
			cursor.execute(get_query,get_data)

		event_photo_data = cursor.fetchall()

		for key,data in enumerate(event_photo_data):
			get_event_photo_like_query = ("""SELECT *
							FROM `event_photo_like` epl							
							where epl.`user_id` = %s and epl.`event_photo_id` = %s""")
			get_event_photo_data = (user_id,data['event_photo_id'])
			event_photo_like_count = cursor.execute(get_event_photo_like_query,get_event_photo_data)

			if event_photo_like_count > 0:
				event_photo_data[key]['is_like'] = 1
			else:
				event_photo_data[key]['is_like'] = 0

			get_event_photo_like_count_query = ("""SELECT count(*) event_photo_like_count
							FROM `event_photo_like` epl							
							where epl.`event_photo_id` = %s""")
			get_event_photo_like_count_data = (data['event_photo_id'])
			count_like = cursor.execute(get_event_photo_like_count_query,get_event_photo_like_count_data)

			if count_like > 0:

				event_photo_like_data =  cursor.fetchone()
				event_photo_data[key]['total_like_count'] = event_photo_like_data['event_photo_like_count']
			else:
				event_photo_data[key]['total_like_count'] = 0

			get_event_photo_comment_count_query = ("""SELECT count(*) event_photo_comment_count
							FROM `event_photo_comments` epc							
							where epc.`event_photo_id` = %s""")
			get_event_photo_comment_count_data = (data['event_photo_id'])
			count_comment = cursor.execute(get_event_photo_comment_count_query,get_event_photo_comment_count_data)

			if count_comment > 0:

				event_photo_comment_data =  cursor.fetchone()
				event_photo_data[key]['total_comment_count'] = event_photo_comment_data['event_photo_comment_count']
			else:
				event_photo_data[key]['total_comment_count'] = 0

			event_photo_data[key]['last_update_ts'] = str(data['last_update_ts'])

			get_event_photo_tag_query = ("""SELECT u.`user_id`,u.`name`
							FROM `tagged_event_photo` tep
							INNER JOIN `user` u on u.`user_id` = tep.`user_id`							
							where tep.`event_photo_id` = %s GROUP BY tep.`user_id`""")		
			get_event_photo_tag_data = (data['event_photo_id'])	
			event_photo_tag_count = cursor.execute(get_event_photo_tag_query,get_event_photo_tag_data)
			event_photo_tag = cursor.fetchall()

			event_photo_data[key]['photo_tag_list'] = event_photo_tag

		get_event_tag_photo_list_query = ("""SELECT ep.*,e.`event_name`,u.`profile_image`,u.`name`
									FROM `tagged_event_photo` tep
									INNER JOIN `event_photos` ep ON ep.`event_photo_id` = tep.`event_photo_id`
									INNER JOIN `event` e ON e.`event_id` = ep.`event_id`
									INNER JOIN `user` u ON u.`user_id` = ep.`user_id`									
									where ep.`event_id` = %s  and tep.`user_id` = %s  and ep.`is_common` = 0 order by tagged_event_photo_id desc""")

		get_event_tag_photo_list_data = (event_id,user_id)
		cursor.execute(get_event_tag_photo_list_query,get_event_tag_photo_list_data)
		event_photo_tag_list_data = cursor.fetchall()
		for tkey,tdata in enumerate(event_photo_tag_list_data):
			get_event_photo_like_query = ("""SELECT *
							FROM `event_photo_like` epl							
							where epl.`user_id` = %s and epl.`event_photo_id` = %s""")
			get_event_photo_data = (user_id,tdata['event_photo_id'])
			event_photo_like_count = cursor.execute(get_event_photo_like_query,get_event_photo_data)

			if event_photo_like_count > 0:
				event_photo_tag_list_data[tkey]['is_like'] = 1
			else:
				event_photo_tag_list_data[tkey]['is_like'] = 0

			get_event_photo_like_count_query = ("""SELECT count(*) event_photo_like_count
							FROM `event_photo_like` epl							
							where epl.`event_photo_id` = %s""")
			get_event_photo_like_count_data = (tdata['event_photo_id'])
			count_like = cursor.execute(get_event_photo_like_count_query,get_event_photo_like_count_data)

			if count_like > 0:

				event_photo_like_data =  cursor.fetchone()
				event_photo_tag_list_data[tkey]['total_like_count'] = event_photo_like_data['event_photo_like_count']
			else:
				event_photo_tag_list_data[tkey]['total_like_count'] = 0

			event_photo_tag_list_data[tkey]['last_update_ts'] = str(tdata['last_update_ts'])

			get_event_photo_tag_query = ("""SELECT u.`user_id`,u.`name`
							FROM `tagged_event_photo` tep
							INNER JOIN `user` u on u.`user_id` = tep.`tagged_by_user_id`							
							where tep.`event_photo_id` = %s GROUP BY tep.`tagged_by_user_id`""")		
			get_event_photo_tag_data = (tdata['event_photo_id'])	
			event_photo_tag_count = cursor.execute(get_event_photo_tag_query,get_event_photo_tag_data)
			event_photo_tag = cursor.fetchall()

			event_photo_tag_list_data[tkey]['photo_tag_list'] = event_photo_tag	

		if len(event_photo_data) == 0:
			event_photo_data = event_photo_tag_list_data
		elif len(event_photo_tag_list_data) == 0:
			event_photo_data = event_photo_data
		else:
			event_photo_data = event_photo_data + event_photo_tag_list_data

		if role == 2:

			get_common_query = ("""SELECT ep.*, e.`event_name`,u.`profile_image`,u.`name`
								FROM `event_photos` ep
								INNER JOIN `event` e ON e.`event_id` = ep.`event_id`
								INNER JOIN `user` u ON u.`user_id` = ep.`user_id`
								where ep.`event_id` = %s and ep.`is_common` = 1 order by event_photo_id desc""")
			get_common_data = (event_id)
			cursor.execute(get_common_query,get_common_data)

			common_photo_data = cursor.fetchall()

			for ckey,cdata in enumerate(common_photo_data):
				get_event_photo_like_query = ("""SELECT *
								FROM `event_photo_like` epl							
								where epl.`user_id` = %s and epl.`event_photo_id` = %s""")
				get_event_photo_data = (user_id,cdata['event_photo_id'])
				event_photo_like_count = cursor.execute(get_event_photo_like_query,get_event_photo_data)

				if event_photo_like_count > 0:
					common_photo_data[ckey]['is_like'] = 1
				else:
					common_photo_data[ckey]['is_like'] = 0

				get_event_photo_like_count_query = ("""SELECT count(*) event_photo_like_count
								FROM `event_photo_like` epl							
								where epl.`event_photo_id` = %s""")
				get_event_photo_like_count_data = (cdata['event_photo_id'])
				count_like = cursor.execute(get_event_photo_like_count_query,get_event_photo_like_count_data)

				if count_like > 0:

					event_photo_like_data =  cursor.fetchone()
					common_photo_data[ckey]['total_like_count'] = event_photo_like_data['event_photo_like_count']
				else:
					common_photo_data[ckey]['total_like_count'] = 0

				get_event_photo_comment_count_query = ("""SELECT count(*) event_photo_comment_count
								FROM `event_photo_comments` epc							
								where epc.`event_photo_id` = %s""")
				get_event_photo_comment_count_data = (data['event_photo_id'])
				count_comment = cursor.execute(get_event_photo_comment_count_query,get_event_photo_comment_count_data)

				if count_comment > 0:

					event_photo_comment_data =  cursor.fetchone()
					common_photo_data[ckey]['total_comment_count'] = event_photo_comment_data['event_photo_comment_count']
				else:
					common_photo_data[ckey]['total_comment_count'] = 0

				common_photo_data[ckey]['last_update_ts'] = str(data['last_update_ts'])

				get_event_photo_tag_query = ("""SELECT u.`user_id`,u.`name`
								FROM `tagged_event_photo` tep
								INNER JOIN `user` u on u.`user_id` = tep.`user_id`							
								where tep.`event_photo_id` = %s""")		
				get_event_photo_tag_data = (cdata['event_photo_id'])	
				event_photo_tag_count = cursor.execute(get_event_photo_tag_query,get_event_photo_tag_data)
				event_photo_tag = cursor.fetchall()

				common_photo_data[ckey]['photo_tag_list'] = event_photo_tag


			if len(common_photo_data) == 0:
				event_photo_data = event_photo_data
			else:
				event_photo_data = event_photo_data + common_photo_data

				
		
		'''get_tagged_user_list_query = ("""SELECT u.`user_id`,u.`name`,u.`profile_image`
											FROM `tagged_event_photo` tep
											INNER JOIN `user` u on u.`user_id` = tep.`user_id`
											where tep.`event_id` = %s and tep.`tagged_by_user_id` = %s GROUP BY tep.`user_id` """)

		get_tagged_user_list_data = (event_id,user_id)
		tagged_count = cursor.execute(get_tagged_user_list_query,get_tagged_user_list_data)
		tagged_user_list = 	cursor.fetchall()'''

		if role == 2:

			tagged_user_list = {}

			
			get_tagged_user_list_another_query = ("""SELECT u.`user_id`,u.`name`,u.`profile_image`
												FROM `tagged_event_photo` tep
												INNER JOIN `user` u on u.`user_id` = tep.`tagged_by_user_id`
												where tep.`event_id` = %s and tep.`user_id` = %s GROUP BY tep.`tagged_by_user_id` """)

			get_tagged_user_list_another_data = (event_id,user_id)
			cursor.execute(get_tagged_user_list_another_query,get_tagged_user_list_another_data)
			tagged_another_user_list = 	cursor.fetchall()

			if len(tagged_user_list) == 0:
				tagged_user_list = tagged_another_user_list
			elif len(tagged_another_user_list) == 0:
				tagged_user_list = tagged_user_list
			else:
				tagged_user_list = tagged_user_list + tagged_another_user_list
		else:
			get_tagged_user_list_query = ("""SELECT u.`user_id`,u.`name`,u.`profile_image`
											FROM `tagged_event_photo` tep
											INNER JOIN `user` u on u.`user_id` = tep.`user_id`
											where tep.`event_id` = %s and tep.`tagged_by_user_id` = %s GROUP BY tep.`user_id` """)

			get_tagged_user_list_data = (event_id,user_id)
			tagged_count = cursor.execute(get_tagged_user_list_query,get_tagged_user_list_data)
			tagged_user_list = 	cursor.fetchall()	




		return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success",
					    "tagged_user_list":tagged_user_list
				},
				"responseList":event_photo_data}), status.HTTP_200_OK

#----------------------Get-Event-Photo-List---------------------#

#----------------------Get-Event-Photo-List---------------------#

@name_space_event.route("/EventPhotoListWithPagination/<int:user_id>/<int:role>/<int:event_id>/<int:page>")	
class EventPhotoListWithPagination(Resource):
	def get(self,user_id,role,event_id,page):
		connection = mysql_connection()
		cursor = connection.cursor()

		if role == 1:
			get_query = ("""SELECT ep.*, e.`event_name`,u.`profile_image`,u.`name`
							FROM `event_photos` ep
							INNER JOIN `event` e ON e.`event_id` = ep.`event_id`
							INNER JOIN `user` u ON u.`user_id` = ep.`user_id`
							where ep.`event_manager_id` = %s and ep.`event_id` = %s order by event_photo_id desc""")
			get_data = (user_id,event_id)
			cursor.execute(get_query,get_data)
		else:
			get_query = ("""SELECT ep.*, e.`event_name`,u.`profile_image`,u.`name`
							FROM `event_photos` ep
							INNER JOIN `event` e ON e.`event_id` = ep.`event_id`
							INNER JOIN `user` u ON u.`user_id` = ep.`user_id`
							where ep.`user_id` = %s and ep.`event_id` = %s and ep.`is_common` = 0 order by event_photo_id desc""")
			get_data = (user_id,event_id)
			cursor.execute(get_query,get_data)

		event_photo_data = cursor.fetchall()

		for key,data in enumerate(event_photo_data):
			get_event_photo_like_query = ("""SELECT *
							FROM `event_photo_like` epl							
							where epl.`user_id` = %s and epl.`event_photo_id` = %s""")
			get_event_photo_data = (user_id,data['event_photo_id'])
			event_photo_like_count = cursor.execute(get_event_photo_like_query,get_event_photo_data)

			if event_photo_like_count > 0:
				event_photo_data[key]['is_like'] = 1
			else:
				event_photo_data[key]['is_like'] = 0

			get_event_photo_like_count_query = ("""SELECT count(*) event_photo_like_count
							FROM `event_photo_like` epl							
							where epl.`event_photo_id` = %s""")
			get_event_photo_like_count_data = (data['event_photo_id'])
			count_like = cursor.execute(get_event_photo_like_count_query,get_event_photo_like_count_data)

			if count_like > 0:

				event_photo_like_data =  cursor.fetchone()
				event_photo_data[key]['total_like_count'] = event_photo_like_data['event_photo_like_count']
			else:
				event_photo_data[key]['total_like_count'] = 0

			get_event_photo_comment_count_query = ("""SELECT count(*) event_photo_comment_count
							FROM `event_photo_comments` epc							
							where epc.`event_photo_id` = %s""")
			get_event_photo_comment_count_data = (data['event_photo_id'])
			count_comment = cursor.execute(get_event_photo_comment_count_query,get_event_photo_comment_count_data)

			if count_comment > 0:

				event_photo_comment_data =  cursor.fetchone()
				event_photo_data[key]['total_comment_count'] = event_photo_comment_data['event_photo_comment_count']
			else:
				event_photo_data[key]['total_comment_count'] = 0

			event_photo_data[key]['last_update_ts'] = str(data['last_update_ts'])

			get_event_photo_tag_query = ("""SELECT u.`user_id`,u.`name`
							FROM `tagged_event_photo` tep
							INNER JOIN `user` u on u.`user_id` = tep.`user_id`							
							where tep.`event_photo_id` = %s""")		
			get_event_photo_tag_data = (data['event_photo_id'])	
			event_photo_tag_count = cursor.execute(get_event_photo_tag_query,get_event_photo_tag_data)
			event_photo_tag = cursor.fetchall()

			event_photo_data[key]['photo_tag_list'] = event_photo_tag

		get_event_tag_photo_list_query = ("""SELECT ep.*,e.`event_name`,u.`profile_image`,u.`name`
									FROM `tagged_event_photo` tep
									INNER JOIN `event_photos` ep ON ep.`event_photo_id` = tep.`event_photo_id`
									INNER JOIN `event` e ON e.`event_id` = ep.`event_id`
									INNER JOIN `user` u ON u.`user_id` = ep.`user_id`									
									where ep.`event_id` = %s  and tep.`user_id` = %s order by tagged_event_photo_id desc""")

		get_event_tag_photo_list_data = (event_id,user_id)
		cursor.execute(get_event_tag_photo_list_query,get_event_tag_photo_list_data)
		event_photo_tag_list_data = cursor.fetchall()
		for tkey,tdata in enumerate(event_photo_tag_list_data):
			get_event_photo_like_query = ("""SELECT *
							FROM `event_photo_like` epl							
							where epl.`user_id` = %s and epl.`event_photo_id` = %s""")
			get_event_photo_data = (user_id,tdata['event_photo_id'])
			event_photo_like_count = cursor.execute(get_event_photo_like_query,get_event_photo_data)

			if event_photo_like_count > 0:
				event_photo_tag_list_data[tkey]['is_like'] = 1
			else:
				event_photo_tag_list_data[tkey]['is_like'] = 0

			get_event_photo_like_count_query = ("""SELECT count(*) event_photo_like_count
							FROM `event_photo_like` epl							
							where epl.`event_photo_id` = %s""")
			get_event_photo_like_count_data = (tdata['event_photo_id'])
			count_like = cursor.execute(get_event_photo_like_count_query,get_event_photo_like_count_data)

			if count_like > 0:

				event_photo_like_data =  cursor.fetchone()
				event_photo_tag_list_data[tkey]['total_like_count'] = event_photo_like_data['event_photo_like_count']
			else:
				event_photo_tag_list_data[tkey]['total_like_count'] = 0

			event_photo_tag_list_data[tkey]['last_update_ts'] = str(tdata['last_update_ts'])

			get_event_photo_tag_query = ("""SELECT u.`user_id`,u.`name`
							FROM `tagged_event_photo` tep
							INNER JOIN `user` u on u.`user_id` = tep.`tagged_by_user_id`							
							where tep.`event_photo_id` = %s""")		
			get_event_photo_tag_data = (tdata['event_photo_id'])	
			event_photo_tag_count = cursor.execute(get_event_photo_tag_query,get_event_photo_tag_data)
			event_photo_tag = cursor.fetchall()

			event_photo_tag_list_data[tkey]['photo_tag_list'] = event_photo_tag	

		if len(event_photo_data) == 0:
			event_photo_data = event_photo_tag_list_data
		elif len(event_photo_tag_list_data) == 0:
			event_photo_data = event_photo_data
		else:
			event_photo_data = event_photo_data + event_photo_tag_list_data

		if role == 2:

			get_common_query = ("""SELECT ep.*, e.`event_name`,u.`profile_image`,u.`name`
								FROM `event_photos` ep
								INNER JOIN `event` e ON e.`event_id` = ep.`event_id`
								INNER JOIN `user` u ON u.`user_id` = ep.`user_id`
								where ep.`event_id` = %s and ep.`is_common` = 1 order by event_photo_id desc""")
			get_common_data = (event_id)
			cursor.execute(get_common_query,get_common_data)

			common_photo_data = cursor.fetchall()

			for ckey,cdata in enumerate(common_photo_data):
				get_event_photo_like_query = ("""SELECT *
								FROM `event_photo_like` epl							
								where epl.`user_id` = %s and epl.`event_photo_id` = %s""")
				get_event_photo_data = (user_id,cdata['event_photo_id'])
				event_photo_like_count = cursor.execute(get_event_photo_like_query,get_event_photo_data)

				if event_photo_like_count > 0:
					common_photo_data[ckey]['is_like'] = 1
				else:
					common_photo_data[ckey]['is_like'] = 0

				get_event_photo_like_count_query = ("""SELECT count(*) event_photo_like_count
								FROM `event_photo_like` epl							
								where epl.`event_photo_id` = %s""")
				get_event_photo_like_count_data = (cdata['event_photo_id'])
				count_like = cursor.execute(get_event_photo_like_count_query,get_event_photo_like_count_data)

				if count_like > 0:

					event_photo_like_data =  cursor.fetchone()
					common_photo_data[ckey]['total_like_count'] = event_photo_like_data['event_photo_like_count']
				else:
					common_photo_data[ckey]['total_like_count'] = 0

				get_event_photo_comment_count_query = ("""SELECT count(*) event_photo_comment_count
								FROM `event_photo_comments` epc							
								where epc.`event_photo_id` = %s""")
				get_event_photo_comment_count_data = (data['event_photo_id'])
				count_comment = cursor.execute(get_event_photo_comment_count_query,get_event_photo_comment_count_data)

				if count_comment > 0:

					event_photo_comment_data =  cursor.fetchone()
					common_photo_data[ckey]['total_comment_count'] = event_photo_comment_data['event_photo_comment_count']
				else:
					common_photo_data[ckey]['total_comment_count'] = 0

				common_photo_data[ckey]['last_update_ts'] = str(data['last_update_ts'])

				get_event_photo_tag_query = ("""SELECT u.`user_id`,u.`name`
								FROM `tagged_event_photo` tep
								INNER JOIN `user` u on u.`user_id` = tep.`user_id`							
								where tep.`event_photo_id` = %s""")		
				get_event_photo_tag_data = (cdata['event_photo_id'])	
				event_photo_tag_count = cursor.execute(get_event_photo_tag_query,get_event_photo_tag_data)
				event_photo_tag = cursor.fetchall()

				common_photo_data[ckey]['photo_tag_list'] = event_photo_tag
		

			if len(common_photo_data) == 0:
				event_photo_data = event_photo_data
			else:
				event_photo_data = event_photo_data + common_photo_data
		
		get_tagged_user_list_query = ("""SELECT u.`user_id`,u.`name`,u.`profile_image`
											FROM `tagged_event_photo` tep
											INNER JOIN `user` u on u.`user_id` = tep.`user_id`
											where tep.`event_id` = %s and tep.`tagged_by_user_id` = %s GROUP BY tep.`tagged_by_user_id` """)

		get_tagged_user_list_data = (event_id,user_id)
		tagged_count = cursor.execute(get_tagged_user_list_query,get_tagged_user_list_data)
		tagged_user_list = 	cursor.fetchall()

		
		get_tagged_user_list_another_query = ("""SELECT u.`user_id`,u.`name`,u.`profile_image`
											FROM `tagged_event_photo` tep
											INNER JOIN `user` u on u.`user_id` = tep.`tagged_by_user_id`
											where tep.`event_id` = %s and tep.`user_id` = %s GROUP BY tep.`user_id` """)

		get_tagged_user_list_another_data = (event_id,user_id)
		cursor.execute(get_tagged_user_list_another_query,get_tagged_user_list_another_data)
		tagged_another_user_list = 	cursor.fetchall()

		if len(tagged_user_list) == 0:
			tagged_user_list = tagged_another_user_list
		elif len(tagged_another_user_list) == 0:
			tagged_user_list = tagged_user_list
		else:
			tagged_user_list = tagged_user_list + tagged_another_user_list	

		new_event_photo_data = []
		#for key,data in enumerate(event_photo_data):

		if page == 1:
			for i in range(page*10):
				print(i)
				for epkey,epdata in enumerate(event_photo_data):			
					if epkey == i:
						print(event_photo_data[epkey])
						new_event_photo_data.append(event_photo_data[epkey])
		else:			
			for i in range((page-1)*10,page*10):
				print(i)
				for epkey,epdata in enumerate(event_photo_data):			
					if epkey == i:
						print(event_photo_data[epkey])
						new_event_photo_data.append(event_photo_data[epkey])
				


		page_count = math.trunc(len(event_photo_data)/10)

		if page_count == 0:
			page_count = 1
		else:
			page_count = page_count + 1	

		return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success",
					    "tagged_user_list":tagged_user_list,
					    "page_count":page_count,
		    			"page": page
				},
				"responseList":new_event_photo_data}), status.HTTP_200_OK

#----------------------Get-Event-Photo-List---------------------#

#----------------------Get-Event-Photo-List---------------------#

@name_space_event.route("/EventPhotoListwithTaggeduseridandUserId/<int:user_id>/<int:event_id>/<int:tagged_by_user_id>")	
class EventPhotoListwithTaggeduseridandUserId(Resource):
	def get(self,user_id,event_id,tagged_by_user_id):
		connection = mysql_connection()
		cursor = connection.cursor()

		get_query = ("""SELECT ep.*, e.`event_name`,u.`profile_image`,u.`name`
							FROM `tagged_event_photo` tep
							INNER JOIN  `event_photos` ep ON ep.`event_photo_id` = tep.`event_photo_id` 
							INNER JOIN `event` e ON e.`event_id` = tep.`event_id`
							INNER JOIN `user` u ON u.`user_id` = ep.`user_id`
							where tep.`user_id` = %s and tep.`event_id` = %s and tep.`tagged_by_user_id` = %s order by event_photo_id desc""")
		get_data = (user_id,event_id,tagged_by_user_id)
		count_event_photo = cursor.execute(get_query,get_data)

		if count_event_photo > 0:

			event_photo_data = cursor.fetchall()

			for key,data in enumerate(event_photo_data):
				get_event_photo_like_query = ("""SELECT *
								FROM `event_photo_like` epl							
								where epl.`user_id` = %s and epl.`event_photo_id` = %s""")
				get_event_photo_data = (user_id,data['event_photo_id'])
				event_photo_like_count = cursor.execute(get_event_photo_like_query,get_event_photo_data)

				if event_photo_like_count > 0:
					event_photo_data[key]['is_like'] = 1
				else:
					event_photo_data[key]['is_like'] = 0

				get_event_photo_comment_count_query = ("""SELECT count(*) event_photo_comment_count
								FROM `event_photo_comments` epc							
								where epc.`event_photo_id` = %s""")
				get_event_photo_comment_count_data = (data['event_photo_id'])
				count_comment = cursor.execute(get_event_photo_comment_count_query,get_event_photo_comment_count_data)

				if count_comment > 0:

					event_photo_comment_data =  cursor.fetchone()
					event_photo_data[key]['total_comment_count'] = event_photo_comment_data['event_photo_comment_count']
				else:
					event_photo_data[key]['total_comment_count'] = 0

				get_event_photo_like_count_query = ("""SELECT count(*) event_photo_like_count
								FROM `event_photo_like` epl							
								where epl.`event_photo_id` = %s""")
				get_event_photo_like_count_data = (data['event_photo_id'])
				count_like = cursor.execute(get_event_photo_like_count_query,get_event_photo_like_count_data)

				if count_like > 0:

					event_photo_like_data =  cursor.fetchone()
					event_photo_data[key]['total_like_count'] = event_photo_like_data['event_photo_like_count']
				else:
					event_photo_data[key]['total_like_count'] = 0

				event_photo_data[key]['last_update_ts'] = str(data['last_update_ts'])

				get_event_photo_tag_query = ("""SELECT u.`user_id`,u.`name`
								FROM `tagged_event_photo` tep
								INNER JOIN `user` u on u.`user_id` = tep.`user_id`							
								where tep.`event_photo_id` = %s""")		
				get_event_photo_tag_data = (data['event_photo_id'])	
				event_photo_tag_count = cursor.execute(get_event_photo_tag_query,get_event_photo_tag_data)
				event_photo_tag = cursor.fetchall()

				event_photo_data[key]['photo_tag_list'] = event_photo_tag		

			get_tagged_user_list_query = ("""SELECT u.`user_id`,u.`name`,u.`profile_image`
											FROM `tagged_event_photo` tep
											INNER JOIN `user` u on u.`user_id` = tep.`user_id`
											where tep.`event_id` = %s GROUP BY tep.`user_id`""")	
			get_tagged_user_list_data = (event_id)
			cursor.execute(get_tagged_user_list_query,get_tagged_user_list_data)
			tagged_user_list = 	cursor.fetchall()	

			return ({"attributes": {
						    "status_desc": "event_details",
						    "status": "success",
						    "tagged_user_list":tagged_user_list
					},
					"responseList":event_photo_data}), status.HTTP_200_OK
		else:
			get_query = ("""SELECT ep.*, e.`event_name`,u.`profile_image`,u.`name`
							FROM `tagged_event_photo` tep
							INNER JOIN  `event_photos` ep ON ep.`event_photo_id` = tep.`event_photo_id` 
							INNER JOIN `event` e ON e.`event_id` = tep.`event_id`
							INNER JOIN `user` u ON u.`user_id` = ep.`user_id`
							where tep.`user_id` = %s and tep.`event_id` = %s and tep.`tagged_by_user_id` = %s order by event_photo_id desc""")
			get_data = (tagged_by_user_id,event_id,user_id)
			count_event_photo = cursor.execute(get_query,get_data)

			if count_event_photo > 0:

				event_photo_data = cursor.fetchall()

				for key,data in enumerate(event_photo_data):
					get_event_photo_like_query = ("""SELECT *
									FROM `event_photo_like` epl							
									where epl.`user_id` = %s and epl.`event_photo_id` = %s""")
					get_event_photo_data = (user_id,data['event_photo_id'])
					event_photo_like_count = cursor.execute(get_event_photo_like_query,get_event_photo_data)

					if event_photo_like_count > 0:
						event_photo_data[key]['is_like'] = 1
					else:
						event_photo_data[key]['is_like'] = 0

					get_event_photo_comment_count_query = ("""SELECT count(*) event_photo_comment_count
									FROM `event_photo_comments` epc							
									where epc.`event_photo_id` = %s""")
					get_event_photo_comment_count_data = (data['event_photo_id'])
					count_comment = cursor.execute(get_event_photo_comment_count_query,get_event_photo_comment_count_data)

					if count_comment > 0:

						event_photo_comment_data =  cursor.fetchone()
						event_photo_data[key]['total_comment_count'] = event_photo_comment_data['event_photo_comment_count']
					else:
						event_photo_data[key]['total_comment_count'] = 0

					get_event_photo_like_count_query = ("""SELECT count(*) event_photo_like_count
									FROM `event_photo_like` epl							
									where epl.`event_photo_id` = %s""")
					get_event_photo_like_count_data = (data['event_photo_id'])
					count_like = cursor.execute(get_event_photo_like_count_query,get_event_photo_like_count_data)

					if count_like > 0:

						event_photo_like_data =  cursor.fetchone()
						event_photo_data[key]['total_like_count'] = event_photo_like_data['event_photo_like_count']
					else:
						event_photo_data[key]['total_like_count'] = 0

					event_photo_data[key]['last_update_ts'] = str(data['last_update_ts'])

					get_event_photo_tag_query = ("""SELECT u.`user_id`,u.`name`
									FROM `tagged_event_photo` tep
									INNER JOIN `user` u on u.`user_id` = tep.`tagged_by_user_id`							
									where tep.`event_photo_id` = %s""")		
					get_event_photo_tag_data = (data['event_photo_id'])	
					event_photo_tag_count = cursor.execute(get_event_photo_tag_query,get_event_photo_tag_data)
					event_photo_tag = cursor.fetchall()

					event_photo_data[key]['photo_tag_list'] = event_photo_tag		

				get_tagged_user_list_query = ("""SELECT u.`user_id`,u.`name`,u.`profile_image`
												FROM `tagged_event_photo` tep
												INNER JOIN `user` u on u.`user_id` = tep.`tagged_by_user_id`
												where tep.`event_id` = %s GROUP BY tep.`user_id`""")	
				get_tagged_user_list_data = (event_id)
				cursor.execute(get_tagged_user_list_query,get_tagged_user_list_data)
				tagged_user_list = 	cursor.fetchall()	

				return ({"attributes": {
							    "status_desc": "event_details",
							    "status": "success",
							    "tagged_user_list":tagged_user_list
						},
						"responseList":event_photo_data}), status.HTTP_200_OK


def Merge(dict1, dict2):
    res = dict1 | dict2
    return res

#----------------------Like-Event-Photo--------------------#

@name_space_event.route("/LikeEventPhoto")
class LikeEventPhoto(Resource):
	@api.expect(like_photo_postmodel)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()
		details = request.get_json()

		event_photo_id = details['event_photo_id']
		user_id = details['user_id']
		is_like = details['is_like']

		if is_like == 1:
			insert_query = ("""INSERT INTO `event_photo_like`(`event_photo_id`,`user_id`) 
						VALUES(%s,%s)""")
			data = (event_photo_id,user_id)
			cursor.execute(insert_query,data)

			get_image_query = ("""SELECT *
									  FROM `event_photos` ep where ep.`event_photo_id` = %s""")
			get_image_data = (event_photo_id)
			image_count = cursor.execute(get_image_query,get_image_data)
			image_data = cursor.fetchone()

			headers = {'Content-type':'application/json', 'Accept':'application/json'}
			sendAppPushNotificationUrl = BASE_URL + "social_photo/SocialPhoto/sendNotifications"

			payloadpushData = {										
										"text":"Some One Liked Photo",
										"title":"Liked Your Photo",
										"image":image_data['image'],
										"user_id":image_data['user_id']
							}
			print(payloadpushData)

			send_push_notification = requests.post(sendAppPushNotificationUrl,data=json.dumps(payloadpushData), headers=headers).json()

		else:
			delete_query = ("""DELETE FROM `event_photo_like` WHERE `event_photo_id` = %s and `user_id` = %s""")
			delData = (event_photo_id,user_id)
			
			cursor.execute(delete_query,delData)

			connection.commit()
			cursor.close()

		return ({"attributes": {
					    "status_desc": "like_event_photo",
					    "status": "success"
				},
				"responseList":details}), status.HTTP_200_OK

#----------------------Like-Event-Photo--------------------#

#----------------------Get-User-List-By-Event-Id--------------------#

@name_space_event.route("/UserListByEventId/<int:event_id>/<int:user_id>")	
class UserListByEventId(Resource):
	def get(self,event_id,user_id):
		connection = mysql_connection()
		cursor = connection.cursor()

		get_user_list_query = ("""SELECT u.`name`,u.`user_id`
							FROM `event_photos` ep	
							INNER JOIN `user` u ON u.`user_id` = ep.`user_id`						
							where ep.`event_id` = %s group by user_id""")
		get_user_list_data = (event_id)
		user_list_count = cursor.execute(get_user_list_query,get_user_list_data)

		new_user_list = []

		user_list = cursor.fetchall()

		for key,data in enumerate(user_list):
			if data['user_id'] != user_id:
				new_user_list.append({"user_id":data['user_id'],"name":data['name']})

		return ({"attributes": {
					    "status_desc": "user_list",
					    "status": "success"
				},
				"responseList":new_user_list}), status.HTTP_200_OK


#----------------------Get-User-List-By-Event-Id--------------------#

#----------------------Tag-Event-Photo--------------------#

@name_space_event.route("/TagEventPhoto")
class TagEventPhoto(Resource):
	@api.expect(tag_photo_postmodel)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()
		details = request.get_json()

		event_photo_id = details['event_photo_id']
		user_ids = details.get('user_id',[])		
		is_tagged = details['is_tagged']
		tagged_by_user_id = details['tagged_by_user_id']

		get_query = ("""SELECT *
				FROM `event_photos` ep				
				WHERE  ep.`event_photo_id` = %s""")
		get_data = (event_photo_id)
		count_event_photo = cursor.execute(get_query,get_data)
		

		if count_event_photo > 0:
			evnet_photo_data = cursor.fetchone()
			event_id = evnet_photo_data['event_id']
		else:
			event_id = 0

		for key,user_id in enumerate(user_ids):
			if is_tagged == 1:
				get_tag_image_query = ("""SELECT *
									  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`user_id` = %s""")
				get_tag_image_data = (event_photo_id,user_id)
				tag_image_count = cursor.execute(get_tag_image_query,get_tag_image_data)

				if tag_image_count < 1:				
					insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
								VALUES(%s,%s,%s,%s)""")
					data = (event_photo_id,event_id,user_id,tagged_by_user_id)
					cursor.execute(insert_query,data)

					get_image_query = ("""SELECT *
										  FROM `event_photos` ep where ep.`event_photo_id` = %s""")
					get_image_data = (event_photo_id)
					image_count = cursor.execute(get_image_query,get_image_data)
					image_data = cursor.fetchone()

					headers = {'Content-type':'application/json', 'Accept':'application/json'}
					sendAppPushNotificationUrl = BASE_URL + "social_photo/SocialPhoto/sendNotifications"

					payloadpushData = {										
											"text":"Tagged Successfully",
											"title":"Tagged Your Photo",
											"image":image_data['image'],
											"user_id":image_data['user_id']
									  }
					print(payloadpushData)

					send_push_notification = requests.post(sendAppPushNotificationUrl,data=json.dumps(payloadpushData), headers=headers).json()


			else:
				delete_query = ("""DELETE FROM `tagged_event_photo` WHERE `event_photo_id` = %s and `user_id` = %s""")
				delData = (event_photo_id,user_id)
				
				cursor.execute(delete_query,delData)

				connection.commit()
				cursor.close()

		return ({"attributes": {
					    "status_desc": "tag_event_photo",
					    "status": "success"
				},
				"responseList":details}), status.HTTP_200_OK

#----------------------Tag-Event-Photo--------------------#

#----------------------Save-Device-Token---------------------#
@name_space.route("/saveDeviceToken")	
class saveDeviceToken(Resource):
	@api.expect(devicetoken_postmodel)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()

		details = request.get_json()		

		device_token_query = ("""SELECT `device_type`,`device_token`
				FROM `devices` WHERE `user_id` = %s and device_type = %s""")
		deviceData = (details['user_id'],details['device_type'])
		count_device_token = cursor.execute(device_token_query,deviceData)

		if count_device_token >0 :
			update_query = ("""UPDATE `devices` SET `device_token` = %s
							WHERE `user_id` = %s and `device_type` = %s""")
			update_data = (details['device_token'],details['user_id'],details['device_type'])
			cursor.execute(update_query,update_data)
		else:
			insert_query = ("""INSERT INTO `devices`(`device_type`,`device_token`,`user_id`) 
							VALUES(%s,%s,%s)""")

			insert_data = (details['device_type'],details['device_token'],details['user_id'])
			cursor.execute(insert_query,insert_data)

		return ({"attributes": {
				    		"status_desc": "device_token_details",
				    		"status": "success"
				    	},
				    	"responseList":details}), status.HTTP_200_OK

#----------------------Save-Device-Token---------------------#

#----------------------Send-Notification---------------------#

@name_space.route("/sendNotifications")
class sendNotifications(Resource):
	@api.expect(notification_model)
	def post(self):
		connection = mysql_connection()
		cursor = connection.cursor()
		details = request.get_json()

		user_id = details['user_id']

		get_device_query = ("""SELECT *
									FROM `devices` WHERE `user_id` = %s""")
		get_device_data = (user_id)
		cursor.execute(get_device_query,get_device_data)
		device_data = cursor.fetchone()
		print(device_data['device_token'])

		data_message = {
							"title" : details['title'],
							"message": details['text'],
							"image-url":details['image']
						}
		print(data_message)
		api_key = 'AAAAxrE-fFw:APA91bFXX69cHux-WctBeQFZBzMxLZXCaBeqsvFTh-67XxZzkE5TZUnvYlMzOARHZTlL6kSxSy3XDb-akfx-UWyai8W0x6T5St7buTRDSCdIFl0T0nOXZu4ULtUa50YIqH9jy9TxePq4'
		device_id = device_data['device_token']
		push_service = FCMNotification(api_key=api_key)
		msgResponse = push_service.notify_single_device(registration_id=device_id,data_message = data_message)
		sent = 'N'
		if msgResponse.get('success') == 1:
			sent = 'Y'
		
		
		connection.commit()
		cursor.close()

		return ({"attributes": {
				    		"status_desc": "Push Notification",
				    		"status": "success"
				    	},
				    	"responseList":msgResponse}), status.HTTP_200_OK

#----------------------Send-Notification---------------------#

#----------------------Delete-Event-Image---------------------#

@name_space_event.route("/deleteEventImage/<int:event_photo_id>")
class deleteEventImage(Resource):
	def delete(self, event_photo_id):
		connection = mysql_connection()
		cursor = connection.cursor()

		delete_query = ("""DELETE FROM `event_photos` WHERE `event_photo_id` = %s """)
		delData = (event_photo_id)		
		cursor.execute(delete_query,delData)

		delete_like_query = ("""DELETE FROM `event_photo_like` WHERE `event_photo_id` = %s """)
		delLikeData = (event_photo_id)		
		cursor.execute(delete_like_query,delLikeData)

		delete_tag_query = ("""DELETE FROM `tagged_event_photo` WHERE `event_photo_id` = %s """)
		delTagData = (event_photo_id)		
		cursor.execute(delete_tag_query,delTagData)

		connection.commit()
		cursor.close()
		
		return ({"attributes": {"status_desc": "Delete Image",
								"status": "success"},
				"responseList": 'Deleted Successfully'}), status.HTTP_200_OK

#----------------------Delete-Event-Image---------------------#

def random_string(letter_count, digit_count):  
    str1 = ''.join((random.choice(string.ascii_letters) for x in range(letter_count)))  
    str1 += ''.join((random.choice(string.digits) for x in range(digit_count)))  
  
    sam_list = list(str1) # it converts the string to list.  
    random.shuffle(sam_list) # It uses a random.shuffle() function to shuffle the string.  
    final_string = ''.join(sam_list)  
    return final_string

