from fastapi import APIRouter,WebSocket,WebSocketDisconnect,Depends,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
import oauth2
import datetime
from config.database import db



 
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
    dt_object = datetime.datetime.fromtimestamp(payload["exp"])
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

                if datetime.datetime.now() > dt_object:
                    await websocket.close()
                    del connected_users[user_id]
                    break

                data = await websocket.receive_json()
                
                for user,user_inst in connected_users.items():
                    if user==admin_id:
                        if 'message' in data:
                            await user_inst.send_json({"id":user_id,"message":data["message"]})
                            source_result=source_collection.insert_one({"sender":user_id,"receipient":admin_id,"content":data["message"],"timestamp":datetime.datetime.now(),"relation":user_id})
                            sourceid=source_result.inserted_id
                            backup_collection.insert_one({"message_id":sourceid,"sender":user_id,"receipient":admin_id,"content":data["message"],"timestamp":datetime.datetime.now(),"relation":user_id})


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
                                source_result=source_collection.insert_one({"sender":admin_id,"receipient":data["id"],"content":data["message"],"timestamp":datetime.datetime.now(),"relation":data["id"]})
                                sourceid=source_result.inserted_id
                                backup_collection.insert_one({"message_id":sourceid,"sender":admin_id,"receipient":data["id"],"content":data["message"],"timestamp":datetime.datetime.now(),"relation":data["id"]})

                            if 'typing' in data:
                                for user, user_inst in connected_users.items():
                                    if user == data["id"]:
                                        await user_inst.send_text("Admin is typing")

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
            "sender": chat["sender"],
            "content": chat["content"],
            "timestamp": chat["timestamp"]
        })
    
    for date in chat_data:
        chat_data[date] = sorted(chat_data[date], key=lambda x: x['timestamp'])
    
    return chat_data



# @router.delete_for_me("/{message_id}")