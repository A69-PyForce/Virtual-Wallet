from utils.currencies_utils import dump_all_currencies
from routers.api.users_router import api_users_router
from routers.api.bank_cards_router import api_bank_cards_router
from fastapi import FastAPI
import uvicorn

app = FastAPI()
app.include_router(api_users_router, tags=["API", "Users"])
app.include_router(api_bank_cards_router, tags=["API", "Bank Cards"])


if __name__ == "__main__":
    
    # Uncomment on first startup to cache currencies and also dump them in database
    # dump_all_currencies()
    
    # Start server with uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)