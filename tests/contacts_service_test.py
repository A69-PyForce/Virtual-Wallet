import unittest
from datetime import datetime
from unittest.mock import patch
from mariadb import IntegrityError
from data.models import ContactModify, UserFromDB, ContactInfo, ListContacts
import services.contacts_service as service

def fake_user():
    return UserFromDB(
        id=1,
        username="alice",
        email="alice@example.com",
        phone_number="1234567890",
        password_hash="hash",
        is_admin=0,
        is_blocked=0,
        is_verified=1,
        balance=0,
        currency_code="USD",
        created_at=datetime.utcnow(),
        avatar_url="avatar.jpg"
    )

class ContactsServiceShould(unittest.TestCase):

    def setUp(self):
        self.user = fake_user()
        self.contact = ContactModify(username="bob")

    @patch('services.contacts_service.read_query')
    @patch('services.contacts_service.insert_query')
    def test_add_contact_success(self, mock_insert, mock_read):
        mock_read.return_value = [(2,)]
        mock_insert.return_value = None
        result = service.add_contact_to_user(self.contact, self.user)
        self.assertTrue(result)

    @patch('services.contacts_service.read_query')
    def test_add_contact_not_found(self, mock_read):
        mock_read.return_value = []
        with self.assertRaises(service.ContactsService_ContactNotFoundError):
            service.add_contact_to_user(self.contact, self.user)

    @patch('services.contacts_service.read_query')
    def test_add_contact_same_as_user(self, mock_read):
        mock_read.return_value = [(self.user.id,)]
        with self.assertRaises(service.ContactsService_ContactSameAsUserError):
            service.add_contact_to_user(self.contact, self.user)

    @patch('services.contacts_service.read_query')
    @patch('services.contacts_service.insert_query')
    def test_add_contact_duplicate(self, mock_insert, mock_read):
        mock_read.return_value = [(2,)]
        mock_insert.side_effect = IntegrityError
        with self.assertRaises(service.ContactsService_ContactAlreadyAddedError):
            service.add_contact_to_user(self.contact, self.user)

    @patch('services.contacts_service.read_query')
    @patch('services.contacts_service.insert_query')
    def test_remove_contact_success(self, mock_insert, mock_read):
        mock_read.return_value = [(2,)]
        mock_insert.return_value = None
        result = service.remove_contact_from_user(self.contact, self.user)
        self.assertTrue(result)

    @patch('services.contacts_service.read_query')
    def test_remove_contact_not_found(self, mock_read):
        mock_read.return_value = []
        with self.assertRaises(service.ContactsService_ContactNotFoundError):
            service.remove_contact_from_user(self.contact, self.user)

    @patch('services.contacts_service.read_query')
    def test_get_contacts_list_for_user(self, mock_read):
        mock_read.return_value = [
            (2, "bob", "bob@example.com", "b.jpg"),
            (3, "carol", "carol@example.com", None)
        ]
        result = service.get_contacts_list_for_user(self.user)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], ContactInfo)
        self.assertEqual(result[1].username, "carol")

    @patch('services.contacts_service.read_query')
    def test_get_all_contacts_for_user(self, mock_read):
        mock_read.side_effect = [ [(25,)],  # total_count
                                  [(i, f"u{i}", f"u{i}@ex.com", None) for i in range(1, 6)] ]
        result = service.get_all_contacts_for_user(self.user, page=2, page_size=5)
        self.assertIsInstance(result, ListContacts)
        self.assertEqual(result.current_page, 2)
        self.assertEqual(result.page_size, 5)
        self.assertEqual(result.total_count, 25)
        self.assertEqual(len(result.contacts), 5)

if __name__ == '__main__':
    unittest.main()
