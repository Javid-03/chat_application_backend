
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import dotenv_values

env = dict(dotenv_values(".env"))

mongo_db_uri = env.get("MONGO_DB_URI")
print(mongo_db_uri)

uri = mongo_db_uri

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')

    print(f"Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


db = client.alacater_messenger

async def get_database():
    yield db
