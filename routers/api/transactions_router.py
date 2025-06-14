from fastapi import APIRouter, Header, Depends
from common import authenticate, responses
import services.transactions_service as service
from data.models import TransactionOut, TransactionCreate, TransactionFilterParams, UserTransactionsResponse

api_transactions_router = APIRouter(prefix="/api/users/transactions")

class TransactionServiceInsufficientFunds(service.TransactionServiceError):
    pass

@api_transactions_router.get("", response_model=UserTransactionsResponse)
def get_user_transactions(u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        return service.get_transactions_for_user(user.id)
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_transactions_router.post("")
def create_transaction(transaction_data: TransactionCreate, u_token: str = Header()):
    sender = authenticate.get_user_or_raise_401(u_token)

    try:
        tx_id = service.create_transaction(transaction_data, sender)
        return responses.Created(f"Transaction created with id {tx_id}.")
    except service.TransactionServiceUserNotFound:
        return responses.NotFound("Receiver not found.")
    except service.TransactionServiceCurrencyNotFound:
        return responses.BadRequest("Invalid currency code.")
    except service.TransactionServiceInsufficientFunds:
        return responses.BadRequest("You don't have enough balance to create this transaction.")
    except service.TransactionServiceError:
        return responses.BadRequest("An issue occured while creating this transaction.")

    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_transactions_router.put("/{transaction_id}/confirm")
def confirm_transaction(transaction_id: int, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        is_updated = service.confirm_transaction(transaction_id, user)
        if not is_updated:
            return responses.NotFound("Transaction not found or cannot be confirmed.")
        return responses.OK("Transaction confirmed successfully.")
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_transactions_router.put("/{transaction_id}/decline")
def decline_transaction(transaction_id: int, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        is_deleted = service.decline_transaction(transaction_id, user)
        if not is_deleted:
            return responses.NotFound("Transaction not found or cannot be declined.")
        return responses.OK("Transaction declined successfully.")
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_transactions_router.get("/history", response_model=list[TransactionOut])
def get_transaction_history(
    # automatically parses query params like ?start_date=... into a validated Pydantic object
    filters: TransactionFilterParams = Depends(),
    u_token: str = Header()
):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        return service.get_user_transaction_history(user, filters)
    except Exception as e:
        print(e)
        return responses.InternalServerError()