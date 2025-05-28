from utils.currencies_utils import dump_all_currencies
from fastapi import FastAPI
import uvicorn

app = FastAPI()
if __name__ == "__main__":
    dump_all_currencies()
    
    # Start server with uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=8001, reload=True)