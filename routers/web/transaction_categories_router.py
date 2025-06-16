from fastapi import APIRouter, Request, Form, HTTPException
from starlette.responses import RedirectResponse
from common import template_config
from common.authenticate import get_user_if_token, get_user_or_raise_401
from data.models import TransactionCategoryCreate
from services.transaction_categories_service import get_all_categories_for_user, create_category_for_user, \
    get_category_by_id_for_user, update_category_for_user, delete_category_for_user

web_transactions_categories_router = APIRouter(prefix='/categories')
templates = template_config.CustomJinja2Templates(directory='templates')

@web_transactions_categories_router.get("")
def list_categories(request: Request):
    user = get_user_if_token(request)
    if not user:
        return RedirectResponse(url="/users/login", status_code=302)
    categories = get_all_categories_for_user(user.id)
    return templates.TemplateResponse(
        "categories.html",
        {"request": request, "user": user, "categories": categories}
    )

@web_transactions_categories_router.get("/new")
def new_category(request: Request):
    user = get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    return templates.TemplateResponse(
        "new_category.html",
        {"request": request, "user": user,"category": None}
    )
@web_transactions_categories_router.post('/new')
def create_category(
    request: Request,
    name: str = Form(...),
    image_url: str = Form("")
):

    # enforce auth
    token = request.cookies.get("u-token")
    user = get_user_or_raise_401(token)

    # normalize optional URL
    url = image_url.strip()
    if not url or len(url) < 5:
        url = None

    data = TransactionCategoryCreate(name=name, image_url=url)
    create_category_for_user(data, user.id)
    return RedirectResponse("/categories", status_code=303)

@web_transactions_categories_router.get("/{category_id}/edit")
def edit_category(request: Request, category_id: int):
    user = get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    cat = get_category_by_id_for_user(category_id, user.id)
    if not cat:
        raise HTTPException(404, "Category not found")
    return templates.TemplateResponse(
        "new_category.html",
        {"request": request, "user": user, "category": cat}
    )

@web_transactions_categories_router.post("/{category_id}/edit")
def update_category(
    request: Request,
    category_id: int,
    name: str = Form(...),
    image_url: str = Form("")
):
    token = request.cookies.get("u-token")
    user = get_user_or_raise_401(token)

    url = image_url.strip()
    if not url or len(url) < 5:
        url = None

    data = TransactionCategoryCreate(name=name, image_url=url)
    updated = update_category_for_user(category_id, user.id, data)
    if not updated:
        raise HTTPException(404, "Unsuccessful update.")
    return RedirectResponse("/categories", status_code=303)


@web_transactions_categories_router.post("/{category_id}/delete")
def delete_category(request: Request, category_id: int):
    token = request.cookies.get("u-token")
    user = get_user_or_raise_401(token)
    removed = delete_category_for_user(category_id, user.id)
    if not removed:
        raise HTTPException(404, "Unsuccessful delete.")
    return RedirectResponse("/categories", status_code=303)