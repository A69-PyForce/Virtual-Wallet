from pydantic import BaseModel, StringConstraints
from typing import Annotated
from data.database import *

# Currency info model for writing or getting from db
class CurrencyInfo(BaseModel):
    """
    Data model representing currency information.

    Attributes:
        code (str): 3-letter currency code (e.g. USD, EUR).
        name (str): Full name of the currency.
    """
    code: Annotated[str, StringConstraints(min_length=3, max_length=3)]
    name: Annotated[str, StringConstraints(min_length=1, max_length=64)]

def add_currency(currency: CurrencyInfo):
    """
    Add a new currency to the database.

    Inserts a currency record into the Currencies table.

    Args:
        currency (CurrencyInfo): The currency data to insert.

    Returns:
        int: The ID of the newly inserted currency row.
    """
    sql = "INSERT INTO Currencies (code, name) VALUES (?, ?)"
    row_id = insert_query(sql=sql, sql_params=(currency.code, currency.name,))
    return row_id
    