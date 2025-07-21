import re
from datetime import datetime
import hashlib
from typing import Union

# Map for converting month numbers to names for date parsing
MONTH_MAP = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}

def parse_date(date_str: str) -> str:
    """
    Converts a date string from 'D.M.YYYY' or 'D.M.YY' format to 'Day Month YYYY' format.
    Handles variations including spaces in the year and 2-digit years.
    Returns '-' if the input is empty or invalid.

    Args:
        date_str (str): The date string to parse.

    Returns:
        str: The formatted date string or '-' if parsing fails.
    """
    if not date_str or date_str.strip() == '-' or date_str.strip() == '':
        return "-"

    # Clean the date string: remove extra spaces, ensure consistent separators
    cleaned_date_str = date_str.replace(' ', '').strip()

    # Attempt to match dates in 'D.M.YYYY' or 'D.M.YY' format
    match = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})', cleaned_date_str)
    if match:
        day, month, year = match.groups()
        try:
            day = int(day)
            month = int(month)
            year = int(year)

            # Handle 2-digit years (e.g., '61' for 1961, '92' for 1992)
            if len(str(year)) == 2:
                # Heuristic: if year is > (current_year_last_two_digits + 5), assume 19xx, otherwise 20xx
                if year > (datetime.now().year % 100 + 5):
                    year = 1900 + year
                else:
                    year = 2000 + year
            
            # Return formatted date using the MONTH_MAP
            return f"{day} {MONTH_MAP.get(month, str(month))} {year}"
        except (ValueError, KeyError):
            # If conversion to int or month mapping fails, return original string
            return date_str 
    
    # Handle cases where the date might already be in "DD Month YYYY" format
    if re.match(r'\d{1,2}\s[A-Za-z]+\s\d{4}', date_str.strip()):
        return date_str.strip()

    # If no known pattern matches, return the original string
    return date_str

def get_safe_string(value: Union[str, None]) -> str:
    """
    Safely converts a value to a string and strips whitespace.
    Returns an empty string if the value is None or not a string.
    """
    if isinstance(value, str):
        return value.strip()
    return ""

def get_safe_int(value: Union[str, dict, None]) -> Union[int, str]:
    """
    Safely converts a value to an integer.
    Handles cases where xmltodict might return a dict for elements with attributes and text.
    Returns an empty string if conversion to a valid integer is not possible.
    """
    if isinstance(value, dict):
        text_val = value.get("#text")
        if isinstance(text_val, str) and text_val.isdigit():
            return int(text_val)
    elif isinstance(value, str) and value.isdigit():
        return int(value)
    return "" # Return empty string for non-numeric or None values

def calculate_sha256(content: bytes) -> str:
    """
    Calculates the SHA256 hash of the given byte content.

    Args:
        content (bytes): The content to hash.

    Returns:
        str: The hexadecimal representation of the SHA256 hash.
    """
    return hashlib.sha256(content).hexdigest()