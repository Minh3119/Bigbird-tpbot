import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from .interface import DatabaseInterface

class MongoDatabase(DatabaseInterface):
    def __init__(self):
        load_dotenv()
        self.client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
        self.db = self.client[os.getenv('DB_NAME', 'discord_bot')]

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data from database"""
        return await self.db.users.find_one({'_id': user_id})

    async def update_user_data(self, user_id: int, data: dict) -> Any:
        """Update user data in database"""
        return await self.db.users.update_one(
            {'_id': user_id},
            {'$set': data},
            upsert=True
        )

    async def close(self) -> None:
        """Close the database connection"""
        self.client.close()