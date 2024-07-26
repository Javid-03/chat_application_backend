from fastapi import FastAPI
from chat_server import chat,chat_socket
from fastapi.middleware.cors import CORSMiddleware
import socketio
from chat_server.chat_socket import socket_app



app= FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat.router)
app.include_router(chat_socket.router)


app.mount("/", socket_app)
