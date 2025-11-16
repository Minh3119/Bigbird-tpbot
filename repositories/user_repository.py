from typing import Optional
from models.user import User
from database.interface import DatabaseInterface

class UserRepository:
    def __init__(self, database: DatabaseInterface):
        self.db = database
        self.collection = 'users'

    async def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user from the database"""
        data = await self.db.get_user_data(user_id)
        return User.from_dict(data) if data is not None else None

    async def save_user(self, user: User) -> None:
        """Save or update a user in the database"""
        await self.db.update_user_data(user.id, user.to_dict())

    async def add_tpb(self, user: User, amount: int) -> None:
        """Add to user's TPB amount and update in database"""
        user.tpb_amount += amount
        await self.save_user(user)

    async def add_tpg(self, user: User, amount: int) -> None:
        """Add to user's TPG amount and update in database"""
        user.tpg_amount += amount
        await self.save_user(user)