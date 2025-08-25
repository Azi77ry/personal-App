from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_uri = os.environ.get('MONGODB_URI')
if not mongo_uri:
    raise ValueError("No MONGODB_URI environment variable set")

client = MongoClient(mongo_uri)
db = client.money_event_manager