import services.currencies_service as currencies_service
from pydantic import BaseModel, StringConstraints
from mariadb import IntegrityError
from typing import Annotated
import traceback
import httpx
import json
import os

from data.database import read_query


# Custom exception for this file
class CurrenciesUtils(Exception):
    pass

# Currency info model for writing or getting from db
class CurrencyInfo(BaseModel):
    code: Annotated[str, StringConstraints(min_length=3, max_length=3)]
    name: Annotated[str, StringConstraints(min_length=1, max_length=64)]

_EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
if not _EXCHANGE_RATE_API_KEY:
    raise CurrenciesUtils("Exchange Rate API Key not found.")

CACHE_FILE = "currencies_cache.json"

async def convert_currency(amount: int|float, from_currency: str, to_currency: str) -> float:
    if from_currency == to_currency: # Return same amount if currencies are also the same
        return amount
    
    # URL for currency exchange rate conversion thing
    URL = f"https://v6.exchangerate-api.com/v6/{_EXCHANGE_RATE_API_KEY}/pair/{from_currency}/{to_currency}/{amount}"
    async with httpx.AsyncClient() as client:
        response = await client.get(URL)
        response.raise_for_status() # Raise error if occured in the external API
        data = response.json()
        return data['conversion_result']

def cache_all_currencies():
    
    # Create a variable for type checking in models
    global ALL_CURRENCIES
    
    try:
        # Try to read cached json
        # Check if the cache file exists and is non-empty
        if os.path.exists(CACHE_FILE) and os.path.getsize(CACHE_FILE) > 0:
            with open(CACHE_FILE, "r") as f:
                ALL_CURRENCIES = tuple(json.load(f))
                
            print(f"[INFO / CURRENCIES UTILS] Loaded currency codes from {CACHE_FILE}.")
        
        # Else fetch data from API and create the cache file
        else:
            URL = f"https://v6.exchangerate-api.com/v6/{_EXCHANGE_RATE_API_KEY}/codes"
            with httpx.Client() as client:
                
                # Send request to API and get supported_codes from the response
                response = client.get(URL)
                response.raise_for_status() # raise the error if API sent one
                data = response.json()
                ALL_CURRENCIES = (pair for pair in data["supported_codes"])
                
                # Save to cache (json file)
                with open(CACHE_FILE, "w") as f:
                    json.dump(list(ALL_CURRENCIES), f)
                    
            print(f"[INFO / CURRENCIES UTILS] Called API and cached currency codes in {CACHE_FILE}.")
            
    except Exception:
        print(traceback.format_exc())
        raise CurrenciesUtils("[ERR / CURRENCIES UTILS] An issue occured while working with the currency codes.")

def dump_all_currencies():
    
    for pair in ALL_CURRENCIES:
        # Create a new CurrencyInfo object and call service to add it to db
        currency = CurrencyInfo(code=pair[0], name=pair[1])
        
        try:
            currencies_service.add_currency(currency)
            print(f"[INFO / CURRENCIES UTILS] {currency} added to database.")
        except IntegrityError: # DB will throw an integrety error if code/name already exist
            print(f"[WARN / CURRENCIES UTILS] {currency} already exists in database.")
            pass
        
# Call cache func to ensure ALL_CURRENCIES exists
cache_all_currencies()

def get_currency_code_by_user_id(user_id: int) -> str | None:
    result = read_query("""
        SELECT c.code
        FROM Users u
        JOIN Currencies c ON u.currency_id = c.id
        WHERE u.id = ?""", (user_id,))
    return result[0][0] if result else None

def get_display_transaction(tx, current_user_id):
    if current_user_id == tx.sender_id:
        return f"You sent {tx.original_amount:.2f} {tx.original_currency_code} (converted to {tx.amount:.2f} {tx.currency_code})"
    elif current_user_id == tx.receiver_id:
        return f"You received {tx.amount:.2f} {tx.currency_code}"
    else:
        return ""