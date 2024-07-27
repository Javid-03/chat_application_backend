from fastapi import APIRouter,WebSocket,WebSocketDisconnect,Depends,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
import oauth2
from datetime import timedelta,datetime
from config.database import db
from bson import ObjectId
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




 
source_collection= db.chat_history         #user
backup_collection=db.chat_history_backup   #admin

router=APIRouter()

connected_users = {}

active_users = {}
auth_scheme = HTTPBearer()


admin_id="javidrahman999@gmail.com"



@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.headers.get('Authorization')
    token = token[len("Bearer "):]
    payload = oauth2.verify_customer_access_token(token)
    print(payload["email"])
    print(payload["exp"])
    dt_object = datetime.fromtimestamp(payload["exp"])
    print(dt_object)
    if payload and payload["email"] not in connected_users :
        await websocket.accept()
    else:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f"Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    user_id=payload["email"]
    
    if user_id!=admin_id:
        connected_users[user_id] = websocket
    else:
        connected_users[admin_id] = websocket

    print(connected_users)
    
    if user_id!=admin_id:
        try:
            while True:

                if datetime.now() > dt_object:
                    await websocket.close()
                    del connected_users[user_id]
                    break

                data = await websocket.receive_json()
                
                for user,user_inst in connected_users.items():
                    if user==admin_id:
                        if 'message' in data:
                            await user_inst.send_json({"id":user_id,"message":data["message"]})
                            source_result=source_collection.insert_one({"sender":user_id,"receipient":admin_id,"content":data["message"],"timestamp":datetime.now(),"relation":user_id})
                            sourceid=source_result.inserted_id
                            backup_collection.insert_one({"message_id":sourceid,"sender":user_id,"receipient":admin_id,"content":data["message"],"timestamp":datetime.now(),"relation":user_id})

                        if 'image' and 'file_name' in data:
                            file_name = data["file_name"]
                            print(file_name)
                            file_content = base64.b64decode(data["image"])
                            print(file_content)

                            content_type, _ = mimetypes.guess_type(file_name)
                            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file_name, Body=file_content, ContentType=content_type)
                            image_link = f"{S3_IMAGE_LINK}{file_name}"
                            print(image_link)
                            await user_inst.send_json({"image":image_link})

                        if 'typing' in data:
                            for user, user_inst in connected_users.items():
                                if user == admin_id:
                                    await user_inst.send_text(f"{user_id} typing...")

                if "ping" in data:
                        if user_id in connected_users:
                            send_inst=connected_users[admin_id]
                            await send_inst.send_text(f"{user_id} is online")
                    
                    

                
        except WebSocketDisconnect:
            del connected_users[user_id]
            await websocket.close()
    else:
        try:
            while True:
                data = await websocket.receive_json()
                for user,user_inst in connected_users.items():
                    if "id" in data:
                        if user== data["id"]:
                            if "message" in data:
                                await user_inst.send_json({"message":data["message"]})
                                source_result=source_collection.insert_one({"sender":admin_id,"receipient":data["id"],"content":data["message"],"timestamp":datetime.now(),"relation":data["id"]})
                                sourceid=source_result.inserted_id
                                backup_collection.insert_one({"message_id":sourceid,"sender":admin_id,"receipient":data["id"],"content":data["message"],"timestamp":datetime.now(),"relation":data["id"]})

                            if 'typing' in data:
                                for user, user_inst in connected_users.items():
                                    if user == data["id"]:
                                        await user_inst.send_text("Admin is typing")

                            if 'image' and 'file_name' in data:
                                file_name = data["file_name"]
                                file_content = base64.b64decode(data["image"])

                                content_type, _ = mimetypes.guess_type(file_name)
                                s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file_name, Body=file_content, ContentType=content_type)
                                image_link = f"{S3_IMAGE_LINK}{file_name}"
                                print(image_link)
                                await user_inst.send_json({"image":image_link})

                            if "ping" in data:
                                if admin_id in connected_users:
                                    await user_inst.send_text(f"Admin is online")
                                    

                if "disconnect" in data:
                    target_user_email = data["disconnect"]
                    if target_user_email in connected_users: 
                        target_ws = connected_users[target_user_email]
                        del connected_users[target_user_email]
                        await target_ws.close() 
        except WebSocketDisconnect:
            del connected_users[user_id]
            await websocket.close()



