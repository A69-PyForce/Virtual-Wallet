import traceback
from data.models import *
from fastapi import APIRouter, Header
from utils.user_auth_token_utils import *
from common import responses, authenticate
from utils.regex_verifictaion_utils import *
import services.contacts_service as contacts_service

api_contacts_router = APIRouter(prefix='/api/users/contacts')

@api_contacts_router.get(path="")
def get_all_contacts_for_user(u_token = Header(), page: int = 1, page_size: int = 10):
    user = authenticate.get_user_or_raise_401(u_token)
    return contacts_service.get_all_contacts_for_user(user, page, page_size)

@api_contacts_router.put(path="")
def add_contact_to_user(contact: ContactModify, u_token = Header()):
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        is_added = contacts_service.add_contact_to_user(contact, user)
        if not is_added: # not too sure about this confict response here
            return responses.Conflict(f"Could not add contact '{contact.username}', a conflict occurred.")
        return responses.OK(f"Contact with '{contact.username}' was added.")
    
    except contacts_service.ContactsService_ContactNotFoundError:
        return responses.BadRequest(f"Contact with '{contact.username}' not found.")
    
    except contacts_service.ContactsService_ContactAlreadyAddedError:
        return responses.BadRequest(f"Contact with '{contact.username}' already added.")
    
    except contacts_service.ContactsService_ContactSameAsUserError:
        return responses.BadRequest("Cannot add yourself as a contact.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
    
@api_contacts_router.delete(path="")
def remove_contact_from_user(contact: ContactModify, u_token = Header()):
    user = authenticate.get_user_or_raise_401(u_token)
    
    try:
        is_deleted = contacts_service.remove_contact_from_user(contact, user)
        if not is_deleted:
            return responses.NotFound(f"Contact '{contact.username}' wasn't associated with the user.")
        return responses.OK(f"Contact with '{contact.username}' was removed.")
    
    except contacts_service.ContactsService_ContactNotFoundError:
        return responses.BadRequest(f"Contact with '{contact.username}' not found.")
    
    except:
        print(traceback.format_exc())
        return responses.InternalServerError()
        