import face_recognition
import numpy as np

def is_match(frame,  database, is_embeddings=True):
    if is_embeddings:
        known_face_encodings, known_face_names = database

    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)
    names = []
    for face_encoding in face_encodings:
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)

        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]

        names.append(name)
    return (face_locations, names)

def db_update( img_encoding,name, prefix='facedb'):
    #obama_image = face_recognition.load_image_file("obama.jpg")
    #obama_face_encoding = face_recognition.face_encodings(obama_image)[0]
    with open(prefix+'_encodings.txt','a') as f:
        f.write(str(img_encoding).replace('\n',' ')[1:-1])
        f.write('\n')
    with open(prefix+'_names.txt','a') as f:
        f.write(name)
        f.write('\n')

def db_load(prefix='facedb'):
    with open(prefix+'_encodings.txt','r') as f:
        encodings = f.read().splitlines()
    encodings = [i.split() for i in encodings]
    with open(prefix+'_names.txt','r') as f:
        names = f.read().splitlines()
    return (np.array(encodings,'float64'),names)

if __name__=='__main__':
    print(db_load('facedb'))

    