import services.bank_cards_api_client as bank_cards_api_client
import utils.bank_card_utils as bank_card_utils
from data.database import *
from data.models import *

# CHANGE ME IF HOST IS DIFFERENT
BANK_CARDS_API_BASE_URL = "http://127.0.0.1:8001/"

class BankCardsService_Error(Exception):
    pass

class BankCardsService_CardNotFoundError(BankCardsService_Error):
    pass

class BankCardsService_CardDeactivatedError(BankCardsService_Error):
    pass

class BankCardsService_CardInsufficientFundsError(BankCardsService_Error):
    pass

class BankCardsService_ExternalAPIError(BankCardsService_Error):
    pass

def add_card_to_user(card: BankCardCreateInfo, user: UserFromDB):
    
    # First check if the card exists inside the Bank Cards API before doing anything else
    response = bank_cards_api_client.get_bank_card_info_response(card.card_info)
    
    # API Client returns APIErrorResponse if Bank Cards API returned an error
    if isinstance(response, bank_cards_api_client.APIErrorResponse):
        
        # API should return 404 if card was not found
        if response.status_code == 404:
            raise BankCardsService_CardNotFoundError("Card not found inside the Bank Cards API.")
        
        # Else raise generic error since we dont want to continue creation of the card
        else:
            raise BankCardsService_ExternalAPIError("An issue occured with the external Bank Cards API.")
    
    # Proceed to encrypt card info if no errors were raised, meaning card exists inside Bank Cards API
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

def get_card_details_by_id(card_id: int, user: UserFromDB):
    
    # Select card information from database
    sql = """SELECT encrypted_card_info, type, is_deactivated, nickname, image_url
    FROM BankCards WHERE id = ? AND user_id = ?"""
    card_data = read_query(sql=sql, sql_params=(card_id, user.id,))
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
    
def withdraw_from_card_to_user_balance(withdraw_info: TransferInfo, card_id: int, user: UserFromDB):
    
    # Get full card info for API request first, call get_card_details_by_id for that,
    # create CardEncryptInfo from result
    card_details = get_card_details_by_id(card_id, user)
    card_info = BankCardEncryptInfo(
        number=card_details.card.number,
        expiration_date=card_details.card.expiration_date,
        card_holder=card_details.card.card_holder,
        check_number=card_details.card.check_number
    )
    
    # Call Bank Cards API client to get card lookup hash and to check if it even exists there
    response = bank_cards_api_client.get_bank_card_info_response(card_info)
    
    # API Client returns APIErrorResponse if Bank Cards API returned an error
    if isinstance(response, bank_cards_api_client.APIErrorResponse):
        
        # API should return 404 if card was not found
        if response.status_code == 404:
            raise BankCardsService_CardNotFoundError("Card not found inside the Bank Cards API.")
        
        # Else raise generic error since we dont want to continue
        else:
            raise BankCardsService_ExternalAPIError("An issue occured with the external Bank Cards API.")
        
    # If all is well call API client again this time with the card lookup hash we got from card info
    withdraw_response = bank_cards_api_client.withdraw_from_bank_card(
        card_lookup_hash=response.card_lookup_hash,
        withdraw_info=withdraw_info
    )
    
    # Same as before client returns error response if an issue occured
    if isinstance(withdraw_response, bank_cards_api_client.APIErrorResponse):
        
        # API should return 404 if card was not found
        if withdraw_response.status_code == 404:
            raise BankCardsService_CardNotFoundError("Card not found inside the Bank Cards API.")
        
        # If code is 402 means card has insufficient funds
        elif withdraw_response.status_code == 402:
            raise BankCardsService_CardInsufficientFundsError("Card has insufficient funds for this withdraw.")
        
        # Else raise generic error since we dont want to continue
        else:
            raise BankCardsService_ExternalAPIError("An issue occured with the external Bank Cards API.")
        
    # If all is well means API has withdrawn funds from the card there, we need to update the User balance
    sql = """UPDATE Users SET balance = balance + ? 
    WHERE id = ? AND username = ?"""
    return update_query(sql=sql, sql_params=(withdraw_response.amount, user.id, user.username,))
    
    
    