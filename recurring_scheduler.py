import asyncio
from datetime import datetime, timedelta
from data.database import read_query, update_query
from data.models import TransactionTemplate
from services.transactions_service import create_transaction_from_recurring

async def process_due_recurring():
    """
    Background worker that continuously processes due recurring transactions.

    - Queries for all recurring transactions where next_exec_date is due.
    - Creates new transactions based on stored templates.
    - Reschedules the next execution date based on the interval and type (DAYS, HOURS, MINUTES).
    - Sleeps for 30 seconds between each check cycle.

    Runs indefinitely as an asyncio task.
    """
    while True:
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

            template = TransactionTemplate(
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=amount,
                currency_id=currency_id,
                category_id=category_id,
                name=name,
                description=description
            )

            created = await create_transaction_from_recurring(template)

            if not created:
                print(f"Failed to execute recurring ID {recurring_id}")
                continue

            now = datetime.now()
            if interval_type == "DAYS":
                next_exec_date = now + timedelta(days=interval)
            elif interval_type == "HOURS":
                next_exec_date = now + timedelta(hours=interval)
            else:
                print(f"Invalid interval type: {interval_type}")
                continue

            # updates the next data
            now = datetime.now()
            if interval_type == "DAYS":
                next_exec_date = now + timedelta(days=interval)
            elif interval_type == "HOURS":
                next_exec_date = now + timedelta(hours=interval)
            elif interval_type == "MINUTES":
                next_exec_date = now + timedelta(minutes=interval)
            else:
                print(f"Invalid interval type: {interval_type}")
                continue

            # updates the next data
            update_query(
                "UPDATE Recurring SET next_exec_date = ? WHERE id = ?",
                (next_exec_date, recurring_id)
            )

            print(f"Recurring ID {recurring_id} executed and scheduled next.")

        print(f"Recurring check complete. Sleeping for 30 seconds.")
        await asyncio.sleep(30)