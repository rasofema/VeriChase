import math

import discord
from discord.ext import commands

from sched import scheduler
from datetime import timedelta
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from secret import TOKEN, GUILD_ID, CHANNEL_ID


intents = discord.Intents.default()
intents.members = True  # Enable member intents for DMs
intents.messages = True  # Enable message handling (for on_message event)

bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

# List to hold user paper suggestions
user_suggestions = []

# Function to send DM to each member of the channel
async def request_papers():
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    channel = discord.utils.get(guild.channels, id=CHANNEL_ID)

    if guild and channel:
        for member in channel.members:
            if not member.bot:  # Don't send DMs to other bots
                try:
                    await member.send(f"Hi {member.name}, this is a friendly reminder to send your suggestions for the reading group!")
                except discord.Forbidden:
                    print(f"Could not DM {member.name}. They might have DMs disabled.")

# Function to create a poll with collected suggestions
async def create_poll():
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    channel = discord.utils.get(guild.channels, id=CHANNEL_ID)
    global user_suggestions

    if user_suggestions and channel:
        poll_message = "**Suggestions for this week's reading group!**\n"
        poll = discord.Poll("Question", timedelta(weeks=1), multiple=True)

        for i in range(math.ceil(len(user_suggestions)/10)):
            for user, paper in user_suggestions[i*10:i*10+10]:
                poll.add_answer(text=f'"{paper}" (Suggested by {user})')
            
            await channel.send(poll_message, poll=poll)
            poll = discord.Poll("Question", timedelta(weeks=1), multiple=True)

        user_suggestions.clear()

# Function to handle DM-based paper suggestions
@bot.event
async def on_message(message):
    # Check if the message is a DM and not from a bot
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        author_name = message.author.name
        paper_name = message.content.strip()

        # Add the suggested paper to the collection
        user_suggestions.append((author_name, paper_name))
        await message.channel.send(f"Thanks {author_name}, your paper '{paper_name}' has been added!")

    # Ensure other bot commands work as well
    await bot.process_commands(message)

# Task that sends DMs and collects papers
async def weekly_paper_collection():
    # Request papers from members
    await request_papers()

# Command to start the weekly task
@bot.command
async def start_collection():
    await weekly_paper_collection()

async def scheduled_collection():
    await weekly_paper_collection()

# Bot startup event
@bot.event
async def on_ready():
    print(f'{bot.user} is here to chase you for papers for the reading group!')
    
    # Schedule the start_collection command
    scheduler.add_job(scheduled_collection, CronTrigger(second=0))
    scheduler.add_job(create_poll, CronTrigger(second=30))
    scheduler.start()

# Running the bot
bot.run(TOKEN)
