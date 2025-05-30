from data.models import UserFromDB
from jose import jwt
import os

# Load environment variables from .env file
_JWT_ENCRYPT_KEY = os.getenv("JWT_ENCRYPT_KEY")

def encode_user_token(user: UserFromDB) -> str | None:
    """
    Encode a JWT User token from a User object.

    Args:
        user (User): The user object to encode.

    Returns:
        str: The generated JWT token as a string if successful.
        None: If the input is not a valid User object.
    """
    if not isinstance(user, UserFromDB): return None
    return jwt.encode({"id": user.id, "username": user.username}, _JWT_ENCRYPT_KEY, algorithm='HS256')

def decode_user_token(token: str) -> dict | None:
    """
    Decode a JWT User token using the encryption key.

    Args:
        token (str): The JWT token string.

    Returns:
        dict: A dictionary with user data ({"id": int, "username": str}) if decoding is successful.
        None: If decoding fails or the token is invalid.
    """
    try: return jwt.decode(token, _JWT_ENCRYPT_KEY, algorithms=['HS256'])
    except: return None