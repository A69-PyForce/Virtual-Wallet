import asyncio

from common.error_handlers import register_error_handlers
from routers.web.transaction_categories_router import web_transactions_categories_router
from routers.web.transactions_router import web_transactions_router
from utils.currencies_utils import dump_all_currencies
from recurring_scheduler import process_due_recurring
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
import uvicorn

# API Routers imports
from routers.api.admin_router import api_admin_router
from routers.api.users_router import api_users_router
from routers.api.bank_cards_router import api_bank_cards_router
from routers.api.contacts_router import api_contacts_router
from routers.api.transaction_categories_router import api_transaction_categories_router
from routers.api.transactions_router import api_transactions_router
from routers.api.recurring_router import api_recurring_router

# WEB Router imports
from routers.web.home_router import web_home_router
from routers.web.users_router import web_users_router

# FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routers
app.include_router(api_users_router, tags=["API", "Users"])
app.include_router(api_admin_router, tags=["API", "Admin"])
app.include_router(api_bank_cards_router, tags=["API", "Bank Cards"])
app.include_router(api_contacts_router, tags=["API", "Contacts"])
app.include_router(api_transaction_categories_router, tags=["API", "Transaction Categories"])
app.include_router(api_transactions_router, tags=["API", "Transactions"])
app.include_router(api_recurring_router, tags=["API", "Recurring"])

# WEB Routers
app.include_router(web_home_router, tags=["WEB", "Home"])
app.include_router(web_users_router, tags=["WEB", "Users"])
app.include_router(web_transactions_router, tags=["WEB", "Transactions"])
app.include_router(web_transactions_categories_router, tags=["WEB", "Transaction Categories"])

# Error handlers
register_error_handlers(app)

# Run file as main
if __name__ == "__main__":
    
    # Recurring transactions processor
    asyncio.run(process_due_recurring())
    
    # Uncomment on first startup to cache currencies and also dump them in database
    dump_all_currencies()
    
    # Start server with uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)