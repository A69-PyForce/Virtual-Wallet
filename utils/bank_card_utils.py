import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.env_loader import BANK_CARDS_ENCRYPT_KEY
from data.models import BankCardEncryptInfo
from cryptography.fernet import Fernet
from datetime import datetime
import traceback

if not BANK_CARDS_ENCRYPT_KEY: raise ValueError("Bank Cards encryption key missing.")

# Create cipher used for encrypt/decrypt
cipher = Fernet(BANK_CARDS_ENCRYPT_KEY)

# Card data separator
_SEP = '|'
    
def encrypt_card_info(card: BankCardEncryptInfo) -> str | None:
    """
    Try to encrypt card details using AES-based encryption.
    
    Args:
        card (BankCardEncryptInfo): The card information.
        
    Returns:
        str|None: The encrypted string if successful or None if error occured during encryption
    """
    try:
        # String with | used for separating the values
        card_data = f"{card.number}{_SEP}{card.expiration_date}{_SEP}{card.card_holder}{_SEP}{card.check_number}"
        encrypted_data = cipher.encrypt(card_data.encode('utf-8'))
        return encrypted_data.decode('utf-8')
    except:
        print(traceback.format_exc())
        return None

def decrypt_card_info(encrypted_card: str) -> BankCardEncryptInfo | None:
    """
    Try to decrypt a encrypted card details back to a BankCardEncryptInfo object.
    
    Args:
        encrypted_card (str): The encrypted card information.
        
    Returns:
        BankCardEncryptInfo|None: The decrypted BankCardEncryptInfo object or None if error occured during decryption.
    """
    try:
        decrypted_data = cipher.decrypt(encrypted_card.encode('utf-8')).decode('utf-8')
        number, expiration_date, card_holder, check_number = decrypted_data.split(_SEP)
        return BankCardEncryptInfo(
            number=number, expiration_date=expiration_date,
            card_holder=card_holder, check_number=check_number
        )
    except:
        print(traceback.format_exc())
        return None

if __name__ == "__main__": # Run some tests for the functions in here if file is run as main
    
    date = datetime.now().strftime(format="%m/%y") # Formats to MM/YY
    card = BankCardEncryptInfo(number="4321876509871234", expiration_date=date, card_holder="E. HADZHIVASILEV", check_number="123")
    print(f"Original card info: {card}")

    encrypted_card = encrypt_card_info(card)
    print(f"Encrypted card info: {encrypted_card}")

    decrypted_card = decrypt_card_info(encrypted_card)
    print(f"Decrypted card info: {decrypted_card}")