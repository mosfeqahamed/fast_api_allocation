# config.py

from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Load the environment variables from the .env file
load_dotenv()

# Fetch the local MongoDB URI from the environment variable
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

# Create an async MongoDB client using Motor
client = AsyncIOMotorClient(MONGODB_URI)

# Access the database
db = client.vehicle_allocation 
