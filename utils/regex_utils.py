import re

# At least 2 symbols and max 20, only upper and lowercase English letters and numbers.
USER_USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_]{2,20}$')

# At least 8 symbols and should contain capital letter, digit, and special symbol (!, +, -, *, &, ^, …). 
USER_PASSWORD_PATTERN = re.compile(r'^(?=.*[A-Z])(?=.*\d)(?=.*[+\-*&^!])[A-Za-z\d+\-*&^!]{8,}$')

# Requires a '@' symbol and a '.' followed by at least 2 characters.
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def match_regex(input_str: str, pattern: re.Pattern):
    """
    Checks if the input string matches the regex pattern with re.
    
    Args:
        input_str (str): The input string to check.
        pattern (Pattern): The regex pattern to check with.
    
    Returns:
        bool: True if match, False if not.
    """
    return bool(re.match(pattern, input_str))