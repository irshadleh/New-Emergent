"""
Database connection — configured for 50K+ user scale.

Connection pool settings:
  - maxPoolSize: 100 connections (sufficient for ~1000 concurrent requests)
  - minPoolSize: 10 (pre-warmed connections)
  - maxIdleTimeMS: 30s (release idle connections)
  - connectTimeoutMS: 5s
  - serverSelectionTimeoutMS: 5s
"""
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=100,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    connectTimeoutMS=5000,
    serverSelectionTimeoutMS=5000,
)

db = client[db_name]
