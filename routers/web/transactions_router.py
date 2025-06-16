from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from common import template_config, authenticate
from services.transaction_categories_service import get_all_categories_for_user
from services.transactions_service import create_transaction, TransactionServiceError, TransactionServiceInsufficientFunds, TransactionServiceUserNotFound
from data.models import TransactionCreate
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
                                      context={"user": user, "categories": categories})

# POST: Process the form
@web_transactions_router.post('/new')
async def process_new_transaction(
    request: Request,
    receiver_username: str = Form(...),
    amount: float = Form(...),
    category_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    is_recurring: str = Form(None)):

    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)

    categories = get_all_categories_for_user(user.id)
    error = None
    success = None
    try:

        tx_create = TransactionCreate(
            receiver_username=receiver_username,
            amount=amount,
            category_id=category_id,
            name=name,
            description=description,
            is_recurring=bool(is_recurring)
        )

        tx_id = await create_transaction(tx_create, user)
        success = f"Transaction created successfully with ID: {tx_id}"
    except Exception as ex:
        error = str(ex)
    return templates.TemplateResponse(
        request=request, name="new_transaction.html",
        context={"user": user, "categories": categories, "error": error, "success": success})
