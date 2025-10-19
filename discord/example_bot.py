#!/usr/bin/env python3
# This example requires the 'message_content' intent.

import asyncio
import datetime
from datetime import time

import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import commands
import os
import requests

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ECHO_API_URL = "http://127.0.0.1:8000/"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

def post_user_message(content, user_id):
    entry_payload = {
        "discordId": user_id,
        "timestamp": str(datetime.datetime.now()),
        "content": content,
        "role": "user",
        "notes": None
    }
    print(entry_payload)

    requests.post(ECHO_API_URL + "entries", json=entry_payload)

def post_bot_message(content, user_id):
    entry_payload = {
        "discordId": user_id,
        "timestamp": str(datetime.datetime.now()),
        "content": content,
        "role": "bot",
        "notes": None
    }
    print(entry_payload)

    requests.post(ECHO_API_URL + "entries", json=entry_payload)

async def send_message_to_channel(message, user_id, channel, sleep_in_seconds=0):
    await asyncio.sleep(sleep_in_seconds)
    post_bot_message(message, user_id)
    await channel.send(message)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Return early if the message is from the bot
    if message.author == bot.user:
        return

    user_id = str(message.author.id)
    if message.content.startswith("!"):
        await bot.process_commands(message)
    else:
        post_user_message(message.content, user_id)

        bot_response = "Log received!"
        await send_message_to_channel(bot_response, user_id, message.channel)
        await send_message_to_channel("Timeout complete, send another message", user_id, message.channel, 10)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def summary(ctx):
    user_id = str(ctx.author.id)
    summary_date = datetime.datetime.now().strftime("%Y-%m-%d")
    summary_content = get_summary(user_id, summary_date)
    await send_message_to_channel(summary_content, str(ctx.author.id), ctx.channel)

def get_summary(user_id, date):
    return requests.get(f'{ECHO_API_URL}/summaries/{user_id}/{date}').json().get("content")

bot.run(DISCORD_TOKEN)