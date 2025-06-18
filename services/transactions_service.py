from datetime import datetime
from data.models import TransactionOut, TransactionCreate, UserFromDB, TransactionFilterParams, \
    UserTransactionsResponse, TransactionTemplate, ListTransactions, TransactionInfo
from data.database import read_query, insert_query, update_query
from services.users_service import get_user_by_username
from utils import currencies_utils
from utils.currencies_utils import get_currency_code_by_user_id


class TransactionServiceError(Exception):
    """
    Base exception class for all transaction service errors.
    """
    pass

class TransactionServiceInsufficientFunds(TransactionServiceError):
    """
    Raised when the sender does not have sufficient balance to perform the transaction.
    """
    pass

class TransactionServiceUserNotFound(TransactionServiceError):
    """
    Raised when the receiver user is not found in the system.
    """
    pass

class TransactionServiceCurrencyNotFound(TransactionServiceError):
    """
    Raised when currency information is missing or invalid.
    """
    pass

def get_transactions_for_user(user_id: int, limit: int | None = None) -> UserTransactionsResponse:
    """
    Retrieve all transactions (sent or received) for a user.

    Args:
        user_id (int): ID of the user.
        limit (int, optional): Optional limit on number of transactions returned.

    Returns:
        UserTransactionsResponse: List of transactions.
    """
    sql = """
        SELECT t.id, t.name, t.description, t.sender_id, t.receiver_id,
               t.amount, c.code, t.category_id, t.is_accepted, t.is_recurring, t.created_at, 
               t.original_amount, t.original_currency_code, tc.name AS category_name, u.username AS receiver_username
        FROM Transactions AS t
        JOIN TransactionCategories AS tc ON t.category_id = tc.id
        JOIN Users AS u ON t.receiver_id = u.id
        JOIN Currencies AS c ON t.currency_id = c.id
        WHERE t.sender_id = ? OR t.receiver_id = ?
        ORDER BY t.id DESC
    """
    sql_params = [user_id, user_id]
    if limit:
        sql += " LIMIT ?"
        sql_params.append(limit)
        
    rows = read_query(sql=sql, sql_params=tuple(sql_params))
    return UserTransactionsResponse(transactions=[TransactionOut.from_query(row) for row in rows])

async def create_transaction(data: TransactionCreate, sender: UserFromDB) -> int:
    """
    Create a new transaction between sender and receiver, handling validations and currency conversion.

    Args:
        data (TransactionCreate): Transaction details.
        sender (UserFromDB): The user initiating the transaction.

    Returns:
        int: ID of the newly created transaction.

    Raises:
        TransactionServiceError: For generic business logic errors.
        TransactionServiceUserNotFound: If receiver does not exist.
        TransactionServiceInsufficientFunds: If sender lacks sufficient funds.
        TransactionServiceCurrencyNotFound: If currency info is missing.
    """
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
    """
    Confirm (approve) a pending transaction by the receiver.

    Performs validation and updates balances.

    Args:
        transaction_id (int): ID of the transaction to confirm.
        user (UserFromDB): The receiver confirming the transaction.

    Returns:
        bool: True if confirmation succeeded.
    """
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


async def decline_transaction(transaction_id: int, user: UserFromDB) -> bool:
    """
    Decline a pending transaction by the receiver and refund sender.

    Args:
        transaction_id (int): ID of the transaction to decline.
        user (UserFromDB): The receiver declining the transaction.

    Returns:
        bool: True if decline and refund succeeded.
    """
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

    delete_sql = "UPDATE Transactions SET is_accepted = -1 WHERE id = ? AND receiver_id = ? AND is_accepted = 0"
    return update_query(delete_sql, (transaction_id, user.id))


