from pydantic import BaseModel, StringConstraints, field_validator, Field
from utils.currencies_utils import ALL_CURRENCIES
from typing import Annotated, Optional, Literal, List
from datetime import datetime, date
from enum import Enum
import phonenumbers

# NOTE: All field constraints are based on database key limitations

# Used encrypting and decrypting card information
class BankCardEncryptInfo(BaseModel):
    number: Annotated[str, StringConstraints(min_length=16, max_length=16)]
    expiration_date: Annotated[str, StringConstraints(min_length=5, max_length=5)]
    card_holder: Annotated[str, StringConstraints(min_length=2, max_length=30)]
    check_number: Annotated[str, StringConstraints(min_length=3, max_length=3)]
    
# Used for creating a new card inside database
class BankCardCreateInfo(BaseModel):
    card_info: BankCardEncryptInfo
    
    # Uses custom field validator for the type, can be either DEBIT or CREDIT
    type: Annotated[str, StringConstraints(min_length=5, max_length=6)]
    @field_validator("type")
    @classmethod
    def validate_currency_code(cls, value):
        if value not in ("DEBIT", "CREDIT"):
            raise ValueError(f"Invalid card type: {value}.")
        return value
    
    nickname: Optional[Annotated[str, StringConstraints(min_length=1, max_length=40)]] = None
    image_url: Optional[Annotated[str, StringConstraints(min_length=1, max_length=256)]] = None

# Used for returning card summaries in the /users/info page
class BankCardSummary(BaseModel):
    id: int
    type: str
    is_deactivated: bool
    nickname: str | None
    image_url: str | None
    
# Used for returning the full information of a given card
class BankCardFullInfo(BaseModel):
    card: BankCardEncryptInfo
    type: str
    is_deactivated: bool
    nickname: str | None
    image_url: str | None
    
# Request Body model used for sending requests for depositing or withdrawing from a bank card
class TransferInfo(BaseModel):
    amount: int | float
    currency_code: str
    
# Amount used in API router for withdraw/deposit
class Amount(BaseModel):
    amount: int | float
    
# Used in API router  for chaning a card nickname
class BankCardNickname(BaseModel):
    nickname: Annotated[str, StringConstraints(min_length=1, max_length=40)] | None

# Used in API router for chaning a card image url
class BankCardImageURL(BaseModel):
    image_url: Annotated[str, StringConstraints(min_length=1, max_length=256)] | None

# User register model - all required fields for registrating a user
class UserRegisterInfo(BaseModel):
    # Additional validations are required, verify using regex utils before setting username
    username: Annotated[str, StringConstraints(min_length=2, max_length=20)]
    
    # Additional validations are required, verify using regex utils before setting email
    email: Annotated[str, StringConstraints(min_length=6, max_length=40)]
    
    # Additional validations are required, verify using regex utils before setting password
    password: Annotated[str, StringConstraints(min_length=8, max_length=40)]
    
    # Uses custom field validator for phone number, must have a region code +359 for example and be overall a valid number
    phone_number: str
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):
        try:
            parsed = phonenumbers.parse(value)
            
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(f"Phone number '{value}' is invalid.")
            return value
        
        except Exception as e:
            raise ValueError(f"{e}")
    
    # Uses custom field validator for the code, during db storage converts to currency_id (match from Currencies table)
    currency_code: Annotated[str, StringConstraints(min_length=3, max_length=3)]
    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, value):
        if not any(value == pair[0] for pair in ALL_CURRENCIES):
            raise ValueError()
        return value

# Used for loggin in a user (duh), no validations required since was already done in registration
class UserLoginInfo(BaseModel):
    username: str
    password: str
    
