from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId
import os
from dotenv import load_dotenv

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


@app.get("/")
async def read_root():
    return {
        "message": "Welcome to the Echo API!",
        "mongodb_connected": client is not None
    }

# --- USER Endpoints ---
@app.get("/users", response_model=List[User])
async def get_all_users():
    """
    Retrieves a list of all users from MongoDB.
    """
    users = []
    for doc in users_collection.find():
        users.append(User.from_mongo_dict(doc))
    return users

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
@app.get("/summaries", response_model=List[Summary])
async def get_all_summaries():
    """
    Retrieves a list of all summaries from MongoDB.
    """
    summaries = []
    for doc in summaries_collection.find():
        summaries.append(Summary.from_mongo_dict(doc))
    return summaries

@app.get("/summaries/{discord_id}/{date_str}", response_model=Summary)
async def get_summary_by_discord_id_and_date(discord_id: str, date_str: str):
    """
    Retrieves a single summary by Discord ID and date (YYYY-MM-DD) from MongoDB.
    """
    summary_data = summaries_collection.find_one({"_id.discordId": discord_id, "_id.date": date_str})
    if summary_data:
        return Summary.from_mongo_dict(summary_data)
    
    raise HTTPException(status_code=404, detail="Summary not found")

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
@app.get("/entries", response_model=List[Entry])
async def get_all_entries():
    """
    Retrieves a list of all entries from MongoDB.
    """
    entries = []
    for doc in entries_collection.find():
        entries.append(Entry.from_mongo_dict(doc))
    return entries

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

@app.post("/entries", response_model=Entry, status_code=201)
async def create_entry(entry: Entry):
    """
    Accepts an entry in JSON format and creates a new entry in MongoDB.
    MongoDB will auto-generate the _id.
    """
    entry_dict = entry.model_dump(by_alias=True, exclude_unset=True)
    if "_id" in entry_dict:
        del entry_dict["_id"]  # Let MongoDB generate the ID
    
    result = entries_collection.insert_one(entry_dict)
    entry.id = str(result.inserted_id)
    return entry

@app.get("/users/{discord_id}/entries", response_model=List[Entry])
async def get_entries_for_user(discord_id: str):
    """
    Retrieves a list of entries filtered by Discord ID from MongoDB.
    """
    entries = []
    for doc in entries_collection.find({"discordId": discord_id}):
        entries.append(Entry.from_mongo_dict(doc))
    return entries