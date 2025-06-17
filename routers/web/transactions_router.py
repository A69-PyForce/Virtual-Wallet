from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from common import template_config, authenticate
from common.authenticate import get_user_or_raise_401
from services.recurring_service import create_recurring_for_user
from services.transaction_categories_service import get_all_categories_for_user
from services.transactions_service import create_transaction, get_user_transaction_history, get_transactions_for_user, \
    confirm_transaction, decline_transaction
from data.models import TransactionCreate, RecurringCreate, IntervalType, TransactionFilterParams

web_transactions_router = APIRouter(prefix='/users/transactions')
templates = template_config.CustomJinja2Templates(directory='templates')


# GET: Show the form
@web_transactions_router.get('/new')
def serve_new_transaction(request: Request):
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    categories = get_all_categories_for_user(user.id)
    return templates.TemplateResponse(request=request, name="new_transaction.html",
                                      context={"request": request, "user": user, "categories": categories,
                                          "error": None, "success": None})

# POST: Process the form
@web_transactions_router.post('/new')
async def process_new_transaction(
        request: Request,
        receiver_username: str = Form(...),
        amount: float = Form(...),
        category_id: int = Form(...),
        name: str = Form(...),
        description: str = Form(""),
        is_recurring: Optional[str] = Form(None),
        recurring_interval: Optional[int] = Form(None),
        recurring_type: Optional[str] = Form(None),
        recurring_start: Optional[str] = Form(None)
):
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)

    categories = get_all_categories_for_user(user.id)
    error = None
    success = None
    try:
        is_recurring_flag = is_recurring == "on"
        tx_create = TransactionCreate(
            receiver_username=receiver_username,
            amount=amount,
            category_id=category_id,
            name=name,
            description=description,
            is_recurring=is_recurring_flag
        )
        tx_id = await create_transaction(tx_create, user)

        # ===== if recurring, create recurring rule =====
        if is_recurring_flag and recurring_interval and recurring_type:
            if recurring_start:

                next_date = datetime.fromisoformat(recurring_start)
            else:
                next_date = datetime.now()
            recurring_data = RecurringCreate(
                transaction_id=tx_id,
                interval=recurring_interval,
                interval_type=IntervalType(recurring_type),
                next_exec_date=next_date
            )
            create_recurring_for_user(recurring_data, user)
            success = "Transaction and recurring rule successfully created!"
        else:
            success = "Transaction successfully created!"

    except Exception as exc:
        error = str(exc)

    return templates.TemplateResponse(
        request=request, name="new_transaction.html",
        context={
            "request": request,
            "user": user,
            "categories": categories,
            "error": error,
            "success": success,
        }
    )

@web_transactions_router.get("/history")
def view_transaction_history(
    request: Request,
    status: str = "",
    direction: str = "",
    start_date: str = "",
    end_date: str = "",
    category_id: int = 0,
    sort_by: str = "date",
    sort_order: str = "desc",
    limit: int = 30,
    offset: int = 0
):
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    filters = TransactionFilterParams(
        status=status if status else None,
        direction=direction if direction else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
        category_id=category_id if category_id else None,
        sort_by=sort_by if sort_by else "date",
        sort_order=sort_order if sort_order else "desc",
        limit=limit,
        offset=offset
    )
    transactions = get_user_transaction_history(user, filters)
    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "user": user,
            "transactions": transactions,
            #filters/status/direction
            "status": status,
            "direction": direction,
            "start_date": start_date,
            "end_date": end_date,
            "category_id": category_id,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    )

@web_transactions_router.post("/{transaction_id}/confirm")
async def confirm_tx(transaction_id: int, request: Request):
    token = request.cookies.get("u-token")
    user = get_user_or_raise_401(token)

    if not user:
        raise HTTPException(403, "User not found.")

    result = await confirm_transaction(transaction_id, user)

    if not result:
        raise HTTPException(404, "Unsuccessful confirmation.")
    return RedirectResponse("/users/transactions/history", status_code=303)

@web_transactions_router.post("/{transaction_id}/decline")
async def decline_tx(transaction_id: int, request: Request):
    token = request.cookies.get("u-token")
    user = get_user_or_raise_401(token)

    if not user:
        raise HTTPException(403, "User not found.")

    result = await decline_transaction(transaction_id, user)
    if not result:
        raise HTTPException(404, "Unsuccessful decline.")
    return RedirectResponse("/users/transactions/history", status_code=303)
