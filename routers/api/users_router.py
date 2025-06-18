import traceback
from data.models import *
import services.users_service as users_service
from common import responses, authenticate
from fastapi import APIRouter, Header, Query
from utils.regex_verifictaion_utils import *
from utils.user_auth_token_utils import *

api_users_router = APIRouter(prefix='/api/users')

@api_users_router.get(path="")
def get_all_users(username: str = None, page: int = 1, page_size: int = 10, u_token = Header()):
    """
    Retrieve a filtered and paginated list of users (for contact search).

    Excludes current user and their existing contacts from results.

    Args:
        username (str, optional): Username filter.
        page (int, optional): Page number. Defaults to 1.
        page_size (int, optional): Page size. Defaults to 10.
        u_token (str): User authentication token.

    Returns:
        UsersPaginationList: Paginated list of users.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    return users_service.list_users_with_total_count(username=username, page=page, page_size=page_size, current_user_id=user.id)

@api_users_router.post(path="/register")
def user_register(register_info: UserRegisterInfo):
    """
    Register a new user account.

    Args:
        register_info (UserRegisterInfo): Registration details.

    Returns:
        Success or error response depending on validation and service checks.
    """
    # Verify User Register data
    if not match_regex(register_info.username, USER_USERNAME_PATTERN):
        return responses.BadRequest(
            "Username must be at least 2 symbols and max 20, only upper and lowercase English letters and numbers.")
        
    if not match_regex(register_info.password, USER_PASSWORD_PATTERN):
        return responses.BadRequest(
            "Password must be at least 8 symbols and should contain capital letter, digit and a special symbol (!, +, -, *, &, ^).")
        
    if not match_regex(register_info.email, USER_EMAIL_PATTERN):
        return responses.BadRequest(
            "Email requires a '@' symbol and a '.' followed by at least 2 characters.")
    
    # Try to create a new User in service
    try:
        service_message = users_service.register_new_user(register_info)
        return responses.Created(service_message)
    
    # If duplicate keys are encountered, service will return the following error
    except users_service.UserService_DuplicateKeyError:
        return responses.BadRequest("Username, email or phone number are already in use!")
    
    # If entered invalid/unsupported currency code
    except users_service.UserService_InvalidCurrencyError:
        return responses.BadRequest("Received a unsupported currency code.")
    
    # Generic handle for all other types of error
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
    
@api_users_router.post(path="/login")
def user_login(login_info: UserLoginInfo):
    """
    Login into an existing user..

    Args:
        user (UserLoginInfo): The user's login information.

    Returns:
        dict: User auth token (u-token) if successful login.
        BadRequest: If login info was invalid.
        Unauthorized: If User is not verified or blocked.
    """
    # Try to login the User
    try:
        user = users_service.login_user(login_info)
        if not user: 
            return responses.NotFound("User with these credentials was not found.")
        
        # Create u-token and return
        u_token = encode_u_token(user)
        if not u_token: 
            return responses.InternalServerError()
        return UTokenResponse(u_token=u_token)
    
    # If check password returned False
    except users_service.UserService_LoginAuthError:
        return responses.BadRequest("An invalid username or password was provided.")
    
    # If User is not verified
    except users_service.UserService_UserNotVerifiedError:
        return responses.Unauthorized("User is not verified.")
    
    # If User blocked 
    except users_service.UserService_UserBlockedError:
        return responses.Unauthorized("User is blocked.")
    
    # Generic handle for all other types of error
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_users_router.get(path="/info", response_model=UserInfo, response_model_exclude={"password_hash"})
def user_info(u_token: str = Header()):
    """
    Retrieve information about the authenticated user.

    Args:
        u_token (str): User authentication token from header.

    Returns:
        User: The authenticated user's information, excluding password.
    """
    # Authenticate user
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        return users_service.get_user_info(user.username)
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_users_router.put(path="/avatar")
def change_user_avatar_url(avatar_url: UserAvatarURL, u_token: str = Header()):
    """
    Register a new user account.

    Args:
        register_info (UserRegisterInfo): Registration details.

    Returns:
        Success or error response depending on validation and service checks.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        is_updated =  users_service.change_user_avatar_url(user, avatar_url)
        if not is_updated: # not too sure about this confict response here
            return responses.Conflict("Could not update user avatar url, a conflict occurred.")
        return responses.OK("User avatar url was successfully updated.")
            
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    