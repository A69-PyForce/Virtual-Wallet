from fastapi import APIRouter, Depends, Header
from data.models import UserSummary, UserFilterParams, TransactionOut, AdminTransactionFilterParams, AdminTransactionOut
from common import authenticate, responses
import services.admin_service as admin_service

api_admin_router = APIRouter(prefix="/api/admin")

@api_admin_router.get("/users", response_model=list[UserSummary])
def get_all_users(filters: UserFilterParams = Depends(), u_token: str = Header()):
    admin = authenticate.get_user_or_raise_401(u_token)

    if not admin.is_admin:
        return responses.Forbidden("Only admins can access this endpoint.")

    try:
        return admin_service.get_all_users(filters)
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_admin_router.put("/users/{user_id}/approve")
def approve_user(user_id: int, u_token: str = Header()):
    admin = authenticate.get_user_or_raise_401(u_token)
    if not admin.is_admin:
        return responses.Forbidden("Admins only.")

    try:
        approved = admin_service.approve_user(user_id)
        if not approved:
            return responses.NotFound("User not found or already approved.")
        return responses.OK("User approved successfully.")
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_admin_router.put("/users/{user_id}/block")
def block_user(user_id: int, u_token: str = Header()):
    admin = authenticate.get_user_or_raise_401(u_token)
    if not admin.is_admin:
        return responses.Forbidden("Admins only.")

    try:
        success = admin_service.set_user_blocked_state(user_id, blocked=True)
        if not success:
            return responses.NotFound("User not found.")
        return responses.OK("User blocked successfully.")
    except Exception as e:
        print(e)
        return responses.InternalServerError()


@api_admin_router.put("/users/{user_id}/unblock")
def unblock_user(user_id: int, u_token: str = Header()):
    admin = authenticate.get_user_or_raise_401(u_token)
    if not admin.is_admin:
        return responses.Forbidden("Admins only.")

    try:
        success = admin_service.set_user_blocked_state(user_id, blocked=False)
        if not success:
            return responses.NotFound("User not found.")
        return responses.OK("User unblocked successfully.")
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_admin_router.get("/transactions", response_model=list[AdminTransactionOut])
def get_all_transactions(filters: AdminTransactionFilterParams = Depends(), u_token: str = Header()):
    admin = authenticate.get_user_or_raise_401(u_token)
    if not admin.is_admin:
        return responses.Forbidden("Admins only.")

    try:
        return admin_service.get_all_transactions(filters)
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_admin_router.put("/transactions/{transaction_id}/deny")
def deny_transaction(transaction_id: int, u_token: str = Header()):
    admin = authenticate.get_user_or_raise_401(u_token)
    if not admin.is_admin:
        return responses.Forbidden("Admins only.")

    try:
        denied = admin_service.deny_transaction(transaction_id)
        if not denied:
            return responses.NotFound("Transaction not found or already accepted.")
        return responses.OK("Transaction was denied and funds returned.")
    except Exception as e:
        print(e)
        return responses.InternalServerError()