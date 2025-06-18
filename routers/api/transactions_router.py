import traceback
from fastapi import APIRouter, Header, Depends
from common import authenticate, responses
import services.transactions_service as service
from data.models import TransactionOut, TransactionCreate, TransactionFilterParams, UserTransactionsResponse

api_transactions_router = APIRouter(prefix="/api/users/transactions")

class TransactionServiceInsufficientFunds(service.TransactionServiceError):
    pass

@api_transactions_router.get("", response_model=UserTransactionsResponse)
def get_user_transactions(limit: int | None = None, u_token: str = Header()):
    """
    Retrieve a list of transactions (both sent and received) for the authenticated user.

    Args:
        limit (int, optional): Optional limit for number of transactions returned.
        u_token (str): User authentication token.

    Returns:
        UserTransactionsResponse: List of user's transactions.
    """
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        return service.get_transactions_for_user(user.id, limit)
    except Exception:
        print(traceback.format_exc())
        return responses.InternalServerError()

@api_transactions_router.post("")
async def create_transaction(transaction_data: TransactionCreate, u_token: str = Header()):
    """
    Create a new transaction between two users.

    Args:
        transaction_data (TransactionCreate): Transaction details.
        u_token (str): User authentication token.

    Returns:
        Success or error response depending on validations.
    """
    sender = authenticate.get_user_or_raise_401(u_token)

    try:
        tx_id = await service.create_transaction(transaction_data, sender)
        return responses.Created(f"Transaction created with id {tx_id}.")
    except service.TransactionServiceUserNotFound:
        return responses.NotFound("Receiver not found.")
    except service.TransactionServiceCurrencyNotFound:
        return responses.BadRequest("Invalid currency code.")
    except service.TransactionServiceInsufficientFunds:
        return responses.BadRequest("You don't have enough balance to create this transaction.")
    except service.TransactionServiceError:
        return responses.BadRequest("An issue occured while creating this transaction.")

    except Exception:
        print(traceback.format_exc())
        return responses.InternalServerError()

@api_transactions_router.put("/{transaction_id}/confirm")
async def confirm_transaction(transaction_id: int, u_token: str = Header()):
    """
    Confirm a pending transaction as receiver.

    Args:
        transaction_id (int): ID of the transaction to confirm.
        u_token (str): User authentication token.

    Returns:
        Success or error response.
    """
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        is_updated = await service.confirm_transaction(transaction_id, user)
        if not is_updated:
            return responses.NotFound("Transaction not found or cannot be confirmed.")
        return responses.OK("Transaction confirmed successfully.")
    except Exception:
        print(traceback.format_exc())
        return responses.InternalServerError()

@api_transactions_router.put("/{transaction_id}/decline")
async def decline_tran(transaction_id: int, u_token: str = Header()):
    """
    Decline a pending transaction and refund sender.

    Args:
        transaction_id (int): ID of the transaction to decline.
        u_token (str): User authentication token.

    Returns:
        Success or error response.
    """
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        is_deleted = await service.decline_transaction(transaction_id, user)
        if not is_deleted:
            return responses.NotFound("Transaction not found or cannot be declined.")
        return responses.OK("Transaction declined successfully.")
    except Exception:
        print(traceback.format_exc())
        return responses.InternalServerError()

@api_transactions_router.get("/history", response_model=list[TransactionOut])
def get_transaction_history(filters: TransactionFilterParams = Depends(),
                            u_token: str = Header()):
    """
    Retrieve full transaction history with filtering, sorting, and pagination.

    Args:
        filters (TransactionFilterParams): Filtering parameters.
        u_token (str): User authentication token.

    Returns:
        List of filtered transactions.
    """
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        return service.get_user_transaction_history(user, filters)
    except Exception:
        print(traceback.format_exc())
        return responses.InternalServerError()