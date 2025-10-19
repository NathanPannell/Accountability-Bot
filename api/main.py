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
    start: time
    end: time
<<<<<<< HEAD
    
    def to_mongo_dict(self):
        """Convert to MongoDB-compatible dictionary"""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat()
        }
    
    @classmethod
    def from_mongo_dict(cls, data: dict):
        """Create from MongoDB dictionary"""
        if isinstance(data.get("start"), str):
            data["start"] = time.fromisoformat(data["start"])
        if isinstance(data.get("end"), str):
            data["end"] = time.fromisoformat(data["end"])
        return cls(**data)
=======
>>>>>>> ebaa844 (feat: add api scaffolding)

class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias="_id")
    name: str
    startDate: datetime
    endDate: Optional[datetime] = None
    preferredFrequency: str
    nextUpdateTime: datetime
    quietHours: QuietHours
    discordId: str
<<<<<<< HEAD
    
    def to_mongo_dict(self):
        """Convert to MongoDB-compatible dictionary"""
        data = self.model_dump(by_alias=True, exclude_unset=True)
        if "_id" in data:
            del data["_id"]
        # Convert QuietHours to serializable format
        if "quietHours" in data:
            data["quietHours"] = self.quietHours.to_mongo_dict()
        return data
    
    @classmethod
    def from_mongo_dict(cls, data: dict):
        """Create User from MongoDB document"""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        if "quietHours" in data and isinstance(data["quietHours"], dict):
            data["quietHours"] = QuietHours.from_mongo_dict(data["quietHours"])
        return cls(**data)
=======
>>>>>>> ebaa844 (feat: add api scaffolding)


class SummaryId(BaseModel):
    userId: str
    date: str

class Summary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[SummaryId] = Field(None, alias="_id")
    userId: str
    date: str
    content: str
    notes: Optional[str] = None


class Entry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias="_id")
    userId: str
    timestamp: datetime
    content: str
    notes: Optional[str] = None

<<<<<<< HEAD
@app.get("/")
async def read_root():
    return {
        "message": "Welcome to the Echo API!",
        "mongodb_connected": client is not None
    }
=======

# --- Dummy Data ---
# Using actual IDs from the example for initial dummy data
dummy_users: List[User] = [
    User(
        id="68f515d3337d475eb0753051",
        name="Alex Kim",
        startDate=datetime.fromisoformat("2025-10-01T08:00:00"),
        endDate=None,
        preferredFrequency="00:30:00",
        nextUpdateTime=datetime.fromisoformat("2025-10-19T10:30:00"),
        quietHours=QuietHours(start=time(22, 0), end=time(7, 0)),
        discordId="kim2001"
    )
]

dummy_summaries: List[Summary] = [
    Summary(
        id=SummaryId(userId="123456789012345678", date="2025-10-19"),
        userId="123456789012345678",
        date="2025-10-19",
        content="You had a productive morning focusing on backend API development and documentation. You maintained good momentum with short, healthy breaks.",
        notes=None
    )
]

dummy_entries: List[Entry] = [
    Entry(
        id="68f51b25c769f1cddfef79bf",
        userId="123456789012345678",
        timestamp=datetime.fromisoformat("2025-10-19T10:15:00Z"),
        content="Started working on the Echo backend API endpoints.",
        notes=None
    ),
    Entry(
        id="68f51b25c769f1cddfef79c0",
        userId="68f515d3337d475eb0753051", # Alex Kim's ID
        timestamp=datetime.fromisoformat("2025-10-19T11:00:00Z"),
        content="Met with team to discuss progress on discord bot.",
        notes="Good discussion."
    ),
    Entry(
        id="68f51b25c769f1cddfef79c1",
        userId="123456789012345678",
        timestamp=datetime.fromisoformat("2025-10-19T14:30:00Z"),
        content="Reviewed pull requests and provided feedback.",
        notes=None
    )
]
# --- End Dummy Data ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI MongoDB scaffolding!"}
>>>>>>> ebaa844 (feat: add api scaffolding)

# --- USER Endpoints ---
@app.get("/users", response_model=List[User])
async def get_all_users():
    """
<<<<<<< HEAD
    Retrieves a list of all users from MongoDB.
    """
    users = []
    for doc in users_collection.find():
        users.append(User.from_mongo_dict(doc))
    return users
