from services.users_service import is_user_authenticated, find_user_by_token
from fastapi import HTTPException, Request
from data.models import UserFromDB

def get_user_or_raise_401(u_token: str) -> UserFromDB:
    """Get UserFromDB object from u_token string or raise 401 Unauthorized."""
    if not is_user_authenticated(u_token):
        raise HTTPException(status_code=401, detail="Expired or invalid u-token.")

    return find_user_by_token(u_token)

def get_user_if_token(request: Request) -> UserFromDB | None:
    """Get UserFromDB object from Request cookies or None."""
    token = request.cookies.get('u-token')
    return find_user_by_token(token)