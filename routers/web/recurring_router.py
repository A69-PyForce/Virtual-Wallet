from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from common import authenticate
import services.recurring_service as recurring_service
from common.template_config import CustomJinja2Templates
from data.models import RecurringCreate

web_recurring_router = APIRouter(prefix="/recurring")
templates = CustomJinja2Templates(directory="templates")

@web_recurring_router.get("/")
def get_recurring_transactions(request: Request):
    user = authenticate.get_user_or_raise_401(request.headers.get("u_token"))
    recurring = recurring_service.get_recurring_by_user(user.id)
    return templates.TemplateResponse("recurring/list.html", {
        "request": request,
        "recurring": recurring
    })

@web_recurring_router.get("/new")
def new_recurring_form(request: Request):
    return templates.TemplateResponse("recurring/create.html", {
        "request": request
    })

@web_recurring_router.post("/new")
def create_recurring_web(
    request: Request,
    transaction_id: int = Form(...),
    interval: int = Form(...),
    interval_type: str = Form(...),
    next_exec_date: str = Form(...)
):
    user = authenticate.get_user_or_raise_401(request.headers.get("u_token"))

    data = RecurringCreate(
        transaction_id=transaction_id,
        interval=interval,
        interval_type=interval_type,
        next_exec_date=next_exec_date
    )

    try:
        recurring_service.create_recurring_for_user(data, user)
        return RedirectResponse(url="/recurring", status_code=HTTP_302_FOUND)
    except Exception as e:
        print(e)
        return templates.TemplateResponse("recurring/create.html", {
            "request": request,
            "error": str(e)
        })
@web_recurring_router.post("/{id}/cancel")
def cancel_recurring_transaction(id: int, request: Request):
    user = authenticate.get_user_or_raise_401(request.headers.get("u_token"))
    recurring_service.cancel(id, user.id)
    return RedirectResponse(url="/recurring", status_code=HTTP_302_FOUND)
