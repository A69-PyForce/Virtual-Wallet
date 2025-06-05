from fastapi import APIRouter, Header, HTTPException
from data.models import TransactionCategoryOut, TransactionCategoryCreate
from common import authenticate, responses
import services.transaction_categories_service as service

api_transaction_categories_router = APIRouter(prefix="/api/users/categories")

@api_transaction_categories_router.get("/", response_model=list[TransactionCategoryOut])
def get_all_categories(u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        return service.get_all_categories_for_user(user.id)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@api_transaction_categories_router.post("", response_model=TransactionCategoryOut)
def create_category(category_data: TransactionCategoryCreate, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        return service.create_category_for_user(category_data, user.id)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@api_transaction_categories_router.delete("/{category_id}")
def delete_category(category_id: int, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        deleted = service.delete_category_for_user(category_id, user.id)
        if not deleted:
            return responses.NotFound(f"Category with id {category_id} not found.")
        return responses.OK(f"Category with id {category_id} deleted successfully.")
    except Exception as e:
        print(e)
        return responses.InternalServerError()

@api_transaction_categories_router.put("/{category_id}", response_model=TransactionCategoryOut)
def update_category(category_id: int, category_data: TransactionCategoryCreate, u_token: str = Header()):
    user = authenticate.get_user_or_raise_401(u_token)

    try:
        updated_category = service.update_category_for_user(category_id, user.id, category_data)
        if not updated_category:
            return responses.NotFound(f"Category with id {category_id} not found.")
        return updated_category
    except Exception as e:
        print(e)
        return responses.InternalServerError()