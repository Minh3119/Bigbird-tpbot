import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        # Bot settings
        self.owner_ids = [int(id) for id in os.getenv('OWNER_IDS', '').split(',') if id]
        
        # Cooldowns and limits
        self.command_cooldown = int(os.getenv('COMMAND_COOLDOWN', '3'))
        
    def get_status_message(self):
        """Get the bot's status message"""
        return os.getenv('STATUS_MESSAGE', 'Type !help')