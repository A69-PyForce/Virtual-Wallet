from pydantic import BaseModel, StringConstraints
from typing import Annotated
from data.database import *

# Currency info model for writing or getting from db
class CurrencyInfo(BaseModel):
    code: Annotated[str, StringConstraints(min_length=3, max_length=3)]
    name: Annotated[str, StringConstraints(min_length=1, max_length=64)]

def add_currency(currency: CurrencyInfo):
    sql = "INSERT INTO Currencies (code, name) VALUES (?, ?)"
    row_id = insert_query(sql=sql, sql_params=(currency.code, currency.name,))
    return row_id
    