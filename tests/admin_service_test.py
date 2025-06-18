import unittest
from unittest.mock import patch
from data.models import UserSummary, UserFilterParams, AdminTransactionFilterParams, AdminTransactionOut
import services.admin_service as service

def fake_user_summary(id=1, username="user", email="test@test.com", phone_number="1234567890",
                      is_blocked=0, is_verified=0, is_admin=0, created_at="2024-01-01", avatar_url=None):
    return UserSummary(id=id, username=username, email=email, phone_number=phone_number,
                       is_blocked=is_blocked, is_verified=is_verified, is_admin=is_admin,
                       created_at=created_at, avatar_url=avatar_url)

def fake_transaction():
    return AdminTransactionOut(
        id=1, name="Payment", description="desc", sender_id=1, receiver_id=2, amount=100.0,
        currency_code="USD", category_id=1, is_accepted=0, is_recurring=0, created_at="2024-01-01",
        original_amount=100.0, original_currency_code="USD",
        sender_username="sender", receiver_username="receiver"
    )

class AdminServiceShould(unittest.TestCase):

    def test_get_all_users_returns_users(self):
        filters = UserFilterParams(is_verified=None, search=None, limit=10, offset=0)
        with patch('services.admin_service.read_query') as mock_query:
            mock_query.return_value = [
                (1, "user", "test@test.com", "1234567890", 0, 1, 0, "2024-01-01", None),
            ]
            result = service.get_all_users(filters)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].username, "user")

    def test_approve_user_success_and_fail(self):
        with patch('services.admin_service.update_query') as mock_update:
            mock_update.return_value = True
            self.assertTrue(service.approve_user(1))
            mock_update.return_value = False
            self.assertFalse(service.approve_user(1))

    def test_set_user_blocked_state(self):
        with patch('services.admin_service.update_query') as mock_update:
            mock_update.return_value = True
            self.assertTrue(service.set_user_blocked_state(1, True))
            mock_update.return_value = False
            self.assertFalse(service.set_user_blocked_state(1, False))

    def test_get_all_transactions_returns_transactions(self):
        filters = AdminTransactionFilterParams(
            start_date=None, end_date=None, direction=None, sender_id=None, receiver_id=None,
            user_id=None, sort_by="date", sort_order="asc", limit=10, offset=0
        )
        with patch('services.admin_service.read_query') as mock_query:
            mock_query.return_value = [
                (1, "Payment", "desc", 1, 2, 100.0, "USD", 1, 0, 0, "2024-01-01", 100.0, "USD", "sender", "receiver")
            ]
            result = service.get_all_transactions(filters)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].name, "Payment")

    def test_deny_transaction_success_and_fail(self):
        with patch('services.admin_service.read_query') as mock_read, \
             patch('services.admin_service.update_query') as mock_update:

            mock_read.return_value = []
            self.assertFalse(service.deny_transaction(1))

            mock_read.return_value = [(1, 100.0, 1)]
            self.assertFalse(service.deny_transaction(1))

            mock_read.return_value = [(1, 100.0, 0)]
            mock_update.side_effect = [True, True]
            self.assertTrue(service.deny_transaction(1))

            mock_update.side_effect = [False]
            self.assertFalse(service.deny_transaction(1))

    def test_count_users(self):
        filters = UserFilterParams(is_verified=None, search=None, limit=10, offset=0)
        with patch('services.admin_service.read_query') as mock_query:
            mock_query.return_value = [(5,)]
            result = service.count_users(filters)
            self.assertEqual(result, 5)

            mock_query.return_value = []
            result = service.count_users(filters)
            self.assertEqual(result, 0)

if __name__ == '__main__':
    unittest.main()
