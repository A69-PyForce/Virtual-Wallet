import services.bank_cards_api_client as bank_cards_api_client
import utils.bank_card_utils as bank_card_utils
from data.database import *
from data.models import *

# CHANGE ME IF HOST IS DIFFERENT
BANK_CARDS_API_BASE_URL = "http://127.0.0.1:8001/"

class BankCardsService_Error(Exception):
    """
    Base exception class for all BankCardsService errors.
    """
    pass

class BankCardsService_CardNotFoundError(BankCardsService_Error):
    """
    Raised when a bank card is not found in the external Bank Cards API or database.
    """
    pass

class BankCardsService_CardDeactivatedError(BankCardsService_Error):
    """
    Raised when attempting to access a deactivated bank card.
    """
    pass

class BankCardsService_CardInsufficientFundsError(BankCardsService_Error):
    """
    Raised when the bank card has insufficient funds for the requested transaction.
    """
    pass

class BankCardsService_UserInsufficientFundsError(BankCardsService_Error):
    """
    Raised when the user does not have sufficient funds to perform a deposit transaction.
    """
    pass

class BankCardsService_ExternalAPIError(BankCardsService_Error):
    """
    Raised when an unexpected error occurs while communicating with the external Bank Cards API.
    """
    pass

def add_card_to_user(card: BankCardCreateInfo, user: UserFromDB):
    """
    Add a new bank card to a user after validating its existence in the external Bank Cards API.

    First verifies that the card exists via external API. If valid, encrypts and stores card info.

    Args:
        card (BankCardCreateInfo): The card details to add.
        user (UserFromDB): The user to associate the card with.

    Returns:
        int: The ID of the newly inserted card.

    Raises:
        BankCardsService_CardNotFoundError: If the card is not found in the external API.
        BankCardsService_ExternalAPIError: If there is an issue communicating with the API.
        BankCardsService_Error: For encryption or database errors.
    """
    
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
    """
    Remove an existing bank card from the user based on matching card data.

    Decrypts stored cards and matches with the provided card data before deletion.

    Args:
        card_to_remove (BankCardCreateInfo): The card data to match for deletion.
        user (UserFromDB): The user attempting to remove the card.

    Returns:
        bool: True if the card was successfully removed.

    Raises:
        BankCardsService_CardNotFoundError: If no matching card was found for the user.
    """
    
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
    """
    Retrieve full details for a user's card.

    Decrypts and returns full card information if the card exists and is not deactivated.

    Args:
        card_id (int): The card ID to retrieve.
        user (UserFromDB): The user requesting card details.

    Returns:
        BankCardFullInfo: Full decrypted card information.

    Raises:
        BankCardsService_CardNotFoundError: If the card does not exist.
        BankCardsService_CardDeactivatedError: If the card is deactivated.
        BankCardsService_Error: If decryption fails.
    """
    
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
    """
    Withdraw funds from the bank card and credit the user's internal balance.

    Validates card existence, calls external API for withdrawal, then updates user's balance.

    Args:
        withdraw_info (TransferInfo): Withdrawal amount and currency.
        card_id (int): The card ID to withdraw from.
        user (UserFromDB): The user receiving funds to their balance.

    Returns:
        bool: True if the withdrawal and balance update succeed.

    Raises:
        BankCardsService_CardNotFoundError: If card not found in external API.
        BankCardsService_CardInsufficientFundsError: If card has insufficient funds.
        BankCardsService_ExternalAPIError: If API communication fails.
    """
    
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
    sql = "UPDATE Users SET balance = balance + ? WHERE id = ? AND username = ?"
    return update_query(sql=sql, sql_params=(withdraw_response.amount, user.id, user.username,))

def deposit_to_card_from_user_balance(deposit_info: TransferInfo, card_id: int, user: UserFromDB):
    """
    Deposit funds from the user's internal balance to the bank card.

    Checks user's balance, validates card, calls external API for deposit, and updates user's balance.

    Args:
        deposit_info (TransferInfo): Deposit amount and currency.
        card_id (int): The card ID to deposit into.
        user (UserFromDB): The user initiating the deposit.

    Returns:
        bool: True if the deposit and balance update succeed.

    Raises:
        BankCardsService_CardNotFoundError: If card not found in external API.
        BankCardsService_UserInsufficientFundsError: If user has insufficient funds.
        BankCardsService_ExternalAPIError: If API communication fails.
    """
    
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
        
    # Before depositing we need to check if User has enough balance for this transaction
    if user.balance < deposit_info.amount:
        raise BankCardsService_UserInsufficientFundsError("User has insufficient funds for this transaction.")
        
    # If all is well call API client again this time with the card lookup hash we got from card info
    deposit_response = bank_cards_api_client.deposit_to_bank_card(
        card_lookup_hash=response.card_lookup_hash,
        deposit_info=deposit_info
    )
    
    # Same as before client returns error response if an issue occured
    if isinstance(deposit_response, bank_cards_api_client.APIErrorResponse):
        
        # API should return 404 if card was not found
        if deposit_response.status_code == 404:
            raise BankCardsService_CardNotFoundError("Card not found inside the Bank Cards API.")
        
        # Else raise generic error since we dont want to continue
        else:
            raise BankCardsService_ExternalAPIError("An issue occured with the external Bank Cards API.")
        
    # If all is well means API has deposited funds to the card there, we need to update the User balance
    sql = "UPDATE Users SET balance = balance - ? WHERE id = ? AND username = ?"
    return update_query(sql=sql, sql_params=(deposit_response.amount, user.id, user.username,))

def change_user_card_nickname(nickname: str, card_id: int, user: UserFromDB):
    """
    Change the nickname for a specific user card.

    Args:
        nickname (str): New nickname to assign.
        card_id (int): The ID of the card.
        user (UserFromDB): The user making the change.

    Returns:
        bool: True if the update was successful.
    """
    
    # Update card nickname in database with this query
    sql = "UPDATE BankCards SET nickname = ? WHERE id = ? AND user_id = ?"
    return update_query(sql=sql, sql_params=(nickname, card_id, user.id,))

def change_user_card_image_url(image_url: str, card_id: int, user: UserFromDB):
    """
    Change the image URL for a specific user card.

    Args:
        image_url (str): New image URL to assign.
        card_id (int): The ID of the card.
        user (UserFromDB): The user making the change.

    Returns:
        bool: True if the update was successful.
    """
    
    # Update card image_url in database with this query
    sql = "UPDATE BankCards SET image_url = ? WHERE id = ? AND user_id = ?"
    return update_query(sql=sql, sql_params=(image_url, card_id, user.id,))
    
    
    