from math import ceil
from typing import Literal

from fastapi import APIRouter, Request, Query
from starlette.responses import RedirectResponse
from common import template_config, authenticate
from data.models import UserFilterParams, AdminTransactionFilterParams
from services.admin_service import set_user_blocked_state, deny_transaction, approve_user, get_all_users, \
    get_all_transactions, count_users
from services.users_service import get_user_by_username

web_admin_router = APIRouter(prefix="/admin")
templates = template_config.CustomJinja2Templates(directory='templates')


@web_admin_router.get("/users")  # /admin/users
def list_users(
    request: Request,
    search: str = Query("", description="Search by username, email or phone"),
    page:   int = Query(1, ge=1, description="Page number"),
):
    """
    Render admin panel page to list all users with pagination and search.

    Args:
        request (Request): FastAPI request object.
        search (str, optional): Search filter for users.
        page (int, optional): Page number for pagination.

    Returns:
        HTML page with list of users.
    """
    admin = authenticate.get_user_if_token(request)
    if not admin or not admin.is_admin:
        return RedirectResponse("/", status_code=302)

    limit = 10
    offset = (page - 1) * limit

    filters = UserFilterParams(
        search=search or None,
        limit=limit,
        offset=offset
    )

    users = get_all_users(filters)
    total_count = count_users(filters)
    total_pages = ceil(total_count / limit) if total_count else 1
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": admin,
            "users": users,
            "search": search,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count
        }
    )

@web_admin_router.post("/users/{user_id}/approve")
def approve_user_web(request: Request, user_id: int):
    """
    Approve a user's registration from admin panel.

    Args:
        request (Request): FastAPI request object.
        user_id (int): ID of user to approve.

    Returns:
        Redirects back to admin user list page.
    """
    admin = authenticate.get_user_if_token(request)
    if not admin or not admin.is_admin:
        return RedirectResponse("/", status_code=302)
    approve_user(user_id)
    return RedirectResponse("/admin/users", status_code=303)

@web_admin_router.post("/users/{user_id}/block")  # POST /admin/users/{id}/block
def block_user(request: Request, user_id: int):
    """
    Block a user account from admin panel.

    Args:
        request (Request): FastAPI request object.
        user_id (int): ID of user to block.

    Returns:
        Redirects back to admin user list page.
    """
    admin = authenticate.get_user_if_token(request)
    if not admin or not admin.is_admin:
        return RedirectResponse("/", status_code=302)
    set_user_blocked_state(user_id,True)
    return RedirectResponse("/admin/users", status_code=303)

@web_admin_router.post("/users/{user_id}/unblock")  # POST /admin/users/{id}/unblock
def unblock_user(request: Request, user_id: int):
    """
    Unblock a previously blocked user account from admin panel.

    Args:
        request (Request): FastAPI request object.
        user_id (int): ID of user to unblock.

    Returns:
        Redirects back to admin user list page.
    """
    admin = authenticate.get_user_if_token(request)
    if not admin or not admin.is_admin:
        return RedirectResponse("/", status_code=302)
    set_user_blocked_state(user_id, False)
    return RedirectResponse("/admin/users", status_code=303)

@web_admin_router.post("/transactions/{transaction_id}/deny")  # POST /admin/transactions/{id}/deny
def deny(request: Request, transaction_id: int):
    """
    Deny a pending transaction from admin panel.

    Args:
        request (Request): FastAPI request object.
        transaction_id (int): ID of transaction to deny.

    Returns:
        Redirects back to admin user list page.
    """
    admin = authenticate.get_user_if_token(request)
    if not admin or not admin.is_admin:
        return RedirectResponse("/", status_code=302)
    deny_transaction(transaction_id)
    return RedirectResponse("/admin/users", status_code=303)

@web_admin_router.get("/users/{username}/view")
def view_user(request: Request,
    username: str,
    start_date: str = "",
    end_date: str = "",
    direction: Literal["incoming", "outgoing", "all"] | None = None,
    sort_by: Literal["date", "amount"] = "date",
    sort_order: Literal["asc", "desc"] = "desc",
    limit: int = 30,
    offset: int = 0
):

    admin = authenticate.get_user_if_token(request)
    if not admin or not admin.is_admin:
        return RedirectResponse("/", status_code=302)

    viewed_user = get_user_by_username(username)
    if not viewed_user:
        return RedirectResponse("/admin/users?error=User not found", status_code=303)

    filters = AdminTransactionFilterParams(
        start_date = start_date or None,
        end_date = end_date or None,
        sender_id = viewed_user.id   if direction == "outgoing" else None,
        receiver_id = viewed_user.id   if direction == "incoming" else None,
        user_id = viewed_user.id,
        direction=direction or None,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    transactions = get_all_transactions(filters)
    return templates.TemplateResponse(
        "admin_user_detail.html",
        {
            "request":      request,
            "user":         admin,
            "viewed_user":  viewed_user,
            "transactions": transactions,
            "start_date":   start_date,
            "end_date":     end_date,
            "direction":    direction,
            "sort_by":      sort_by,
            "sort_order":   sort_order,
            "limit":        limit,
            "offset":       offset,
        }
    )

