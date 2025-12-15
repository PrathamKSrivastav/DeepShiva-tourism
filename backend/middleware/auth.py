from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_handler import decode_access_token
from utils.database import get_database
from typing import Optional
from bson import ObjectId  # ADD THIS IMPORT
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[dict]:
    """
    Get current user from JWT token (Optional authentication)
    Returns None if no token or invalid token (allows anonymous access)
    """
    if not credentials:
        logger.info("⚠️ No credentials provided")
        return None
    
    token = credentials.credentials
    logger.info(f"🔍 Decoding token in get_current_user...")
    
    payload = decode_access_token(token)
    if not payload:
        logger.error("❌ Token decode failed")
        return None
    
    user_id = payload.get("sub")
    email = payload.get("email")
    
    if not user_id:
        logger.error("❌ No 'sub' in token payload")
        return None
    
    logger.info(f"✅ User authenticated from token: {email} (ID: {user_id})")
    
    # Return user data directly from token payload
    # No need to query database - token already contains verified user info
    return {
        "_id": user_id,
        "id": user_id,
        "email": email,
        "name": payload.get("name"),
        "picture": payload.get("picture"),
        "email_verified": payload.get("email_verified", True)
    }



async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Require authentication (raises 401 if not authenticated)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Fetch user from database
    try:
        db = get_database()
        
        # FIX: Convert string to ObjectId before querying
        if isinstance(user_id, str):
            user_id_obj = ObjectId(user_id)
        else:
            user_id_obj = user_id
        
        user = await db.users.find_one({"_id": user_id_obj})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user["_id"] = str(user["_id"])
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def require_admin(current_user: dict = Depends(require_auth)) -> dict:
    """
    Require admin role
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user
