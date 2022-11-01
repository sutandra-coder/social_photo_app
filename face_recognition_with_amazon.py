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
import random, string
import boto3
from botocore.config import Config
import urllib.request
import cv2

ACCESS_KEY =  'AKIATWWALMDJOK5DMPTP'
SECRET_KEY = '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'

app = Flask(__name__)
cors = CORS(app)

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

face_recognition_with_amazon = Blueprint('face_recognition_with_amazon', __name__)
api = Api(face_recognition_with_amazon,  title='Amazon Textract',description='Amazon Textract')
name_space = api.namespace('faceRecognitionWithAmazon',description='Face Recognition With Amazon')

@name_space.route("/FaceRecognition")
class FaceRecognition(Resource):
	def get(self):
		connection = mysql_connection()
		cursor = connection.cursor()

		user_id = 8

		get_user_profile_query = ("""SELECT *
								FROM `user_profile_images` WHERE `user_id` = %s""")		
		get_user_profile_data = (user_id)
		user_profile_count = cursor.execute(get_user_profile_query,get_user_profile_data)

		user_profile= cursor.fetchone()

		print(user_profile)

		get_event_manager_photo = ("""SELECT *
								FROM `event_photos` WHERE `event_manager_id` = 1 and `event_photo_id` = 189""")	
		get_event_manager_photo_data_count =  cursor.execute(get_event_manager_photo)
		get_event_manager_photo_data = cursor.fetchone()

		name = "sourav"

		urllib.request.urlretrieve(user_profile['profile_image'], "./images/"+str(user_profile['user_id'])+"-"+str(user_profile['image_no'])+"-"+name+".jpg")
		
		urllib.request.urlretrieve(get_event_manager_photo_data['image'], "./images/"+str(user_profile['user_id'])+"-2-"+name+".jpg")
		
		source_file = "./images/"+str(user_profile['user_id'])+"-"+str(user_profile['image_no'])+"-"+name+".jpg"
		target_file = "./images/"+str(user_profile['user_id'])+"-2-"+name+".jpg"

		imageSource=open(source_file,'rb')
		imageTarget=open(target_file,'rb')

		my_config = Config(
		    region_name = 'us-east-1'
		)

		client=boto3.client('rekognition',config=my_config,aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
		response=client.compare_faces(SimilarityThreshold=80,
 				SourceImage={'Bytes': imageSource.read()},
 				TargetImage={'Bytes': imageTarget.read()})

		is_matches = len(response['FaceMatches'])
		if is_matches == 1:
			if response['SourceImageFace']['Confidence'] >= 99:
				print("True")
			else:
				print("False")
		else:
			print("False")

		return ({"attributes": {
					    "status_desc": "face_recogniti",
					    "status": "success"
				},
				"responseList":response}), status.HTTP_200_OK


def compare_faces(sourceFile, targetFile):
 my_config = Config(
		    region_name = 'us-east-1'
		)
 client=boto3.client('rekognition',config=my_config,aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)

 imageSource=open(sourceFile,'rb')
 imageTarget=open(targetFile,'rb')
 response=client.compare_faces(SimilarityThreshold=80,
 SourceImage={'Bytes': imageSource.read()},
 TargetImage={'Bytes': imageTarget.read()})

 print(response)

 for faceMatch in response['FaceMatches']:
	 position = faceMatch['Face']['BoundingBox']
	 similarity = str(faceMatch['Similarity'])
	 print('The face at ' +
	 str(position['Left']) + ' ' +
	 str(position['Top']) +
	 ' matches with ' + similarity + '% confidence')
 imageSource.close()
 imageTarget.close()
 return len(response['FaceMatches'])

@name_space.route("/UpdateImage")
class UpdateImage(Resource):
	def get(self):
		connection = mysql_connection()
		cursor = connection.cursor()

		get_event_manager_photo = ("""SELECT *
								FROM `event_photos` WHERE `event_id` = 1""")	
		get_event_manager_photo_data_count =  cursor.execute(get_event_manager_photo)
		get_event_manager_photo_data = cursor.fetchall()

		for key,photo_data in enumerate(get_event_manager_photo_data):
			photo_data_image = photo_data['image']
			x = photo_data_image.split("/")

			update_query = ("""UPDATE `event_photos` SET `image_name` = %s
					WHERE `event_photo_id` = %s """)
			update_data = (x[4],photo_data['event_photo_id'])
			cursor.execute(update_query,update_data)

		connection.commit()
		cursor.close()

		return ({"attributes": {"status_desc": "Update Customer Exchange Device Ans",
								"status": "success"},
				"responseList": 'Updated Successfully'}), status.HTTP_200_OK


@name_space.route("/detectFace")
class detectFace(Resource):
	def get(self):

		name = "sourav"
		urllib.request.urlretrieve('https://d1lwvo1ffrod0a.cloudfront.net/1111/IMG_4222.jpg', "home/ubuntu/flaskproject/images/"+name+".jpg")
		source_file = "home/ubuntu/flaskproject/images/"+name+".jpg"
		
		img = cv2.imread(source_file)
  
		# OpenCV opens images as BRG 
		# but we want it as RGB We'll 
		# also need a grayscale version
		img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		  
		  
		# Use minSize because for not 
		# bothering with extra-small 
		# dots that would look like STOP signs
		stop_data = cv2.CascadeClassifier('home/ubuntu/flaskproject/stop_data.xml')
		  
		found = stop_data.detectMultiScale(img_gray, 
		                                   minSize =(40, 40))
		  
		# Don't do anything if there's 
		# no sign
		amount_found = len(found)
		  
		if amount_found != 0:
			a = 'success'
		else:
			a = 'failure'
			
		return ({"attributes": {"status_desc": "Update Customer Exchange Device Ans",
								"status": "success"},
				"responseList": a}), status.HTTP_200_OK





