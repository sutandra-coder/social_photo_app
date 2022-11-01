from flask import Flask, request, jsonify, json
from flask_api import status
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
import face_recognition
import numpy as np
from PIL import Image, ImageDraw
from IPython.display import display
import urllib.request

app = Flask(__name__)
cors = CORS(app)

#----------------------database-connection---------------------#
def mysql_connection():
	connection = pymysql.connect(host='creamsonservices.com',
	                             user='creamson_langlab',
	                             password='Langlab@123',
	                             db='social_photo',
	                             charset='utf8mb4',
	                             cursorclass=pymysql.cursors.DictCursor)
	return connection

def connect_logindb():
	connection = pymysql.connect(host='creamsonservices.com',
	                             user='creamson_langlab',
	                             password='Langlab@123',
	                             db='creamson_logindb',
	                             charset='utf8mb4',
								cursorclass=pymysql.cursors.DictCursor)
	return connection

def mysql_connection_event():
	connection = pymysql.connect(host='creamsonservices.com',
	                             user='creamson_langlab',
	                             password='Langlab@123',
	                             db='event',
	                             charset='utf8mb4',
	                             cursorclass=pymysql.cursors.DictCursor)
	return connection

#----------------------database-connection---------------------#


social_photo_face_recognition = Blueprint('social_photo_face_recognitiom_api', __name__)
api = Api(social_photo_face_recognition,  title='Social Photo Face Recognition API',description='Social Photo Face Recognition')

name_space = api.namespace('SocialPhotoWithFaceRecognition',description='Social Photo')

upload_parser = api.parser()
#upload_parser.add_argument('file', location='files', type=FileStorage, required=True)
upload_parser.add_argument('image', location='files',type=FileStorage, required=True)

update_user_model = api.model('updateUser', {
	"name":fields.String,
	"profile_image":fields.String
})

event_photo_postmodel = api.model('EventPhoto', {
	"image":fields.String(required=True),
	"text":fields.String,
	"event_id":fields.Integer(required=True),	
	"event_manager_id":fields.Integer(required=True),
	"user_id":fields.Integer(required=True),
})

event_photo_postmodel_multiple = api.model('EventPhotoMultiple', {	
	"image":fields.List(fields.String),
	"text":fields.String,
	"event_id":fields.Integer(required=True),	
	"event_manager_id":fields.Integer(required=True),
	"user_id":fields.Integer(required=True),
})



BASE_URL = 'http://ec2-18-221-89-14.us-east-2.compute.amazonaws.com/flaskapp/'

#----------------------Update-User---------------------#

