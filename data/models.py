from pydantic import BaseModel, StringConstraints, field_validator
from utils.currencies_utils import ALL_CURRENCIES
from datetime import datetime
from typing import Annotated

# NOTE: All field constraints are based on database key limitations

 # Used only to test the bank card utils, subject to change since db table is different from this.
class BankCardInfo(BaseModel):
    number: Annotated[str, StringConstraints(min_length=16, max_length=16)]
    expiration_date: Annotated[str, StringConstraints(min_length=5, max_length=5)]
    card_holder: Annotated[str, StringConstraints(min_length=2, max_length=30)]
    check_number: Annotated[str, StringConstraints(min_length=3, max_length=3)]

# Used for returning card summaries in the /users/info page
class BankCardSummary(BaseModel):
    id: int
    type: str
    is_deactivated: bool
    nickname: str | None
    image_url: str | None

# User register model - all required fields for registrating a user
class UserRegisterInfo(BaseModel):
    # Additional validations are required, verify using regex utils before setting username
    username: Annotated[str, StringConstraints(min_length=2, max_length=20)]
    
    # Additional validations are required, verify using regex utils before setting email
    email: Annotated[str, StringConstraints(min_length=6, max_length=40)]
    
    # Additional validations are required, verify using regex utils before setting password
    password: Annotated[str, StringConstraints(min_length=4, max_length=40)]
    
    phone_number: Annotated[str, StringConstraints(min_length=6, max_length=32)]
    
    # Uses custom field validator for the code, during db storage converts to currency_id (match from Currencies table)
    currency_code: Annotated[str, StringConstraints(min_length=3, max_length=3)]
    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, value):
        if not any(value == pair[0] for pair in ALL_CURRENCIES):
            raise ValueError(f"Invalid currency code: {value}.")
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

# Used for returning a User info JSON for the /users/info page
class UserInfo(BaseModel):
    user: UserFromDB
    cards: list[BankCardSummary]