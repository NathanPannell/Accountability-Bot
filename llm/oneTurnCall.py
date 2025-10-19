import os
import json
import re
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from PROMPTS import PERSONAS, ONE_TURN_CALL_TEMPLATE

load_dotenv()

def get_openai_client():
    """Get OpenAI client, raising an exception if API key is not found."""
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("❌ OPENAI_API_KEY not found in environment variables")
    return AsyncOpenAI()

client = None

async def chat(message, temperature=0.7):
    """Send a message to OpenAI and get response."""
    try:
        openai_client = get_openai_client()
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message}],
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_time_from_message(message):
    """Extract time information from user message."""
    # Common time patterns
    time_patterns = [
        r'(\d+)\s*hours?',  # "2 hours", "1 hour"
        r'(\d+)\s*hrs?',    # "2 hrs", "1 hr"
        r'(\d+)\s*minutes?', # "30 minutes", "15 minute"
        r'(\d+)\s*mins?',   # "30 mins", "15 min"
        r'(\d+)\s*h',       # "2h", "1h"
        r'(\d+)\s*m',       # "30m", "15m"
        r'(\d+)\s*:\s*(\d+)', # "2:30", "1:15"
    ]
    
    message_lower = message.lower()
    
    for pattern in time_patterns:
        match = re.search(pattern, message_lower)
        if match:
            if ':' in pattern:  # Handle HH:MM format
                hours = int(match.group(1))
                minutes = int(match.group(2))
                total_minutes = hours * 60 + minutes
                if total_minutes >= 60:
                    return f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"
                else:
                    return f"{total_minutes}m"
            else:  # Handle single number format
                number = int(match.group(1))
                if 'hour' in pattern or 'hr' in pattern or pattern.endswith('h'):
                    return f"{number}h"
                elif 'minute' in pattern or 'min' in pattern or pattern.endswith('m'):
                    return f"{number}m"
    
    return None

async def generate_one_turn_response(user_message, persona="coach", default_time="30sec"):
    """
    Generate a one-turn response based on user message and persona.
    
    Args:
        user_message (str): The user's message
        persona (str): The persona to use ("coach", "mindful", "drill")
        default_time (str): Default time period if no time is mentioned (default: "30sec")
    
    Returns:
        dict: {
            "reply": str,
            "time": str or None,
            "nextCheckIn": str
        }
    """
    try:
        # Validate persona
        if persona not in PERSONAS:
            persona = "coach"
        
        persona_config = PERSONAS[persona]
        
        # Create prompt for LLM using the template
        prompt = ONE_TURN_CALL_TEMPLATE.format(
            persona_name=persona_config["name"],
            persona_description=persona_config["description"],
            persona_tone=persona_config["tone"],
            persona_examples=persona_config["examples"],
            user_message=user_message,
            time_period=default_time,  # Pass default time to LLM to use if no time found
            default_time=default_time
        )

        # Get LLM response
        llm_response = await chat(prompt, temperature=0.8)
        
        if not llm_response:
            return {
                "reply": "Thanks for the update!",
                "time": default_time,
                "nextCheckIn": "What's next on your agenda?"
            }
        
        # Parse JSON response
        try:
            parsed_response = json.loads(llm_response.strip())
            return {
                "reply": parsed_response.get("reply", "Thanks for the update!"),
                "time": parsed_response.get("time", default_time),  # LLM now determines the time
                "nextCheckIn": parsed_response.get("nextCheckIn", "What's next on your agenda?")
            }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "reply": llm_response.strip(),
                "time": default_time,
                "nextCheckIn": "What's next on your agenda?"
            }
            
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return {
            "reply": "Thanks for the update!",
            "time": default_time,
            "nextCheckIn": "What's next on your agenda?"
        }

async def main():
    """Test the one-turn call functionality."""
    test_messages = [
        "I am driving to my mum's house which is 2 hours away.",
        "Working on coding for 30 minutes",
        "Taking a 15 minute coffee break",
        "In a meeting for the next hour",
        "Just finished lunch, feeling energized",
        "Working on my project",
        "Reading a book",
        "Cleaning my room",
        "yeah i grinded another 30 seconds so im very happy. i gotta attend the judging ceremony now, though. ill be back in an hour",
        "I've been grinding on a hackathon since past 2 hours"
    ]
    
    personas = ["drill"]
    
    for message in test_messages:
        print(f"\n📝 User message: '{message}'")
        print("=" * 50)
        
        for persona in personas:
            response = await generate_one_turn_response(message, persona)
            print(f"\n🎭 {persona.upper()} persona:")
            print(f"   Reply: {response['reply']}")
            print(f"   Time: {response['time']}")
            print(f"   Next check-in: {response['nextCheckIn']}")

if __name__ == "__main__":
    asyncio.run(main())
