from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

from common import template_config
from common.authenticate import get_user_or_raise_401
from data.models import UserFilterParams
from routers.api.admin_router import get_all_users
from services.admin_service import set_user_blocked_state, deny_transaction

web_admin_router = APIRouter(prefix="/admin")
templates = template_config.CustomJinja2Templates(directory='templates')

@web_admin_router.get("/users")  # /admin/users
def list_users(request: Request):
    token = request.cookies.get("u-token")
    admin = get_user_or_raise_401(token)
    if not admin.is_admin:
        return RedirectResponse("/", status_code=302)
    filters = UserFilterParams()
    users = get_all_users(filters)
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "user": admin, "users": users}
    )


@web_admin_router.post("/users/{user_id}/block")  # POST /admin/users/{id}/block
def block_user(request: Request, user_id: int):
    token = request.cookies.get("u-token")
    admin = get_user_or_raise_401(token)
    if not admin.is_admin:
        return RedirectResponse("/", status_code=302)
    set_user_blocked_state(user_id,True)
    return RedirectResponse("/admin/users", status_code=303)


@web_admin_router.post("/users/{user_id}/unblock")  # POST /admin/users/{id}/unblock
def unblock_user(request: Request, user_id: int):
    token = request.cookies.get("u-token")
    admin = get_user_or_raise_401(token)
    if not admin.is_admin:
        return RedirectResponse("/", status_code=302)
    set_user_blocked_state(user_id, False)
    return RedirectResponse("/admin/users", status_code=303)


@web_admin_router.post("/transactions/{transaction_id}/deny")  # POST /admin/transactions/{id}/deny
def deny(request: Request, transaction_id: int):
    token = request.cookies.get("u-token")
    admin = get_user_or_raise_401(token)
    if not admin.is_admin:
        return RedirectResponse("/", status_code=302)
    deny_transaction(transaction_id)
    return RedirectResponse("/admin/users", status_code=303)