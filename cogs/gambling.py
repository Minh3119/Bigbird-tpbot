import json
import random
from typing import Literal
import discord
from discord.ext import commands
from discord import app_commands

from repositories.user_repository import UserRepository


class GamblingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.user_repository = UserRepository(bot.db)

        # Load outcome messages
        with open('data/hilo_outcomes.json', 'r', encoding='utf-8') as f:
            self.hilo_outcomes = json.load(f)
        
        with open('data/twoup_outcomes.json', 'r', encoding='utf-8') as f:
            self.twoup_outcomes = json.load(f)
    
    @app_commands.command(name='hilo', description='Play hi-lo / tài xỉu')
    async def hi_lo(self, interaction: discord.Interaction, guess:Literal["high","low"], bet_amount: int, currency: Literal["tpb", "tpg"]):
        await interaction.response.defer()

        # Check if user is registered
        user = await self.user_repository.get_user(interaction.user.id)
        if not user:
            await interaction.followup.send(
                "You need to register first! Use `/register`",
                ephemeral=True
            )
            return

        # Ensure user has the chosen currency amount
        currency_amount = user.tpb_amount if currency == "tpb" else user.tpg_amount

        # Validate bet amount
        if bet_amount <= 0:
            await interaction.followup.send("Your bet must be greater than 0.", ephemeral=True)
            return
        if bet_amount > currency_amount:
            await interaction.followup.send(f"You don't have enough {currency.upper()} to make that bet.", ephemeral=True)
            return

        # Roll 3 dice
        dice = [random.randint(1, 6) for _ in range(3)]
        total = sum(dice)
        result = "low" if total <= 10 else "high"

        # Win or lose
        win = False
        outcome = random.choice(self.hilo_outcomes['incorrect'])
        if (total == 3):
            result = "🥀 triple ones 🥀"
            outcome = random.choice(self.hilo_outcomes['triple_ones'])
            win = False
        elif (total == 18):
            result = "💥 triple sixes 💥"
            outcome = random.choice(self.hilo_outcomes['triple_sixes'])
            win = False
        elif (guess == result):
            outcome = random.choice(self.hilo_outcomes['correct'])
            win = True

        if win:
            winnings = bet_amount
            tax = int(winnings * 0.1)  # Calculate 10% tax
            net_winnings = winnings - tax

            if currency == "tpb":
                user.tpb_amount += net_winnings
            else:
                user.tpg_amount += net_winnings

            # Transfer tax to bot's account
            bot_user = await self.user_repository.get_user(self.bot.user.id)
            if bot_user:
                if currency == "tpb":
                    bot_user.tpb_amount += tax
                else:
                    bot_user.tpg_amount += tax
                await self.user_repository.save_user(bot_user)
        else:
            if currency == "tpb":
                user.tpb_amount -= bet_amount
            else:
                user.tpg_amount -= bet_amount

        await self.user_repository.save_user(user)

        # Create a more polished response with an embed
        embed = discord.Embed(
            title=result.upper(),
            color=discord.Color.green() if win else discord.Color.red()
        )

        # Show individual dice
        embed.add_field(
            name="Dice Rolls",
            value=f"🎲 {dice[0]} 🎲 {dice[1]} 🎲 {dice[2]}",
            inline=True
        )

        # Show result and guess
        embed.add_field(name="Total", value=str(total), inline=True)
        embed.add_field(name="Result", value=outcome, inline=True)

        # Footer
        embed.set_footer(text="hi-lo / tài xỉu game 🎲")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name='two-up', description='Play two-up / chẵn lẻ')
    async def two_up(self, interaction: discord.Interaction, guess:Literal["two heads","two tails"], bet_amount: int, currency: Literal["tpb", "tpg"]):
        await interaction.response.defer()

        # Check if user is registered
        user = await self.user_repository.get_user(interaction.user.id)
        if not user:
            await interaction.followup.send(
                "You need to register first! Use `/register`",
                ephemeral=True
            )
            return
        
        # Ensure user has the chosen currency amount
        currency_amount = user.tpb_amount if currency == "tpb" else user.tpg_amount

        # Validate bet amount
        if bet_amount <= 0:
            await interaction.followup.send("Your bet must be greater than 0.", ephemeral=True)
            return
        if bet_amount > currency_amount:
            await interaction.followup.send(f"You don't have enough {currency.upper()} to make that bet.", ephemeral=True)
            return
        
         # Flip 3 coins
        coins = [random.choice(["Heads", "Tails"]) for _ in range(3)]
        heads = coins.count("Heads")
        tails = coins.count("Tails")

        # Determine outcome
        outcome = ""
        result = None  # "win", "lose", or "neutral"

        if heads == 3 or tails == 3:
            outcome = random.choice(self.twoup_outcomes['neutral'])
            result = "neutral"
        elif (guess == "two heads" and heads == 2) or (guess == "two tails" and tails == 2):
            outcome = random.choice(self.twoup_outcomes['win'])
            result = "win"
            winnings = bet_amount
            tax = int(winnings * 0.1)  # Calculate 10% tax
            net_winnings = winnings - tax

            if currency == "tpb":
                user.tpb_amount += net_winnings
            else:
                user.tpg_amount += net_winnings

            # Transfer tax to bot's account
            bot_user = await self.user_repository.get_user(self.bot.user.id)
            if bot_user:
                if currency == "tpb":
                    bot_user.tpb_amount += tax
                else:
                    bot_user.tpg_amount += tax
                await self.user_repository.save_user(bot_user)
        else:
            outcome = random.choice(self.twoup_outcomes['lose'])
            result = "lose"
            if currency == "tpb":
                user.tpb_amount -= bet_amount
            else:
                user.tpg_amount -= bet_amount

        # Build the embed
        embed = discord.Embed(
            title=result.upper(),
            color=discord.Color.green() if result == "win" else discord.Color.red() if result == "lose" else discord.Color.gold()
        )
        embed.add_field(name="Coin Toss", value=" | ".join(coins), inline=True)

        embed.add_field(name="Outcome", value=outcome, inline=False)
        embed.set_footer(text="two-up / chẵn lẻ game 🪙")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GamblingCog(bot))