@name_space.route("/UpdateUser/<int:user_id>/<int:event_id>")
class UpdateUser(Resource):
	@api.expect(update_user_model)
	def put(self,user_id,event_id):

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

		

		get_user_profile_query = ("""SELECT *
							FROM `user` WHERE `user_id` = %s""")		
		get_user_profile_data = (user_id)
		user_profile_count = cursor.execute(get_user_profile_query,get_user_profile_data)

		if user_profile_count > 0:
			user_profile = cursor.fetchone()
			print(user_profile)

			urllib.request.urlretrieve(user_profile['profile_image'], "home/ubuntu/flaskproject/images/"+str(user_profile['user_id'])+"-"+user_profile['name']+".jpg")		
			profile_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(user_profile['user_id'])+"-"+user_profile['name']+".jpg")	
			
			profile_image_encoding = face_recognition.face_encodings(profile_image)[0]		

			# Create arrays of known face encodings and their names
			known_face_encodings = [
			    profile_image_encoding
			]
			known_face_names = [
			 user_profile['name']
			]
			print('Learned encoding for', len(known_face_encodings), 'image.')

			if event_id == 0:
				print(event_id)
			else:
				get_event_photo_list_query = ("""SELECT *
									FROM `event_photos` WHERE `event_id` = %s and `user_id`<> %s""")
				get_event_photo_list_data = (event_id,user_id)
				event_photo_count = cursor.execute(get_event_photo_list_query,get_event_photo_list_data)

				if event_photo_count > 0 :
					event_photo_list_data = cursor.fetchall()

					for key,data in enumerate(event_photo_list_data):

						try:
							unknown_image_name = random_string(2,2)
							urllib.request.urlretrieve(data['image'], "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
							#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
							unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
							#print(unknown_image)

							known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(user_profile['user_id'])+"-"+user_profile['name']+".jpg")
							
							profile_image_encoding = face_recognition.face_encodings(known_image)[0]
							unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

							matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

							listToStr = ''.join(map(str, matches))

							print(listToStr)

							if listToStr == 'True': 
								get_tag_image_query = ("""SELECT *
												  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`user_id` = %s""")
								get_tag_image_data = (data['event_photo_id'],data['user_id'])
								tag_image_count = cursor.execute(get_tag_image_query,get_tag_image_data)

								if tag_image_count < 1:
									insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
											VALUES(%s,%s,%s,%s)""")
									data = (data['event_photo_id'],event_id,user_id,data['user_id'])
									cursor.execute(insert_query,data)

									'''get_image_query = ("""SELECT *
														  FROM `event_photos` ep where ep.`event_photo_id` = %s""")
									get_image_data = (data['event_photo_id'])
									image_count = cursor.execute(get_image_query,get_image_data)
									image_data = cursor.fetchone()

									headers = {'Content-type':'application/json', 'Accept':'application/json'}
									sendAppPushNotificationUrl = BASE_URL + "social_photo/SocialPhoto/sendNotifications"

									payloadpushData = {										
															"text":"Tagged Successfully",
															"title":"Tagged Your Photo",
															"image":data['image'],
															"user_id":data['user_id']
													  }
									print(payloadpushData)

									send_push_notification = requests.post(sendAppPushNotificationUrl,data=json.dumps(payloadpushData), headers=headers).json()'''

						except IndexError as e:	
							print(e)


		connection.commit()
		cursor.close()

		
		return ({"attributes": {"status_desc": "Update User",
								"status": "success"},
				"responseList": 'Updated Successfully'}), status.HTTP_200_OK

#----------------------Update-User---------------------#


@name_space.route("/faceRecognition")	
class faceRecognition(Resource):
	def get(self):

		connection = mysql_connection()
		cursor = connection.cursor()	

		'''get_user_profile_query = ("""SELECT *
							FROM `user` WHERE `user_id` = 11""")
		user_profile_count = cursor.execute(get_user_profile_query)		
		user_profile = cursor.fetchone()			

		url = "https://d1lwvo1ffrod0a.cloudfront.net/11/download.png" 
		urllib.request.urlretrieve(url, "download.jpg")		

		urllib.request.urlretrieve(user_profile['profile_image'], user_profile['name']+".jpg")		
		known_image = face_recognition.load_image_file(user_profile['name']+".jpg")		

		unknown_image = face_recognition.load_image_file("download.jpg")		

		profile_image_encoding = face_recognition.face_encodings(known_image)[0]
		unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

		results = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

		print(results)'''

		known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/sut.jpeg")
		unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/sutpramit.jpeg")

		biden_encoding = face_recognition.face_encodings(known_image)[0]
		unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

		results = face_recognition.compare_faces([biden_encoding], unknown_encoding)

		print(results)


#----------------------Add-Event-Photo--------------------#

@name_space.route("/AddEventPhoto")
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

		get_user_list_query = ("""SELECT *
							FROM `user` WHERE `event_manager_id` = %s""")
		get_user_list_data = (event_manager_id)
		user_list_count = cursor.execute(get_user_list_query,get_user_list_data)

		if user_list_count > 0:
			user_list = cursor.fetchall()

			for key,data in enumerate(user_list):
				profile_image_url = data['profile_image']

				try:
					if(profile_image_url != ''):

						urllib.request.urlretrieve(profile_image_url, "home/ubuntu/flaskproject/images/"+str(data['user_id'])+'-'+data['name']+".jpg")		
						#known_image = face_recognition.load_image_file(data['name']+".jpg")
						known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(data['user_id'])+'-'+data['name']+".jpg")

						unknown_image_name = random_string(2,2)
						urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
						#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
						unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")

						profile_image_encoding = face_recognition.face_encodings(known_image)[0]
						unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

						#face_locations = face_recognition.face_locations(unknown_image)
						#face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

						#face_distances = face_recognition.face_distance(unknown_image, face_encodings)
						#best_match_index = np.argmin(face_distances)
						matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

						listToStr = ''.join(map(str, matches))

						print(listToStr)
		  
						if listToStr == 'True':
							uuid= data['user_id']
							get_tag_image_query = ("""SELECT *
											  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`user_id` = %s""")
							get_tag_image_data = (event_photo_id,uuid)
							tag_image_count = cursor.execute(get_tag_image_query,get_tag_image_data)

							if tag_image_count < 1:
								insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
										VALUES(%s,%s,%s,%s)""")
								data = (event_photo_id,event_id,uuid,user_id)
								
								vice_data = (event_photo_id,event_id,user_id,uuid)
								cursor.execute(insert_query,data)
								#cursor.execute(insert_query,vice_data)

								'''insert_vice_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
										VALUES(%s,%s,%s,%s)""")
								vice_data = (event_photo_id,event_id,user_id,data['user_id'])
								cursor.execute(insert_vice_query,vice_data)'''

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
				except IndexError as e:
					print(e)	

		connection.commit()
		cursor.close()

		return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success"
				},
				"responseList":details}), status.HTTP_200_OK

