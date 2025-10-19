import asyncio
import json
from summarizer import generate_summarizer
from tts import text_to_speech

async def main():
    """Simple POC that generates a summary and converts it to audio"""
    
    # Load sample entries
    try:
        with open("sample_entries.json", 'r') as file:
            entries = json.load(file)
    except FileNotFoundError:
        print("❌ sample_entries.json not found")
        return
    
    # Generate summary
    print("📝 Generating summary...")
    summary = await generate_summarizer(entries, summary_length="short", persona="mindful")
    
    if summary:
        print("📝 Summary:")
        print(summary)
        print("\n" + "="*50)
        
        # Convert to audio
        print("🎵 Converting to audio...")
        audio_file = await text_to_speech(summary, voice="alloy", user="USER")
        
        if audio_file:
            print(f"✅ Done! Audio saved to: {audio_file}")
        else:
            print("❌ Failed to generate audio")
    else:
        print("❌ Failed to generate summary")

if __name__ == "__main__":
    asyncio.run(main())
