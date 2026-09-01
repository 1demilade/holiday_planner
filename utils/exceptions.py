class InvalidCountryCodeError(Exception):
    """Raised when the country code has an invalid format"""
    pass

class InvalidYearError(Exception):
    """Raised when year has an invalid format"""
    pass

class UnsupportedCountryCodeError(Exception):
    """Raised when Nager.Date does not support the requested country."""
    pass

class APIRequestError(Exception):
    """Raised when an API request fails."""
    pass

class APIResponseError(Exception):
    """Raised when the API response is invalid."""
    pass
