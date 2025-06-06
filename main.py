from utils.currencies_utils import dump_all_currencies
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
import uvicorn

from routers.api.users_router import api_users_router
from routers.api.bank_cards_router import api_bank_cards_router
from routers.api.contacts_router import api_contacts_router
from routers.api.transaction_categories_router import api_transaction_categories_router
from routers.api.transactions_router import api_transactions_router

from routers.web.users_router import web_users_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_users_router, tags=["API", "Users"])
app.include_router(api_bank_cards_router, tags=["API", "Bank Cards"])
app.include_router(api_contacts_router, tags=["API", "Contacts"])
app.include_router(api_transaction_categories_router, tags=["API", "Transaction Categories"])
app.include_router(api_transactions_router, tags=["API", "Transactions"])

app.include_router(web_users_router, tags=["WEB", "Users"])

if __name__ == "__main__":
    
    # Uncomment on first startup to cache currencies and also dump them in database
    # dump_all_currencies()
    # Start server with uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)