#----------------------Add-Event-Photo--------------------#

#----------------------Add-Event-Photo--------------------#

@name_space.route("/AddEventPhotoMultiple")
class AddEventPhotoMultiple(Resource):
	@api.expect(event_photo_postmodel_multiple)
	def post(self):

		connection = mysql_connection()
		cursor = connection.cursor()		
		details = request.get_json()

		#image = details['image']
		text = details['text']
		event_id = details['event_id']
		event_manager_id = details['event_manager_id']
		user_id = details['user_id']

		images = details.get('image',[])

		for key,image in enumerate(images):			

			insert_query = ("""INSERT INTO `event_photos`(`image`,`text`,`event_id`,`event_manager_id`,`user_id`) 
							VALUES(%s,%s,%s,%s,%s)""")
			data = (image,text,event_id,event_manager_id,user_id)
			cursor.execute(insert_query,data)

			event_photo_id = cursor.lastrowid
			
			details['event_photo_id'] = event_photo_id

			get_user_list_query = ("""SELECT *
								FROM `user` WHERE `event_manager_id` = %s""")
			get_user_list_data = (event_manager_id)
			user_list_count = cursor.execute(get_user_list_query,get_user_list_data)

			if user_list_count > 0:
				user_list = cursor.fetchall()

				for key,data in enumerate(user_list):
					profile_image_url = data['profile_image']

					try:
						if(profile_image_url != ''):

							urllib.request.urlretrieve(profile_image_url, "home/ubuntu/flaskproject/images/"+str(data['user_id'])+'-'+data['name']+".jpg")		
							#known_image = face_recognition.load_image_file(data['name']+".jpg")
							known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(data['user_id'])+'-'+data['name']+".jpg")

							unknown_image_name = random_string(2,2)
							urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
							#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
							unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")

							profile_image_encoding = face_recognition.face_encodings(known_image)[0]
							unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

							#face_locations = face_recognition.face_locations(unknown_image)
							#face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

							#face_distances = face_recognition.face_distance(unknown_image, face_encodings)
							#best_match_index = np.argmin(face_distances)
							matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

							listToStr = ''.join(map(str, matches))

							print(listToStr)
			  
							if listToStr == 'True':
								uuid= data['user_id']
								get_tag_image_query = ("""SELECT *
												  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`user_id` = %s""")
								get_tag_image_data = (event_photo_id,uuid)
								tag_image_count = cursor.execute(get_tag_image_query,get_tag_image_data)

								if tag_image_count < 1:
									insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
											VALUES(%s,%s,%s,%s)""")
									data = (event_photo_id,event_id,uuid,user_id)
									
									vice_data = (event_photo_id,event_id,user_id,uuid)
									cursor.execute(insert_query,data)
									#cursor.execute(insert_query,vice_data)

									'''insert_vice_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
											VALUES(%s,%s,%s,%s)""")
									vice_data = (event_photo_id,event_id,user_id,data['user_id'])
									cursor.execute(insert_vice_query,vice_data)'''

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
					except IndexError as e:
						print(e)	

		connection.commit()
		cursor.close()

		return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success"
				},
				"responseList":details}), status.HTTP_200_OK

#----------------------Add-Event-Photo--------------------#

#----------------------Add-Event-Photo--------------------#


@name_space.route("/AddEventPhotowithFile")
class AddEventPhotowithFile(Resource):
	@name_space.expect(upload_parser)
	def post(self):
		print(request)


#----------------------Multiple-Face-Recognition--------------------#

@name_space.route("/multiplefaceRecognition/<int:event_id>/<int:user_id>")	
class multiplefaceRecognition(Resource):
	def get(self,event_id,user_id):

		connection = mysql_connection()
		cursor = connection.cursor()

		get_user_profile_query = ("""SELECT *
							FROM `user` WHERE `user_id` = %s""")		
		get_user_profile_data = (user_id)
		user_profile_count = cursor.execute(get_user_profile_query,get_user_profile_data)

		
		user_profile = cursor.fetchone()
		print(user_profile)

		get_event_photo_list_query = ("""SELECT `image`
								FROM `event_photos` WHERE `event_id` = %s and `user_id`<> %s""")
		get_event_photo_list_data = (event_id,user_id)
		event_photo_count = cursor.execute(get_event_photo_list_query,get_event_photo_list_data)

		event_photo_list = cursor.fetchall()

		for key,data in enumerate(event_photo_list):
			try:
				unknown_image_name = random_string(2,2)
				urllib.request.urlretrieve(data['image'], "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
						#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
				unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")			

				known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(user_profile['user_id'])+"-"+user_profile['name']+".jpg")
						
				profile_image_encoding = face_recognition.face_encodings(known_image)[0]
				unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

				matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

				listToStr = ''.join(map(str, matches))

				print(listToStr)
			except IndexError as e:
				print(e)

		return ({"attributes": {
					    "status_desc": "event_photo_list",
					    "status": "success"
				},
				"responseList":event_photo_list}), status.HTTP_200_OK

#----------------------Multiple-Face-Recognition--------------------#


def random_string(letter_count, digit_count):  
    str1 = ''.join((random.choice(string.ascii_letters) for x in range(letter_count)))  
    str1 += ''.join((random.choice(string.digits) for x in range(digit_count)))  
  
    sam_list = list(str1) # it converts the string to list.  
    random.shuffle(sam_list) # It uses a random.shuffle() function to shuffle the string.  
    final_string = ''.join(sam_list)  
    return final_string


#----------------------Update-User---------------------#

@name_space.route("/UpdateUserEventPhoto/<int:user_id>/<int:event_id>")
class UpdateUserEventPhoto(Resource):
	@api.expect(update_user_model)
	def put(self,user_id,event_id):

		connection = mysql_connection_event()
		cursor = connection.cursor()

		connection_logindb = connect_logindb()
		cursorlogindb = connection_logindb.cursor()

		details = request.get_json()

		if details and "name" in details:
			name = details['name']

			update_query = ("""UPDATE `institution_user_credential` SET `FIRST_NAME` = %s
						WHERE `INSTITUTION_USER_ID` = %s """)
			update_data = (name,user_id)
			cursorlogindb.execute(update_query,update_data)

		if details and "profile_image" in details:
			profile_image = details['profile_image']

			update_query = ("""UPDATE `institution_user_credential` SET `IMAGE_URL` = %s
						WHERE `INSTITUTION_USER_ID` = %s """)
			update_data = (profile_image,user_id)
			cursorlogindb.execute(update_query,update_data)

		

		get_user_profile_query = ("""SELECT *
							FROM `institution_user_credential` WHERE `INSTITUTION_USER_ID` = %s""")		
		get_user_profile_data = (user_id)
		user_profile_count = cursorlogindb.execute(get_user_profile_query,get_user_profile_data)

		if user_profile_count > 0:
			user_profile = cursorlogindb.fetchone()
			print(user_profile)

			urllib.request.urlretrieve(user_profile['profile_image'], "home/ubuntu/flaskproject/images/"+str(user_profile['INSTITUTION_USER_ID'])+"-"+user_profile['FIRST_NAME']+".jpg")		
			profile_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(user_profile['INSTITUTION_USER_ID'])+"-"+user_profile['FIRST_NAME']+".jpg")	
			
			profile_image_encoding = face_recognition.face_encodings(profile_image)[0]		

			# Create arrays of known face encodings and their names
			known_face_encodings = [
			    profile_image_encoding
			]
			known_face_names = [
			 user_profile['FIRST_NAME']
			]
			print('Learned encoding for', len(known_face_encodings), 'image.')

			get_event_photo_list_query = ("""SELECT *
								FROM `event_photos` WHERE `event_id` = %s and `client_id`<> %s""")
			get_event_photo_list_data = (event_id,user_id)
			event_photo_count = cursor.execute(get_event_photo_list_query,get_event_photo_list_data)

			if event_photo_count > 0 :
				event_photo_list_data = cursor.fetchall()

				for key,data in enumerate(event_photo_list_data):

					try:
						unknown_image_name = random_string(2,2)
						urllib.request.urlretrieve(data['image'], "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
						#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
						unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
						#print(unknown_image)

						known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(user_profile['INSTITUTION_USER_ID'])+"-"+user_profile['FIRST_NAME']+".jpg")
						
						profile_image_encoding = face_recognition.face_encodings(known_image)[0]
						unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

						matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

						listToStr = ''.join(map(str, matches))

						print(listToStr)

						if listToStr == 'True': 
							if data['guest_id'] == 0:
								get_tag_image_query = ("""SELECT *
												  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`tagged_user_id` = %s""")
								get_tag_image_data = (data['event_photo_id'],data['guest_id'])
								tag_image_count = cursor.execute(get_tag_image_query,get_tag_image_data)

								if tag_image_count < 1:
									insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
											VALUES(%s,%s,%s,%s)""")
									data = (data['event_photo_id'],event_id,user_id,data['guest_id'])
									cursor.execute(insert_query,data)

							else:
								get_tag_image_query = ("""SELECT *
												  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`tagged_user_id` = %s""")
								get_tag_image_data = (data['event_photo_id'],data['client_id'])
								tag_image_count = cursor.execute(get_tag_image_query,get_tag_image_data)

								if tag_image_count < 1:
									insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
											VALUES(%s,%s,%s,%s)""")
									data = (data['event_photo_id'],event_id,user_id,data['client_id'])
									cursor.execute(insert_query,data)

								'''get_image_query = ("""SELECT *
													  FROM `event_photos` ep where ep.`event_photo_id` = %s""")
								get_image_data = (data['event_photo_id'])
								image_count = cursor.execute(get_image_query,get_image_data)
								image_data = cursor.fetchone()

								headers = {'Content-type':'application/json', 'Accept':'application/json'}
								sendAppPushNotificationUrl = BASE_URL + "social_photo/SocialPhoto/sendNotifications"

								payloadpushData = {										
														"text":"Tagged Successfully",
														"title":"Tagged Your Photo",
														"image":data['image'],
														"user_id":data['user_id']
												  }
								print(payloadpushData)

								send_push_notification = requests.post(sendAppPushNotificationUrl,data=json.dumps(payloadpushData), headers=headers).json()'''

					except IndexError as e:	
						print(e)


		connection.commit()
		cursor.close()

		
		return ({"attributes": {"status_desc": "Update User",
								"status": "success"},
				"responseList": 'Updated Successfully'}), status.HTTP_200_OK

#----------------------Update-User---------------------#

#----------------------Add-Event-Photo--------------------#

@name_space.route("/AddEventPhotoEventPhoto")
class AddEventPhotoEventPhoto(Resource):
	@api.expect(event_photo_postmodel)
	def post(self):

		connection = mysql_connection_event()
		cursor_event = connection.cursor()

		connection_logindb = connect_logindb()
		cursorlogindb = connection_logindb.cursor()
				
		details = request.get_json()

		image = details['image']
		text = details['text']
		event_id = details['event_id']
		event_manager_id = details['event_manager_id']
		user_id = details['user_id']

		get_user_role_query = ("""SELECT * FROM institution_user_credential_master where `INSTITUTION_USER_ID` = %s""")
		get_user_role_data = (user_id)
		user_role_count = cursorlogindb.execute(get_user_role_query,get_user_role_data)

		if user_role_count > 0:
			user_role_data =  cursorlogindb.fetchone()	
			if user_role_data['INSTITUTION_USER_ROLE'] == 'G1':
				get_client_query = ("""SELECT * FROM `guardian_dtls` where `INSTITUTION_USER_ID_GUARDIAN` = %s""")
				get_client_data = (user_id)
				count_client_data = cursorlogindb.execute(get_client_query,get_client_data)

				if count_client_data > 0:
					client_data = cursorlogindb.fetchone()
					insert_query = ("""INSERT INTO `event_photos`(`image`,`text`,`event_id`,`guest_id`,`client_id`,`event_manager_id`) 
									VALUES(%s,%s,%s,%s,%s,%s)""")
					data = (image,text,event_id,user_id,client_data['TITUTION_USER_ID_STUDENT'],event_manager_id)
					cursor_event.execute(insert_query,data)

					event_photo_id = cursor_event.lastrowid
					
					details['event_photo_id'] = event_photo_id

					get_user_list_query = ("""SELECT iuc.`INSTITUTION_USER_ID`,iuc.`INSTITUTION_USER_NAME`,iuc.`INSTITUTION_USER_PASSWORD`,iuc.`FIRST_NAME`,iuc.`LAST_NAME`,iuc.`PRIMARY_CONTACT_NUMBER`,iuc.`IMAGE_URL`
							FROM `guardian_dtls` gd
							INNER JOIN `institution_user_credential` iuc ON iuc.`INSTITUTION_USER_ID` = gd.`INSTITUTION_USER_ID_GUARDIAN`
							WHERE `client_id` = %s""")
					get_user_list_data = (client_data['TITUTION_USER_ID_STUDENT'])
					user_list_count = cursorlogindb.execute(get_user_list_query,get_user_list_data)

					if user_list_count > 0:
						user_list = cursorlogindb.fetchall()

						for key,data in enumerate(user_list):
							profile_image_url = data['IMAGE_URL']

							try:
								if(profile_image_url != ''):

									urllib.request.urlretrieve(profile_image_url, "home/ubuntu/flaskproject/images/"+str(data['INSTITUTION_USER_ID'])+'-'+data['FIRST_NAME']+".jpg")		
									#known_image = face_recognition.load_image_file(data['name']+".jpg")
									known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(data['INSTITUTION_USER_ID'])+'-'+data['FIRST_NAME']+".jpg")

									unknown_image_name = random_string(2,2)
									urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
									#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
									unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")

									profile_image_encoding = face_recognition.face_encodings(known_image)[0]
									unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

									#face_locations = face_recognition.face_locations(unknown_image)
									#face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

									#face_distances = face_recognition.face_distance(unknown_image, face_encodings)
									#best_match_index = np.argmin(face_distances)
									matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

									listToStr = ''.join(map(str, matches))

									print(listToStr)
					  
									if listToStr == 'True':
										uuid= data['INSTITUTION_USER_ID']
										get_tag_image_query = ("""SELECT *
														  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`tagged_user_id` = %s""")
										get_tag_image_data = (event_photo_id,uuid)
										tag_image_count = cursor_event.execute(get_tag_image_query,get_tag_image_data)

										if tag_image_count < 1:
											insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`tagged_user_id`,`photo_user_id`) 
													VALUES(%s,%s,%s,%s)""")
											data = (event_photo_id,event_id,uuid,user_id)
											
											vice_data = (event_photo_id,event_id,user_id,uuid)
											cursor_event.execute(insert_query,data)
											#cursor.execute(insert_query,vice_data)

											'''insert_vice_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
													VALUES(%s,%s,%s,%s)""")
											vice_data = (event_photo_id,event_id,user_id,data['user_id'])
											cursor.execute(insert_vice_query,vice_data)'''

											get_image_query = ("""SELECT *
																  FROM `event_photos` ep where ep.`event_photo_id` = %s""")
											get_image_data = (event_photo_id)
											image_count = cursor_event.execute(get_image_query,get_image_data)
											image_data = cursor_event.fetchone()

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
							except IndexError as e:
								print(e)			
				
						
					details['event_photo_id'] = event_photo_id
			elif user_role_data['INSTITUTION_USER_ROLE'] == 'S1':
				insert_query = ("""INSERT INTO `event_photos`(`image`,`text`,`event_id`,`client_id`,`event_manager_id`) 
									VALUES(%s,%s,%s,%s,%s)""")
				data = (image,text,event_id,user_id,event_manager_id)
				cursor_event.execute(insert_query,data)

				event_photo_id = cursor_event.lastrowid
					
				details['event_photo_id'] = event_photo_id

				get_user_list_query = ("""SELECT iuc.`INSTITUTION_USER_ID`,iuc.`INSTITUTION_USER_NAME`,iuc.`INSTITUTION_USER_PASSWORD`,iuc.`FIRST_NAME`,iuc.`LAST_NAME`,iuc.`PRIMARY_CONTACT_NUMBER`,iuc.`IMAGE_URL`
							FROM `guardian_dtls` gd
							INNER JOIN `institution_user_credential` iuc ON iuc.`INSTITUTION_USER_ID` = gd.`INSTITUTION_USER_ID_GUARDIAN`
							WHERE `client_id` = %s""")
				get_user_list_data = (client_id)
				user_list_count = cursorlogindb.execute(get_user_list_query,get_user_list_data)

				if user_list_count > 0:
					user_list = cursorlogindb.fetchall()

					for key,data in enumerate(user_list):
						profile_image_url = data['IMAGE_URL']

						try:
							if(profile_image_url != ''):

								urllib.request.urlretrieve(profile_image_url, "home/ubuntu/flaskproject/images/"+str(data['INSTITUTION_USER_ID'])+'-'+data['FIRST_NAME']+".jpg")		
								#known_image = face_recognition.load_image_file(data['name']+".jpg")
								known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(data['INSTITUTION_USER_ID'])+'-'+data['FIRST_NAME']+".jpg")

								unknown_image_name = random_string(2,2)
								urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
								#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
								unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")

								profile_image_encoding = face_recognition.face_encodings(known_image)[0]
								unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

								#face_locations = face_recognition.face_locations(unknown_image)
								#face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

								#face_distances = face_recognition.face_distance(unknown_image, face_encodings)
								#best_match_index = np.argmin(face_distances)
								matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

								listToStr = ''.join(map(str, matches))

								print(listToStr)
				  
								if listToStr == 'True':
									uuid= data['INSTITUTION_USER_ID']
									get_tag_image_query = ("""SELECT *
													  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`tagged_user_id` = %s""")
									get_tag_image_data = (event_photo_id,uuid)
									tag_image_count = cursor_event.execute(get_tag_image_query,get_tag_image_data)

									if tag_image_count < 1:
										insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`tagged_user_id`,`photo_user_id`) 
												VALUES(%s,%s,%s,%s)""")
										data = (event_photo_id,event_id,uuid,user_id)
										
										vice_data = (event_photo_id,event_id,user_id,uuid)
										cursor_event.execute(insert_query,data)
										#cursor.execute(insert_query,vice_data)

										'''insert_vice_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
												VALUES(%s,%s,%s,%s)""")
										vice_data = (event_photo_id,event_id,user_id,data['user_id'])
										cursor.execute(insert_vice_query,vice_data)'''

										get_image_query = ("""SELECT *
															  FROM `event_photos` ep where ep.`event_photo_id` = %s""")
										get_image_data = (event_photo_id)
										image_count = cursor_event.execute(get_image_query,get_image_data)
										image_data = cursor_event.fetchone()

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
						except IndexError as e:
							print(e)			

		'''insert_query = ("""INSERT INTO `event_photos`(`image`,`text`,`event_id`,`event_manager_id`,`user_id`) 
						VALUES(%s,%s,%s,%s,%s)""")
		data = (image,text,event_id,event_manager_id,user_id)
		cursor.execute(insert_query,data)'''

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