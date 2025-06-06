from data.models import RecurringCreate, UserFromDB, RecurringOut
from data.database import insert_query, read_query, update_query


def create_recurring_for_user(data: RecurringCreate, user: UserFromDB) -> int:
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