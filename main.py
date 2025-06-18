from common.error_handlers import register_error_handlers
from utils.currencies_utils import dump_all_currencies
from recurring_scheduler import process_due_recurring
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI
import uvicorn
import asyncio

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
from routers.web.contacts_router import web_contacts_router
from routers.web.recurring_router import web_recurring_router
from routers.web.admin_router import web_admin_router
from routers.web.transaction_categories_router import web_transactions_categories_router
from routers.web.transactions_router import web_transactions_router
from routers.web.bank_cards_router import web_bank_cards_router

# FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """
    Serve favicon for web frontend.
    """
    return FileResponse("static/images/favicon.ico")

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
app.include_router(web_contacts_router, tags=["WEB", "Contacts"])
app.include_router(web_admin_router, tags=["WEB", "Admin"])
app.include_router(web_transactions_router, tags=["WEB", "Transactions"])
app.include_router(web_transactions_categories_router, tags=["WEB", "Transaction Categories"])
app.include_router(web_recurring_router, tags=["WEB", "Recurring Transaction"])
app.include_router(web_bank_cards_router, tags=["WEB", "Bank Cards"])

# Error handlers
register_error_handlers(app)

@app.on_event("startup")
async def start_recurring_scheduler():
    """
    Start recurring transaction background processor on application startup.
    """
    asyncio.create_task(process_due_recurring())

# Run file as main
if __name__ == "__main__":

    # Uncomment on first startup to cache currencies and also dump them in database
    dump_all_currencies()
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)