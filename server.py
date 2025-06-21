import os, gridfs, json, pika
from flask import Flask, request
from flask_pymongo import PyMongo
from auth import validate
from auth_SVC import access
from storage import util


server = Flask(__name__)
server.config['MONGO_URI'] = "mongodb://host.minikube.internal:27017/videos"

mongo = PyMongo(server)

fs = gridfs.GridFS(mongo.db)

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

@server.route('/login', methods=['POST'])
def login():
    token, err = access.login(request)
    if not err:
        return token
    else:
        return err

@server.route('/upload', methods=['POST'])
def upload():
    print("Upload request received")
    access, err = validate.token(request)

    access = json.loads(access)

    if access['is_admin']:
        if len(request.files) > 1 or len(request.files) < 1:
            return "Only one file can be uploaded at a time", 400
        
        for _, f in request.files.items():
            err = util.upload(f, fs, channel, access)

            if err:
                print(err)
                return err
            
        return "File uploaded successfully", 200
    else:
        return "You are not authorized to upload files", 403
    

@server.route('/download', methods=['GET'])
def download():
    pass

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=8080)