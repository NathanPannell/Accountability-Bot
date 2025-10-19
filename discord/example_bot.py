#!/usr/bin/env python3
# This example requires the 'message_content' intent.

import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import commands
import os
import requests

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

def send_message_to_db(message):
    # Placeholder function to simulate sending a message to a database
    payload = {
        "user": str(message.author.id),
        "user_name": str(message.author.name),
        "timestamp": str(message.created_at),
        "content": message.content
    }
    # response = requests.post("http://your-database-endpoint", json=payload)


async def start_timer(seconds, channel):
    await asyncio.sleep(seconds)
    print("Timer finished")
    await channel.send('Please add another log entry!')

    
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
    else:
        await message.channel.send('Log received!')
        send_message_to_db(message)

        await start_timer(10, message.channel)



@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

bot.run(DISCORD_TOKEN)
