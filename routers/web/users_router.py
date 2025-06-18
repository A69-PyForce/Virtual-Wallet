import io
import json
import traceback
import cloudinary
from PIL import Image
from data.models import *
import cloudinary.uploader
from pydantic import ValidationError
from utils.user_auth_token_utils import *
from config.env_loader import CLDNR_CONFIG
from utils.regex_verifictaion_utils import *
import services.users_service as users_service
from fastapi.responses import RedirectResponse
from common import responses, authenticate, template_config
import services.transactions_service as transactions_service
from fastapi import APIRouter, Request, Form, File, UploadFile

# Load currencies from cache file
with open('currencies_cache.json', 'r') as f:
    currencies = json.load(f)

web_users_router = APIRouter(prefix='/users')
templates = template_config.CustomJinja2Templates(directory='templates')

# ====================================================== REGISTER ENDPOINT ======================================================

@web_users_router.get('/register')
def serve_register(request: Request):
    """
    Render registration page with available currencies.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML page with registration form.
    """
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
    except ValidationError as ve:
        print(traceback.format_exc())
        return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                f"{ve.errors()[0]["msg"]}", "currencies": currencies})

    except users_service.UserService_DuplicateKeyError:
            return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                "Username, email or phone number are already in use!", "currencies": currencies})

    except users_service.UserService_InvalidCurrencyError:
            return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                    "Invalid Currency.", "currencies": currencies})

    except:
        print(traceback.format_exc())
        return templates.TemplateResponse(request=request, name="register.html", context={"error_message":
                "An issue occured while creating your account. Try again later.", "currencies": currencies})

# ====================================================== LOGIN ENDPOINT ======================================================

@web_users_router.get('/login')
def serve_login(request: Request):
    """
    Render login page.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML page with login form.
    """
    return templates.TemplateResponse(request=request, name="login.html")

@web_users_router.post('/login')
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Handle login form submission.

    Validates credentials, generates authentication token.

    Args:
        request (Request): FastAPI request object.
        username (str): Username.
        password (str): Password.

    Returns:
        Redirect with auth token or re-render login page with errors.
    """

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
        response = RedirectResponse(url='/users/dashboard', status_code=302)
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

# ===================================================== DASHBOARD ENDPOINT =====================================================
@web_users_router.get('/dashboard')
def serve_dashboard(request: Request):
    """
    Render user dashboard page with recent transactions and cards.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML dashboard page.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)

    user_info = users_service.get_user_info(user.username)
    if not user_info:
        return RedirectResponse("/users/login", status_code=302)

    user_transactions = transactions_service.get_transactions_for_user(user_id=user_info.user.id, limit=4)

    return templates.TemplateResponse(request=request, name="dashboard.html",
                                    context={"user": user_info.user, "cards": user_info.cards,
                                            "transactions": user_transactions.transactions})

# ===================================================== SETTINGS ENDPOINT ======================================================
@web_users_router.get('/settings')
def serve_settings(request: Request):
    """
    Render user profile settings page.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML settings page.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)

    user_info = users_service.get_user_info(user.username)
    if not user_info:
        return RedirectResponse("/users/login", status_code=302)

    return templates.TemplateResponse(request=request, name="settings.html",
                                    context={"user": user_info.user, "cards": user_info.cards})


# ====================================================== AVATAR ENDPOINT ======================================================

@web_users_router.post('/settings/avatar')
def change_avatar(request: Request, file: UploadFile = File(...)):
    """
    Handle avatar image upload and update via Cloudinary.

    Args:
        request (Request): FastAPI request object.
        file (UploadFile): Uploaded image file.

    Returns:
        Redirect to settings page after upload.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)

    if CLDNR_CONFIG:

        try:
            # Read uploader image
            image_contents = file.file.read()

            # Process image with Pillow & resize
            image = Image.open(io.BytesIO(image_contents))
            resized_image = image.resize((192, 192))

            # Save resized image to buffer
            buffer = io.BytesIO()
            resized_image.save(buffer, format=image.format or "JPEG")
            buffer.seek(0)

            # Upload image with Cloudinary and get the generated URL
            result = cloudinary.uploader.upload(buffer, folder="virtual-wallet-user-avatars")
            image_url = result["secure_url"]

            # Create avatar object for service
            avatar = UserAvatarURL(avatar_url=image_url)

            # Set avatar url in DB and redirect to same page to refresh
            users_service.change_user_avatar_url(user, avatar)
            return RedirectResponse("/users/settings", status_code=302)

        except:
            print(traceback.format_exc())
            pass

    # Call to same page to refresh
    return RedirectResponse("/users/settings", status_code=302)

# ====================================================== LOGOUT ENDPOINT ======================================================
@web_users_router.get('/logout')
def logout():
    """
    Logout user by removing authentication token cookie.

    Returns:
        Redirect to homepage.
    """
    response = RedirectResponse(url='/', status_code=302)
    response.delete_cookie("u-token")
    return response # del auth cookie and redirect to homepage


