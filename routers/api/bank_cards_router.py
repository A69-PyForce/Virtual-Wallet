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
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        card_id = bank_cards_service.add_card_to_user(card_info, user)
        return responses.Created(content=f"Created a new card with id {card_id}.")
    
    except bank_cards_service.BankCardsService_CardNotFoundError:
        return responses.NotFound(content="The given card was not found inside Bank Cards API.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_bank_cards_router.delete(path="")
def add_card_to_user(card_info: BankCardEncryptInfo, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        is_removed = bank_cards_service.remove_card_from_user(card_info, user)
        if not is_removed: 
            print(traceback.format_exc())
            return responses.InternalServerError()
        
        return responses.Created(content="Successfuly removed the requested card.")
    
    except bank_cards_service.BankCardsService_CardNotFoundError:
        return responses.NotFound(content="The given card was not found for this User.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_bank_cards_router.get(path="/{card_id}")
def get_card_details_for_user(card_id, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        return bank_cards_service.get_card_details_by_id(card_id, user.id)
    
    except bank_cards_service.BankCardsService_CardNotFoundError:
        return responses.NotFound(content=f"Card with id {card_id} was not found for this user.")
    
    except bank_cards_service.BankCardsService_CardDeactivatedError:
        return responses.BadRequest(content=f"Card with id {card_id} is deactivated.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()