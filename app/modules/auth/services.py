from datetime import datetime, timedelta, timezone

import jwt
from pydantic import EmailStr
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.config import settings
from app.modules.user.models import User
from app.core.log import get_logger

logger = get_logger(__name__, settings.LOG_FILE_PATH)


class AuthService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM

    def hash_password(self, password: str) -> str:
        """Hash password using werkzeug"""
        return generate_password_hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password using werkzeug"""
        return check_password_hash(hashed_password, plain_password)

    async def authenticate_user(
        self, username_or_email: str, password: str
    ) -> User | None:
        """Authenticate user by username/email and password"""
        user = await User.find_one(
            {
                "$or": [{"email": username_or_email}, {"username": username_or_email}],
                "is_active": True,
            }
        )

        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> dict | None:
        """Decode JWT access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError:
            logger.warning("Invalid token")
            return None

    async def register_user(
        self, username: str, email: EmailStr, full_name: str, password: str
    ) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = await User.find_one(
            {"$or": [{"email": email}, {"username": username}]}
        )
        if existing_user:
            if existing_user.email == email:
                raise ValueError("Email already registered")
            if existing_user.username == username:
                raise ValueError("Username already taken")

        # Hash password and create user
        password_hash = self.hash_password(password)
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            is_active=True,
        )
        await user.insert()
        return user

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID"""
        try:
            return await User.get(user_id)
        except Exception:
            return None

    async def get_user_by_email(self, email: EmailStr) -> User | None:
        """Get user by email"""
        return await User.find_one({"email": email, "is_active": True})

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username"""
        return await User.find_one({"username": username, "is_active": True})

    async def update_user_preferences(
        self, user_id: str, preferences: dict
    ) -> User | None:
        """Update user preferences"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update preferences
        current_preferences = user.preferences or {}
        current_preferences.update(preferences)
        user.preferences = current_preferences
        user.updated_at = datetime.now(timezone.utc)
        await user.save()
        return user

    async def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        if not self.verify_password(old_password, user.password_hash):
            return False

        user.password_hash = self.hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await user.save()
        return True


auth_service = AuthService()