# Used for returning a User model from database
class UserFromDB(BaseModel):
    id: int
    username: str
    email: str
    phone_number: str
    password_hash: str | None
    is_admin: bool
    is_blocked: bool
    is_verified: bool
    balance: float
    currency_code: str
    created_at: datetime
    avatar_url: str | None
    
    @classmethod
    def from_query(cls, id, username, email, phone_number, password_hash, is_admin, is_blocked, is_verified, balance, currency_code, created_at, avatar_url):
        return cls(
            id=id,
            username=username,
            email=email,
            phone_number=phone_number,
            password_hash=password_hash,
            is_admin=is_admin,
            is_blocked=is_blocked,
            is_verified=is_verified,
            balance=balance,
            currency_code=currency_code,
            created_at=created_at,
            avatar_url=avatar_url
        )
    
 # Used for generating a auth u_token in token utils
class UserTokenInfo(BaseModel):
    id: int
    username: str

# Used for returning a list of all users in users service
class UserListInfo(BaseModel):
    id: int
    username: str
    avatar_url: str | None

# Used in get_all_users endpoint in users router to return all users
class UsersPaginationList(BaseModel):
    users: List[UserListInfo]
    total_count: int
    total_pages: int
    current_page: int
    page: int
    page_size: int

# Used for returning a User info JSON for the /users/info page
class UserInfo(BaseModel):
    user: UserFromDB
    cards: list[BankCardSummary]

# Used in contacts router for adding/removing a contact
class ContactModify(BaseModel):
    username: str

# Used in contacts service/router for returning a list of Contacts with pagination
class ContactInfo(BaseModel):
    id: int
    username: str
    email: str
    avatar_url : str | None
class ListContacts(BaseModel):
    contacts: List[ContactInfo]
    total_count: int
    total_pages: int
    current_page: int
    page: int
    page_size: int

# Used in users router for changing avatar url
class UserAvatarURL(BaseModel):
    avatar_url: Annotated[str, StringConstraints(min_length=1, max_length=256)] | None

# Used for returning User auth token response
class UTokenResponse(BaseModel):
    u_token: str

class TransactionCategoryCreate(BaseModel):
    name: Annotated[str, StringConstraints(min_length=2, max_length=40)]
    image_url: Optional[Annotated[str, StringConstraints(min_length=5, max_length=256)]] = None

