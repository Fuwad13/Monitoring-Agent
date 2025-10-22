"""
User service layer for business logic and database operations.
Follows best practices with separation of concerns.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import EmailStr

from app.modules.user.models import User


class UserService:
    """Service class for user-related business logic"""

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return await User.get(user_id)
        except Exception:
            return None

    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        """Get user by email"""
        return await User.find_one({"email": email, "is_active": True})

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await User.find_one({"username": username, "is_active": True})

    async def update_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> Optional[User]:
        """Update user preferences"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update preferences
        current_preferences = user.preferences or {}
        current_preferences.update(preferences)

        # Update user
        user.preferences = current_preferences
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

        return user

    async def update_user_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        email: Optional[EmailStr] = None,
    ) -> Optional[User]:
        """Update user profile information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Check if email is already taken by another user
        if email and email != user.email:
            existing_user = await User.find_one(
                {"email": email, "_id": {"$ne": user.id}}
            )
            if existing_user:
                raise ValueError("Email already registered")

        # Update fields
        if full_name:
            user.full_name = full_name
        if email:
            user.email = email

        user.updated_at = datetime.now(timezone.utc)
        await user.save()

        return user

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

        return True

    async def activate_user(self, user_id: str) -> bool:
        """Activate user account"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        await user.save()

        return True


# Global service instance
user_service = UserService()
