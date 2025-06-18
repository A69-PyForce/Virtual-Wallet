import unittest
from unittest.mock import patch
from pydantic import ValidationError
import services.currencies_service as service

class CurrenciesServiceShould(unittest.TestCase):

    @patch('services.currencies_service.insert_query')
    def test_add_currency_success(self, mock_insert):
        mock_insert.return_value = 10
        currency = service.CurrencyInfo(code="USD", name="United States Dollar")
        result = service.add_currency(currency)
        self.assertEqual(result, 10)
        mock_insert.assert_called_once_with(
            sql="INSERT INTO Currencies (code, name) VALUES (?, ?)",
            sql_params=("USD", "United States Dollar",)
        )

    def test_currencyinfo_validation_code_length(self):
        with self.assertRaises(ValidationError):
            service.CurrencyInfo(code="US", name="Short Code")

    def test_currencyinfo_validation_name_length(self):
        with self.assertRaises(ValidationError):
            service.CurrencyInfo(code="EUR", name="")

if __name__ == '__main__':
    unittest.main()