class TransactionCategoryOut(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None

    @classmethod
    def from_query(cls, row: tuple):
        return cls(
            id=row[0],
            name=row[1],
            image_url=row[2]
        )

class TransactionCreate(BaseModel):
    category_id: int
    name: Annotated[str, StringConstraints(min_length=2, max_length=32)]
    description: Annotated[str, StringConstraints(min_length=2, max_length=256)]
    receiver_username: Annotated[str, StringConstraints(min_length=2, max_length=20)]
    amount: float
    is_recurring: bool = False

class TransactionOut(BaseModel):
    id: int
    name: str
    description: str
    sender_id: int
    receiver_id: int
    amount: float
    currency_code: str
    category_id: int
    is_accepted: int
    is_recurring: bool
    created_at: datetime
    original_amount: float
    original_currency_code: str
    category_name: str
    receiver_name: str

    @classmethod
    def from_query(cls, row: tuple):
        return cls(
            id=row[0],
            name=row[1],
            description=row[2],
            sender_id=row[3],
            receiver_id=row[4],
            amount=row[5],
            currency_code=row[6],
            category_id=row[7],
            is_accepted=row[8],
            is_recurring=bool(row[9]),
            created_at=row[10],
            original_amount=row[11],
            original_currency_code=row[12],
            category_name=row[13],
            receiver_name=row[14])

# Used in the GET transactions/{id} router/service
class TransactionInfo(BaseModel):
    id: int
    name: str
    description: str
    sender_id: int
    receiver_id: int
    amount: float
    currency_code: str
    category_id: int
    is_accepted: int
    is_recurring: bool
    created_at: datetime
    original_amount: float
    original_currency_code: str
    category_name: str
    sender_username: str
    receiver_username: str
    category_image_url: str | None

    @classmethod
    def from_query(cls, row: tuple):
        return cls(
            id=row[0],
            name=row[1],
            description=row[2],
            sender_id=row[3],
            receiver_id=row[4],
            amount=row[5],
            currency_code=row[6],
            category_id=row[7],
            is_accepted=row[8],
            is_recurring=bool(row[9]),
            created_at=row[10],
            original_amount=row[11],
            original_currency_code=row[12],
            category_name=row[13],
            sender_username=row[14],
            receiver_username=row[15],
            category_image_url=row[16]
        )


class UserTransactionsResponse(BaseModel):
    transactions: list[TransactionOut]

class IntervalType(str, Enum):
    HOURS = "HOURS"
    DAYS = "DAYS"
    MINUTES = "MINUTES"

class RecurringCreate(BaseModel):
    transaction_id: int
    interval: int # example each month
    interval_type: IntervalType
    next_exec_date: datetime #when it will be done for the first time

class RecurringOut(BaseModel):
    id: int
    transaction_id: int
    interval: int
    interval_type: str
    next_exec_date: datetime

    @classmethod
    def from_query(cls, row: tuple):
        return cls(
            id=row[0],
            transaction_id=row[1],
            interval=row[2],
            interval_type=row[3],
            next_exec_date=row[4]
        )

class TransactionFilterParams(BaseModel):
    """
    Query parameter model for filtering and paginating transactions.

    Automatically built by FastAPI when used with Depends():
    - Filters by date range, direction (incoming/outgoing), and category
    - Supports sorting and pagination
    """
    start_date: date | None = None
    end_date: date | None = None
    direction: Literal["incoming", "outgoing"] | None = None
    category_id: int | None = None
    sort_by: Optional[Literal["date", "amount"]] = "date"
    sort_order: Optional[Literal["asc", "desc"]] = "desc"
    limit: int = Field(default=20, ge=1)
    offset: int = Field(default=0, ge=0)
    status: Literal["pending", "confirmed", "declined"] | None = None

class UserSummary(BaseModel):
    id: int
    username: str
    email: str
    phone_number: str
    is_blocked: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    avatar_url: str | None

    @classmethod
    def from_query(cls, row: tuple):
        return cls(
            id=row[0],
            username=row[1],
            email=row[2],
            phone_number=row[3],
            is_blocked=bool(row[4]),
            is_verified=bool(row[5]),
            is_admin=bool(row[6]),
            created_at=row[7],
            avatar_url=row[8]
        )

class UserFilterParams(BaseModel):
    search: str | None = None
    is_verified: bool | None = None
    limit: int = Field(default=20, ge=1)
    offset: int = Field(default=0, ge=0)

class AdminTransactionFilterParams(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    sender_id: int | None = None
    receiver_id: int | None = None
    user_id: int | None = None
    direction: Literal["incoming", "outgoing", "all"] | None = None
    sort_by: Optional[Literal["date", "amount"]] = "date"
    sort_order: Optional[Literal["asc", "desc"]] = "desc"
    limit: int = Field(default=20, ge=1)
    offset: int = Field(default=0, ge=0)

class TransactionTemplate(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float
    currency_id: int
    category_id: int
    name: str
    description: str

class ListTransactions(BaseModel):
    transactions: list[TransactionInfo]
    total_count: int
    total_pages: int
    current_page: int
    page: int
    page_size: int

class AdminTransactionOut(BaseModel):
    id: int
    name: str
    amount: float
    currency_code: str
    sender_username: str
    receiver_username: str
    is_accepted: int
    created_at: datetime

    @classmethod
    def from_query(cls, row: tuple):
        return cls(
            id                = row[0],
            name              = row[1],
            amount            = row[5],
            currency_code     = row[6],
            sender_username   = row[13],
            receiver_username = row[14],
            is_accepted       = row[8],
            created_at        = row[10],
        )
    
class ListTransactions(BaseModel):
    transactions: list[TransactionInfo]
    total_count: int
    total_pages: int
    current_page: int
    page: int
    page_size: int