from utils.currencies_utils import ALL_CURRENCY_CODES
from pydantic import BaseModel, StringConstraints
from typing import Annotated

 # Used only to test the bank card utils, subject to change since db table is different from this.
class BankCardInfo(BaseModel):
    number: Annotated[str, StringConstraints(min_length=16, max_length=16)]
    expiration_date: Annotated[str, StringConstraints(min_length=5, max_length=5)]
    card_holder: Annotated[str, StringConstraints(min_length=2, max_length=30)]
    check_number: Annotated[str, StringConstraints(min_length=3, max_length=3)]