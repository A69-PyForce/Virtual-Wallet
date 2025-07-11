import traceback
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from common import template_config, authenticate
from data.database import insert_query
from data.models import BankCardCreateInfo, BankCardEncryptInfo, TransferInfo, BankCardNickname, BankCardImageURL
from services import bank_cards_service, users_service, bank_cards_api_client
from utils.bank_card_utils import encrypt_card_info
from PIL import Image
import io
import cloudinary
import cloudinary.uploader
from config.env_loader import CLDNR_CONFIG

templates = template_config.CustomJinja2Templates(directory='templates')
web_bank_cards_router = APIRouter(prefix='/users/cards')


@web_bank_cards_router.get('/new')
def serve_add_card_form(request: Request):
    """
    Render form for adding a new bank card.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML page with new card form.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse('/users/login', status_code=302)

    return templates.TemplateResponse(request=request, name='new_bank_card.html', context={"user": user})


@web_bank_cards_router.post('/new')
def process_add_card(
        request: Request,
        card_number: str = Form(...),
        expiration_date: str = Form(...),
        card_holder: str = Form(...),
        ccv: str = Form(...),
        card_type: str = Form(...),
        nickname: str = Form(None),
        image_url: str = Form(None)
):

    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse('/users/login', status_code=302)

    error_message = None
    # Basic validation
    if not card_number or not card_number.strip():
        error_message = "Card number is required."
    
    if not expiration_date or not expiration_date.strip():
        error_message = "Expiration date is required."

    if not card_holder or not card_holder.strip():
        error_message = "Card holder name is required."
        
    if not ccv or not ccv.strip():
        error_message = "CCV is required."
    
    if not card_type or card_type not in ["DEBIT", "CREDIT"]:
        error_message = "Please select a valid card type (Debit or Credit)."

    try:
        encrypt_info = BankCardEncryptInfo(
            number=card_number.strip(),
            expiration_date=expiration_date.strip(),
            card_holder=card_holder.strip(),
            check_number=ccv.strip()
        )
        card_info = BankCardCreateInfo(
            card_info=encrypt_info,
            type=card_type.upper(), #"DEBIT" or "CREDIT"
            nickname=nickname.strip() if nickname else None,
            image_url=image_url.strip() if image_url else None
        )

        bank_cards_service.add_card_to_user(card_info, user)

        return RedirectResponse(url="/users/dashboard", status_code=302)

    except bank_cards_service.BankCardsService_CardNotFoundError:
        error_message = "Card not found. Please verify the card details and try again."
    
    except bank_cards_service.BankCardsService_ExternalAPIError:
        error_message = "Unable to verify card. Please try again later."
    
    except bank_cards_service.BankCardsService_Error:
        error_message = "Failed to add card. Please try again."

    except Exception:
        print(traceback.format_exc())
        error_message = "An unexpected error occurred. Please try again later."
    
    return templates.TemplateResponse("new_bank_card.html", context={
        "request": request,
         "error_message": error_message,
        "user": user,
        "card_number": card_number,
        "expiration_date": expiration_date,
        "card_holder": card_holder,
        "ccv": ccv,
        "card_type": card_type,
        "nickname": nickname,
        "image_url": image_url
    })

@web_bank_cards_router.get("/{card_id}")
def get_card_details(card_id: int, request: Request):
    """
    Render card management page showing all linked cards for the user.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML page with user's bank cards.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)

    try:
        card = bank_cards_service.get_card_details_by_id(card_id, user)
        if not card:
            return templates.TemplateResponse("card_management.html", {
                "request": request,
                "user": user,
                "error_message": "Card not found."
            })
        # card is BankCardFullInfo
        return templates.TemplateResponse("card_management.html", {
            "request": request,
            "user": user,
            "card_id": card_id,
            "type": card.type,
            "is_deactivated": card.is_deactivated,
            "nickname": card.nickname,
            "image_url": card.image_url,
            "number": card.card.number,
            "expiration_date": card.card.expiration_date,
            "card_holder": card.card.card_holder,
            "ccv": card.card.check_number,
        })
    except Exception:
        print(traceback.format_exc())
        return templates.TemplateResponse("card_management.html", {
            "request": request,
            "user": user,
            "error_message": "Could not load card details."
        })

