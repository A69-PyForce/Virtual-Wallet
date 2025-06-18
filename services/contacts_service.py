from mariadb import IntegrityError
from data.database import *
from data.models import *
from data.models import ListContacts

class ContactsService_Error(BaseException):
    """
    Base exception class for all ContactsService errors.
    """
    pass

class ContactsService_ContactNotFoundError(ContactsService_Error):
    """
    Raised when a contact user is not found in the system.
    """
    pass

class ContactsService_ContactAlreadyAddedError(ContactsService_Error):
    """
    Raised when attempting to add a contact that is already in user's contact list.
    """
    pass

class ContactsService_ContactSameAsUserError(ContactsService_Error):
    """
    Raised when attempting to add oneself as a contact.
    """
    pass

def add_contact_to_user(contact: ContactModify, user: UserFromDB):
    """
    Add a new contact to a user's contact list.

    Looks up the contact user by username and inserts a relation into UserContacts.
    Prevents adding oneself or duplicate contacts.

    Args:
        contact (ContactModify): The contact to add.
        user (UserFromDB): The authenticated user adding the contact.

    Returns:
        bool: True if contact was successfully added, False otherwise.

    Raises:
        ContactsService_ContactNotFoundError: If contact username is not found.
        ContactsService_ContactSameAsUserError: If user tries to add themselves.
        ContactsService_ContactAlreadyAddedError: If contact already exists.
    """
    
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
         # insert_query returns None when the insert happened for some reason.
        return insert_query(sql=sql, sql_params=(user.id, contact_id,)) is None
    
    # Integrety error raise means contact is already added
    except IntegrityError:
        raise ContactsService_ContactAlreadyAddedError(f"Contact with '{contact.username}' already added.")
    
def remove_contact_from_user(contact: ContactModify, user: UserFromDB):
    """
    Remove a contact from a user's contact list.

    Looks up the contact user by username and deletes the relation from UserContacts.

    Args:
        contact (ContactModify): The contact to remove.
        user (UserFromDB): The authenticated user performing the removal.

    Returns:
        bool: True if contact was successfully removed.

    Raises:
        ContactsService_ContactNotFoundError: If contact username is not found.
    """
    
    # Query to find the contact id from the username
    sql = "SELECT id FROM Users WHERE username = ?"
    contact_id = read_query(sql=sql, sql_params=(contact.username,))
    if not contact_id:
        raise ContactsService_ContactNotFoundError(f"Contact with '{contact.username}' not found.")
    contact_id = contact_id[0][0]
    
    # Query to delete the entry where the ids match up
    sql = "DELETE FROM UserContacts WHERE user_id = ? AND contact_id = ?"
     # insert_query returns None when the insert happened for some reason.
    return insert_query(sql=sql, sql_params=(user.id, contact_id,)) is None

def get_contacts_list_for_user(user: UserFromDB) -> list[ContactInfo]:
    """
    Retrieve all contacts for a user (non-paginated version).

    Args:
        user (UserFromDB): The authenticated user.

    Returns:
        list[ContactInfo]: List of all contacts associated with the user.
    """
    sql = """SELECT u.id, u.username, u.email, u.avatar_url 
    FROM Users AS u JOIN UserContacts 
    AS uc WHERE u.id = uc.contact_id 
    AND user_id = ? 
    ORDER BY u.username"""
    
    contacts = []
    data = read_query(sql=sql, sql_params=(user.id,))
    for row in data:
        contacts.append(ContactInfo(id=row[0], username=row[1], email=row[2], avatar_url=row[3]))
    return contacts

def get_all_contacts_for_user(user: UserFromDB, page: int = 1, page_size: int = 10) -> ListContacts:
    """
    Retrieve all contacts for a user with pagination.

    Args:
        user (UserFromDB): The authenticated user.
        page (int, optional): Page number for pagination. Defaults to 1.
        page_size (int, optional): Number of contacts per page. Defaults to 10.

    Returns:
        ListContacts: Paginated contact list, including metadata (total count, total pages, etc).
    """
    # First get total count for pagination
    count_sql = """SELECT COUNT(*) 
                  FROM Users AS u JOIN UserContacts AS uc
                  WHERE u.id = uc.contact_id 
                  AND user_id = ?"""
    total_count = read_query(sql=count_sql, sql_params=(user.id,))[0][0]
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query to get paginated contacts with id, username and avatar_url
    sql = """SELECT u.id, u.username, u.email, u.avatar_url
             FROM Users AS u JOIN UserContacts AS uc
             WHERE u.id = uc.contact_id 
             AND user_id = ?
             ORDER BY u.username
             LIMIT ? OFFSET ?"""
             
    contacts_data = read_query(sql=sql, sql_params=(user.id, page_size, offset))
    contacts_list = []
    for row in contacts_data:
        contacts_list.append(ContactInfo(id=row[0], username=row[1], email=row[2], avatar_url=row[3]))
    
    total_pages = (total_count + page_size - 1) // page_size
    return ListContacts(
        contacts=contacts_list,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        page=page,
        page_size=page_size
    )

    