from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class DatabaseInterface(ABC):
    @abstractmethod
    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data from database"""
        pass

    @abstractmethod
    async def update_user_data(self, user_id: int, data: dict) -> Any:
        """Update user data in database"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection"""
        pass