from common.logger import get_logger
from data.models import *
import requests
import socket
import os

logger = get_logger(name=__name__)

# Response model for returning an error from API
class APIErrorResponse(BaseModel):
    """
    Response model for returning an error from the external Bank Cards API.

    Attributes:
        detail (str): Error message description.
        status_code (int): HTTP status code returned from the API.
    """
    detail: str
    status_code: int

# Response model for getting a card from API
class CardBalanceResponse(BaseModel):
    """
    Response model representing the card balance received from the external Bank Cards API.

    Attributes:
        card_lookup_hash (str): The internal hash identifier for the card.
        balance (int | float): The current balance of the card.
        currency_code (str): Currency code of the card balance.
    """
    card_lookup_hash: str
    balance: int | float
    currency_code: str

# Response model for depositing or withdrawing from a bank card
class CardTransferResponse(BaseModel):
    """
    Response model for card deposit or withdrawal operations.

    Attributes:
        amount (int | float): The amount transferred.
        currency_code (str): Currency code used in the transaction.
        transfer_type (str): Type of transfer ("deposit" or "withdraw").
    """
    amount: int | float
    currency_code: str
    transfer_type: str

# Get base URL and port from env file
HOST_URL = os.getenv("BANK_CARDS_API_HOST_URL")
if not HOST_URL: raise ValueError("Bank Cards API HOST URL not specified in environment file.")

PORT = os.getenv("BANK_CARDS_API_PORT")
if not PORT: raise ValueError("Bank Cards API port not specified in environment file.")

def is_bank_cards_api_online() -> bool:
    """
    Check if the external Bank Cards API is reachable.

    Attempts to establish a socket connection to the external API service.

    Returns:
        bool: True if the API is reachable, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST_URL, int(PORT))) == 0 # Returns True if conn success
    
def get_bank_card_info_response(card_info: BankCardEncryptInfo):
    """
    Retrieve card balance information from the external Bank Cards API.

    Sends a GET request to the API with encrypted card information.
    If the API is online and responds with 200 OK, returns a CardBalanceResponse.
    Otherwise, returns an APIErrorResponse with details.

    Args:
        card_info (BankCardEncryptInfo): Encrypted card information payload.

    Returns:
        CardBalanceResponse | APIErrorResponse: Response depending on API result.
    """
    
    # Check if API is online
    if is_bank_cards_api_online():
        
        # Send GET request to API
        response = requests.get( 
            url=f"http://{HOST_URL}:{PORT}/bankcards",
            json={
                "number": card_info.number,
                "expiration_date": card_info.expiration_date,
                "card_holder": card_info.card_holder,
                "check_number": card_info.check_number
            }
        )
        # If status code is 200 assemble Card response object
        if response.status_code == 200:
            response = response.json()   
            return CardBalanceResponse(
                card_lookup_hash=response["card_lookup_hash"],
                balance=response["balance"],
                currency_code=response["currency_code"]
            )
            
        # Otherwise log and return error response
        else:
            logger.warning(msg=f"Bank Cards API returned error response with code {response.status_code}.")
            return APIErrorResponse(
                detail=response.json()["detail"],
                status_code=response.status_code
            )
    
    # If API is not online log and return error response
    logger.error(msg="Bank Cards API is offline.")
    return APIErrorResponse(
        detail="Bank Cards API is offline.",
        status_code=503
    )
    
def withdraw_from_bank_card(card_lookup_hash: str, withdraw_info: TransferInfo):
    """
    Perform a withdrawal operation on a bank card via the external Bank Cards API.

    Sends a PUT request to withdraw funds from the specified card.
    If the withdrawal succeeds, returns a CardTransferResponse.
    Otherwise, returns an APIErrorResponse.

    Args:
        card_lookup_hash (str): The hash identifier for the bank card.
        withdraw_info (TransferInfo): Withdrawal details (amount and currency).

    Returns:
        CardTransferResponse | APIErrorResponse: Response depending on API result.
    """
    
    # Check if API is online
    if is_bank_cards_api_online():
        
        # Send PUT request to API
        response = requests.put(
            url=f"http://{HOST_URL}:{PORT}/bankcards/withdraw/{card_lookup_hash}",
            json={
                "amount": withdraw_info.amount,
                "currency_code": withdraw_info.currency_code
            }
        )
        # If withdraw is completed successfuly (API returns code 200) return CardTransferResponse object
        if response.status_code == 200:
            response = response.json()
            return CardTransferResponse(
                amount=response["amount"],
                currency_code=response["currency_code"],
                transfer_type=response["transfer_type"]
            )
            
        # Otherwise log and return error response
        else:
            logger.warning(msg=f"Bank Cards API returned error response with code {response.status_code}.")
            return APIErrorResponse(
                detail=response.json()["detail"],
                status_code=response.status_code
            )
            
    # If API is not online log and return error response
    logger.error(msg="Bank Cards API is offline.")
    return APIErrorResponse(
        detail="Bank Cards API is offline.",
        status_code=503
    )
    
def deposit_to_bank_card(card_lookup_hash: str, deposit_info: TransferInfo):
    """
    Perform a deposit operation on a bank card via the external Bank Cards API.

    Sends a PUT request to deposit funds to the specified card.
    If the deposit succeeds, returns a CardTransferResponse.
    Otherwise, returns an APIErrorResponse.

    Args:
        card_lookup_hash (str): The hash identifier for the bank card.
        deposit_info (TransferInfo): Deposit details (amount and currency).

    Returns:
        CardTransferResponse | APIErrorResponse: Response depending on API result.
    """
    
    # Check if API is online
    if is_bank_cards_api_online():
        
        # Send PUT request to API
        response = requests.put(
            url=f"http://{HOST_URL}:{PORT}/bankcards/deposit/{card_lookup_hash}",
            json={
                "amount": deposit_info.amount,
                "currency_code": deposit_info.currency_code
            }
        )
        # If deposit is completed successfuly (API returns code 200) return CardTransferResponse object
        if response.status_code == 200:
            response = response.json()
            return CardTransferResponse(
                amount=response["amount"],
                currency_code=response["currency_code"],
                transfer_type=response["transfer_type"]
            )
            
        # Otherwise log and return error response
        else:
            logger.warning(msg=f"Bank Cards API returned error response with code {response.status_code}.")
            return APIErrorResponse(
                detail=response.json()["detail"],
                status_code=response.status_code
            )
            
    # If API is not online log and return error response
    logger.error(msg="Bank Cards API is offline.")
    return APIErrorResponse(
        detail="Bank Cards API is offline.",
        status_code=503
    )
            
            