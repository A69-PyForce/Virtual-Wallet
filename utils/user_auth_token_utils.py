from datetime import datetime, timedelta, timezone
from config.env_loader import JWT_ENCRYPT_KEY
from jose import ExpiredSignatureError, jwt
from data.models import UserTokenInfo
from jose import jwt
import traceback
import os

def encode_u_token(user: UserTokenInfo, expires_in_minutes: int = 10) -> str | None:
    """
    Encode a JWT User token from a UserTokenInfo object with a default expiration time of 10 minutes.

    Args:
        user (UserTokenInfo): The UserTokenInfo object to encode the token with.
        expires_in_minutes (int): Time in minutes from now when the token will expire.

    Returns:
        str|None: The generated JWT token as a string if successful or None if operation failed.
    """
    try:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        payload = {
            "id": user.id,
            "username": user.username,
            "exp": int(expire.timestamp())
        }
        return jwt.encode(payload, JWT_ENCRYPT_KEY)
    
    except Exception:
        print(traceback.format_exc())
        return None

def decode_u_token(u_token: str) -> dict | None:
    """
    Decode a JWT User token using the encryption key.

    Args:
        token (str): The JWT token string.

    Returns:
        dict|None: A dictionary with user data and token expiration date ({"id": int, "username": str, "exp": int}) \n
        or None if the u_token has expired or decoding fails (will print the traceback).
    """
    try:
        return jwt.decode(u_token, JWT_ENCRYPT_KEY)
    
    except ExpiredSignatureError:
        return None
    
    except AttributeError:
        return None
        
    except Exception:
        print(traceback.format_exc())
        return None