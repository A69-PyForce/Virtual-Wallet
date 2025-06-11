from fastapi import APIRouter, Header
from common import authenticate, responses
from data.models import RecurringCreate, RecurringOut
import services.recurring_service as service

api_recurring_router = APIRouter(prefix="/api/users/recurring")


@api_recurring_router.get("", response_model=list[RecurringOut])
def get_user_recurring(u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        return service.get_recurring_by_user(user.id)
    except Exception as e:
        print(e)
        return responses.InternalServerError()
@api_recurring_router.post("")
def create_recurring(data: RecurringCreate, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        recurring_id = service.create_recurring_for_user(data, user)
        return responses.Created(f"Recurring created with id {recurring_id}")
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_recurring_router.delete("/{recurring_id}")
def delete_recurring(recurring_id: int, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        deleted = service.delete_recurring(recurring_id, user)
        if not deleted:
            return responses.NotFound("Recurring not found or unauthorized.")
        return responses.OK("Recurring transaction cancelled.")
    except Exception as e:
        print(e)
        return responses.InternalServerError()