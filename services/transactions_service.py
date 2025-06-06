from data.database import read_query, insert_query, update_query
from data.models import TransactionOut, TransactionCreate, UserFromDB, TransactionFilterParams
from services.users_service import get_user_by_username


class TransactionServiceError(Exception):
    pass

class TransactionServiceUserNotFound(TransactionServiceError):
    pass

class TransactionServiceCurrencyNotFound(TransactionServiceError):
    pass

def get_transactions_for_user(user_id: int) -> list[TransactionOut]:
    sql = """
        SELECT t.id, t.name, t.description, t.sender_id, t.receiver_id,
               t.amount, c.code, t.category_id, t.is_accepted, t.is_recurring
        FROM Transactions AS t
        JOIN Currencies AS c ON t.currency_id = c.id
        WHERE t.sender_id = ? OR t.receiver_id = ?
        ORDER BY t.id DESC
    """
    rows = read_query(sql, (user_id, user_id))
    return [TransactionOut.from_query(row) for row in rows]

def create_transaction(data: TransactionCreate, sender: UserFromDB) -> int:
    receiver = get_user_by_username(data.receiver_username)
    if not receiver:
        raise TransactionServiceUserNotFound("Receiver not found.")

    if sender.balance < data.amount:
        raise TransactionServiceError("Insufficient funds.")

    #blocking the amount
    update_sender = update_query("UPDATE Users SET balance = balance - ? WHERE id = ?", (data.amount, sender.id))
    if not update_sender:
        raise TransactionServiceError("Failed to block funds from sender.")

    result = read_query("SELECT id FROM Currencies WHERE code = ?", (data.currency_code,))
    if not result:
        raise TransactionServiceCurrencyNotFound(f"Currency code '{data.currency_code}' not found.")
    currency_id = result[0][0]

    sql = """INSERT INTO Transactions 
        (category_id, name, description, sender_id, receiver_id, amount, currency_id, is_accepted, is_recurring)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)"""
    return insert_query(sql, (
        data.category_id, data.name, data.description,
        sender.id, receiver.id, data.amount,
        currency_id, data.is_recurring
    ))


def confirm_transaction(transaction_id: int, user: UserFromDB) -> bool:
    sql = """
        SELECT amount, currency_id, sender_id, receiver_id, is_accepted
        FROM Transactions WHERE id = ?
    """
    result = read_query(sql, (transaction_id,))
    if not result:
        return False

    amount, currency_id, sender_id, receiver_id, is_accepted = result[0]

    if user.id != receiver_id or is_accepted:
        return False

    updated = update_query(
        "UPDATE Transactions SET is_accepted = 1 WHERE id = ?", (transaction_id,))
    if not updated:
        return False

    update_receiver = update_query(
        "UPDATE Users SET balance = balance + ? WHERE id = ?", (amount, receiver_id,))

    return update_receiver


def decline_transaction(transaction_id: int, user: UserFromDB) -> bool:
    sql = """SELECT amount, sender_id, receiver_id, is_accepted FROM Transactions WHERE id = ?"""

    result = read_query(sql, (transaction_id,))
    if not result:
        return False

    amount, sender_id, receiver_id, is_accepted = result[0]

    if user.id != receiver_id or is_accepted:
        return False

    #refund the amount to the sender if it was declined from receiver
    refund_sender = update_query(
        "UPDATE Users SET balance = balance + ? WHERE id = ?",
        (amount, sender_id))

    if not refund_sender:
        return False

    delete_sql = "DELETE FROM Transactions WHERE id = ? AND receiver_id = ? AND is_accepted = 0"
    return update_query(delete_sql, (transaction_id, user.id))


def get_user_transaction_history(user: UserFromDB, filters: TransactionFilterParams) -> list[TransactionOut]:
    query = """
        SELECT t.id, t.name, t.description, t.sender_id, t.receiver_id,
               t.amount, c.code, t.category_id, t.is_accepted, t.is_recurring, t.id
        FROM Transactions t
        JOIN Currencies c ON t.currency_id = c.id
        WHERE (t.sender_id = ? OR t.receiver_id = ?)
    """
    params = [user.id, user.id]

    if filters.start_date:
        query += " AND DATE(t.id) >= ?"
        params.append(filters.start_date)
    if filters.end_date:
        query += " AND DATE(t.id) <= ?"
        params.append(filters.end_date)
    if filters.direction == "incoming":
        query += " AND t.receiver_id = ?"
        params.append(user.id)
    elif filters.direction == "outgoing":
        query += " AND t.sender_id = ?"
        params.append(user.id)
    if filters.category_id:
        query += " AND t.category_id = ?"
        params.append(filters.category_id)

    sort_column = "t.id" if filters.sort_by == "date" else "t.amount"
    query += f" ORDER BY {sort_column} {filters.sort_order.upper()}"

    query += " LIMIT ? OFFSET ?"
    params += [filters.limit, filters.offset]

    results = read_query(query, tuple(params))
    return [TransactionOut.from_query(row) for row in results]