def get_user_transaction_history(user: UserFromDB, filters: TransactionFilterParams) -> ListTransactions:
    """
    Retrieve transaction history for a user with full filtering, sorting and pagination support.

    Args:
        user (UserFromDB): The authenticated user.
        filters (TransactionFilterParams): Filtering and pagination parameters.

    Returns:
        ListTransactions: Paginated and filtered list of transactions.
    """
    base_query = """
        FROM Transactions t
        JOIN TransactionCategories tc ON t.category_id = tc.id
        JOIN Users s ON t.sender_id = s.id
        JOIN Users r ON t.receiver_id = r.id
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
        base_query += " AND DATE(t.created_at) >= ?"
        params.append(filters.start_date)
    if filters.end_date:
        base_query += " AND DATE(t.created_at) <= ?"
        params.append(filters.end_date)

    if filters.direction == "incoming":
        base_query += " AND t.receiver_id = ?"
        params.append(user.id)
    elif filters.direction == "outgoing":
        base_query += " AND t.sender_id = ?"
        params.append(user.id)

    if filters.category_id:
        base_query += " AND t.category_id = ?"
        params.append(filters.category_id)

    if filters.status:
        if filters.status == "pending":
            base_query += " AND t.is_accepted = 0"
        elif filters.status == "confirmed":
            base_query += " AND t.is_accepted = 1"
        elif filters.status == "declined":
            base_query += " AND t.is_accepted = -1"

    # Get total count
    count_query = f"SELECT COUNT(*) {base_query}"
    total_count = read_query(count_query, tuple(params))[0][0]

    page_size = filters.limit or 30
    total_pages = (total_count + page_size - 1) // page_size
    
    # Ensure page is within valid range
    current_page = filters.offset // page_size + 1 if filters.offset else 1
    if current_page > total_pages:
        current_page = total_pages
    if current_page < 1:
        current_page = 1
        
    offset = (current_page - 1) * page_size

    # Sorting (safe against SQL injection)
    if filters.sort_by not in ("date", "amount", "name"):
        sort_column = "t.created_at"
    else:
        sort_column = {
            "date": "t.created_at",
            "amount": "t.amount",
            "name": "t.name"
        }[filters.sort_by]
    sort_order = filters.sort_order.upper() if (filters.sort_order and filters.sort_order.upper()
                                                in ("ASC", "DESC")) else "DESC"
    # Main query for transactions
    query = f"""
        SELECT 
            t.id, t.name, t.description, t.sender_id, t.receiver_id,
            t.amount, c.code, t.category_id, t.is_accepted, t.is_recurring, t.created_at,
            t.original_amount, t.original_currency_code, tc.name AS category_name,
            s.username AS sender_username, r.username AS receiver_username,
            tc.image_url AS category_image_url
        {base_query}
        ORDER BY {sort_column} {sort_order}
        LIMIT ? OFFSET ?
    """
    params += [page_size, offset]

    results = read_query(query, tuple(params))
    transactions = [TransactionInfo.from_query(row) for row in results]
    
    return ListTransactions(
        transactions=transactions,
        total_count=total_count,
        total_pages=total_pages,
        current_page=current_page,
        page=current_page,
        page_size=page_size
    )

async def create_transaction_from_recurring(template: TransactionTemplate) -> bool:
    """
    Create a transaction based on a recurring transaction template.

    Performs validations and handles currency conversion.

    Args:
        template (TransactionTemplate): Recurring transaction template.

    Returns:
        bool: True if transaction creation succeeded.
    """
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

def get_transaction_by_id(transaction_id: int, user: UserFromDB) -> TransactionInfo | None:
    """
    Retrieve a single transaction by ID, ensuring the user has permission to view it.

    Args:
        transaction_id (int): ID of the transaction.
        user (UserFromDB): The user requesting the transaction data.

    Returns:
        TransactionInfo | None: Transaction info if found, otherwise None.
    """
    sql = """
        SELECT 
            t.id, t.name, t.description, t.sender_id, t.receiver_id,
            t.amount, c.code, t.category_id, t.is_accepted, t.is_recurring, t.created_at,
            t.original_amount, t.original_currency_code, tc.name AS category_name,
            s.username AS sender_username, r.username AS receiver_username,
            tc.image_url AS category_image_url
        FROM Transactions t
        JOIN TransactionCategories tc ON t.category_id = tc.id
        JOIN Users s ON t.sender_id = s.id
        JOIN Users r ON t.receiver_id = r.id
        JOIN Currencies c ON t.currency_id = c.id
        WHERE t.id = ? AND (t.sender_id = ? OR t.receiver_id = ?)
    """
    result = read_query(sql, (transaction_id, user.id, user.id))
    if not result:
        return None
    return TransactionInfo.from_query(result[0])
