from datetime import datetime

from data.models import TransactionOut, TransactionCreate, UserFromDB, TransactionFilterParams, \
    UserTransactionsResponse, TransactionTemplate
from data.database import read_query, insert_query, update_query
from services.users_service import get_user_by_username
from utils import currencies_utils
from utils.currencies_utils import get_currency_code_by_user_id


class TransactionServiceError(Exception):
    pass

class TransactionServiceInsufficientFunds(TransactionServiceError):
    pass

class TransactionServiceUserNotFound(TransactionServiceError):
    pass

class TransactionServiceCurrencyNotFound(TransactionServiceError):
    pass

def get_transactions_for_user(user_id: int, limit: int | None = None) -> UserTransactionsResponse:
    sql = """
        SELECT t.id, t.name, t.description, t.sender_id, t.receiver_id,
               t.amount, c.code, t.category_id, t.is_accepted, t.is_recurring, t.created_at, 
               t.original_amount, t.original_currency_code
        FROM Transactions AS t
        JOIN Currencies AS c ON t.currency_id = c.id
        WHERE t.sender_id = ? OR t.receiver_id = ?
        ORDER BY t.id DESC
    """
    sql_params = [user_id, user_id]
    if limit:
        sql += " LIMIT ?"
        sql_params.append(limit)
        
    rows = read_query(sql=sql, sql_params=sql_params)
    return UserTransactionsResponse(transactions=[TransactionOut.from_query(row) for row in rows])

async def create_transaction(data: TransactionCreate, sender: UserFromDB) -> int:
    receiver = get_user_by_username(data.receiver_username)
    #Check recipient
    if sender.is_blocked:
        raise TransactionServiceError("Blocked users cannot make transactions.")

    if not receiver:
        raise TransactionServiceUserNotFound("Receiver not found.")

    if sender.id == receiver.id:
        raise TransactionServiceError("Cannot send money to yourself.")

    if sender.balance < data.amount:
        raise TransactionServiceInsufficientFunds("Insufficient funds.")

    if data.amount <= 0:
        raise TransactionServiceError("Amount must be greater than zero.")
    #Check valid category
    check_cat = read_query("SELECT id FROM TransactionCategories WHERE id = ? AND user_id = ?",
                           (data.category_id, sender.id))
    if not check_cat:
        raise TransactionServiceError("Invalid or unauthorized category.")
    # Get the currencies from the base
    sender_currency = get_currency_code_by_user_id(sender.id)
    receiver_currency = get_currency_code_by_user_id(receiver.id)

    if not sender_currency or not receiver_currency:
        raise TransactionServiceError("Missing currency information for sender or receiver.")

    #Convert if necessary
    amount_to_store = data.amount
    if sender_currency != receiver_currency:
        amount_to_store = await currencies_utils.convert_currency(
            data.amount, sender_currency, receiver_currency
        )

    #blocking the amount
    update_sender = update_query("UPDATE Users SET balance = balance - ? WHERE id = ?", (data.amount, sender.id))
    if not update_sender:
        raise TransactionServiceError("Failed to deduct balance from sender.")
    # Get currency_id for recipient
    currency_id = read_query(
        "SELECT id FROM Currencies WHERE code = ?", (receiver_currency,))
    if not currency_id:
        raise TransactionServiceError("Receiver's currency not found.")
    currency_id = currency_id[0][0]

    sql = """INSERT INTO Transactions 
        (category_id, name, description, sender_id, receiver_id, amount, currency_id, is_accepted, 
        is_recurring, original_amount, original_currency_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)"""
    return insert_query(sql, (
        data.category_id, data.name, data.description,
        sender.id, receiver.id, amount_to_store,
        currency_id, data.is_recurring, data.amount, sender_currency
    ))

async def confirm_transaction(transaction_id: int, user: UserFromDB) -> bool:
    sql = """
        SELECT amount, currency_id, sender_id, receiver_id, is_accepted
        FROM Transactions WHERE id = ?
    """
    result = read_query(sql, (transaction_id,))
    if not result:
        return False

    amount, currency_id, sender_id, receiver_id, is_accepted = result[0]

    # validations
    if user.id != receiver_id or is_accepted:
        return False
    if sender_id == receiver_id:
        return False

    # approve transaction
    updated = update_query(
        "UPDATE Transactions SET is_accepted = 1 WHERE id = ?", (transaction_id,))
    if not updated:
        return False

    # get the currency code of the transaction

    tx_currency_result = read_query("SELECT code FROM Currencies WHERE id = ?", (currency_id,))
    if not tx_currency_result:
        return False
    tx_currency = tx_currency_result[0][0]

    user_currency = get_currency_code_by_user_id(receiver_id)
    if not user_currency:
        return False

    # convert if necessary
    final_amount = amount
    if tx_currency != user_currency:
        final_amount = await currencies_utils.convert_currency(
            amount, tx_currency, user_currency)

    return update_query("UPDATE Users SET balance = balance + ? WHERE id = ?",
        (final_amount, receiver_id))


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
               t.amount, c.code, t.category_id, t.is_accepted, t.is_recurring, t.created_at, 
               t.original_amount, t.original_currency_code
        FROM Transactions t
        JOIN Currencies c ON t.currency_id = c.id
        WHERE (t.sender_id = ? OR t.receiver_id = ?)
    """
    params = [user.id, user.id]
    #converting data
    if filters.start_date and isinstance(filters.start_date, str):
        filters.start_date = datetime.strptime(filters.start_date, '%Y-%m-%d').date()
    if filters.end_date and isinstance(filters.end_date, str):
        filters.end_date = datetime.strptime(filters.end_date, '%Y-%m-%d').date()

    if filters.start_date:
        query += " AND DATE(t.created_at) >= ?"
        params.append(filters.start_date)
    if filters.end_date:
        query += " AND DATE(t.created_at) <= ?"
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

async def create_transaction_from_recurring(template: TransactionTemplate) -> bool:
    if template.sender_id == template.receiver_id:
        print("[Recurring] Sender and receiver cannot be the same.")
        return False

    if template.amount <= 0:
        print("[Recurring] Amount must be greater than zero.")
        return False

    balance_check = read_query("SELECT balance FROM Users WHERE id = ?", (template.sender_id,))
    if not balance_check or balance_check[0][0] < template.amount:
        print(f"[Recurring] Sender {template.sender_id} has insufficient balance.")
        return False

    sender_currency = get_currency_code_by_user_id(template.sender_id)
    receiver_currency = get_currency_code_by_user_id(template.receiver_id)

    if not sender_currency or not receiver_currency:
        return False

    final_amount = template.amount
    if sender_currency != receiver_currency:
        final_amount = await currencies_utils.convert_currency(
            template.amount, sender_currency, receiver_currency
        )

    update_sender = update_query(
        "UPDATE Users SET balance = balance - ? WHERE id = ?",
        (template.amount, template.sender_id)
    )
    if not update_sender:
        print(f"[Recurring] Failed to deduct from sender {template.sender_id}.")
        return False

    currency_id = read_query("SELECT id FROM Currencies WHERE code = ?", (receiver_currency,))
    if not currency_id:
        return False
    currency_id = currency_id[0][0]

    insert_query("""
        INSERT INTO Transactions (
            category_id, name, description,
            sender_id, receiver_id, amount,
            currency_id, is_accepted, is_recurring, original_amount, original_currency_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
    """, (
        template.category_id, template.name, template.description,
        template.sender_id, template.receiver_id, final_amount,
        currency_id, template.amount, sender_currency
    ))

    print(f"[Recurring] Transaction created from {template.sender_id} to {template.receiver_id}.")
    return True
