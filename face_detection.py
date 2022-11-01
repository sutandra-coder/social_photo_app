import cv2
from matplotlib import pyplot as plt
from flask import Flask, request, jsonify, json
from flask import Blueprint
from flask_api import status
from flask_restplus import Api, Resource, fields
from flask_cors import CORS, cross_origin
import face_recognition
import numpy as np
from PIL import Image, ImageDraw
from IPython.display import display

app = Flask(__name__)
cors = CORS(app)

face_detection = Blueprint('face_detection_api', __name__)
api = Api(face_detection,  title='Face Detection API',description='Face Detection')
name_space = api.namespace('SocialPhoto',description='Social Photo')

#----------------------Face-Detection---------------------#

@name_space.route("/faceDetection")	
class faceDetection(Resource):
	def get(self):	  

		img = cv2.imread("group.png")
  
		# OpenCV opens images as BRG 
		# but we want it as RGB We'll 
		# also need a grayscale version
		img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		  
		  
		# Use minSize because for not 
		# bothering with extra-small 
		# dots that would look like STOP signs
		stop_data = cv2.CascadeClassifier('stop_data.xml')
		  
		found = stop_data.detectMultiScale(img_gray, 
		                                   minSize =(40, 40))
		  
		# Don't do anything if there's 
		# no sign
		amount_found = len(found)
		  
		if amount_found != 0:
		      
		    # There may be more than one
		    # sign in the image
		    for (x, y, width, height) in found:
		          
		        # We draw a green rectangle around
		        # every recognized sign
		        cv2.rectangle(img_rgb, (x, y), 
		                      (x + height, y + width), 
		                      (0, 255, 0), 5)
		          
		# Creates the environment of 
		# the picture and shows it
		plt.subplot(1, 1, 1)
		plt.imshow(img_rgb)
		plt.show()

#----------------------Face-Detection---------------------#

#----------------------Face-Detection---------------------#

@name_space.route("/faceRecognition")	
class faceRecognition(Resource):
	def get(self):	 	
		# This is an example of running face recognition on a single image
		# and drawing a box around each person that was identified.

		# Load a sample picture and learn how to recognize it.
		obama_image = face_recognition.load_image_file("44_barack_obama.jpg")
		obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

		# Load a second sample picture and learn how to recognize it.
		biden_image = face_recognition.load_image_file("biden.jpg")
		biden_face_encoding = face_recognition.face_encodings(biden_image)[0]

		# Create arrays of known face encodings and their names
		known_face_encodings = [
		    obama_face_encoding,
		    biden_face_encoding
		]
		known_face_names = [
		    "Barack Obama",
		    "Joe Biden"
		]
		print('Learned encoding for', len(known_face_encodings), 'images.')

		# Load an image with an unknown face
		unknown_image = face_recognition.load_image_file("download.png")

		# Find all the faces and face encodings in the unknown image
		face_locations = face_recognition.face_locations(unknown_image)
		face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

		# Convert the image to a PIL-format image so that we can draw on top of it with the Pillow library
		# See http://pillow.readthedocs.io/ for more about PIL/Pillow
		pil_image = Image.fromarray(unknown_image)
		# Create a Pillow ImageDraw Draw instance to draw with
		draw = ImageDraw.Draw(pil_image)

		# Loop through each face found in the unknown image
		for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
		    # See if the face is a match for the known face(s)
		    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

		    name = "Unknown"

		    # Or instead, use the known face with the smallest distance to the new face
		    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
		    best_match_index = np.argmin(face_distances)
		    if matches[best_match_index]:
		        name = known_face_names[best_match_index]

		    # Draw a box around the face using the Pillow module
		    draw.rectangle(((left, top), (right, bottom)), outline=(0, 0, 255))

		    # Draw a label with a name below the face
		    text_width, text_height = draw.textsize(name)
		    draw.rectangle(((left, bottom - text_height - 10), (right, bottom)), fill=(0, 0, 255), outline=(0, 0, 255))
		    draw.text((left + 6, bottom - text_height - 5), name, fill=(255, 255, 255, 255))


		# Remove the drawing library from memory as per the Pillow docs
		del draw

		# Display the resulting image
		display(pil_image)
		pil_image.show()
