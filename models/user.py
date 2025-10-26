from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    name: str
    registered_at: float
    balance: int = 0

    @classmethod
    def create(cls, id: int, name: str, registered_at: float) -> 'User':
        return cls(
            id=id,
            name=name,
            registered_at=registered_at,
            balance=0
        )

    def to_dict(self) -> dict:
        """Convert user object to dictionary for database storage"""
        return {
            '_id': self.id,
            'name': self.name,
            'registered_at': self.registered_at,
            'balance': self.balance
        }

    @classmethod
    def from_dict(cls, data: dict) -> Optional['User']:
        """Create a User instance from dictionary data"""
        if not data:
            return None
        
        return cls(
            id=data['_id'],
            name=data['name'],
            registered_at=data['registered_at'],
            balance=data.get('balance', 0)
        )