from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from bson import ObjectId
import logging

from config import settings
from utils.database import get_database
from utils.jwt_handler import create_access_token, decode_access_token

router = APIRouter()
logger = logging.getLogger(__name__)

# ============= Models =============

class GoogleLoginRequest(BaseModel):
    credential: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# ============= Dependencies =============

async def get_current_user(authorization: str = Header(None)):
    """
    Get current user from JWT token
    """
    if not authorization:
        logger.warning("❌ No authorization header")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2:
            logger.warning(f"❌ Invalid auth header format: {authorization[:50]}")
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        scheme, token = parts
        if scheme.lower() != 'bearer':
            logger.warning(f"❌ Invalid auth scheme: {scheme}")
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        logger.info(f"🔍 Verifying token: {token[:30]}...")
        
        # Decode token
        payload = decode_access_token(token)
        if payload is None:
            logger.warning("❌ Token decode returned None")
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        logger.info(f"✅ Token decoded successfully")
        logger.info(f"📋 Payload: sub={payload.get('sub')}, email={payload.get('email')}")
        
        # Get user from database
        db = get_database()
        user_id = payload.get("sub")
        
        if not user_id:
            logger.warning("❌ No user_id in token payload")
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            logger.warning(f"❌ User not found in DB: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")
        
        logger.info(f"✅ User authenticated: {user.get('email')}")
        return user
        
    except ValueError as e:
        logger.error(f"❌ Token parse error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected auth error: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# ============= Routes =============

@router.post("/auth/google", response_model=AuthResponse)
async def google_login(request: GoogleLoginRequest):
    """
    Authenticate user with Google OAuth token
    """
    try:
        logger.info("🔐 Google login attempt started")
        
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        # Extract user info from Google
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        picture = idinfo.get('picture', None)
        
        logger.info(f"🔐 Google token verified for: {email}")
        
        # Check if user exists
        db = get_database()
        existing_user = await db.users.find_one({"google_id": google_id})
        
        if existing_user:
            # Update last login
            await db.users.update_one(
                {"_id": existing_user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            user_id = str(existing_user["_id"])
            role = existing_user.get("role", "user")
            logger.info(f"✅ Existing user logged in: {email} (role: {role})")
        else:
            # Create new user
            # Check if email is in admin list
            role = "admin" if email in settings.ADMIN_EMAILS else "user"
            
            new_user = {
                "google_id": google_id,
                "email": email,
                "name": name,
                "picture": picture,
                "role": role,
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            
            result = await db.users.insert_one(new_user)
            user_id = str(result.inserted_id)
            logger.info(f"✅ New user created: {email} (role: {role})")
        
        # Create JWT token
        token_data = {
            "sub": user_id,
            "email": email,
            "role": role
        }
        access_token = create_access_token(token_data)
        
        logger.info(f"🎫 JWT token created for: {email}")
        logger.info(f"📝 Token preview: {access_token[:30]}...")
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "role": role
            }
        )
        
    except ValueError as e:
        logger.error(f"❌ Invalid Google token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        logger.error(f"❌ Google login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/auth/verify")
async def verify_user_token(current_user: dict = Depends(get_current_user)):
    """
    Verify if the current token is valid and return user info
    """
    logger.info(f"✅ Token verification endpoint called")
    logger.info(f"✅ User verified: {current_user.get('email')}")
    
    return {
        "valid": True,
        "user": {
            "id": str(current_user.get("_id")),
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "picture": current_user.get("picture"),
            "role": current_user.get("role", "user")
        }
    }

@router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information
    """
    return {
        "id": str(current_user.get("_id")),
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "picture": current_user.get("picture"),
        "role": current_user.get("role", "user"),
        "created_at": current_user.get("created_at"),
        "last_login": current_user.get("last_login")
    }

@router.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client-side will clear the token)
    """
    logger.info(f"👋 User logged out: {current_user.get('email')}")
    return {"message": "Logged out successfully"}

async def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency: ensure the current user is an admin.
    """
    if current_user.get("role") != "admin":
        logger.warning(f"⚠️ Non-admin access attempt: {current_user.get('email')}")
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/auth/admin-check")
async def check_admin(current_user: dict = Depends(get_current_user)):
    """
    Check if current user is admin
    """
    is_admin = current_user.get("role") == "admin"
    
    if not is_admin:
        logger.warning(f"⚠️ Non-admin access attempt: {current_user.get('email')}")
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info(f"✅ Admin access granted: {current_user.get('email')}")
    return {
        "is_admin": True,
        "user": {
            "id": str(current_user.get("_id")),
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "role": current_user.get("role")
        }
    }
