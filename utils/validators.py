"""
validators.py
"""

import re

from utils.exceptions import InvalidCountryCodeError, InvalidYearError

def validate_country_code(country_code):
    """Validate the format of a country code. Country code must contain two uppercase letters."""
    if not isinstance(country_code, str): # make sure the value is a string
        raise InvalidCountryCodeError("Country code must be a string")
    
    country_code = country_code.strip().upper() # remove accidental spaces and switch to uppercase
    pattern = r"[A-Z]{2}$" # exactly two upperscase letters

    if not re.fullmatch(pattern, country_code):
        raise InvalidCountryCodeError("Couuntry code must contain exactly two letters, e.g. NG, US, or GB")
    
    return country_code

def validate_year(year):
    """Validate the format and range of a year."""

    year = str(year).strip() # change year to string

    pattern = r"^\d{4}$" # exactly four digits
    
    if not re.fullmatch(pattern, year):
        raise InvalidYearError("Year must be a four-digit number, e.g. 2026.")
    
    year = int(year) # change year back to int

    if year < 1900 or year > 9999:
        raise InvalidYearError("Year must be between 1900 and 9999.")
    
    return year
