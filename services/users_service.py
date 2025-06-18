import utils.user_auth_token_utils as user_auth_token_utils
import utils.user_password_utils as user_password_utils
from mariadb import IntegrityError
from data.database import *
from data.models import *

class UserService_Error(Exception):
    """
    Base exception class for all user service errors.
    """
    pass

class UserService_DuplicateKeyError(UserService_Error):
    """
    Raised when a username, email, or phone number is already in use.
    """
    pass

class UserService_InvalidCurrencyError(UserService_Error):
    """
    Raised when the provided currency code is invalid or not found.
    """
    pass

class UserService_LoginAuthError(UserService_Error):
    """
    Raised when login credentials are invalid.
    """
    pass

class UserService_TokenError(UserService_Error):
    """
    Raised when authentication token decoding fails.
    """
    pass

class UserService_UserBlockedError(UserService_Error):
    """
    Raised when the user account is blocked.
    """
    pass

class UserService_UserNotVerifiedError(UserService_Error):
    """
    Raised when the user account is not verified.
    """
    pass

def _assemble_user_from_data(user_data: list|tuple) -> UserFromDB:
    """
    Assemble a UserFromDB object from raw database row data.

    Args:
        user_data (list | tuple): Raw user data retrieved from the database.

    Returns:
        UserFromDB: Fully populated UserFromDB object.
    """
    return UserFromDB(
        id=user_data[0], username=user_data[1], email=user_data[2], phone_number=user_data[3],
        password_hash=user_data[4], is_admin=user_data[5], is_blocked=user_data[6],
        is_verified=user_data[7], balance=user_data[8], currency_code=user_data[9],
        created_at=user_data[10], avatar_url=user_data[11]
    )

def get_user_by_username(username: str) -> UserFromDB | None:
    """
    Retrieve a user from the database by username.

    Args:
        username (str): Username to search for.

    Returns:
        UserFromDB | None: User object if found, otherwise None.
    """

    # Try to get User with specified username from database
    sql = """SELECT id, username, email, phone_number, password_hash, is_admin, is_blocked, is_verified, balance, currency_id, created_at, avatar_url
    FROM Users WHERE username = ?"""
    user_data = read_query(sql=sql, sql_params=(username,))
    if not user_data: return None

    # Find currency code from currency id in user_data and replace it
    user_data = list(user_data[0])
    currency_id = user_data[9]
    currency_code = read_query(sql="SELECT code FROM Currencies WHERE id = ?", sql_params=(currency_id,))[0][0]
    user_data[9] = currency_code

    # Create UserFromDB object and return
    return _assemble_user_from_data(user_data)

def register_new_user(register_info: UserRegisterInfo) -> str:
    """
    Register a new user into the system.

    Validates currency, hashes password, inserts user, handles duplicate keys.

    Args:
        register_info (UserRegisterInfo): User registration data.

    Returns:
        str: Success message if user created.

    Raises:
        UserService_DuplicateKeyError: If username, email or phone are already taken.
        UserService_InvalidCurrencyError: If provided currency is invalid.
        UserService_Error: For general creation errors.
    """

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
    """
    Authenticate a user using username and password.

    Args:
        login_info (UserLoginInfo): Login credentials.

    Returns:
        UserFromDB: Authenticated user object.

    Raises:
        UserService_LoginAuthError: If credentials are invalid.
        UserService_UserBlockedError: If user account is blocked.
        UserService_UserNotVerifiedError: If user account is not verified.
    """

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
    """
    Validate a user's authentication token.

    Args:
        u_token (str): User token.

    Returns:
        bool: True if token is valid, False otherwise.
    """

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
    """
    Retrieve a user by decoding the provided authentication token.

    Args:
        u_token (str): User token.

    Returns:
        UserFromDB | None: User object if found, otherwise None.
    """

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
    """
    Retrieve full user information including attached bank cards.

    Args:
        username (str): Username to retrieve info for.

    Returns:
        UserInfo | None: Full user info with cards, or None if user not found.
    """

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

def list_users_with_total_count(username: str = None, page: int = 1, page_size: int = 10, current_user_id: int = None):
    """
    Retrieve a paginated list of users for searching and adding contacts.

    Supports filtering by username and excludes current user and already added contacts.

    Args:
        username (str, optional): Username filter. Defaults to None.
        page (int, optional): Page number for pagination. Defaults to 1.
        page_size (int, optional): Number of users per page. Defaults to 10.
        current_user_id (int, optional): Exclude current user and their existing contacts.

    Returns:
        UsersPaginationList: Paginated list of users.
    """
    # Base query for counting total users
    count_sql = "SELECT COUNT(*) FROM Users WHERE 1=1"
    # Base query for getting users
    sql = """SELECT id, username, email, avatar_url 
             FROM Users 
             WHERE 1=1"""

    params = []

    # Add username filter if provided
    if username:
        count_sql += " AND username LIKE ?"
        sql += " AND username LIKE ?"
        params.append(f"%{username}%")

    # Exclude current user if provided
    if current_user_id:
        count_sql += " AND id != ?"
        sql += " AND id != ?"
        params.append(current_user_id)

        # Exclude existing contacts
        count_sql += """ AND id NOT IN (
            SELECT contact_id FROM UserContacts WHERE user_id = ?
        )"""
        sql += """ AND id NOT IN (
            SELECT contact_id FROM UserContacts WHERE user_id = ?
        )"""
        params.append(current_user_id)

    # Get total count
    total_count = read_query(sql=count_sql, sql_params=tuple(params))[0][0]

    # Add pagination
    sql += " ORDER BY username LIMIT ? OFFSET ?"
    params.extend([page_size, (page - 1) * page_size])

    # Get paginated users
    users_data = read_query(sql=sql, sql_params=tuple(params))
    users_list = []
    for row in users_data:
        users_list.append(UserListInfo(id=row[0], username=row[1], email=row[2], avatar_url=row[3]))

    return UsersPaginationList(
        users=users_list,
        total_count=total_count,
        total_pages=(total_count + page_size - 1) // page_size,
        current_page=page,
        page=page,
        page_size=page_size
    )

def change_user_avatar_url(user: UserFromDB, avatar_url: UserAvatarURL):
    """
    Change the avatar URL for a user.

    Args:
        user (UserFromDB): The user to update.
        avatar_url (UserAvatarURL): The new avatar URL.

    Returns:
        bool: True if avatar URL was successfully updated.
    """

    # Query to do the thingie
    sql = "UPDATE Users SET avatar_url = ? WHERE id = ? AND username = ?"
    return insert_query(sql=sql, sql_params=(avatar_url.avatar_url, user.id, user.username,)) != 0