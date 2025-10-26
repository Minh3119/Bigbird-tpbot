import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import random
import json
from repositories.user_repository import UserRepository
from models.user import User

COLOR_OPTIONS = {
    'blue': '🟦',
    'green': '🟩',
    'orange': '🟧'
}

class LawButton(discord.ui.Button):
    def __init__(self, answer: str, correct: bool):
        super().__init__(style=discord.ButtonStyle.primary, label=answer)
        self.correct = correct
        self.answer = answer

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        view = self.view
        if not isinstance(view, LawView):
            return
        if view.is_finished():
            return

        if self.correct:
            reward = random.randint(40, 60)
            await view.user_repository.add_balance(view.user, reward)
            embed = discord.Embed(
                title="✅ Correct Answer!",
                description=f"You earned {reward} TPB!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Wrong Answer!",
                description=f"The correct answer was: {view.correct_answer}",
                color=discord.Color.red()
            )

        for button in view.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True
        await interaction.edit_original_response(embed=embed, view=view)
        view.stop()

class LawView(discord.ui.View):
    def __init__(self, user_repository: UserRepository, user: User, correct_answer: str, options: list[str]):
        super().__init__(timeout=30)
        self.user_repository = user_repository
        self.user = user
        self.correct_answer = correct_answer
        self.message: discord.Message | None = None  # Initialize message attribute
        
        # Randomize options order
        random.shuffle(options)
        
        # Add buttons for each option
        for option in options:
            self.add_item(LawButton(option, option == correct_answer))

    async def on_timeout(self):
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True
        try:
            if isinstance(self.message, discord.Message):
                await self.message.edit(
                    embed=discord.Embed(
                        title="⏱️ Time's Up!",
                        description="You took too long to answer.",
                        color=discord.Color.dark_grey()
                    ),
                    view=self
                )
        except:
            pass

class Work(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.user_repository = UserRepository(bot.db)

    @app_commands.command(name="register", description="Create a new account to use the bot")
    @app_commands.checks.cooldown(1, 300)  # 5 minutes cooldown
    async def register(self, interaction: discord.Interaction):
        try:
            # Check if user already exists
            existing_user = await self.user_repository.get_user(interaction.user.id)
            if existing_user:
                await interaction.response.send_message("You already have an account!", ephemeral=True)
                return

            # Create new user
            user = User.create(
                id=interaction.user.id,
                name=str(interaction.user),
                registered_at=datetime.now().timestamp()
            )
            await self.user_repository.save_user(user)
            
            # Log successful registration
            self.logger.info(f'New user registered: {user.name} (ID: {user.id})')
            
            # Send welcome message
            embed = discord.Embed(
                title="🎉 Registration Successful!",
                description="Welcome to the bot!",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            self.logger.error(f'Error registering user {interaction.user}: {str(e)}', exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Sorry, there was an error creating your account. Please try again later.",
                    ephemeral=True
                )

    @app_commands.command(name="color", description="Guess the color and earn TPB! (cooldown: 6 minutes)")
    @app_commands.checks.cooldown(1, 360)  # 6 minutes cooldown
    async def color_slash_command(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            # Check if user is registered
            user = await self.user_repository.get_user(interaction.user.id)
            if not user:
                await interaction.response.send_message(
                    "You need to register first! Use `/register`",
                    ephemeral=True
                )
                return

            # Generate random color and create options
            correct_color = random.choice(list(COLOR_OPTIONS.keys()))
            color_emoji = COLOR_OPTIONS[correct_color]

            # Create message with options
            message = f"What is this color? {color_emoji}\n\nA. Blue\nB. Green\nC. Orange"
            await interaction.followup.send(message)

            def check(m):
                return (m.author == interaction.user and 
                       m.channel == interaction.channel and 
                       m.content.upper() in ['A', 'B', 'C'])

            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                
                # Convert answer to color
                answer_map = {'A': 'blue', 'B': 'green', 'C': 'orange'}
                user_answer = answer_map[msg.content.upper()]

                if user_answer == correct_color:
                    # Generate random reward between 10 and 20
                    reward = random.randint(10, 20)
                    await self.user_repository.add_balance(user, reward)
                    await interaction.followup.send(f"🎉 Correct! You earned {reward} TPB!")
                else:
                    await interaction.followup.send(f"❌ Sorry, that's incorrect. The color was {correct_color}.")

            except TimeoutError:
                await interaction.followup.send("Time's up! You took too long to answer.")

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.followup.send(
                    "An error occurred while playing the game. Please try again.",
                    ephemeral=True
                )

    @app_commands.command(name="law", description="Test your knowledge of the laws and earn TPB! (cooldown: 16 minutes)")
    @app_commands.checks.cooldown(1, 960)  # 16 minutes cooldown
    async def law_slash_command(self, interaction: discord.Interaction):
        try:
            # Defer response to allow time for processing
            await interaction.response.defer()

            # Check if user is registered
            user = await self.user_repository.get_user(interaction.user.id)
            if not user:
                await interaction.followup.send(
                    "You need to register first! Use `/register`",
                    ephemeral=True
                )
                return

            question = random.choice(self.bot.law_questions)
            
            # Create embed with the question
            embed = discord.Embed(
                title="📜 Law Knowledge Test",
                description=question['sentence'],
                color=discord.Color.blue()
            )
            
            # Create view with buttons
            view = LawView(
                user_repository=self.user_repository,
                user=user,
                correct_answer=question['correct'],
                options=question['options']
            )
            
            # Send the message and store it in the view for timeout handling
            await interaction.followup.send(embed=embed, view=view)
            view.message = await interaction.original_response()

        except Exception as e:
            self.logger.error(f"Error in law quiz for {interaction.user}: {str(e)}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while starting the quiz. Please try again.",
                    ephemeral=True
                )


async def setup(bot):
    await bot.add_cog(Work(bot))