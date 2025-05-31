import traceback
from data.models import *
from common import responses, authenticate
from fastapi import APIRouter, Header
from utils.regex_verifictaion_utils import *
from utils.user_auth_token_utils import *
import services.bank_cards_service as bank_cards_service

api_bank_cards_router = APIRouter(prefix='/api/bankcards')

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