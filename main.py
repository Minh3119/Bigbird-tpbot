import os
import asyncio
import argparse
import threading
import discord
import json
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from database.db import MongoDatabase
from utils.config import Config
from utils.logger import setup_logger

# Load environment variables
load_dotenv()


# --- Web server setup ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# Setup logging
logger = setup_logger()

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = False

PREFIX = os.getenv('PREFIX', 'tpb')

def get_prefix(bot, message):
    # Support both "abc help" and "abchelp"
    return commands.when_mentioned_or(PREFIX, PREFIX + ' ')(bot, message)


class Bot(commands.Bot):
    def __init__(self, sync_mode='local'):
        super().__init__(command_prefix=get_prefix, intents=intents)
        self.config = Config()
        self.db = MongoDatabase()
        self.logger = logger
        self.sync_mode = sync_mode

        # Load law questions
        with open('data/laws.json', 'r', encoding='utf-8') as f:
            self.law_questions = json.load(f)

    async def setup_hook(self):
        # Load all cogs
        try:
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        logger.info(f'Successfully loaded cog: {filename[:-3]}')
                    except Exception as e:
                        logger.error(f'Failed to load cog {filename[:-3]}: {str(e)}', exc_info=True)
        except Exception as e:
            logger.error(f'Error loading cogs: {str(e)}', exc_info=True)
            raise

        logger.info(f'Startup complete - {len(self.cogs)} cogs loaded')
        
        # Handle slash command syncing based on mode
        logger.info(f"Syncing slash commands in {self.sync_mode} mode...")
        try:
            if self.sync_mode == 'global':
                # Sync commands globally
                await self.tree.sync()
                logger.info("Synced commands globally")
            else:
                # Sync commands to specific guilds
                guild_ids = os.getenv('GUILD_IDS', '').split(',')
                guild_ids = [int(id.strip()) for id in guild_ids if id.strip()]
                
                if not guild_ids:
                    logger.warning("No guild IDs specified for command syncing")
                    return

                for guild_id in guild_ids:
                    guild = discord.Object(id=guild_id)
                    self.tree.copy_global_to(guild=guild)
                    await self.tree.sync(guild=guild)
                    logger.info(f"Synced commands to guild ID: {guild_id}")

        except Exception as e:
            logger.error(f"Failed to sync slash commands: {str(e)}", exc_info=True)

    async def on_ready(self):
        if self.user:
            logger.info(f'Bot logged in as {self.user.name} (ID: {self.user.id})')
        else:
            logger.warning('Bot user is None during on_ready event')

    async def close(self):
        logger.info('Beginning shutdown process...')
        try:
            await self.db.close()
            logger.info('Database connection closed')
        except Exception as e:
            logger.error(f'Error during database shutdown: {str(e)}', exc_info=True)
        await super().close()
        logger.info('Bot shutdown complete')

async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Discord bot with configurable command sync')
    parser.add_argument('--global-sync', action='store_true', help='Sync commands globally')
    parser.add_argument('--local-sync', action='store_true', help='Sync commands to specific guilds only')
    args = parser.parse_args()

    # Determine sync mode
    if args.global_sync and args.local_sync:
        logger.error("Cannot use both --global-sync and --local-sync at the same time")
        return
    sync_mode = 'global' if args.global_sync else 'local'

    bot = Bot(sync_mode=sync_mode)
    try:
        async with bot:
            token = os.getenv('DISCORD_TOKEN')
            if not token:
                raise ValueError("DISCORD_TOKEN environment variable is not set")
            threading.Thread(target=run_web).start()    # Start web server
            await bot.start(token)                      # Start bot
    except KeyboardInterrupt:
        logger.info("Received shutdown signal - initiating graceful shutdown...")
        await bot.close()
    except Exception as e:
        logger.error(f"Critical error occurred: {str(e)}", exc_info=True)
        raise
    finally:
        if hasattr(bot, 'db'):
            try:
                await bot.db.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")