import traceback
from data.models import *
import services.users_service as users_service
from common import responses, authenticate
from fastapi import APIRouter, Header
from utils.regex_verifictaion_utils import *

api_users_router = APIRouter(prefix='/api/users')

@api_users_router.post('/register')
def user_register(user: UserRegisterInfo):
    """
    Register a new user.

    Args:
        user (UserRegisterInfo): The user's registration information.

    Returns:
        Created: If user is successfully registered.
        BadRequest: If username is already in use or registration data is invalid.
    """
    
    # Verify User Register data
    if not match_regex(user.username, USER_USERNAME_PATTERN):
        return responses.BadRequest(
            "Username must be at least 2 symbols and max 20, only upper and lowercase English letters and numbers.")
        
    if not match_regex(user.password, USER_PASSWORD_PATTERN):
        return responses.BadRequest(
            "Password must be at least 8 symbols and should contain capital letter, digit and a special symbol (!, +, -, *, &, ^).")
        
    if not match_regex(user.email, USER_EMAIL_PATTERN):
        return responses.BadRequest(
            "Email requires a '@' symbol and a '.' followed by at least 2 characters.")
    
    # Try to create a new User in service
    try:
        service_message = users_service.register_new_user(user)
        return responses.Created(service_message)
    
    # If duplicate keys are encountered, service will return the following error
    except users_service.UserServiceDuplicateKeyError:
        return responses.BadRequest("Username, email or phone number are already in use!")
    
    # Generic handle for all other types of error
    except:
        print(traceback.format_exc())
        return responses.InternalServerError("An issue occured while creating your account.")