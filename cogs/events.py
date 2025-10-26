import discord
from discord.ext import commands
from discord import app_commands
from repositories.user_repository import UserRepository

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.user_repository = UserRepository(bot.db)
        self.bot.tree.on_error = self.on_app_command_error

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(int(error.retry_after), 60)
            await ctx.send(f"Please wait {minutes}m {seconds}s before using this command again!")
        elif isinstance(error, commands.MissingPermissions):
            self.logger.warning(f'Permission denied: {ctx.author} attempted to use {ctx.command}')
            await ctx.send("You don't have permission to use this command!")
        else:
            self.logger.error(f'Unhandled error in {ctx.command}: {str(error)}', exc_info=True)
            await ctx.send(f"An error occurred: {str(error)}")

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global app command error handler"""
        # Check if interaction was already responded to
        if interaction.response.is_done():
            send = interaction.followup.send
        else:
            send = interaction.response.send_message
            
        # Handle cooldown errors
        if isinstance(error, app_commands.CommandOnCooldown):
            minutes, seconds = divmod(int(error.retry_after), 60)
            hours, minutes = divmod(minutes, 60)
            
            if hours > 0:
                time_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"
            
            await send(
                f"⏰ This command is on cooldown. Try again in **{time_str}**",
                ephemeral=True
            )

        elif isinstance(error, app_commands.CheckFailure):
            await send(
                "You don't have permission to use this command!", 
                ephemeral=True
            )
        else:
            self.logger.error(f"Error in {interaction.command}: {str(error)}", exc_info=True)
            await send(
                "An error occurred while processing your command!", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Events(bot))