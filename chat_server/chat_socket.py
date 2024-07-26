from fastapi import APIRouter,WebSocket
import socketio
import oauth2



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
    print(f"Message from {sid}: {data['message']}")
    await sio.emit(data['event'], data['message'],to=connected_users[data["user"]])
    print(connected_users[data["user"]])

    print(f"Message broadcasted: {data}")


@sio.event
async def user_message(sid, data):
    print(f"Message from {sid}: {data['message']}")
    await sio.emit(data['event'], data['message'],to=connected_users["admin"])
    print(connected_users["admin"])

    print(f"Message broadcasted: {data}")

