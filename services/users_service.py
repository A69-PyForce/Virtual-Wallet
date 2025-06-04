import utils.user_auth_token_utils as user_auth_token_utils
import utils.user_password_utils as user_password_utils
from mariadb import IntegrityError
from data.database import *
from data.models import *

class UserService_Error(Exception):
    pass

class UserService_DuplicateKeyError(UserService_Error):
    pass

class UserService_InvalidCurrencyError(UserService_Error):
    pass

class UserService_LoginAuthError(UserService_Error):
    pass

class UserService_TokenError(UserService_Error):
    pass

class UserService_UserBlockedError(UserService_Error):
    pass

class UserService_UserNotVerifiedError(UserService_Error):
    pass

def _assemble_user_from_data(user_data: list|tuple) -> UserFromDB:
    return UserFromDB(
        id=user_data[0], username=user_data[1], email=user_data[2], phone_number=user_data[3],
        password_hash=user_data[4], is_admin=user_data[5], is_blocked=user_data[6],
        is_verified=user_data[7], balance=user_data[8], currency_code=user_data[9],
        created_at=user_data[10], avatar_url=user_data[11]
    )

def get_user_by_username(username: str) -> UserFromDB | None:
    
    # Try to get User with specified username from database
    sql = """SELECT id, username, email, phone_number, password_hash, is_admin, is_blocked, is_verified, balance, currency_id, created_at, avatar_url
    FROM Users WHERE username = ?"""
    user_data = read_query(sql=sql, sql_params=(username,))
    if not user_data: None
    
    # Find currency code from currency id in user_data and replace it
    user_data = list(user_data[0])
    currency_id = user_data[9]
    currency_code = read_query(sql="SELECT code FROM Currencies WHERE id = ?", sql_params=(currency_id,))[0][0]
    user_data[9] = currency_code
    
    # Create UserFromDB object and return
    return _assemble_user_from_data(user_data)

def register_new_user(register_info: UserRegisterInfo) -> str:
    
    # Try to find the submitted currency's id in the currencies table
    currency_id = read_query(sql="SELECT id FROM Currencies WHERE code = ?", sql_params=(register_info.currency_code,))
    if not currency_id: raise UserService_InvalidCurrencyError(f"Couldn't find currency with code {register_info.currency_code}.")
    
    # Hash the register password for secure storage in db
    hashed_password = user_password_utils.hash_password(register_info.password)
    if not hashed_password: raise UserService_Error("Couldn't hash user password.")
    
    # Insert new user and return message if successful
    sql = """INSERT INTO Users (username, email, phone_number, password_hash, currency_id)
    VALUES (?, ?, ?, ?, ?)"""
    
    try:
        user_id = insert_query(sql=sql, sql_params=(
            register_info.username, register_info.email, 
            register_info.phone_number, hashed_password, currency_id[0][0]
            ))
    except IntegrityError:
        raise UserService_DuplicateKeyError("Username, email or phone number are already in use!")
    
    if not user_id: raise UserService_Error("Couldn't create user.")
    return f"Created a new user with username '{register_info.username}'."

def login_user(login_info: UserLoginInfo) -> UserFromDB:
    
    # Get User via username from database and try to match password
    user = get_user_by_username(login_info.username)
    if not user: raise UserService_LoginAuthError("Invalid credentials")
    is_password_matched = user_password_utils.check_password(login_info.password, user.password_hash)
    
    # Raise error if password missmatches the one gotten from database
    if not is_password_matched: raise UserService_LoginAuthError("Invalid credentials")
    
    # Raise error if User is blocked
    if user.is_blocked: raise UserService_UserBlockedError("User is blocked.")
    
    # Raise error if User is not verified
    if not user.is_verified: raise UserService_UserNotVerifiedError("User is not verified.")
    
    # If all checks pass reset password hash for security and return the User object
    user.password_hash = None 
    return user

def is_user_authenticated(u_token: str) -> bool:
    
    # Try to decode provided token and unpack id, username
    decoded = user_auth_token_utils.decode_u_token(u_token)
    
    # Decoding will return None if invalid token or it has expired
    if not decoded: return False 
    id, username, _ = decoded.values()
    
    # Try to find User with the decoded id and username in database and return if found or not
    sql = """SELECT id, username FROM Users WHERE id = ? AND username = ?"""
    user_data = read_query(sql=sql, sql_params=(id, username,))
    if not user_data: return False
    return True
    
def find_user_by_token(u_token: str) -> UserFromDB | None:
    
    # Try to decode provided token and unpack id, username
    decoded = user_auth_token_utils.decode_u_token(u_token)
    
    # Decoding will return None if invalid token or it has expired
    if not decoded: return None 
    _, username, _ = decoded.values()
    
    # Get User from database, reset password hash and return
    user = get_user_by_username(username)
    if not user: return None
    user.password_hash = None
    return user

def get_user_info(username: str):
    
    # Create UserFromDB object and reset password_hash
    user = get_user_by_username(username)
    if not user: return None
    user.password_hash = None
    
    # Get all cards of User
    sql = """SELECT id, type, is_deactivated, nickname, image_url
    FROM BankCards WHERE user_id = ?"""
    cards_data = read_query(sql=sql, sql_params=(user.id,))
    cards = []
    for row in cards_data:
        cards.append(
            BankCardSummary(id=row[0], type=row[1], is_deactivated=row[2], nickname=row[3], image_url=row[4])
        )
    return UserInfo(user=user, cards=cards)

def list_users_with_total_count(username_filter: Optional[str], page: int, page_size: int):
    offset = (page - 1) * page_size
    
    # Build filter condition
    where_clause = " WHERE is_blocked = 0 AND is_verified = 1"
    sql_params = []
    
    if username_filter:
        where_clause = " AND username LIKE ?"
        sql_params.append(f"%{username_filter}%")
    
    # Build the main SQL query for paged users data
    users_sql = "SELECT id, username, avatar_url FROM Users" + where_clause + " ORDER BY username LIMIT ? OFFSET ?"
    
    # Append pagination parameters
    sql_params.extend([page_size, offset])
    
    # Exec the users query
    users_list = read_query(sql=users_sql, sql_params=tuple(sql_params))
    
    # Return the list with user info
    return [UserListInfo(id=user[0], username=user[1], avatar_url=user[2]) for user in users_list]

def change_user_avatar_url(user: UserFromDB, avatar_url: UserAvatarURL):
    
    # Query to do the thingie 
    sql = "UPDATE Users SET avatar_url = ? WHERE id = ? AND username = ?"
    return insert_query(sql=sql, sql_params=(avatar_url.avatar_url, user.id, user.username,)) != 0