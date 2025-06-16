from data.database import read_query, insert_query, update_query
from data.models import TransactionCategoryOut, TransactionCategoryCreate


def get_all_categories_for_user(user_id: int) -> list[TransactionCategoryOut]:
    sql = """SELECT id, name, image_url
             FROM TransactionCategories
             WHERE user_id = ?"""
    rows = read_query(sql, (user_id,))
    return [TransactionCategoryOut.from_query(row) for row in rows]

def get_category_by_id_for_user(category_id: int, user_id: int) -> TransactionCategoryOut | None:
    sql = """
        SELECT id, name, image_url
          FROM TransactionCategories
         WHERE id = ? AND user_id = ?
    """
    rows = read_query(sql, (category_id, user_id))
    if not rows:
        return None
    return TransactionCategoryOut.from_query(rows[0])


def create_category_for_user(category: TransactionCategoryCreate, user_id: int):
    sql = """
        INSERT INTO TransactionCategories (user_id, name, image_url)
        VALUES (?, ?, ?)
    """
    category_id = insert_query(sql, (user_id, category.name, category.image_url))
    return TransactionCategoryOut(id=category_id, name=category.name, image_url=category.image_url)


def delete_category_for_user(category_id: int, user_id: int) -> bool:
    sql = "DELETE FROM TransactionCategories WHERE id = ? AND user_id = ?"
    return update_query(sql, (category_id, user_id))


def update_category_for_user(category_id: int, user_id: int,
                             category_data: TransactionCategoryCreate) -> TransactionCategoryOut | None:
    sql = """
        UPDATE TransactionCategories
        SET name = ?, image_url = ?
        WHERE id = ? AND user_id = ?
    """
    update_query(sql, (category_data.name, category_data.image_url, category_id, user_id))

    return TransactionCategoryOut(id=category_id, name=category_data.name, image_url=category_data.image_url)