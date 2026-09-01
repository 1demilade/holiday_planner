"""
holiday_api.py

Handles comuncation with Nager.Date API
"""

import requests

from utils.exceptions import APIRequestError, APIResponseError
from utils.validators import validate_country_code, validate_year
from models.holiday import Holiday


class HolidayAPIClient:
    """Client responsible for communicating with Nager,Date,"""

    BASE_URL = "https://nagerholidays.com/api/v4" # base URL for the Nager Date
    TIMEOUT = 10 # maximum amount of time to wait for the API

    def __init__(self):
        """Create a reusable HTTP session.
        A Session allows requests to reuse the same connection instead of creating a new connection for each request."""
        self.session = requests.Session()

    def get_holidays(self, country_code, year):
        """Retrieve public holidays for a country and year."""

        # validate user's input
        country_code = validate_country_code(country_code)
        year = validate_year(year)
        
        # construct API endpoint
        url = f"{self.BASE_URL}/Holidays/{country_code}/{year}"
        
        try:
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise APIRequestError(("The request timed out."))
        except requests.exceptions.ConnectionError:
            raise APIRequestError("Could not connect to the holiday API.")
        except requests.exceptions.HTTPError as e:
             if response.status_code == 404:
                raise UnsupportedCountryError(f"No holiday information found for {country_code} in {year}.")
                raise APIRequestError(f"API returned HTTP {response.status_code}: {e}.")
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"API request failed: {e}.")
        
        try:
            data = response.json()
        except ValueError:
            raise APIResponseError("The API resturned invalid JSON.")
        if not isinstance(data, list):
            raise APIResponseError("Unexpected API response format.")
        
        holidays = []
        for item in data:
            try:
                holiday = Holiday(
                    name=item["name"],
                    date=item["date"],
                    holiday_type=", ".join(item.get("holidayTypes", [])),
                    country_code=country_code
                    )
                holidays.append(holiday)
            except KeyError as e:
                raise APIResponseError(f"Missing holiday field: {e}")
        
        return holidays
    
    def close(self):
        self.session.close()

