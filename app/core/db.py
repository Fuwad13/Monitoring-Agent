"""
Database connection and initialization for the monitoring agent.
"""

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.modules.user.models import User


class Database:
    """Database connection manager"""

    def __init__(self):
        self.client: AsyncMongoClient = None
        self.database = None

    async def connect(self):
        """Connect to MongoDB and initialize Beanie"""
        try:
            # Create Motor client with SSL/TLS options
            self.client = AsyncMongoClient(settings.MONGODB_URI)

            # Test connection with a simple ping
            await self.client.admin.command("ping")
            print("Ping successful. Connected to MongoDB.")

            # Get database
            self.database = self.client.monitoring_agent

            # Initialize Beanie with User model
            await init_beanie(database=self.database, document_models=[User])

            print("✅ Database connected successfully!")

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            # Don't raise the exception - let the app start without DB
            self.client = None
            self.database = None

    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔌 Database disconnected")

    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.client is not None and self.database is not None

    async def health_check(self) -> dict:
        """Check database health"""
        if not self.is_connected():
            return {"status": "disconnected", "error": "No database connection"}

        try:
            await self.client.admin.command("ping")
            return {"status": "healthy", "database": "monitoring_agent"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global database instance
database = Database()
