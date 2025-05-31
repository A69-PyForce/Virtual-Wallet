import utils.bank_card_utils as bank_card_utils
from mariadb import IntegrityError
from data.database import *
from data.models import *
import requests

# CHANGE ME IF HOST IS DIFFERENT
BANK_CARDS_API_BASE_URL = "http://127.0.0.1:8001/bankcards"

class BankCardsService_Error(Exception):
    pass

class BankCardsService_CardNotFoundError(BankCardsService_Error):
    pass

def add_card_to_user(card: BankCardCreateInfo, user: UserFromDB):
    
    # First check if the card exists inside the Bank API before doing anything else
    response = requests.get(
        url=BANK_CARDS_API_BASE_URL,
        json={
            "number": card.card_info.number,
            "expiration_date": card.card_info.expiration_date,
            "card_holder": card.card_info.card_holder,
            "check_number": card.card_info.check_number
        }
    )
    # print(response.json())
    
    # API should return 404 if card was not found
    if response.status_code == 404:
        raise BankCardsService_CardNotFoundError("Card not found inside the Bank Cards API.")
    
    # API should return 500 if another error occured there
    if response.status_code == 500:
        raise BankCardsService_Error("An issue occured inside Bank Cards API.")
    
    # Encrypt card information
    encrypted_card_info = bank_card_utils.encrypt_card_info(card.card_info)
    if not encrypted_card_info: 
        raise BankCardsService_Error("An issue occured while creating your Bank Card.")
    
    # Insert into BankCards table
    sql = """INSERT INTO BankCards (user_id, encrypted_card_info, type, nickname, image_url)
    VALUES (?, ?, ?, ?, ?)"""
    card_id = insert_query(sql=sql, sql_params=(user.id, encrypted_card_info, card.type, card.nickname, card.image_url,))
    if not card_id: 
        raise BankCardsService_Error("An issue occured while creating your Bank Card.")
    return card_id