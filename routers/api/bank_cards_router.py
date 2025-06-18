import traceback
from data.models import *
from common import responses, authenticate
from fastapi import APIRouter, Header
from utils.regex_verifictaion_utils import *
from utils.user_auth_token_utils import *
import services.bank_cards_service as bank_cards_service

api_bank_cards_router = APIRouter(prefix='/api/users/bankcards')

@api_bank_cards_router.post(path="")
def add_card_to_user(card_info: BankCardCreateInfo, u_token: str = Header()):
    """
    Add a new bank card to the authenticated user account.

    Args:
        card_info (BankCardCreateInfo): Card details to add.
        u_token (str): User authentication token.

    Returns:
        Success or error response depending on API checks.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        card_id = bank_cards_service.add_card_to_user(card_info, user)
        return responses.Created(content=f"Created a new card with id {card_id}.")
    
    except bank_cards_service.BankCardsService_CardNotFoundError:
        return responses.NotFound(content="The given card was not found inside Bank Cards API.")
    
    except bank_cards_service.BankCardsService_ExternalAPIError:
        return responses.ServiceUnavailable(content="Bank cards service is unavailable. Try again later.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_bank_cards_router.delete(path="")
def add_card_to_user(card_info: BankCardEncryptInfo, u_token: str = Header()):
    """
    Remove a bank card from the authenticated user account.

    Args:
        card_info (BankCardEncryptInfo): Card data used to identify the card for removal.
        u_token (str): User authentication token.

    Returns:
        Success or error response.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        is_removed = bank_cards_service.remove_card_from_user(card_info, user)
        if not is_removed: 
            print(traceback.format_exc())
            return responses.InternalServerError()
        
        return responses.OK("Successfuly removed the requested card.")
    
    except bank_cards_service.BankCardsService_CardNotFoundError:
        return responses.NotFound(content="The given card was not found for this User.")
    
    except bank_cards_service.BankCardsService_ExternalAPIError:
        return responses.ServiceUnavailable("Bank Cards Service is unavailable.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_bank_cards_router.get(path="/{card_id}")
def get_card_details_for_user(card_id, u_token: str = Header()):
    """
    Retrieve full details of a specific bank card for the user.

    Args:
        card_id (int): ID of the card.
        u_token (str): User authentication token.

    Returns:
        Full card details if found, or error response.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        return bank_cards_service.get_card_details_by_id(card_id, user)
    
    except bank_cards_service.BankCardsService_CardNotFoundError:
        return responses.NotFound(content=f"Card with id {card_id} was not found for this user.")
    
    except bank_cards_service.BankCardsService_CardDeactivatedError:
        return responses.BadRequest(content=f"Card with id {card_id} is deactivated.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_bank_cards_router.put(path="/{card_id}/withdraw")
def withdraw_from_card_to_user_balance(card_id: int, amount: Amount, u_token: str = Header()):
    """
    Withdraw funds from the specified card and credit user's internal balance.

    Args:
        card_id (int): ID of the card.
        amount (Amount): Amount to withdraw.
        u_token (str): User authentication token.

    Returns:
        Success or error response.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        withdraw_info = TransferInfo(
            amount=amount.amount,
            currency_code=user.currency_code
        )
        is_updated = bank_cards_service.withdraw_from_card_to_user_balance(withdraw_info, card_id, user)
        if not is_updated:
            print(traceback.format_exc())
            return responses.InternalServerError()
        return responses.OK(f"{withdraw_info.amount} {withdraw_info.currency_code} were deposited into your User account.")
    
    except bank_cards_service.BankCardsService_CardNotFoundError:
        return responses.NotFound(content=f"Card with id {card_id} was not found for this user.")
    
    except bank_cards_service.BankCardsService_CardDeactivatedError:
        return responses.BadRequest(content=f"Card with id {card_id} is deactivated.")
    
    except bank_cards_service.BankCardsService_CardInsufficientFundsError:
        return responses.BadRequest(content=f"Card has insufficient funds for this withdraw.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_bank_cards_router.put(path="/{card_id}/deposit")
def deposit_to_card_from_user_balance(card_id: int, amount: Amount, u_token: str = Header()):
    """
    Deposit funds from user's internal balance to the specified bank card.

    Args:
        card_id (int): ID of the card.
        amount (Amount): Amount to deposit.
        u_token (str): User authentication token.

    Returns:
        Success or error response.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        deposit_info = TransferInfo(
            amount=amount.amount,
            currency_code=user.currency_code
        )
        is_updated = bank_cards_service.deposit_to_card_from_user_balance(deposit_info, card_id, user)
        if not is_updated:
            print(traceback.format_exc())
            return responses.InternalServerError()
        return responses.OK(f"{deposit_info.amount} {deposit_info.currency_code} were deposited into back into your bank card.")
    
    except bank_cards_service.BankCardsService_CardNotFoundError:
        return responses.NotFound(content=f"Card with id {card_id} was not found for this user.")
    
    except bank_cards_service.BankCardsService_CardDeactivatedError:
        return responses.BadRequest(content=f"Card with id {card_id} is deactivated.")
    
    except bank_cards_service.BankCardsService_UserInsufficientFundsError:
        return responses.BadRequest(content=f"User has insufficient funds for this deposit.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_bank_cards_router.put(path="/{card_id}/nickname")
def change_user_card_nickname(card_id: int, name: BankCardNickname, u_token: str = Header()):
    """
    Change nickname for a specific bank card.

    Args:
        card_id (int): ID of the card.
        name (BankCardNickname): New nickname.
        u_token (str): User authentication token.

    Returns:
        Success or error response.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        is_updated = bank_cards_service.change_user_card_nickname(name.nickname, card_id, user)
        if not is_updated:
            return responses.NotFound(f"Card with id {card_id} was not found for this user.")
        return responses.OK(f"Successfuly changed the card's nickname to '{name.nickname}'.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
    
@api_bank_cards_router.put(path="/{card_id}/image")
def change_user_card_nickname(card_id: int, image: BankCardImageURL, u_token: str = Header()):
    """
    Change image URL for a specific bank card.

    Args:
        card_id (int): ID of the card.
        image (BankCardImageURL): New image URL.
        u_token (str): User authentication token.

    Returns:
        Success or error response.
    """
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        is_updated = bank_cards_service.change_user_card_image_url(image.image_url, card_id, user)
        if not is_updated:
            return responses.NotFound(f"Card with id {card_id} was not found for this user.")
        return responses.OK(f"Successfuly changed the card's image url.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()