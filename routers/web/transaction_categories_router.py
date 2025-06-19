import io
import traceback
import cloudinary
from PIL import Image
import cloudinary.uploader
from common import template_config
from config.env_loader import CLDNR_CONFIG
from starlette.responses import RedirectResponse
from data.models import TransactionCategoryCreate
from common.authenticate import get_user_if_token, get_user_or_raise_401
from fastapi import APIRouter, Request, Form, HTTPException, UploadFile, File
from services.transaction_categories_service import get_all_categories_for_user, create_category_for_user, \
    get_category_by_id_for_user, update_category_for_user, delete_category_for_user\



web_transactions_categories_router = APIRouter(prefix='/categories')
templates = template_config.CustomJinja2Templates(directory='templates')

@web_transactions_categories_router.get("")
def list_categories(request: Request):
    """
    Render categories management page.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML page with list of user's categories.
    """
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
    """
    Render form to create a new transaction category.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTML form page for new category creation.
    """
    user = get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    return templates.TemplateResponse(
        "category.html",
        {"request": request, "user": user, "category": None}
    )

@web_transactions_categories_router.post('/new')
async def create_category(
    request: Request,
    name: str = Form(...),
    image_url: str = Form(""),
    file: UploadFile = File(None)
):
    # enforce auth
    token = request.cookies.get("u-token")
    user = get_user_or_raise_401(token)

    # Handle file upload if present
    if file and file.filename:
        try:
            # Read uploader image
            image_contents = await file.read()
            
            # Process image with Pillow & resize
            image = Image.open(io.BytesIO(image_contents))
            resized_image = image.resize((192, 192))
            
            # Save resized image to buffer
            buffer = io.BytesIO()
            resized_image.save(buffer, format=image.format or "JPEG")
            buffer.seek(0)
            
            # Upload image with Cloudinary and get the generated URL
            if CLDNR_CONFIG:
                result = cloudinary.uploader.upload(buffer, folder="virtual-wallet-category-images")
                image_url = result["secure_url"]
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            print(traceback.format_exc())
            image_url = None

    url = image_url.strip() if image_url else None
    if not url or len(url) < 5:
        url = None

    data = TransactionCategoryCreate(name=name, image_url=url)
    create_category_for_user(data, user.id)
    return RedirectResponse("/categories", status_code=303)

@web_transactions_categories_router.get("/{category_id}/edit")
def edit_category(request: Request, category_id: int):
    """
    Render form to edit an existing category.

    Args:
        request (Request): FastAPI request object.
        category_id (int): ID of category to edit.

    Returns:
        HTML form page pre-filled with category data.
    """
    user = get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    cat = get_category_by_id_for_user(category_id, user.id)
    if not cat:
        raise HTTPException(404, "Category not found")
    return templates.TemplateResponse(
        "category.html",
        {"request": request, "user": user, "category": cat}
    )

@web_transactions_categories_router.post("/{category_id}/edit")
async def update_category(
    request: Request,
    category_id: int,
    name: str = Form(...),
    file: UploadFile = File(None)
):
    token = request.cookies.get("u-token")
    user = get_user_or_raise_401(token)

    # Get current category to preserve existing image_url if no new image is uploaded
    current_category = get_category_by_id_for_user(category_id, user.id)
    if not current_category:
        raise HTTPException(404, "Category not found")

    image_url = current_category.image_url

    # Handle file upload if present
    if file and file.filename:
        try:
            # Read uploader image
            image_contents = await file.read()
            
            # Process image with Pillow & resize
            image = Image.open(io.BytesIO(image_contents))
            resized_image = image.resize((192, 192))
            
            # Save resized image to buffer
            buffer = io.BytesIO()
            resized_image.save(buffer, format=image.format or "JPEG")
            buffer.seek(0)
            
            # Upload image with Cloudinary and get the generated URL
            if CLDNR_CONFIG:
                result = cloudinary.uploader.upload(buffer, folder="virtual-wallet-category-images")
                image_url = result["secure_url"]
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            print(traceback.format_exc())
            # Keep existing image_url if upload fails
            image_url = current_category.image_url

    data = TransactionCategoryCreate(name=name, image_url=image_url)
    updated = update_category_for_user(category_id, user.id, data)
    if not updated:
        raise HTTPException(404, "Unsuccessful update.")
    return RedirectResponse("/categories", status_code=303)

@web_transactions_categories_router.post("/{category_id}/delete")
def delete_category(request: Request, category_id: int):
    """
    Delete a transaction category.

    Args:
        request (Request): FastAPI request object.
        category_id (int): ID of category to delete.

    Returns:
        Redirect to category management page.
    """
    token = request.cookies.get("u-token")
    user = get_user_or_raise_401(token)
    removed = delete_category_for_user(category_id, user.id)
    if not removed:
        raise HTTPException(404, "Unsuccessful delete.")
    return RedirectResponse("/categories", status_code=303)