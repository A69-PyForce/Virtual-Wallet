import traceback
from data.models import *
from fastapi import APIRouter, Header, Form
from fastapi import APIRouter, Request
from utils.user_auth_token_utils import *
from common import responses, authenticate
from utils.regex_verifictaion_utils import *
from fastapi.responses import RedirectResponse
import common.template_config as template_config
import services.contacts_service as contacts_service

web_contacts_router = APIRouter(prefix='/users/contacts')
templates = template_config.CustomJinja2Templates(directory='templates')

@web_contacts_router.get('')
def serve_contacts(request: Request, page: int = 1, page_size: int = 5):
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    
    contacts = contacts_service.get_all_contacts_for_user(user, page=page, page_size=page_size)
    return templates.TemplateResponse(
        request=request, 
        name="contacts.html", 
        context={
            "contacts": contacts.contacts,
            "current_page": contacts.current_page,
            "total_pages": contacts.total_pages,
            "total_count": contacts.total_count,
            "page_size": contacts.page_size
        }
    )

@web_contacts_router.post('/add')
def add_contact(request: Request, username: str = Form(...)):
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    
    try:
        contact = ContactModify(username=username)
        is_added = contacts_service.add_contact_to_user(contact, user)
        if not is_added:
            return RedirectResponse("/users/contacts?error=Could not add contact", status_code=302)
        return RedirectResponse("/users/contacts?success=Contact added successfully", status_code=302)
    
    except contacts_service.ContactsService_ContactNotFoundError:
        return RedirectResponse("/users/contacts?error=User not found", status_code=302)
    
    except contacts_service.ContactsService_ContactAlreadyAddedError:
        return RedirectResponse("/users/contacts?error=Contact already added", status_code=302)
    
    except contacts_service.ContactsService_ContactSameAsUserError:
        return RedirectResponse("/users/contacts?error=Cannot add yourself as a contact", status_code=302)
    
    except:
        print(traceback.format_exc())
        return RedirectResponse("/users/contacts?error=An error occurred", status_code=302)

@web_contacts_router.post('/remove')
def remove_contact(request: Request, username: str = Form(...)):
    user = authenticate.get_user_if_token(request)
    if not user:
        return RedirectResponse("/users/login", status_code=302)
    
    try:
        contact = ContactModify(username=username)
        is_removed = contacts_service.remove_contact_from_user(contact, user)
        if not is_removed:
            return RedirectResponse("/users/contacts?error=Contact not found in your contacts list", status_code=302)
        return RedirectResponse("/users/contacts?success=Contact removed successfully", status_code=302)
    
    except contacts_service.ContactsService_ContactNotFoundError:
        return RedirectResponse("/users/contacts?error=User not found", status_code=302)
    
    except:
        print(traceback.format_exc())
        return RedirectResponse("/users/contacts?error=An error occurred", status_code=302)