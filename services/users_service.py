import utils.user_password_utils as user_password_utils
from mariadb import IntegrityError
from data.database import *
from data.models import *

class UserServiceError(Exception):
    pass

class UserServiceDuplicateKeyError(UserServiceError):
    pass

def register_new_user(user: UserRegisterInfo):
    
    # Try to find the submitted currency's id in the currencies table
    currency_id = read_query(sql="SELECT id FROM Currencies WHERE code = ?", sql_params=(user.currency_code,))
    if not currency_id: raise UserServiceError(f"Couldn't find currency with code {user.currency_code}.")
    
    # Hash the register password for secure storage in db
    hashed_password = user_password_utils.hash_password(user.password)
    if not hashed_password: raise UserServiceError("Couldn't hash user password.")
    
    # Insert new user and return message if successful
    sql = """INSERT INTO Users (username, email, phone_number, password_hash, currency_id)
    VALUES (?, ?, ?, ?, ?)"""
    
    try:
        user_id = insert_query(sql=sql, sql_params=(user.username, user.email, user.phone_number, hashed_password, currency_id[0][0]))
    except IntegrityError:
        raise UserServiceDuplicateKeyError("Username, email or phone number are already in use!")
    
    if not user_id: raise UserServiceError("Couldn't create user.")
    return f"Created a new user with username '{user.username}'."