import traceback
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from common import template_config, authenticate
from data.database import insert_query
from data.models import BankCardCreateInfo, BankCardEncryptInfo, TransferInfo, BankCardNickname, BankCardImageURL
from services import bank_cards_service, users_service, bank_cards_api_client
from utils.bank_card_utils import encrypt_card_info

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

    return templates.TemplateResponse(request=request, name='new_card.html', context={"user": user})


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

    try:
        encrypt_info = BankCardEncryptInfo(
            number=card_number,
            expiration_date=expiration_date,
            card_holder=card_holder,
            check_number=ccv
        )
        card_info = BankCardCreateInfo(
            card_info=encrypt_info,
            type=card_type.upper(), #"DEBIT" or "CREDIT"
            nickname=nickname,
            image_url=image_url
        )

        bank_cards_service.add_card_to_user(card_info, user)

        return RedirectResponse(url="/users/cards/manage", status_code=302)

    except Exception:
        print(traceback.format_exc())
        return templates.TemplateResponse("new_card.html", {
            "request": request,
            "error_message": "An unexpected error occurred. Please try again later.",
            "user": user
        })
@web_bank_cards_router.get("/manage")
def manage_user_cards(request: Request):
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
        user_info = users_service.get_user_info(user.username)
        cards = user_info.cards  #  list[BankCardSummary]
        return templates.TemplateResponse("card_management.html", {
            "request": request,
            "user": user,
            "cards": cards
        })
    except Exception:
        print(traceback.format_exc())
        return templates.TemplateResponse("card_management.html", {
            "request": request,
            "user": user,
            "cards": [],
            "error_message": "Could not load bank cards."
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

    return RedirectResponse("/users/cards/manage", status_code=302)

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

    return RedirectResponse("/users/cards/manage", status_code=302)

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
        return RedirectResponse('/users/login', status_code=302)

    try:
        name = BankCardNickname(nickname=nickname)
        bank_cards_service.change_user_card_nickname(name.nickname, card_id, user)
    except Exception:
        print(traceback.format_exc())

    return RedirectResponse("/users/cards/manage", status_code=302)

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

    return RedirectResponse("/users/cards/manage", status_code=302)

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

    return RedirectResponse("/users/cards/manage", status_code=302)