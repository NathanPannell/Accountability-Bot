import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

def get_openai_client():
    """Get OpenAI client, raising an exception if API key is not found."""
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("❌ OPENAI_API_KEY not found in environment variables")
    return AsyncOpenAI()

openai_client = None

def generate_filename(user="USER", custom_hash=None):
    """
    Generate filename in format: USER_DAY_HASH.mp3
    
    Args:
        user (str): Username (default: "USER")
        custom_hash (str): Custom hash, if None will generate from current date
    
    Returns:
        str: Formatted filename
    """
    if custom_hash is None:
        # Generate hash from current date
        today = datetime.now().strftime("%Y-%m-%d")
        custom_hash = hashlib.md5(today.encode()).hexdigest()[:8]
    
    return f"{user}_{datetime.now().strftime('%Y%m%d')}_{custom_hash}.mp3"

async def text_to_speech(text, voice="alloy", user="USER", custom_hash=None):
    """
    Convert text to speech using OpenAI's TTS API
    
    Args:
        text (str): The text to convert to speech
        voice (str): Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        user (str): Username for filename (default: "USER")
        custom_hash (str): Custom hash for filename, if None will generate from date
    
    Returns:
        str: Path to the generated audio file, or None if failed
    """
    try:
        # Generate filename and ensure audio directory exists
        filename = generate_filename(user, custom_hash)
        audio_dir = "audio"
        os.makedirs(audio_dir, exist_ok=True)
        output_file = os.path.join(audio_dir, filename)
        
        client = get_openai_client()
        response = await client.audio.speech.create(
            model="tts-1", # tts-1-hd, 
            voice=voice, # alloy, echo, fable, onyx, nova, shimmer
            input=text
        )
        
        # Save the audio file
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        print(f"🎵 Audio saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return None
if __name__ == "__main__":
    import asyncio
    import sys
    
    # Print usage information
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("🎵 Text-to-Speech Generator")
        print("Usage: python tts.py [voice] [user] [custom_hash]")
        print("\nArguments:")
        print("  voice: alloy, echo, fable, onyx, nova, shimmer (default: alloy)")
        print("  user: Username for filename (default: USER)")
        print("  custom_hash: Custom hash for filename (default: auto-generated)")
        print("\nExample: python tts.py nova john abc123")
        print("Output: audio/USER_20241225_abc123.mp3")
        print("\nNote: Text will be read from stdin")
        exit(0)
    
    voice = sys.argv[1] if len(sys.argv) > 1 else "alloy"
    user = sys.argv[2] if len(sys.argv) > 2 else "USER"
    custom_hash = sys.argv[3] if len(sys.argv) > 3 else None
    
    async def main():
        print("📝 Enter text to convert to speech (press Ctrl+D when done):")
        try:
            text = input()
            if text.strip():
                print("🎵 Generating audio...")
                audio_file = await text_to_speech(text, voice=voice, user=user, custom_hash=custom_hash)
                if audio_file:
                    print(f"✅ Audio generated successfully: {audio_file}")
                else:
                    print("❌ Failed to generate audio")
            else:
                print("❌ No text provided")
        except EOFError:
            print("❌ No text provided")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
    
    asyncio.run(main())

