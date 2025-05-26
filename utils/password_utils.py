import traceback
import hashlib
import bcrypt
import base64

def hash_password(password: str) -> str | None:
    """
    Try to securely hash a password using SHA-256 and bcrypt.

    Args:
        password (str): The plain text password.

    Returns:
        str|None: The bcrypt-hashed password, encoded as a 60-character string or None if operation failed.
    """
    try:
        return bcrypt.hashpw(
            base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest()),
            bcrypt.gensalt()
        )
    except:
        print(traceback.format_exc())
        return None
    
def check_password(password: str, hashed_password: str) -> bool:
    """
    Check if a given password matches a password hash from database. \n
    Used for User authentication.

    Args:
        password (str): The plain text password.
        hashed_password (str): The hashed password from the database.

    Returns:
        bool: True if passwords match, False if not or operation failed.
    """
    try:
        return bcrypt.checkpw(
            password=base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest()),
            hashed_password=hashed_password
        )
    except:
        print(traceback.format_exc())
        return False
    
if __name__ == "__main__": # Run some tests for the functions in here if file is run as main

    # Multipliers to check if password hash is constant lenght
    PASSWORD = "Emko2004!" # * 100_000_000
    CHECK_WITH = "Emko2004!" # * 100_000_000

    hash = hash_password(PASSWORD)
    print(f"Password hash: {hash}")
    print(f"Is password correct: {check_password(CHECK_WITH, hash)}")