from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.log import get_logger
from app.core.config import settings
from app.modules.auth import auth_service, LoginRequest, RegisterRequest, Token
from app.modules.auth.dependencies import get_current_user
from app.modules.user.models import User

logger = get_logger(__name__, settings.LOG_FILE_PATH)

security = HTTPBearer()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def signup(request: RegisterRequest):
    try:
        logger.info(f"User registration attempt for email: {request.email}")

        user = await auth_service.register_user(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            password=request.password,
        )

        logger.info(f"User registered successfully: {user.username}")

        return {
            "message": "User registered successfully",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
            },
        }

    except ValueError as e:
        logger.warning(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/signin", response_model=Token)
async def signin(request: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        logger.info(f"Login attempt for: {request.username_or_email}")

        # Authenticate user
        user = await auth_service.authenticate_user(
            username_or_email=request.username_or_email, password=request.password
        )

        if not user:
            logger.warning(f"Authentication failed for: {request.username_or_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Create access token
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
        }
        access_token = auth_service.create_access_token(data=token_data)

        logger.info(f"User logged in successfully: {user.username}")

        return Token(access_token=access_token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/signout")
async def signout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Sign out user (client should delete token)"""
    try:
        # Decode token to verify it's valid
        token = credentials.credentials
        payload = auth_service.decode_access_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        logger.info(f"User signed out: {payload.get('username', 'unknown')}")

        return {
            "message": "Signed out successfully",
            "detail": "Please delete the token from client storage",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during signout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "preferences": current_user.preferences,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat(),
        "updated_at": current_user.updated_at.isoformat(),
    }
