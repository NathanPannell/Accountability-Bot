import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from PROMPTS import SUMMARY_TEMPLATE, PERSONAS, SUMMARY_CONFIGS

load_dotenv()

def get_openai_client():
    """Get OpenAI client, raising an exception if API key is not found."""
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("❌ OPENAI_API_KEY not found in environment variables")
    return AsyncOpenAI()

client = None

async def chat(message):
    try:
        openai_client = get_openai_client()
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def generate_summarizer(entries, summary_length="short", persona="coach"):
    try:
        entries_text = ""
        for entry in entries:
            entries_text += f"[{entry.get('timestamp', 'Unknown')}] ({entry.get('source', 'unknown')}, {entry.get('role', 'unknown')}): {entry.get('content', 'No content')}\n"
        
        persona = persona if persona in PERSONAS else "coach"
        summary_length = summary_length if summary_length in SUMMARY_CONFIGS else "short"
        
        persona_config = PERSONAS[persona]
        summary_config = SUMMARY_CONFIGS[summary_length]
        
        prompt = SUMMARY_TEMPLATE.format(
            persona_name=persona_config["name"],
            persona_description=persona_config["description"],
            persona_tone=persona_config["tone"],
            persona_examples=persona_config["examples"],
            summary_length=summary_config["length"],
            summary_goals=summary_config["goals"].format(persona_tone=persona_config["tone"]),
            summary_instruction=summary_config["instruction"],
            entries=entries_text
        )
        
        return await chat(prompt)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    # Print usage information
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("📝 Daily Summary Generator")
        print("Usage: python summarizer.py [summary_length] [persona]")
        print("\nArguments:")
        print("  summary_length: short, medium, long (default: short)")
        print("  persona: coach, mindful, drill (default: mindful)")
        print("\nExample: python summarizer.py medium coach")
        exit(0)
    
    summary_length = sys.argv[1] if len(sys.argv) > 1 else "short"
    persona = sys.argv[2] if len(sys.argv) > 2 else "mindful"
    
    async def main():
        try:
            with open("sample_entries.json", 'r') as file:
                entries = json.load(file)
            
            # Generate summary
            result = await generate_summarizer(entries, summary_length, persona)
            if result:
                print("📝 Daily Summary:")
                print(result)
            else:
                print("❌ Failed to generate summary")
        except FileNotFoundError:
            print("❌ File not found: sample_entries.json")
        except json.JSONDecodeError:
            print("❌ Invalid JSON: sample_entries.json")
    
    asyncio.run(main())