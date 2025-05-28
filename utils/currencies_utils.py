import services.currencies_service as currencies_service
from pydantic import BaseModel, StringConstraints
from mariadb import IntegrityError
from typing import Annotated
import traceback
import httpx
import json
import os

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

def cache_all_currency_codes():
    
    # Create a variable for type checking in models
    global ALL_CURRENCY_CODES
    
    try:
        # Try to read cached json
        # Check if the cache file exists and is non-empty
        if os.path.exists(CACHE_FILE) and os.path.getsize(CACHE_FILE) > 0:
            with open(CACHE_FILE, "r") as f:
                ALL_CURRENCY_CODES = tuple(json.load(f))
                
            print(f"[INFO / CURRENCIES UTILS] Loaded currency codes from {CACHE_FILE}.")
        
        # Else fetch data from API and create the cache file
        else:
            URL = f"https://v6.exchangerate-api.com/v6/{_EXCHANGE_RATE_API_KEY}/codes"
            with httpx.Client() as client:
                
                # Send request to API and get supported_codes from the response
                response = client.get(URL)
                response.raise_for_status() # raise the error if API sent one
                data = response.json()
                ALL_CURRENCY_CODES = (pair for pair in data["supported_codes"])
                
                # Save to cache (json file)
                with open(CACHE_FILE, "w") as f:
                    json.dump(list(ALL_CURRENCY_CODES), f)
                    
            print(f"[INFO / CURRENCIES UTILS] Called API and cached currency codes in {CACHE_FILE}.")
            
    except Exception:
        print(traceback.format_exc())
        raise CurrenciesUtils("[ERR / CURRENCIES UTILS] An issue occured while working with the currency codes.")

def dump_all_currencies():
    
    # Call cache func to ensure ALL_CURRENCY_CODES exists
    cache_all_currency_codes()
    
    for pair in ALL_CURRENCY_CODES:
        # Create a new CurrencyInfo object and call service to add it to db
        currency = CurrencyInfo(code=pair[0], name=pair[1])
        
        try:
            currencies_service.add_currency(currency)
            print(f"[INFO / CURRENCIES UTILS] {currency} added to database.")
        except IntegrityError: # DB will throw an integrety error if code/name already exist
            print(f"[WARN / CURRENCIES UTILS] {currency} already exists in database.")
            pass