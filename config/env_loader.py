import os
import cloudinary

# Load Claudinary config from .env for the user avatar and category images. |
CLDNR_CONFIG = {
    "cldnr_cloud_name": os.getenv("CLDNR_CLOUD_NAME"),
    "cldnr_api_key": os.getenv("CLDNR_API_KEY"),
    "cldnr_api_secret": os.getenv("CLDNR_API_SECRET")
}
if all(CLDNR_CONFIG.values()) != None:
    cloudinary.config(
        cloud_name=CLDNR_CONFIG["cldnr_cloud_name"],
        api_key=CLDNR_CONFIG["cldnr_api_key"],
        api_secret=CLDNR_CONFIG["cldnr_api_secret"]
    )
else:
    CLDNR_CONFIG = None
    
# Load DB config from .env for database connection.
DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "database": os.getenv("DB_NAME"),
}

# DB Connection pool configuration
POOL_CONFIG = {
    "pool_name": "mypool",
    "pool_size": 20,
    "pool_reset_connection": True
}

# Cache file
CURRENCIES_CACHE_FILE = "currencies_cache.json"

# Load JWT Key from .env for user auth tokens
JWT_ENCRYPT_KEY = os.getenv("JWT_ENCRYPT_KEY")

# Load Exchange rate API key for currencies & currency conversion
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

# Get Bank Cards encrypt key from .env file
BANK_CARDS_ENCRYPT_KEY = os.getenv("DB_BANK_CARDS_ENCRYPT_KEY")