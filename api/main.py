from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId
import os
import sys
import re
from dotenv import load_dotenv

# Add path to import from llm directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'llm'))
from summarizer import generate_summarizer
from oneTurnCall import generate_one_turn_response

# Load environment variables
load_dotenv()

# --- MongoDB Connection ---
MONGO_CONNECTION_STRING = os.getenv("connection_string")

if not MONGO_CONNECTION_STRING:
    raise RuntimeError("MongoDB connection string not found in .env file")

client = None
db = None
users_collection = None
summaries_collection = None
entries_collection = None

try:
    client = MongoClient(MONGO_CONNECTION_STRING)
    # Test the connection
    client.admin.command('ping')
    print("Connected to MongoDB successfully!")
    
    # Set up database and collections
    db = client.main
    users_collection = db.user
    summaries_collection = db.summary
    entries_collection = db.entry
    
except ConnectionFailure as e:
    raise RuntimeError(f"Could not connect to MongoDB: {e}")
except Exception as e:
    raise RuntimeError(f"Error connecting to MongoDB: {e}")

# --- End MongoDB Connection ---


app = FastAPI()

# Pydantic models for the collections

class QuietHours(BaseModel):
    start: str  # Store as string in "HH:MM" format
    end: str

class UserId(BaseModel):
    discordId: str

class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[UserId] = Field(None, alias="_id")
    name: str
    startDate: datetime
    endDate: Optional[datetime] = None
    preferredFrequency: str
    nextUpdateTime: datetime
    quietHours: QuietHours
    
    @classmethod
    def from_mongo_dict(cls, data: dict):
        """Create User from MongoDB document"""
        # _id is already in the correct format from MongoDB
        return cls(**data)


class SummaryId(BaseModel):
    discordId: str
    date: str

class Summary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[SummaryId] = Field(None, alias="_id")
    content: str
    notes: Optional[str] = None
    
    @classmethod
    def from_mongo_dict(cls, data: dict):
        """Create Summary from MongoDB document"""
        return cls(**data)


class Entry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias="_id")
    discordId: str
    timestamp: datetime
    content: str
    notes: Optional[str] = None
    role: str  # "bot" or "user"
    
    @classmethod
    def from_mongo_dict(cls, data: dict):
        """Create Entry from MongoDB document"""
        if "_id" in data and isinstance(data["_id"], ObjectId):
            data["_id"] = str(data["_id"])
        return cls(**data)


class BotResponse(BaseModel):
    """Response from the bot for a one-turn call"""
    reply: str
    timeout_seconds: int
    followup_message: str


class EntryResponse(BaseModel):
    """Response when creating an entry"""
    entry: Entry
    bot_response: Optional[BotResponse] = None


@app.get("/health")
async def read_root():
    return {
        "status": "UP",
        "mongodb": "CONNECTED" if client is not None else "NOT CONNECTED"
    }

