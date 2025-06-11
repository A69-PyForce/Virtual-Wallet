from data.database import read_query, update_query
from data.models import UserSummary, UserFilterParams, AdminTransactionFilterParams, TransactionOut


def get_all_users(filters: UserFilterParams) -> list[UserSummary]:
    # Dummy true condition - dynamically add more conditions later without worrying about commas or the first AND
    sql = """
        SELECT id, username, email, phone_number, is_blocked, is_verified, is_admin
        FROM Users
        WHERE 1=1 

    """
    params = []

    if filters.is_verified is not None:
        sql += " AND is_verified = ?"
        params.append(int(filters.is_verified))

    if filters.search:
        sql += " AND (username LIKE ? OR email LIKE ? OR phone_number LIKE ?)"
        like_term = f"%{filters.search}%"
        params.extend([like_term, like_term, like_term])

    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([filters.limit, filters.offset])

    rows = read_query(sql, tuple(params))
    return [UserSummary.from_query(row) for row in rows]


def approve_user(user_id: int) -> bool:
    sql = "UPDATE Users SET is_verified = 1 WHERE id = ? AND is_verified = 0"
    return update_query(sql, (user_id,))

def set_user_blocked_state(user_id: int, blocked: bool) -> bool:
    sql = "UPDATE Users SET is_blocked = ? WHERE id = ?"
    return update_query(sql, (int(blocked), user_id))

def get_all_transactions(filters: AdminTransactionFilterParams) -> list[TransactionOut]:
    sql = """
        SELECT t.id, t.name, t.description, t.sender_id, t.receiver_id,
               t.amount, c.code, t.category_id, t.is_accepted, t.is_recurring, t.created_at
        FROM Transactions t
        JOIN Currencies c ON t.currency_id = c.id
        WHERE 1=1
    """
    params = []

    if filters.start_date:
        sql += " AND DATE(t.created_at) >= ?"
        params.append(filters.start_date)
    if filters.end_date:
        sql += " AND DATE(t.created_at) <= ?"
        params.append(filters.end_date)
    if filters.sender_id:
        sql += " AND t.sender_id = ?"
        params.append(filters.sender_id)
    if filters.receiver_id:
        sql += " AND t.receiver_id = ?"
        params.append(filters.receiver_id)
    if filters.direction == "incoming":
        sql += " AND t.receiver_id IS NOT NULL"
    elif filters.direction == "outgoing":
        sql += " AND t.sender_id IS NOT NULL"

    sort_column = "t.created_at" if filters.sort_by == "date" else "t.amount"
    sql += f" ORDER BY {sort_column} {filters.sort_order.upper()} LIMIT ? OFFSET ?"
    params += [filters.limit, filters.offset]

    rows = read_query(sql, tuple(params))
    return [TransactionOut.from_query(row) for row in rows]


def deny_transaction(transaction_id: int) -> bool:
    sql = """
        SELECT sender_id, amount, is_accepted
        FROM Transactions
        WHERE id = ?
    """
    result = read_query(sql, (transaction_id,))
    if not result:
        return False

    sender_id, amount, is_accepted = result[0]

    if is_accepted:
        return False

    update_sender = update_query("UPDATE Users SET balance = balance + ? WHERE id = ?",
                                 (amount, sender_id))

    if not update_sender:
        return False

    return update_query("DELETE FROM Transactions WHERE id = ?", (transaction_id,))