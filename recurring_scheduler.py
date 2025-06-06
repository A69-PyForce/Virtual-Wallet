from threading import Timer
from datetime import datetime
from data.database import read_query, update_query
from services.transactions_service import create_transaction_from_recurring

def process_due_recurring():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for due recurring...")

    sql = """
        SELECT r.id, r.transaction_id, r.interval, r.interval_type,
               t.category_id, t.name, t.description,
               t.sender_id, t.receiver_id, t.amount, t.currency_id
        FROM Recurring r
        JOIN Transactions t ON r.transaction_id = t.id
        WHERE r.next_exec_date <= NOW()
    """

    due = read_query(sql)

    for row in due:
        (recurring_id, transaction_id, interval, interval_type,
         category_id, name, description,
         sender_id, receiver_id, amount, currency_id) = row

        print(f"Executing recurring ID {recurring_id} (Tx from {sender_id} to {receiver_id})")

        created = create_transaction_from_recurring(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=amount,
            currency_id=currency_id,
            category_id=category_id,
            name=name,
            description=description
        )

        if not created:
            print(f"Failed to execute recurring ID {recurring_id}")
            continue

        # updates the next data
        update_query(
            f"UPDATE Recurring SET next_exec_date = DATE_ADD(next_exec_date, INTERVAL {interval} {interval_type}) WHERE id = ?",
            (recurring_id,)
        )

        print(f"Recurring ID {recurring_id} executed and scheduled next.")

    # resets the timer (checks on every 30 sec)
    Timer(30.0, process_due_recurring).start()