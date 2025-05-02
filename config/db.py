import mongoengine
from dotenv import load_dotenv
import os

load_dotenv()

def connect_db():
    try:
        mongoengine.connect(
            db=os.getenv("MONGO_DB_NAME"),
            host=os.getenv("MONGO_URI"),
            uuidRepresentation='standard'
        )
        print("DB connected")
    except Exception as e:
        print("Error connecting to DB:", e)
