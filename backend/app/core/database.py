"""MongoDB Database connection manager using Motor async client."""

import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

from app.core.config import settings
from app.core.logging import logger


class DatabaseManager:
    """Manages AsyncIOMotorClient connections and collection access."""

    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.is_connected: bool = False
        self._in_memory_evaluations: dict[str, dict] = {}

    async def connect(self) -> None:
        """Establish connection pool to MongoDB."""
        try:
            logger.info("Connecting to MongoDB at %s...", settings.MONGODB_URI)
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                serverSelectionTimeoutMS=2000
            )
            self.db = self.client[settings.MONGODB_DB_NAME]
            # Verify connectivity
            await self.client.admin.command("ping")
            self.is_connected = True
            logger.info("Successfully connected to MongoDB database: %s", settings.MONGODB_DB_NAME)
        except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as e:
            self.is_connected = False
            logger.warning("MongoDB connection could not be established immediately: %s. Application will run in degraded/mock mode if needed.", e)

    async def disconnect(self) -> None:
        """Close connection pool."""
        self.is_connected = False
        if self.client:
            logger.info("Closing MongoDB connections...")
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB client disconnected.")

    async def ping(self) -> bool:
        """Check if database responds to ping command."""
        if not self.client:
            return False
        try:
            await self.client.admin.command("ping")
            self.is_connected = True
            return True
        except PyMongoError:
            self.is_connected = False
            return False

    def get_collection(self, collection_name: str):
        """Retrieve a collection instance."""
        if self.db is None:
            raise RuntimeError("Database connection has not been initialized.")
        return self.db[collection_name]

    async def save_evaluation(self, evaluation_data: dict) -> str:
        """Persist an evaluation record to MongoDB or in-memory fallback store."""
        eval_id = str(evaluation_data.get("evaluation_id") or uuid.uuid4())
        created_at = evaluation_data.get("created_at") or datetime.now(timezone.utc).isoformat()

        evaluation_data["evaluation_id"] = eval_id
        evaluation_data["created_at"] = created_at

        # Save to MongoDB if connected
        if self.is_connected and self.db is not None:
            try:
                collection = self.db["evaluations"]
                doc_to_save = dict(evaluation_data)
                result = await collection.insert_one(doc_to_save)
                evaluation_data["_id"] = str(result.inserted_id)
            except Exception as e:
                logger.warning("Failed saving evaluation to MongoDB (%s); stored in in-memory fallback.", e)
                self.is_connected = False

        # Always maintain in-memory store for instant retrieval & offline resilience
        self._in_memory_evaluations[eval_id] = evaluation_data
        return eval_id

    async def get_evaluation(self, report_id: str) -> dict | None:
        """Retrieve a stored evaluation record by its evaluation ID or ObjectId."""
        # 1. Try fetching from MongoDB if available
        if self.is_connected and self.db is not None:
            try:
                from bson import ObjectId

                collection = self.db["evaluations"]
                query: dict = {"$or": [{"evaluation_id": report_id}]}
                if ObjectId.is_valid(report_id):
                    query["$or"].append({"_id": ObjectId(report_id)})

                doc = await collection.find_one(query)
                if doc:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    if "evaluation_id" not in doc:
                        doc["evaluation_id"] = doc.get("_id", report_id)
                    return doc
            except Exception as e:
                logger.warning("Error fetching evaluation from MongoDB (%s); checking in-memory fallback.", e)

        # 2. Check in-memory fallback
        return self._in_memory_evaluations.get(report_id)


db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase | None:
    """Dependency provider for route handlers."""
    return db_manager.db
