import pika, json

def upload(f, fs, channel, access):
    try:
        fid = fs.put(f)
    except Exception as e:
        return f"internal server error at file upload \n {e}", 500

    #print(access, flush=True)
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access['sub'],
    }

    try:
        print(message, flush=True)
        channel.basic_publish(
            exchange='',
            routing_key='video',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as e:
        fs.delete(fid)
        return f"internal server error at message publish \n {e}", 500