=======
    Retrieves a list of all users.
    In a real application, this would fetch data from MongoDB's 'users' collection.
    """
    # if users_collection: return [User(**doc) for doc in users_collection.find()] # Convert to Pydantic model
    return dummy_users
>>>>>>> ebaa844 (feat: add api scaffolding)

@app.get("/users/{user_id}", response_model=User)
async def get_user_by_id(user_id: str):
    """
<<<<<<< HEAD
    Retrieves a single user by their ID from MongoDB.
    """
    try:
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User.from_mongo_dict(user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID format: {str(e)}")
    
=======
    Retrieves a single user by their ID.
    In a real application, this would fetch data from MongoDB's 'users' collection.
    """
    # if users_collection:
    #     user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    #     if user_data: return User(**user_data)
    for user in dummy_users:
        if user.id == user_id:
            return user
>>>>>>> ebaa844 (feat: add api scaffolding)
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users", response_model=User, status_code=201)
async def create_user(user: User):
    """
<<<<<<< HEAD
    Accepts a user in JSON format and creates a new user in MongoDB.
    """
    user_dict = user.to_mongo_dict()
    
    result = users_collection.insert_one(user_dict)
    user.id = str(result.inserted_id)
=======
    Accepts a user in JSON format and creates a new user.
    In a real application, this would insert the user into MongoDB's 'users' collection.
    """
    # if users_collection:
    #     # Pydantic's .dict(by_alias=True) will convert 'id' to '_id'
    #     user_dict = user.dict(by_alias=True, exclude_unset=True)
    #     # MongoDB generates _id if not provided, or uses the one provided if valid
    #     result = users_collection.insert_one(user_dict)
    #     user.id = str(result.inserted_id) # Update with the actual ID generated by MongoDB
    #     return user
    
    # For dummy data, ensure a unique ID
    new_id = f"dummy-user-id-{len(dummy_users) + 1}"
    user.id = new_id
    dummy_users.append(user)
>>>>>>> ebaa844 (feat: add api scaffolding)
    return user

# --- SUMMARY Endpoints ---
@app.get("/summaries", response_model=List[Summary])
async def get_all_summaries():
    """
<<<<<<< HEAD
    Retrieves a list of all summaries from MongoDB.
    """
    summaries = []
    for doc in summaries_collection.find():
        summaries.append(Summary(**doc))
    return summaries
=======
    Retrieves a list of all summaries.
    In a real application, this would fetch data from MongoDB's 'summaries' collection.
    """
    # if summaries_collection: return [Summary(**doc) for doc in summaries_collection.find()]
    return dummy_summaries
>>>>>>> ebaa844 (feat: add api scaffolding)

@app.get("/summaries/{user_id}/{date_str}", response_model=Summary)
async def get_summary_by_user_and_date(user_id: str, date_str: str):
    """
<<<<<<< HEAD
    Retrieves a single summary by userId and date (YYYY-MM-DD) from MongoDB.
    """
    summary_data = summaries_collection.find_one({"_id.userId": user_id, "_id.date": date_str})
    if summary_data:
        return Summary(**summary_data)
    
=======
    Retrieves a single summary by userId and date (YYYY-MM-DD).
    In a real application, this would fetch data from MongoDB's 'summaries' collection.
    """
    # if summaries_collection:
    #     summary_data = summaries_collection.find_one({"_id.userId": user_id, "_id.date": date_str})
    #     if summary_data: return Summary(**summary_data)
    for summary in dummy_summaries:
        # Check against both id.userId and id.date, or userId and date directly
        if summary.userId == user_id and summary.date == date_str:
            return summary
>>>>>>> ebaa844 (feat: add api scaffolding)
    raise HTTPException(status_code=404, detail="Summary not found")

@app.post("/summaries", response_model=Summary, status_code=201)
async def create_summary(summary: Summary):
    """
<<<<<<< HEAD
    Accepts a summary in JSON format and creates a new summary in MongoDB.
    """
    summary.id = SummaryId(userId=summary.userId, date=summary.date)
    summary_dict = summary.model_dump(by_alias=True, exclude_unset=True)
    
    # Check if summary already exists
    existing = summaries_collection.find_one({"_id.userId": summary.userId, "_id.date": summary.date})
    if existing:
        raise HTTPException(status_code=409, detail="Summary for this user and date already exists")
    
    summaries_collection.insert_one(summary_dict)
=======
    Accepts a summary in JSON format and creates a new summary.
    In a real application, this would insert the summary into MongoDB's 'summaries' collection.
    """
    # if summaries_collection:
    #     # Construct the composite _id before inserting
    #     summary.id = SummaryId(userId=summary.userId, date=summary.date)
    #     summary_dict = summary.dict(by_alias=True, exclude_unset=True)
    #     result = summaries_collection.insert_one(summary_dict)
    #     # No id update needed here as composite id is already set
    #     return summary
    
    # For dummy data, check for duplicates and set composite ID
    if any(s.userId == summary.userId and s.date == summary.date for s in dummy_summaries):
        raise HTTPException(status_code=409, detail="Summary for this user and date already exists")
    
    summary.id = SummaryId(userId=summary.userId, date=summary.date)
    dummy_summaries.append(summary)
