import json
import traceback
from fastapi.responses import RedirectResponse
from data.models import *
from utils.user_auth_token_utils import *
from utils.regex_verifictaion_utils import *
import services.users_service as users_service
from common import responses, authenticate, template_config
from fastapi import APIRouter, Request, Form, File, UploadFile

# Load currencies from cache file
with open('currencies_cache.json', 'r') as f:
    currencies = json.load(f)

web_users_router = APIRouter(prefix='/users')
templates = template_config.CustomJinja2Templates(directory='templates')

# ====================================================== REGISTER ENDPOINTS ======================================================

@web_users_router.get('/register')
def serve_register(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"currencies": currencies})

@web_users_router.post(path="/register")
def user_register(request: Request, username: str = Form(...),
                  email: str = Form(...), password: str = Form(...),
                  phone_number: str = Form(...), currency_code: str = Form(...)):
    
    try:
        
        # Verify User Register data
        if not match_regex(username, USER_USERNAME_PATTERN):
            return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                "Username must be at least 2 symbols and max 20, only upper and lowercase English letters and numbers.",
                "currencies": currencies})
            
        if not match_regex(password, USER_PASSWORD_PATTERN):
            return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                "Password must be at least 8 symbols and should contain capital letter, digit and a special symbol (!, +, -, *, &, ^).",
                "currencies": currencies})
            
        if not match_regex(email, USER_EMAIL_PATTERN):
            return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                "Email requires a '@' symbol and a '.' followed by at least 2 characters.", "currencies": currencies})
            
        # Create register info basemodel and call service
        register_info = UserRegisterInfo(username=username, email=email, password=password, phone_number=phone_number, currency_code=currency_code)
        user = users_service.register_new_user(register_info=register_info)
        
        # Return login page if user is created or this page with error if not
        if not user:
            return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                "An issue occured while creating your account. Try again later.", "currencies": currencies})
        return RedirectResponse(url='/users/login', status_code=302)
        
    # BaseModel will return value error if some constraint wasn't met
    except ValueError as ve:
        print(traceback.format_exc())
        return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                f"Invalid form input: {ve}", "currencies": currencies})
    except:
        print(traceback.format_exc())
        return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                "An issue occured while creating your account. Try again later.", "currencies": currencies})
        
# ====================================================== LOGIN ENDPOINTS ======================================================

@web_users_router.get('/login')
def serve_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@web_users_router.post('/login')
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    
    # Try to login the User
    try:
        login_info = UserLoginInfo(username=username, password=password)
        user = users_service.login_user(login_info)
        if not user: 
            return templates.TemplateResponse(request=request, name="login.html", context={"error_message":
                "User with these credentials was not found."})
        
        # Create u-token attach to cookies and return info page
        u_token = encode_u_token(user)
        if not u_token: 
            return templates.TemplateResponse(request=request, name="login.html", context={"error_message":
                "Could not login user. Try again later."})
        
        token = encode_u_token(user)
        response = RedirectResponse(url='/users/info', status_code=302)
        response.set_cookie('u-token', token)
        return response
    
    # If check password returned False
    except users_service.UserService_LoginAuthError:
        return templates.TemplateResponse(request=request, name="login.html", context={"error_message":
                "An invalid username or password was provided."})
    
    # If User is not verified
    except users_service.UserService_UserNotVerifiedError:
        return templates.TemplateResponse(request=request, name="login.html", context={"error_message":
                "User is not verified."})
    
    # If User blocked 
    except users_service.UserService_UserBlockedError:
        return templates.TemplateResponse(request=request, name="login.html", context={"error_message":
                "User is blocked."})
    
    # Generic handle for all other types of error
    except:
        print(traceback.format_exc())
        return templates.TemplateResponse(request=request, name="login.html", context={"error_message":
                "An internal issue occured. Try again later."})
        
# ====================================================== INFO ENDPOINTS ======================================================
@web_users_router.get('/info')
def serve_info(request: Request):
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    
    user_info = users_service.get_user_info(user.username)
    if not user_info:
        return RedirectResponse("/users/login", status_code=302)
    
    return templates.TemplateResponse(request=request, name="user_info.html", 
                                      context={"user": user_info.user, "cards": user_info.cards})
    
        
