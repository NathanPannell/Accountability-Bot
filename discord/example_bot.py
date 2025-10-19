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
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def send_welcome_message(member, ctx=None):
    """Send welcome DM to a member. If DMs are disabled, post a notice in the server.
    
    Args:
        member: The discord.Member to send the welcome message to
        ctx: Optional command context (if called from a command)
    """
    welcome_text = f"""
👋 Hey {member.name}! Welcome to the server!

I'm your personal productivity coach. I help you track your daily progress and keep you accountable.

**Try sending me a message about what you're working on right now!**

Example: "Just finished my morning workout" or "Starting work on my project"
    """.strip()
    
    try:
        await member.send(welcome_text)
        # If called from a command, acknowledge in the channel
        if ctx:
            await ctx.send(f"✅ {member.mention}, I've sent you a welcome DM!")
    except discord.Forbidden:
        # Can't DM the user; notify in a server channel
        notice = f"{member.mention}, I couldn't send you a DM. Please enable DMs from server members to receive the welcome message."
        
        # If called from a command, send the notice there
        if ctx:
            await ctx.send(notice)
        else:
            # Called from on_member_join, find an appropriate channel
            guild = member.guild
            target_channel = None
            
            # Prefer the guild's system channel if available and writable
            if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
                target_channel = guild.system_channel
            else:
                # Fallback: find the first text channel the bot can send messages in
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        target_channel = ch
                        break
            
            if target_channel:
                await target_channel.send(notice)
            else:
                # As a last resort, log to console
                print(f"Couldn't DM {member.name} and found no channel to notify them in {guild.name}.")


@bot.event
async def on_member_join(member):
    """Send welcome DM when someone joins the server."""
    await send_welcome_message(member)


@bot.command()
async def welcome(ctx):
    """Send a welcome DM to the user who invoked the command."""
    await send_welcome_message(ctx.author, ctx=ctx)

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

async def send_audio_file(ctx, audio_file_path):
    """Send an audio file to Discord channel by downloading from API."""
    try:
        # Extract filename from the path
        filename = os.path.basename(audio_file_path)
        
        # Download audio file from API
        print(f"🎵 Downloading audio file from API: {filename}")
        response = requests.get(f"{ECHO_API_URL}audio/{filename}")
        
        if response.status_code != 200:
            print(f"❌ Failed to download audio file: HTTP {response.status_code}")
            await ctx.send("📢 Audio file not available.")
            return
        
        # Save to temporary file
        temp_file_path = f"temp_{filename}"
        with open(temp_file_path, "wb") as f:
            f.write(response.content)
        
        # Send the audio file
        audio_file = discord.File(temp_file_path, filename="summary.mp3")
        await ctx.send("🎵 Here's your daily summary audio:", file=audio_file)
        print(f"✅ Audio file sent successfully: {filename}")
        
        # Clean up temporary file
        try:
            os.remove(temp_file_path)
            print(f"🧹 Cleaned up temporary file: {temp_file_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Failed to clean up temporary file: {cleanup_error}")
        
    except Exception as e:
        print(f"❌ Error sending audio file: {e}")
        await ctx.send("📢 Failed to send audio file.")
        raise

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
async def summary(ctx, persona: str = DEFAULT_PERSONA, voice: str = "alloy"):
    """
    Get your daily summary.
    Usage: !summary [persona] [voice]
    Personas: coach, mindful, drill
    Voices: alloy, echo, fable, onyx, nova, shimmer
    """
    user_id = str(ctx.author.id)
    summary_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Validate voice parameter
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if voice not in valid_voices:
        await ctx.send(f"❌ Invalid voice. Choose from: {', '.join(valid_voices)}")
        return
    
    try:
        summary_data = get_summary(user_id, summary_date, persona, voice)
        summary_content = summary_data.get("content", "No summary available")
        
        # Send text summary
        await send_bot_message(summary_content, user_id, ctx.channel)
        
        # Send audio file if available
        audio_file_path = summary_data.get("audio_file_path")
        if audio_file_path:
            try:
                print(f"🎵 Sending audio file to Discord: {audio_file_path}")
                await send_audio_file(ctx, audio_file_path)
            except Exception as e:
                print(f"❌ Failed to send audio file: {e}")
                await ctx.send("📢 Summary audio is available but couldn't be sent. Try again later.")
        else:
            print(f"ℹ️ No audio file available for user {user_id} on {summary_date}")
            await ctx.send("📝 Text summary sent. Audio version not available.")
            
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

def get_summary(user_id, date, persona=DEFAULT_PERSONA, voice="alloy"):
    """Fetch summary from the API."""
    response = requests.get(
        f'{ECHO_API_URL}summaries/{user_id}/{date}?persona={persona}&voice={voice}'
    )
    
    if response.status_code == 200:
        return response.json()  # Return full JSON response
    else:
        raise Exception(f"API returned status code {response.status_code}")

bot.run(DISCORD_TOKEN)