@web_bank_cards_router.post("/{card_id}/deposit")
def deposit_to_card(card_id: int, amount: float = Form(...), request: Request = None):
    """
    Deposit funds from user balance to a bank card.

    Args:
        card_id (int): ID of the card.
        amount (float): Amount to deposit.
        request (Request): FastAPI request object.

    Returns:
        Redirect to card management page.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse('/users/login', status_code=302)

    try:
        deposit_info = TransferInfo(amount=amount, currency_code=user.currency_code)
        bank_cards_service.deposit_to_card_from_user_balance(deposit_info, card_id, user)
    except Exception:
        print(traceback.format_exc())

    return RedirectResponse("/users/dashboard", status_code=302)

@web_bank_cards_router.post("/{card_id}/withdraw")
def withdraw_from_card(card_id: int, amount: float = Form(...), request: Request = None):
    """
    Withdraw funds from a bank card to user's balance.

    Args:
        card_id (int): ID of the card.
        amount (float): Amount to withdraw.
        request (Request): FastAPI request object.

    Returns:
        Redirect to card management page.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse('/users/login', status_code=302)

    try:
        withdraw_info = TransferInfo(amount=amount, currency_code=user.currency_code)
        bank_cards_service.withdraw_from_card_to_user_balance(withdraw_info, card_id, user)
    except Exception:
        print(traceback.format_exc())

    return RedirectResponse("/users/dashboard", status_code=302)

@web_bank_cards_router.post("/{card_id}/nickname")
def update_card_nickname(card_id: int, nickname: str = Form(...), request: Request = None):
    """
    Update nickname for a specific bank card.

    Args:
        card_id (int): ID of the card.
        nickname (str): New nickname value.
        request (Request): FastAPI request object.

    Returns:
        Redirect to card management page.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse(f'/users/login', status_code=302)

    try:
        name = BankCardNickname(nickname=nickname)
        bank_cards_service.change_user_card_nickname(name.nickname, card_id, user)
    except Exception:
        print(traceback.format_exc())

    return RedirectResponse(f'/users/cards/{card_id}', status_code=302)

@web_bank_cards_router.post("/{card_id}/image")
def update_card_image(card_id: int, image_url: str = Form(...), request: Request = None):
    """
    Update image URL for a specific bank card.

    Args:
        card_id (int): ID of the card.
        image_url (str): New image URL value.
        request (Request): FastAPI request object.

    Returns:
        Redirect to card management page.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse('/users/login', status_code=302)

    try:
        img = BankCardImageURL(image_url=image_url)
        bank_cards_service.change_user_card_image_url(img.image_url, card_id, user)
    except Exception:
        print(traceback.format_exc())

    return RedirectResponse(f'/users/cards/{card_id}', status_code=302)

@web_bank_cards_router.post("/{card_id}/delete")
def delete_card(card_id: int, request: Request = None):
    """
    Delete a bank card from user's account.

    Args:
        card_id (int): ID of the card.
        request (Request): FastAPI request object.

    Returns:
        Redirect to card management page.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse('/users/login', status_code=302)

    try:
        encrypted_card = bank_cards_service.get_card_details_by_id(card_id, user).card
        bank_cards_service.remove_card_from_user(encrypted_card, user)
    except Exception:
        print(traceback.format_exc())

    return RedirectResponse("/users/dashboard", status_code=302)

@web_bank_cards_router.post("/{card_id}/image_upload")
async def upload_card_image(card_id: int, request: Request, file: UploadFile = File(...)):
    """
    Upload and update the image for a specific bank card.
    Args:
        card_id (int): ID of the card.
        request (Request): FastAPI request object.
        file (UploadFile): Uploaded image file.
    Returns:
        Redirect to card management page.
    """
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse('/users/login', status_code=302)
    
    image_url = None
    if CLDNR_CONFIG and file and file.filename:
        try:
            image_contents = await file.read()
            image = Image.open(io.BytesIO(image_contents))
            resized_image = image.resize((368, 180))
            buffer = io.BytesIO()
            resized_image.save(buffer, format=image.format or "JPEG")
            buffer.seek(0)
            result = cloudinary.uploader.upload(buffer, folder="virtual-wallet-card-images")
            image_url = result["secure_url"]
            
        except Exception:
            print(traceback.format_exc())
            image_url = None
    if image_url:
        bank_cards_service.change_user_card_image_url(image_url, card_id, user)
    return RedirectResponse(f"/users/cards/{card_id}", status_code=302)