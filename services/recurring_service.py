from data.models import RecurringCreate, UserFromDB, RecurringOut
from data.database import insert_query, read_query, update_query


def create_recurring_for_user(data: RecurringCreate, user: UserFromDB) -> int:
    """
    Create a recurring rule for a user's transaction.

    This function verifies that the provided transaction belongs to the user.
    It also ensures that there is no existing recurring rule for the given transaction.
    If validations pass, it inserts a new recurring rule into the database.

    Args:
        data (RecurringCreate): The recurring rule data to create, including transaction ID, interval, interval type, and next execution date.
        user (UserFromDB): The authenticated user object performing the operation.

    Returns:
        int: The ID of the newly inserted recurring rule.

    Raises:
        Exception: If the transaction does not belong to the user or if a recurring rule for the transaction already exists.
    """
    ownership_check = read_query(
        "SELECT id FROM Transactions WHERE id = ? AND sender_id = ?",
        (data.transaction_id, user.id))

    if not ownership_check:
        raise Exception("You can only create recurring for your own transactions.")

    exists = read_query("SELECT id FROM Recurring WHERE transaction_id = ?", (data.transaction_id,))
    if exists:
        raise Exception("Recurring rule for this transaction already exists.")

    sql = """
        INSERT INTO Recurring (transaction_id, `interval`, interval_type, next_exec_date)
        VALUES (?, ?, ?, ?)
    """
    return insert_query(sql, (
        data.transaction_id,
        data.interval,
        data.interval_type,
        data.next_exec_date))

def get_recurring_by_user(user_id: int) -> list[RecurringOut]:
    """
    Retrieve all recurring rules for a specific user.

    The function returns a list of recurring rules where the user is the sender of the associated transaction.

    Args:
        user_id (int): The ID of the user whose recurring rules are to be retrieved.

    Returns:
        list[RecurringOut]: A list of recurring rule objects for the user.
    """
    sql = """
        SELECT r.id, r.transaction_id, r.`interval`, r.interval_type, r.next_exec_date
        FROM Recurring r
        JOIN Transactions t ON r.transaction_id = t.id
        WHERE t.sender_id = ?
        ORDER BY r.next_exec_date ASC
    """
    rows = read_query(sql, (user_id,))
    return [RecurringOut.from_query(row) for row in rows]


def delete_recurring(recurring_id: int, user: UserFromDB) -> bool:
    """
    Delete a recurring rule if it belongs to the user.

    The function verifies that the recurring rule exists and is linked to a transaction owned by the user.
    If validation passes, it deletes the recurring rule.

    Args:
        recurring_id (int): The ID of the recurring rule to delete.
        user (UserFromDB): The authenticated user attempting the deletion.

    Returns:
        bool: True if the deletion was successful, False if the recurring rule does not exist or does not belong to the user.
    """
    sql = """
        SELECT r.id
        FROM Recurring r
        JOIN Transactions t ON r.transaction_id = t.id
        WHERE r.id = ? AND t.sender_id = ?
    """
    result = read_query(sql, (recurring_id, user.id))
    if not result:
        return False

    delete_sql = "DELETE FROM Recurring WHERE id = ?"
    return update_query(delete_sql, (recurring_id,))