from data.models import *
import requests
import socket
import os

# Response model for returning an error from API
class APIErrorResponse(BaseModel):
    detail: str
    status_code: int

# Response model for getting a card from API
class CardBalanceResponse(BaseModel):
    card_lookup_hash: str
    balance: int | float
    currency_code: str

# Response model for depositing or withdrawing from a bank card
class CardTransferResponse(BaseModel):
    amount: int | float
    currency_code: str
    transfer_type: str

# Get base URL and port from env file
HOST_URL = os.getenv("BANK_CARDS_API_HOST_URL")
if not HOST_URL: raise ValueError("Bank Cards API HOST URL not specified in environment file.")

PORT = os.getenv("BANK_CARDS_API_PORT")
if not PORT: raise ValueError("Bank Cards API port not specified in environment file.")

def is_bank_cards_api_online() -> bool:
    """Function to test if API is online."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST_URL, int(PORT))) == 0 # Returns True if conn success
    
def get_bank_card_info_response(card_info: BankCardEncryptInfo):
    
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
            
        # Otherwise return error response
        else:
            return APIErrorResponse(
                detail=response.json()["detail"],
                status_code=response.status_code
            )
    
    # If API is not online return this error response
    return APIErrorResponse(
        detail="Bank Cards API is offline.",
        status_code=503
    )
    
def withdraw_from_bank_card(card_lookup_hash: str, withdraw_info: TransferInfo):
    
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
        # If status code isn't 200 return an error object
        else:
            return APIErrorResponse(
                detail=response.json()["detail"],
                status_code=response.status_code
            )
            
    # If API was offline 
    return APIErrorResponse(
        detail="Bank Cards API is offline.",
        status_code=503
    )
    
def deposit_to_bank_card(card_lookup_hash: str, deposit_info: TransferInfo):
    
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
        # If status code isn't 200 return an error object
        else:
            return APIErrorResponse(
                detail=response.json()["detail"],
                status_code=response.status_code
            )
            
    # If API was offline 
    return APIErrorResponse(
        detail="Bank Cards API is offline.",
        status_code=503
    )
            
            