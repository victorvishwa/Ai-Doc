from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import settings

# Create MongoDB client
client = AsyncIOMotorClient(settings.MONGODB_URI)

# Get database instance
db = client[settings.DATABASE_NAME]

# Collections
users = db.users
documents = db.documents
chat_history = db.chat_history 