@router.get("/{user_id}")
def chat_history(user_id:str):
    chat=[]
    data=source_collection.find({"relation":user_id})
    for i in data:
        chat.append(i)
    sorted_timestamp = sorted(chat, key=lambda x: x['timestamp'])
    print(sorted_timestamp)
    
    sorted_chat=[]

    for i in sorted_timestamp:
        sorted_chat.append({"sender":i["sender"],"content":i["content"]})

    return sorted_chat


@router.get("/chat_user/{user_id}")
async def chat_history_user(user_id: str):
    chat_data = {}
    
    data = source_collection.find({"relation": user_id})
    
    for chat in data:
        date = chat['timestamp'].date()  
        
        date_str = date.strftime('%Y-%m-%d') 
        
        if date_str not in chat_data:
            chat_data[date_str] = []
        
        chat_data[date_str].append({
            "id":str(chat["_id"]),
            "sender": chat["sender"],
            "content": chat["content"],
            "timestamp": chat["timestamp"]
        })
    
    for date in chat_data:
        chat_data[date] = sorted(chat_data[date], key=lambda x: x['timestamp'])
    
    return chat_data


@router.get("/chat_admin/{user_id}")
async def chat_history_admin(user_id: str):
    chat_data = {}
    
    data = backup_collection.find({"relation": user_id})
    
    for chat in data:
        date = chat['timestamp'].date()  
        
        date_str = date.strftime('%Y-%m-%d') 
        
        if date_str not in chat_data:
            chat_data[date_str] = []
        
        chat_data[date_str].append({
            "id":str(chat["_id"]),
            "message_id":str(chat["message_id"]),
            "sender": chat["sender"],
            "content": chat["content"],
            "timestamp": chat["timestamp"]
        })
    
    for date in chat_data:
        chat_data[date] = sorted(chat_data[date], key=lambda x: x['timestamp'])
    
    return chat_data



@router.delete("/delete_for_me/{message_id}")
async def delete_for_me_user(message_id:str):
    id=ObjectId(message_id)
    delete_for_me=source_collection.delete_one({"_id":id})
    
    if delete_for_me.deleted_count==1:
        return "Deleted"
    else:
        return "Not deleted"



@router.delete("/delete_for_everyone/{message_id}")
async def delete_for_everyone_user(message_id:str):
    id=ObjectId(message_id)
    message_data=source_collection.find_one({"_id":id})
    if message_data:
        if message_data["timestamp"]+timedelta(minutes=1)>=datetime.now():
            user=source_collection.delete_one({"_id":id})
            admin=backup_collection.delete_one({"message_id":id})
            if user.deleted_count==1 or admin.deleted_count==1:
                return "deleted"
            else:
                return "Not deleted"
        else:
            return "cannot delete: time exceeded"
    else:
        return "Data not found"
    

@router.delete("/delete_for_me_admin/{message_id}")
async def delete_for_me_admin(message_id:str):
    id=ObjectId(message_id)
    delete_for_me=backup_collection.delete_one({"_id":id})
    
    if delete_for_me.deleted_count==1:
        return "Deleted"
    else:
        return "Not deleted"
    
@router.delete("/delete_for_everyone_admin/{message_id}")
async def delete_for_everyone_admin(message_id:str):
    id=ObjectId(message_id)
    message_data=backup_collection.find_one({"message_id":id})
    if message_data:
        user=source_collection.delete_one({"_id":id})
        admin=backup_collection.delete_one({"message_id":id})
        if user.deleted_count==1 or admin.deleted_count==1:
            return "deleted"
        else:
            return "Not deleted"
    else:
        return "Data not found"