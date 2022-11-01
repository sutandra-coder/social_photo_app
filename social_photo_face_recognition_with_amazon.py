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
import threading
import boto3
from botocore.config import Config
import os

ACCESS_KEY =  'AKIATWWALMDJOK5DMPTP'
SECRET_KEY = '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'

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

social_photo_face_recognition_with_amazon = Blueprint('social_photo_face_recognition_with_amazon_api', __name__)
api = Api(social_photo_face_recognition_with_amazon,  title='Social Photo Face Recognition with amazon',description='Social Photo Face Recognition With Amazon')
name_space = api.namespace('SocialPhotoWithFaceRecognitionWithAmazon',description='Social Photo Face Recognition with amazon')

update_user_model = api.model('updateUser', {
	"name":fields.String,
	"profile_image":fields.String,
	"image_no":fields.Integer
})

event_photo_postmodel = api.model('EventPhoto', {
	"image":fields.String(required=True),
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

		user_data = {}

		user_data['name'] = details['name']
		user_data['profile_image'] = details['profile_image']
		user_data['image_no'] = details['image_no']



		print(user_data)

		def updateProfileImageAsync(**kwargs):
			user_data = kwargs.get('user_data', {})
			name = user_data['name']


			if user_data and "name" in user_data:
				name = user_data['name']

				update_query = ("""UPDATE `user` SET `name` = %s
							WHERE `user_id` = %s """)
				update_data = (name,user_id)
				cursor.execute(update_query,update_data)

			if user_data and "profile_image" in user_data:
				profile_image = user_data['profile_image']
				image_no = user_data['image_no']

				update_query = ("""UPDATE `user` SET `profile_image` = %s
							WHERE `user_id` = %s """)
				update_data = (profile_image,user_id)
				cursor.execute(update_query,update_data)

				get_image_query = ("""SELECT * FROM `user_profile_images` where `user_id` = %s and `image_no` = %s""")
				get_image_data = (user_id,image_no)
				image_count = cursor.execute(get_image_query,get_image_data)

				if image_count > 0:
					update_query = ("""UPDATE `user_profile_images` SET `profile_image` = %s
					WHERE `user_id` = %s and `image_no` = %s""")
					update_data = (profile_image,user_id,image_no)
					cursor.execute(update_query,update_data)
					
				else:			
					insert_query = ("""INSERT INTO `user_profile_images`(`user_id`,`profile_image`,`image_no`) 
													VALUES(%s,%s,%s)""")			
					data = (user_id,profile_image,image_no)
					cursor.execute(insert_query,data)

			get_user_profile_query = ("""SELECT *
								FROM `user_profile_images` WHERE `user_id` = %s""")		
			get_user_profile_data = (user_id)
			user_profile_count = cursor.execute(get_user_profile_query,get_user_profile_data)

			if user_profile_count > 0:
				user_profiles = cursor.fetchall()

				for key,user_profile in enumerate(user_profiles):
					new_name = str(user_profile['user_id'])+name+str(user_profile['image_no'])
					print(new_name)

					urllib.request.urlretrieve(user_profile['profile_image'], "home/ubuntu/flaskproject/images/"+str(user_profile['user_id'])+"-"+str(user_profile['image_no'])+"-"+name+".jpg")		

					if event_id == 0:
						print(event_id)
					else:
						get_event_photo_list_query = ("""SELECT *
										FROM `event_photos` WHERE `event_id` = %s and `user_id`<> %s""")
						get_event_photo_list_data = (event_id,user_id)
						event_photo_count = cursor.execute(get_event_photo_list_query,get_event_photo_list_data)

						if event_photo_count > 0 :
							event_photo_list_data = cursor.fetchall()

							for ekey,edata in enumerate(event_photo_list_data):

								try:
									#unknown_image_name = random_string(2,2)
									unknown_image_name = str(user_profile['user_id'])+"-"+str(user_profile['image_no'])+"-"+str(edata['event_photo_id'])+"-"+edata['image_name']
									urllib.request.urlretrieve(edata['image'], "home/ubuntu/flaskproject/images/"+unknown_image_name)
									#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
									#unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
									#print(unknown_image)

									unknown_image = "home/ubuntu/flaskproject/images/"+unknown_image_name

									known_image = "home/ubuntu/flaskproject/images/"+str(user_profile['user_id'])+"-"+str(user_profile['image_no'])+"-"+name+".jpg"

									'''known_image = face_recognition.load_image_file("./images/"+str(user_profile['user_id'])+"-"+str(user_profile['image_no'])+"-"+name+".jpg")
									
									profile_image_encoding = face_recognition.face_encodings(known_image)[0]
									unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

									matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

									listToStr = ''.join(map(str, matches))

									print(listToStr)

									if listToStr == 'True':'''

									imageSource=open(known_image,'rb')
									imageTarget=open(unknown_image,'rb')

									my_config = Config(
									    region_name = 'us-east-1'
									)

									client=boto3.client('rekognition',config=my_config,aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
									response=client.compare_faces(SimilarityThreshold=80,
							 				SourceImage={'Bytes': imageSource.read()},
							 				TargetImage={'Bytes': imageTarget.read()})

									is_matches = len(response['FaceMatches'])

									#imageSource.close()
									#imageTarget.close()

									if is_matches == 1 and response['SourceImageFace']['Confidence'] >= 99: 
										get_tag_image_query = ("""SELECT *
														  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`user_id` = %s and tep.`event_id` = %s""")
										get_tag_image_data = (edata['event_photo_id'],user_id,event_id)
										tag_image_count = cursor.execute(get_tag_image_query,get_tag_image_data)

										if tag_image_count < 1:
											insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
													VALUES(%s,%s,%s,%s)""")
											data = (edata['event_photo_id'],event_id,user_id,edata['user_id'])
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

		thread = threading.Thread(target=updateProfileImageAsync, kwargs={
                    'user_data': user_data})
		thread.start()

		dir = 'home/ubuntu/flaskproject/images/'
		for f in os.listdir(dir):
		    os.remove(os.path.join(dir, f))	


		return ({"attributes": {"status_desc": "Update User",
								"status": "success"},
				"responseList": 'Updated Successfully'}), status.HTTP_200_OK

#----------------------Update-User---------------------#

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

		image_name_split = image.split("/")
		#image_name = image_name_split[4]
		image_name = random_string(2,2)+"jpeg"

		insert_query = ("""INSERT INTO `event_photos`(`image`,`image_name`,`text`,`event_id`,`event_manager_id`,`user_id`) 
						VALUES(%s,%s,%s,%s,%s,%s)""")
		data = (image,image_name,text,event_id,event_manager_id,user_id)
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
				'''get_tagged_images_query = ("""SELECT ep.`image`,ep.`event_photo_id`,ep.`event_id`
													  FROM `tagged_event_photo` tep 
													  INNER JOIN `event_photos` ep ON ep.`event_photo_id` = tep.`event_photo_id`
													  where tep.`user_id` = %s """)
				get_tagged_image_query = (data['user_id'])
				get_tagged_image_count =  cursor.execute(get_tagged_images_query,get_tagged_image_query)

				if get_tagged_image_count > 0:
					tagged_image_data =  cursor.fetchall()

					for tkey,tdata in enumerate(tagged_image_data):
						urllib.request.urlretrieve(tdata['image'], "home/ubuntu/flaskproject/images/"+str(data['user_id'])+"-tagged_image.jpg")		
								#known_image = face_recognition.load_image_file(data['name']+".jpg")
						known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(data['user_id'])+"-tagged_image.jpg")

						unknown_image_name = random_string(2,2)
						urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
								#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
						unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")

						profile_image_encoding = face_recognition.face_encodings(known_image)[0]
						unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

						matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

						listToStr = ''.join(map(str, matches))

						print(listToStr)

						if listToStr == 'True':
							get_tag_image_query = ("""SELECT *
												  FROM `tagged_event_photo` tep where tep.`event_photo_id` = %s and tep.`user_id` = %s""")
							get_tag_image_data = (tdata['event_photo_id'],data['user_id'])
							tag_image_count = cursor.execute(get_tag_image_query,get_tag_image_data)

							if tag_image_count < 1:
								insert_query = ("""INSERT INTO `tagged_event_photo`(`event_photo_id`,`event_id`,`user_id`,`tagged_by_user_id`) 
											VALUES(%s,%s,%s,%s)""")
								data = (tdata['event_photo_id'],tdata['event_id'],data['user_id'],user_id)
									
								vice_data = (event_photo_id,event_id,user_id,data['user_id'])
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

								send_push_notification = requests.post(sendAppPushNotificationUrl,data=json.dumps(payloadpushData), headers=headers).json()'''
												

				get_user_profile_image_query = ("""SELECT *
							FROM `user_profile_images` WHERE `user_id` = %s limit 1""")
				get_user_profile_image_data = (data['user_id'])
				user_profile_image_count = cursor.execute(get_user_profile_image_query,get_user_profile_image_data)

				if user_profile_image_count > 0:
					user_profile_images = cursor.fetchall()
					print(user_profile_images)
					for upkey,user_profile_image in enumerate(user_profile_images):

						try:
							if(user_profile_image['profile_image'] != ''):
								print(user_profile_image['image_no'])

								known_image = "home/ubuntu/flaskproject/images/"+str(data['user_id'])+"-"+str(user_profile_image['image_no'])+"-"+data['name']+".jpeg"

								print(known_image)

								urllib.request.urlretrieve(user_profile_image['profile_image'], known_image)		
								#known_image = face_recognition.load_image_file(data['name']+".jpg")
								#known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(data['user_id'])+"-"+str(user_profile_image['image_no'])+"-"+data['name']+".jpg")
								

								#unknown_image_name = random_string(2,2)
								unknown_image_name = str(data['user_id'])+"-"+image_name

								urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name)

								#urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
								#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
								#unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
								unknown_image = "home/ubuntu/flaskproject/images/"+unknown_image_name

								'''profile_image_encoding = face_recognition.face_encodings(known_image)[0]
								unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

								#face_locations = face_recognition.face_locations(unknown_image)
								#face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

								#face_distances = face_recognition.face_distance(unknown_image, face_encodings)
								#best_match_index = np.argmin(face_distances)
								matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

								listToStr = ''.join(map(str, matches))

								print(listToStr)
				  
								if listToStr == 'True':'''

								imageSource=open(known_image,'rb')
								imageTarget=open(unknown_image,'rb')

								my_config = Config(
									   region_name = 'us-east-1'
								)

								client=boto3.client('rekognition',config=my_config,aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
								response=client.compare_faces(SimilarityThreshold=80,
							 				SourceImage={'Bytes': imageSource.read()},
							 				TargetImage={'Bytes': imageTarget.read()})

								is_matches = len(response['FaceMatches'])

								if is_matches == 1 and response['SourceImageFace']['Confidence'] >= 99:
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

				else:
					print('hii')
					profile_image_url = data['profile_image']

					try:
						if(profile_image_url != ''):

							urllib.request.urlretrieve(profile_image_url, "home/ubuntu/flaskproject/images/"+str(data['user_id'])+'-'+data['name']+".jpg")		
							#known_image = face_recognition.load_image_file(data['name']+".jpg")
							known_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+str(data['user_id'])+'-'+data['name']+".jpg")

							#unknown_image_name = random_string(2,2)
							unknown_image_name = str(data['user_id'])+"-"+image_name

							urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name)

							#urllib.request.urlretrieve(image, "home/ubuntu/flaskproject/images/"+unknown_image_name+".jpg")
							#unknown_image = face_recognition.load_image_file(unknown_image_name+".jpg")
							unknown_image = face_recognition.load_image_file("home/ubuntu/flaskproject/images/"+unknown_image_name)

							'''profile_image_encoding = face_recognition.face_encodings(known_image)[0]
							unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

							#face_locations = face_recognition.face_locations(unknown_image)
							#face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

							#face_distances = face_recognition.face_distance(unknown_image, face_encodings)
							#best_match_index = np.argmin(face_distances)
							matches = face_recognition.compare_faces([profile_image_encoding], unknown_encoding)

							listToStr = ''.join(map(str, matches))

							print(listToStr)
			  
							if listToStr == 'True':'''

							imageSource=open(known_image,'rb')
							imageTarget=open(unknown_image,'rb')

							my_config = Config(
								   region_name = 'us-east-1'
							)

							client=boto3.client('rekognition',config=my_config,aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
							response=client.compare_faces(SimilarityThreshold=80,
							 				SourceImage={'Bytes': imageSource.read()},
							 				TargetImage={'Bytes': imageTarget.read()})

							is_matches = len(response['FaceMatches'])

							if is_matches == 1 and response['SourceImageFace']['Confidence'] >= 99:
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

		dir = 'home/ubuntu/flaskproject/images/'
		for f in os.listdir(dir):
		    os.remove(os.path.join(dir, f))

		connection.commit()
		cursor.close()

		return ({"attributes": {
					    "status_desc": "event_details",
					    "status": "success"
				},
				"responseList":details}), status.HTTP_200_OK

#----------------------Add-Event-Photo--------------------#

def random_string(letter_count, digit_count):  
    str1 = ''.join((random.choice(string.ascii_letters) for x in range(letter_count)))  
    str1 += ''.join((random.choice(string.digits) for x in range(digit_count)))  
  
    sam_list = list(str1) # it converts the string to list.  
    random.shuffle(sam_list) # It uses a random.shuffle() function to shuffle the string.  
    final_string = ''.join(sam_list)  
    return final_string

  #----------------------Add-Event-Photo--------------------#

#----------------------Remove-Photo-From-Folder--------------------#

@name_space.route("/removePhotoFromFoder")
class removePhotoFromFoder(Resource):	
	def get(self):
		dir = 'home/ubuntu/flaskproject/images/'
		for f in os.listdir(dir):
		    os.remove(os.path.join(dir, f))

  #----------------------Remove-Photo-From-Folder--------------------#