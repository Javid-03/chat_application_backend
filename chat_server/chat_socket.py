from fastapi import APIRouter,WebSocket
import socketio
import oauth2
from dotenv import dotenv_values
import mimetypes
import boto3
import base64


env = dict(dotenv_values(".env"))

S3_IMAGE_LINK = env.get("S3_IMAGE_LINK")
S3_BUCKET_NAME = env.get("S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = env.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = env.get("AWS_REGION_NAME")



s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION_NAME
)





router=APIRouter()



sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

socket_app = socketio.ASGIApp(sio)



connected_users={}


@sio.event
async def connect(sid,environ):
    headers = environ.get('HTTP_AUTHORIZATION')
    if headers:
        authorization_token = headers.split(' ')[1]
        print(f"Authorization token: {authorization_token}")
        try:
            payload = oauth2.verify_customer_access_token(authorization_token)
            connected_users[payload["email"]]=sid

        except:
            payload=oauth2.verify_access_token(authorization_token)
            connected_users['admin']=sid


        print(connected_users)
        
    else:
        print("No authorization token found")
        await sio.disconnect(sid)
    




@sio.event
async def admin_message(sid, data):
    if 'message' in data:
        await sio.emit(data['event'], data['message'],to=connected_users[data["user"]])
    elif 'image' and 'file_name':
        file_name = data["file_name"]
        file_content = base64.b64decode(data["image"])

        content_type, _ = mimetypes.guess_type(file_name)
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file_name, Body=file_content, ContentType=content_type)
        image_link = f"{S3_IMAGE_LINK}{file_name}"
        await sio.emit(data['event'], image_link,to=connected_users[data["user"]])
        
    print(connected_users[data["user"]])

    print(f"Message broadcasted: {data}")


@sio.event
async def user_message(sid, data):
    if 'message' in data:
        await sio.emit(data['event'], data['message'],to=connected_users["admin"])
    elif 'image' and 'file_name':
        file_name = data["file_name"]
        file_content = base64.b64decode(data["image"])

        content_type, _ = mimetypes.guess_type(file_name)
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file_name, Body=file_content, ContentType=content_type)
        image_link = f"{S3_IMAGE_LINK}{file_name}"
        await sio.emit(data['event'], image_link,to=connected_users["admin"])



    print(connected_users["admin"])

    print(f"Message broadcasted: {data}")

