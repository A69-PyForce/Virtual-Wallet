from data.database import read_query, insert_query, update_query
from data.models import TransactionCategoryOut, TransactionCategoryCreate

def get_all_categories_for_user(user_id: int) -> list[TransactionCategoryOut]:
    """
    Retrieve all transaction categories for a given user.

    Only returns categories that are not marked as deleted.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list[TransactionCategoryOut]: List of the user's active transaction categories.
    """
    sql = """SELECT id, name, image_url
             FROM TransactionCategories
             WHERE user_id = ? AND is_deleted = 0"""
    rows = read_query(sql, (user_id,))
    return [TransactionCategoryOut.from_query(row) for row in rows]

def get_category_by_id_for_user(category_id: int, user_id: int) -> TransactionCategoryOut | None:
    """
    Retrieve a specific transaction category by its ID for a given user.

    Only returns the category if it exists and is not marked as deleted.

    Args:
        category_id (int): The ID of the category.
        user_id (int): The ID of the user.

    Returns:
        TransactionCategoryOut | None: The category data if found, otherwise None.
    """
    sql = """
        SELECT id, name, image_url
          FROM TransactionCategories
         WHERE id = ? AND user_id = ? AND is_deleted = 0"""
    rows = read_query(sql, (category_id, user_id))
    if not rows:
        return None
    return TransactionCategoryOut.from_query(rows[0])


def create_category_for_user(category: TransactionCategoryCreate, user_id: int):
    """
    Create a new transaction category for a user.

    Args:
        category (TransactionCategoryCreate): The data for the new category.
        user_id (int): The ID of the user.

    Returns:
        TransactionCategoryOut: The newly created category object.
    """
    sql = """
        INSERT INTO TransactionCategories (user_id, name, image_url)
        VALUES (?, ?, ?)
    """
    category_id = insert_query(sql, (user_id, category.name, category.image_url))
    return TransactionCategoryOut(id=category_id, name=category.name, image_url=category.image_url)


def delete_category_for_user(category_id: int, user_id: int) -> bool:
    """
    Soft-delete a transaction category for a user.

    Marks the category as deleted without removing it from the database.

    Args:
        category_id (int): The ID of the category to delete.
        user_id (int): The ID of the user.

    Returns:
        bool: True if the update was successful.
    """
    sql = "UPDATE TransactionCategories SET is_deleted = 1 WHERE id = ? AND user_id = ?"
    return update_query(sql, (category_id, user_id))


def update_category_for_user(category_id: int, user_id: int,
                             category_data: TransactionCategoryCreate) -> TransactionCategoryOut | None:
    """
    Update a transaction category for a user.

    Args:
        category_id (int): The ID of the category to update.
        user_id (int): The ID of the user.
        category_data (TransactionCategoryCreate): The new category data.

    Returns:
        TransactionCategoryOut | None: The updated category object.
    """
    sql = """
        UPDATE TransactionCategories
        SET name = ?, image_url = ?
        WHERE id = ? AND user_id = ?
    """
    update_query(sql, (category_data.name, category_data.image_url, category_id, user_id))

    return TransactionCategoryOut(id=category_id, name=category_data.name, image_url=category_data.image_url)

def change_category_image_url(category_id: int, avatar_url: str) -> bool:
    """
    Update the image URL of a transaction category.

    Args:
        category_id (int): The ID of the category.
        avatar_url (str): The new image URL to assign.

    Returns:
        bool: True if the update was successful.
    """
    
    # Query to do the thingie 
    sql = "UPDATE TransactionCategories SET image_url = ? WHERE id = ?"
    return insert_query(sql=sql, sql_params=(avatar_url, category_id,)) != 0