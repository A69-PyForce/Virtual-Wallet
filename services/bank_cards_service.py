import utils.bank_card_utils as bank_card_utils
from data.database import *
from data.models import *
import requests

# CHANGE ME IF HOST IS DIFFERENT
BANK_CARDS_API_BASE_URL = "http://127.0.0.1:8001/"

class BankCardsService_Error(Exception):
    pass

class BankCardsService_CardNotFoundError(BankCardsService_Error):
    pass

class BankCardsService_CardDeactivatedError(BankCardsService_Error):
    pass

def add_card_to_user(card: BankCardCreateInfo, user: UserFromDB):
    
    # First check if the card exists inside the Bank API before doing anything else
    response = requests.get(
        url=BANK_CARDS_API_BASE_URL + "bankcards",
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

def remove_card_from_user(card_to_remove: BankCardCreateInfo, user: UserFromDB):
    
    # Select id and card info of all of the cards that belong to the given User
    sql = "SELECT id, encrypted_card_info FROM BankCards WHERE user_id = ?"
    cards_data = read_query(sql=sql, sql_params=(user.id,))
    
    # For every card found, decrypt its information and try to match it with the given card
    for row in cards_data:
        decrypted_card = bank_card_utils.decrypt_card_info(row[1])
        if decrypted_card == card_to_remove:
            
            # Remove the card from database via id if its matched
            sql = "DELETE FROM BankCards WHERE id = ?"
            return update_query(sql=sql, sql_params=(row[0],))
    
    # If no cards were found raise error
    raise BankCardsService_CardNotFoundError("The given card was not found for this user.")

def get_card_details_by_id(card_id: int, user_id: int):
    
    # Select card information from database
    sql = """SELECT encrypted_card_info, type, is_deactivated, nickname, image_url
    FROM BankCards WHERE id = ? AND user_id = ?"""
    card_data = read_query(sql=sql, sql_params=(card_id, user_id,))
    if not card_data:
        raise BankCardsService_CardNotFoundError("The card was not found.")
    
    # Raise error if card is deactivated (not sure if this should be done)
    if card_data[0][2]:
        raise BankCardsService_CardDeactivatedError("The card is deactivated.")
    
    # Decrypt card information from encrypted_card_info field
    card_info = bank_card_utils.decrypt_card_info(card_data[0][0])
    if not card_info:
        raise BankCardsService_Error("Couldn't decrypt card info.")
    
    # Return BankCardFullInfo object to router
    return BankCardFullInfo(
        card=card_info,
        type=card_data[0][1],
        is_deactivated=card_data[0][2],
        nickname=card_data[0][3],
        image_url=card_data[0][4]
    )
    
    