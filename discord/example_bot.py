# This example requires the 'message_content' intent.

import asyncio
import discord
from dotenv import load_dotenv
import os

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def send_message_to_db(message):
    # Placeholder function to simulate sending a message to a database
    print(f"Message sent to database: {message.content}")

async def start_timer(seconds, channel):
    await asyncio.sleep(seconds)
    print("Timer finished")
    await channel.send('Please add another log entry!')

    
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await message.channel.send('Log received!')
    send_message_to_db(message)

    await start_timer(10, message.channel)

client.run(DISCORD_TOKEN)
