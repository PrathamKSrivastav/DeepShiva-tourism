from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from config import settings
import logging

logger = logging.getLogger(__name__)

def create_access_token(data: dict) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode and verify JWT token
    Returns payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding JWT: {str(e)}")
        return None

def verify_token(token: str) -> bool:
    """
    Verify if token is valid
    """
    payload = decode_access_token(token)
    return payload is not None
