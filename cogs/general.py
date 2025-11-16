from datetime import datetime
from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color

class General(commands.Cog):
    """General purpose commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping(self, interaction: Interaction):
        latency = round(self.bot.latency * 1000)  # Convert to milliseconds
        await interaction.response.send_message(f'Pong! Latency: {latency}ms')

    @app_commands.command(name="help", description="Get information about the bot.")
    async def help_command(self, interaction: Interaction):
        help_text = (
            "Hello! I'm your friendly Discord bot. Here are some commands you can use:\n"
            "/ping - Check the bot's latency.\n"
            "/help - Get information about the bot.\n"
            "More commands will be added soon!"
        )
        await interaction.response.send_message(help_text)

    #@app_commands.command(name="cooldowns", description="View cooldown status for all bot commands.")
    async def cooldowns(self, interaction: Interaction):
        """Display all command cooldowns and their remaining durations."""
        await interaction.response.defer()
    
        embed = Embed(
            title="⏰ Command Cooldowns",
            description="Here are the cooldown statuses for all commands:",
            color=Color.blue(),
            timestamp=datetime.now()
        )
        
        # Get all app commands from the bot
        commands_with_cooldowns = []
        
        for command in self.bot.tree.walk_commands():
            if isinstance(command, app_commands.Group):
                # Skip groups
                continue

            # Check if command has cooldown
            buckets = getattr(command, '_buckets', None)

            if buckets is not None:
                cooldown = getattr(buckets, '_cooldown', None)
                if cooldown:
                    rate = cooldown.rate
                    per = cooldown.per

                    # Get the bucket for this specific user
                    try:
                        bucket = buckets.get_bucket(interaction)
                        retry_after = bucket.get_retry_after()
                        
                        if retry_after and retry_after > 0:
                            # Command is on cooldown
                            minutes, seconds = divmod(int(retry_after), 60)
                            hours, minutes = divmod(minutes, 60)
                            
                            if hours > 0:
                                time_str = f"{hours}h {minutes}m {seconds}s"
                            elif minutes > 0:
                                time_str = f"{minutes}m {seconds}s"
                            else:
                                time_str = f"{seconds}s"
                            
                            commands_with_cooldowns.append({
                                'name': command.qualified_name,
                                'status': '🔴',
                                'time': time_str,
                                'on_cooldown': True
                            })
                        else:
                            # Command is available
                            commands_with_cooldowns.append({
                                'name': command.qualified_name,
                                'status': '🟢',
                                'time': f"{rate} use(s) per {int(per)}s",
                                'on_cooldown': False
                            })
                    except:
                        # If bucket doesn't exist or error occurs, command is available
                        commands_with_cooldowns.append({
                            'name': command.qualified_name,
                            'status': '🟢',
                            'time': f"{rate} use(s) per {int(per)}s",
                            'on_cooldown': False
                        })
            
        
        # Sort: cooldowns first, then available commands
        # commands_with_cooldowns.sort(key=lambda x: (not x['on_cooldown'], x['name']))
        
        if not commands_with_cooldowns:
            embed.description = "✨ No commands with cooldowns found!"
            embed.color = Color.green()
        else:
            # Add commands to embed
            on_cooldown_list = []
            available_list = []
            
            for cmd in commands_with_cooldowns:
                entry = f"{cmd['status']} **/{cmd['name']}** - `{cmd['time']}`"
                if cmd['on_cooldown']:
                    on_cooldown_list.append(entry)
                else:
                    available_list.append(entry)
            
            if on_cooldown_list:
                embed.add_field(
                    name="🔴 On Cooldown",
                    value="\n".join(on_cooldown_list),
                    inline=False
                )
                embed.color = Color.red()
            
            if available_list:
                embed.add_field(
                    name="🟢 Available",
                    value="\n".join(available_list),
                    inline=False
                )
                if not on_cooldown_list:
                    embed.color = Color.green()
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))