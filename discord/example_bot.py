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
API_HOST = os.getenv("API_HOST", "uvic-hackathon-api")
API_PORT = os.getenv("API_PORT", "8000")
ECHO_API_URL = f"http://{API_HOST}:{API_PORT}/"
DEFAULT_PERSONA = "drill"  # Can be "coach", "mindful", or "drill"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

def post_user_message_and_get_response(content, user_id, persona=DEFAULT_PERSONA):
    """
    Posts a user message to the API and gets the bot response.
    
    Returns:
        dict with 'entry' and 'bot_response' (if available)
    """
    entry_payload = {
        "discordId": user_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "content": content,
        "role": "user",
        "notes": None
    }
    print(f"📤 Posting user entry: {entry_payload}")

    response = requests.post(
        f"{ECHO_API_URL}entries?persona={persona}", 
        json=entry_payload
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"📥 Received response: {data}")
        return data
    else:
        print(f"❌ Error posting entry: {response.status_code}")
        return None

def post_bot_message(content, user_id):
    """Posts a bot message to the API (without expecting a bot response)."""
    entry_payload = {
        "discordId": user_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "content": content,
        "role": "bot",
        "notes": None
    }
    print(f"📤 Posting bot entry: {entry_payload}")

    try:
        response = requests.post(ECHO_API_URL + "entries", json=entry_payload)
        if response.status_code != 201:
            print(f"❌ Error posting bot message: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception posting bot message: {e}")

async def send_bot_message(message, user_id, channel):
    """Send a bot message to Discord and log it to the API."""
    post_bot_message(message, user_id)
    await channel.send(message)

def format_time_duration(seconds):
    """Convert seconds to a human-readable time format."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:  # Less than 1 hour
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return f"{minutes}m{remaining_seconds}s"
    else:  # 1 hour or more
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours}h{remaining_minutes}m"

async def schedule_followup_message(message, user_id, channel, delay_seconds):
    """Schedule a followup message to be sent after a delay."""
    formatted_time = format_time_duration(delay_seconds)
    print(f"⏰ Scheduling followup message in {formatted_time}")
    await asyncio.sleep(delay_seconds)
    await send_bot_message(message, user_id, channel)

@bot.event
async def on_ready():
    print(f'✅ We have logged in as {bot.user}')
    print(f'🎭 Default persona: {DEFAULT_PERSONA}')

@bot.event
async def on_message(message):
    # Return early if the message is from the bot
    if message.author == bot.user:
        return

    user_id = str(message.author.id)
    
    # Process commands if message starts with !
    if message.content.startswith("!"):
        await bot.process_commands(message)
    else:
        # Post user message and get bot response
        response_data = post_user_message_and_get_response(
            message.content, 
            user_id, 
            persona=DEFAULT_PERSONA
        )
        
        if response_data and response_data.get("bot_response"):
            bot_response = response_data["bot_response"]
            
            # Send immediate reply
            timeout_seconds = bot_response.get("timeout_seconds", 30)  # Default 30 seconds
            formatted_time = format_time_duration(timeout_seconds)

            initial_reply = bot_response.get("reply", "Log received!")  + f"\nI'll check back in {formatted_time}."
            await send_bot_message(initial_reply, user_id, message.channel)
            
            # Schedule followup message
            followup_message = bot_response.get("followup_message", "How did it go?")
            
            # Create background task for followup
            asyncio.create_task(
                schedule_followup_message(
                    followup_message, 
                    user_id, 
                    message.channel, 
                    timeout_seconds
                )
            )
        else:
            # Fallback if no bot response
            await send_bot_message("Log received!", user_id, message.channel)

@bot.command()
async def hello(ctx):
    """Greet the user."""
    await ctx.send(f"Hello {ctx.author.mention}! 👋")

@bot.command()
async def summary(ctx, persona: str = DEFAULT_PERSONA):
    """
    Get your daily summary.
    Usage: !summary [persona]
    Personas: coach, mindful, drill
    """
    user_id = str(ctx.author.id)
    summary_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    try:
        summary_content = get_summary(user_id, summary_date, persona)
        await send_bot_message(summary_content, user_id, ctx.channel)
    except Exception as e:
        error_msg = f"❌ Error getting summary: {str(e)}"
        print(error_msg)
        await ctx.send(error_msg)

@bot.command()
async def persona(ctx, new_persona: str = None):
    """
    Check or change the bot persona.
    Usage: !persona [coach|mindful|drill]
    """
    global DEFAULT_PERSONA
    
    valid_personas = ["coach", "mindful", "drill"]
    
    if new_persona is None:
        # Just show current persona
        await ctx.send(f"🎭 Current persona: **{DEFAULT_PERSONA}**\nAvailable: {', '.join(valid_personas)}")
    elif new_persona.lower() in valid_personas:
        # Change persona
        DEFAULT_PERSONA = new_persona.lower()
        await ctx.send(f"🎭 Persona changed to: **{DEFAULT_PERSONA}**")
    else:
        await ctx.send(f"❌ Invalid persona. Choose from: {', '.join(valid_personas)}")

def get_summary(user_id, date, persona=DEFAULT_PERSONA):
    """Fetch summary from the API."""
    response = requests.get(
        f'{ECHO_API_URL}summaries/{user_id}/{date}?persona={persona}'
    )
    
    if response.status_code == 200:
        return response.json().get("content", "No summary available")
    else:
        raise Exception(f"API returned status code {response.status_code}")

bot.run(DISCORD_TOKEN)