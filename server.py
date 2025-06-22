import os, gridfs, json, pika
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_SVC import access
from storage import util
from bson import ObjectId

server = Flask(__name__)

mongo_vidoe = PyMongo(
    server,
    uri='mongodb://mongodb:27017/videos',
    )

mongo_mp3 = PyMongo(
    server,
    uri='mongodb://mongodb:27017/mp3s',
    )

fs_video = gridfs.GridFS(mongo_vidoe.db)
fs_mp3 = gridfs.GridFS(mongo_mp3.db)

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
    access, err = validate.token(request)
    if err:
        return err
    access = json.loads(access)

    if access['is_admin']:
        if len(request.files) > 1 or len(request.files) < 1:
            return "Only one file can be uploaded at a time", 400
        
        for _, f in request.files.items():
            err = util.upload(f, fs_video, channel, access)

            if err:
                return err
            
        return "File uploaded successfully", 200
    else:
        return "You are not authorized to upload files", 403
    

@server.route('/download', methods=['GET'])
def download():
    access, err = validate.token(request)
    if err:
        return err
    access = json.loads(access)

    if access['is_admin']:
        fid_string = request.args.get('fid')
        if not fid_string:
            return "fid is required", 400
        try:
            out = fs_mp3.get(ObjectId(fid_string))
            return send_file(out, as_attachment=True, download_name=fid_string + ".mp3")
        except Exception as e:
            return f"Internal server error at file download \n {e}", 404
        
    return "Unauthorized to download files", 401

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=8080)