# --- USER Endpoints ---
@app.get("/users/{discord_id}", response_model=User)
async def get_user_by_discord_id(discord_id: str):
    """
    Retrieves a single user by their Discord ID from MongoDB.
    """
    try:
        user_data = users_collection.find_one({"_id.discordId": discord_id})
        if user_data:
            return User.from_mongo_dict(user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Discord ID format: {str(e)}")
    
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users", response_model=User, status_code=201)
async def create_user(user: User):
    """
    Accepts a user in JSON format and creates a new user in MongoDB.
    The discordId in the request body will be used as the _id.
    """
    user_dict = user.model_dump(by_alias=True, exclude_unset=True)
    
    # Ensure _id is set correctly
    if not user_dict.get("_id"):
        raise HTTPException(status_code=400, detail="discordId is required in _id")
    
    # Check if user already exists
    existing = users_collection.find_one({"_id.discordId": user_dict["_id"]["discordId"]})
    if existing:
        raise HTTPException(status_code=409, detail="User with this discordId already exists")
    
    users_collection.insert_one(user_dict)
    return user

# --- SUMMARY Endpoints ---
@app.get("/summaries/{discord_id}/{date_str}", response_model=Summary)
async def get_summary_by_discord_id_and_date(
    discord_id: str, 
    date_str: str,
    summary_length: str = "short",  # Query parameter: short, medium, long
    persona: str = "drill"  # Query parameter: coach, mindful, drill
):
    """
    Retrieves a single summary by Discord ID and date (YYYY-MM-DD) from MongoDB.
    If summary doesn't exist, fetches entries for that day and generates a new summary.
    If no entries exist for that day, returns an appropriate message.
    
    Query parameters:
    - summary_length: "short", "medium", or "long" (default: "short")
    - persona: "coach", "mindful", or "drill" (default: "mindful")
    """
    # First, check if summary already exists
    summary_data = summaries_collection.find_one({"_id.discordId": discord_id, "_id.date": date_str})
    if summary_data:
        return Summary.from_mongo_dict(summary_data)
    
    # Summary doesn't exist, fetch entries for that day
    try:
        # Parse the date string to get start and end of day
        from datetime import datetime as dt
        date_obj = dt.strptime(date_str, "%Y-%m-%d")
        start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Fetch all entries for this user on this day
        entries_cursor = entries_collection.find({
            "discordId": discord_id,
            "timestamp": {
                "$gte": start_of_day,
                "$lte": end_of_day
            }
        }).sort("timestamp", 1)  # Sort by timestamp ascending
        
        entries_list = list(entries_cursor)
        
        # If no entries exist for that day
        if not entries_list:
            summary_content = f"No entries found for {date_str}. Start journaling to get your daily summary!"
            new_summary = Summary(
                id=SummaryId(discordId=discord_id, date=date_str),
                content=summary_content,
                notes="No entries available"
            )
            summaries_collection.insert_one(new_summary.model_dump(by_alias=True, exclude_unset=True))
            return new_summary
        
        # Convert MongoDB entries to format expected by summarizer
        entries_for_summarizer = []
        for entry in entries_list:
            entries_for_summarizer.append({
                "timestamp": entry["timestamp"].isoformat(),
                "role": entry["role"],
                "content": entry["content"],
                "source": "entry"  # You can customize this based on your needs
            })
        
        # Generate summary using the summarizer
        summary_content = await generate_summarizer(
            entries_for_summarizer, 
            summary_length=summary_length,
            persona=persona
        )
        
        if not summary_content:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        # Save the generated summary to the database
        new_summary = Summary(
            id=SummaryId(discordId=discord_id, date=date_str),
            content=summary_content,
            notes=f"Generated from {len(entries_list)} entries"
        )
        
        summaries_collection.insert_one(new_summary.model_dump(by_alias=True, exclude_unset=True))
        return new_summary
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.post("/summaries", response_model=Summary, status_code=201)
async def create_summary(summary: Summary):
    """
    Accepts a summary in JSON format and creates a new summary in MongoDB.
    The _id must contain discordId and date.
    """
    summary_dict = summary.model_dump(by_alias=True, exclude_unset=True)
    
    if not summary_dict.get("_id"):
        raise HTTPException(status_code=400, detail="_id with discordId and date is required")
    
    # Check if summary already exists
    existing = summaries_collection.find_one({
        "_id.discordId": summary_dict["_id"]["discordId"],
        "_id.date": summary_dict["_id"]["date"]
    })
    if existing:
        raise HTTPException(status_code=409, detail="Summary for this user and date already exists")
    
    summaries_collection.insert_one(summary_dict)
    return summary

# --- ENTRY Endpoints ---
@app.get("/entries/{entry_id}", response_model=Entry)
async def get_entry_by_id(entry_id: str):
    """
    Retrieves a single entry by its MongoDB ObjectId from MongoDB.
    """
    try:
        entry_data = entries_collection.find_one({"_id": ObjectId(entry_id)})
        if entry_data:
            return Entry.from_mongo_dict(entry_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid entry ID format: {str(e)}")
    
    raise HTTPException(status_code=404, detail="Entry not found")

def convert_time_to_seconds(time_str: str) -> int:
    """Convert time string like '2h', '30m', '2h30m' to seconds"""
    if not time_str:
        return 900  # Default 15 minutes
    
    total_seconds = 0
    
    # Match hours
    hours_match = re.search(r'(\d+)h', time_str.lower())
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    
    # Match minutes
    minutes_match = re.search(r'(\d+)m', time_str.lower())
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    
    return total_seconds if total_seconds > 0 else 900  # Default to 15 minutes if nothing found

def get_last_n_entries(discord_id: str, n: int = 10) -> List[dict]:
    """Fetch the last N entries for a user"""
    entries_cursor = entries_collection.find({
        "discordId": discord_id
    }).sort("timestamp", -1).limit(n)
    
    return list(entries_cursor)

@app.post("/entries", response_model=EntryResponse, status_code=201)
async def create_entry(entry: Entry, persona: str = "drill"):
    """
    Accepts an entry in JSON format and creates a new entry in MongoDB.
    If the entry is from a user, generates a bot response using the last 10 entries.
    
    Query parameters:
    - persona: "coach", "mindful", or "drill" (default: "drill")
    
    Returns the created entry and bot response with:
    - reply: Initial message to send immediately
    - timeout_seconds: Time to wait before sending followup
    - followup_message: Message to send after timeout
    """
    entry_dict = entry.model_dump(by_alias=True, exclude_unset=True)
    if "_id" in entry_dict:
        del entry_dict["_id"]  # Let MongoDB generate the ID
    
    # Save the entry to MongoDB
    result = entries_collection.insert_one(entry_dict)
    entry.id = str(result.inserted_id)
    
    # Only generate bot response if this is a user entry
    bot_response = None
    if entry.role == "user":
        try:
            # Fetch the last 10 entries for this user (including the one just added)
            last_entries_cursor = entries_collection.find({
                "discordId": entry.discordId
            }).sort("timestamp", -1).limit(10)
            
            last_entries = list(last_entries_cursor)
            
            # Convert entries to format for context (optional - could be used for more advanced responses)
            # For now, we'll just use the current message for the one-turn response
            
            # Generate one-turn response
            response = await generate_one_turn_response(
                user_message=entry.content,
                persona=persona
            )
            
            if response:
                # Convert time string to seconds
                timeout_seconds = convert_time_to_seconds(response.get("time"))
                
                bot_response = BotResponse(
                    reply=response.get("reply", "Thanks for the update!"),
                    timeout_seconds=timeout_seconds,
                    followup_message=response.get("nextCheckIn", "What's next on your agenda?")
                )
        except Exception as e:
            print(f"Error generating bot response: {e}")
            # Don't fail the request if bot response generation fails
            # Just return without bot_response
    
    return EntryResponse(
        entry=entry,
        bot_response=bot_response
    )

@app.get("/users/{discord_id}/entries", response_model=List[Entry])
async def get_entries_for_user(discord_id: str):
    """
    Retrieves a list of entries filtered by Discord ID from MongoDB.
    """
    entries = []
    for doc in entries_collection.find({"discordId": discord_id}):
        entries.append(Entry.from_mongo_dict(doc))
    return entries