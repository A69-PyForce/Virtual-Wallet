import unittest
from unittest.mock import patch
from data.models import TransactionCategoryOut, TransactionCategoryCreate
import services.transaction_categories_service as service

def fake_category(id=1, name="Food", image_url="img.jpg"):
    return TransactionCategoryOut(id=id, name=name, image_url=image_url)

class TransactionCategoriesServiceShould(unittest.TestCase):

    def test_get_all_categories_for_user_returns_categories(self):
        with patch('services.transaction_categories_service.read_query') as mock_query:
            mock_query.return_value = [
                (1, "Food", "img.jpg"),
                (2, "Transport", None)
            ]
            result = service.get_all_categories_for_user(1)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].name, "Food")

    def test_get_category_by_id_for_user_found_and_none(self):
        with patch('services.transaction_categories_service.read_query') as mock_query:
            mock_query.return_value = [(1, "Food", "img.jpg")]
            category = service.get_category_by_id_for_user(1, 1)
            self.assertIsInstance(category, TransactionCategoryOut)
            self.assertEqual(category.name, "Food")

            mock_query.return_value = []
            category = service.get_category_by_id_for_user(999, 1)
            self.assertIsNone(category)

    def test_create_category_for_user_returns_category(self):
        with patch('services.transaction_categories_service.insert_query') as mock_insert:
            mock_insert.return_value = 42
            cat_data = TransactionCategoryCreate(name="Food", image_url="img.jpg")
            result = service.create_category_for_user(cat_data, 1)
            self.assertIsInstance(result, TransactionCategoryOut)
            self.assertEqual(result.id, 42)
            self.assertEqual(result.name, "Food")

    def test_delete_category_for_user_success_and_fail(self):
        with patch('services.transaction_categories_service.update_query') as mock_update:
            mock_update.return_value = True
            self.assertTrue(service.delete_category_for_user(1, 1))
            mock_update.return_value = False
            self.assertFalse(service.delete_category_for_user(1, 1))

    def test_update_category_for_user_returns_updated_object(self):
        with patch('services.transaction_categories_service.update_query') as mock_update:
            mock_update.return_value = True
            cat_data = TransactionCategoryCreate(name="Updated", image_url="new.jpg")
            result = service.update_category_for_user(1, 1, cat_data)
            self.assertIsInstance(result, TransactionCategoryOut)
            self.assertEqual(result.name, "Updated")

    def test_change_category_image_url_success_and_fail(self):
        with patch('services.transaction_categories_service.insert_query') as mock_insert:
            mock_insert.return_value = 1
            self.assertTrue(service.change_category_image_url(1, "url.jpg"))
            mock_insert.return_value = 0
            self.assertFalse(service.change_category_image_url(1, "url.jpg"))

if __name__ == '__main__':
    unittest.main()