>>>>>>> ebaa844 (feat: add api scaffolding)
    return summary

# --- ENTRY Endpoints ---
@app.get("/entries", response_model=List[Entry])
async def get_all_entries():
    """
<<<<<<< HEAD
    Retrieves a list of all entries from MongoDB.
    """
    entries = []
    for doc in entries_collection.find():
        doc["_id"] = str(doc["_id"])
        entries.append(Entry(**doc))
    return entries
=======
    Retrieves a list of all entries.
    In a real application, this would fetch data from MongoDB's 'entries' collection.
    """
    # if entries_collection: return [Entry(**doc) for doc in entries_collection.find()]
    return dummy_entries
>>>>>>> ebaa844 (feat: add api scaffolding)

@app.get("/entries/{entry_id}", response_model=Entry)
async def get_entry_by_id(entry_id: str):
    """
<<<<<<< HEAD
    Retrieves a single entry by its ID from MongoDB.
    """
    try:
        entry_data = entries_collection.find_one({"_id": ObjectId(entry_id)})
        if entry_data:
            entry_data["_id"] = str(entry_data["_id"])
            return Entry(**entry_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid entry ID format: {str(e)}")
    
=======
    Retrieves a single entry by its ID.
    In a real application, this would fetch data from MongoDB's 'entries' collection.
    """
    # if entries_collection:
    #     entry_data = entries_collection.find_one({"_id": ObjectId(entry_id)})
    #     if entry_data: return Entry(**entry_data)
    for entry in dummy_entries:
        if entry.id == entry_id:
            return entry
>>>>>>> ebaa844 (feat: add api scaffolding)
    raise HTTPException(status_code=404, detail="Entry not found")

@app.post("/entries", response_model=Entry, status_code=201)
async def create_entry(entry: Entry):
    """
<<<<<<< HEAD
    Accepts an entry in JSON format and creates a new entry in MongoDB.
    """
    entry_dict = entry.model_dump(by_alias=True, exclude_unset=True)
    if "_id" in entry_dict:
        del entry_dict["_id"]  # Let MongoDB generate the ID
    
    result = entries_collection.insert_one(entry_dict)
    entry.id = str(result.inserted_id)
=======
    Accepts an entry in JSON format and creates a new entry.
    In a real application, this would insert the entry into MongoDB's 'entries' collection.
    """
    # if entries_collection:
    #     entry_dict = entry.dict(by_alias=True, exclude_unset=True)
    #     result = entries_collection.insert_one(entry_dict)
    #     entry.id = str(result.inserted_id)
    #     return entry
    
    new_id = f"dummy-entry-id-{len(dummy_entries) + 1}"
    entry.id = new_id
    dummy_entries.append(entry)
>>>>>>> ebaa844 (feat: add api scaffolding)
    return entry

@app.get("/users/{user_id}/entries", response_model=List[Entry])
async def get_entries_for_user(user_id: str):
    """
<<<<<<< HEAD
    Retrieves a list of entries filtered by a specific user ID from MongoDB.
    """
    entries = []
    for doc in entries_collection.find({"userId": user_id}):
        doc["_id"] = str(doc["_id"])
        entries.append(Entry(**doc))
    return entries
=======
    Retrieves a list of entries filtered by a specific user ID.
    In a real application, this would fetch data from MongoDB's 'entries' collection.
    """
    # if entries_collection:
    #     return [Entry(**doc) for doc in entries_collection.find({"userId": user_id})]
    return [entry for entry in dummy_entries if entry.userId == user_id]

# To run this file:
# 1. Save it as api/main.py
# 2. Install FastAPI and Uvicorn: pip install fastapi "uvicorn[standard]"
# 3. Run from your terminal: uvicorn api.main:app --reload
# 4. Open your browser to http://127.0.0.1:8000/docs for the interactive API documentation.
>>>>>>> ebaa844 (feat: add api scaffolding)
