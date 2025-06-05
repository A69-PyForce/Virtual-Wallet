from mariadb import IntegrityError
from data.database import *
from data.models import *

class ContactsService_Error(BaseException):
    pass

class ContactsService_ContactNotFoundError(ContactsService_Error):
    pass

class ContactsService_ContactAlreadyAddedError(ContactsService_Error):
    pass

class ContactsService_ContactSameAsUserError(ContactsService_Error):
    pass

def add_contact_to_user(contact: ContactInfo, user: UserFromDB):
    
    # Query to find the contact id from the username
    sql = "SELECT id FROM Users WHERE username = ?"
    contact_id = read_query(sql=sql, sql_params=(contact.username,))
    if not contact_id:
        raise ContactsService_ContactNotFoundError(f"Contact with '{contact.username}' not found.")
    contact_id = contact_id[0][0]
    
    # Check if contact_id is the same as user.id
    if contact_id == user.id:
        raise ContactsService_ContactSameAsUserError("Cannot add yourself as a contact.")
    
    try:
        # Query to add the found contact id as a new entry in UserContacts along with the user's id
        sql = "INSERT INTO UserContacts (user_id, contact_id) VALUES (?, ?)"
        return insert_query(sql=sql, sql_params=(user.id, contact_id,)) is not None
    
    # Integrety error raise means contact is already added
    except IntegrityError:
        raise ContactsService_ContactAlreadyAddedError(f"Contact with '{contact.username}' already added.")
    
def remove_contact_from_user(contact: ContactInfo, user: UserFromDB):
    
    # Query to find the contact id from the username
    sql = "SELECT id FROM Users WHERE username = ?"
    contact_id = read_query(sql=sql, sql_params=(contact.username,))
    if not contact_id:
        raise ContactsService_ContactNotFoundError(f"Contact with '{contact.username}' not found.")
    contact_id = contact_id[0][0]
    
    # Query to delete the entry where the ids match up
    sql = "DELETE FROM UserContacts WHERE user_id = ? AND contact_id = ?"
    return insert_query(sql=sql, sql_params=(user.id, contact_id,)) is not None
        

    