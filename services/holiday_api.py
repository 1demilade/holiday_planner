"""
holiday_api.py

Handles communication with Nager.Date API  to retrieve public holiday information 
for a given country and year. It uses the requests library to make HTTP requests 
and includes error handling for various scenarios, such as timeouts, connection errors, 
and invalid responses. The HolidayAPIClient class provides a method to get holidays 
and returns a list of Holiday objects.
"""

import requests

from utils.exceptions import APIRequestError, APIResponseError, UnsupportedCountryCodeError
from utils.validators import validate_country_code, validate_year
from models.holiday import Holiday


class HolidayAPIClient:
    """Client responsible for communicating with Nager.Date."""

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
            # make the API request with timeout
            response = self.session.get(url, timeout=self.TIMEOUT) 
            response.raise_for_status()
        except requests.exceptions.Timeout: # Handle timeout exception
            raise APIRequestError(("The request timed out."))
        except requests.exceptions.ConnectionError: # Handle connection error
            raise APIRequestError("Could not connect to the holiday API.")
        except requests.exceptions.HTTPError as e: # Handle HTTP errors
            if response.status_code == 404:
                raise UnsupportedCountryCodeError(f"No holiday information found for {country_code} in {year}.")
            if response.status_code >= 500:
                raise APIRequestError(f"Server error: {response.status_code}. Please try again later.")
        except requests.exceptions.RequestException as e: # Handle any other request exceptions
            raise APIRequestError(f"API request failed: {e}.")
        
        try:
            data = response.json()
        except ValueError: # Handle JSON decoding error
            raise APIResponseError("The API returned invalid JSON.")
        if not isinstance(data, list): #Handle unxepected response format
            raise APIResponseError("Unexpected API response format.")
        
        holidays = [] # list to store Holiday objects
        for item in data: # iterate through each holiday item in the API response
            try: # create a Holiday object frommt he API response data
                holiday = Holiday(
                    name=item["name"],
                    date=item["date"],
                    holiday_type=", ".join(item.get("holidayTypes", [])),
                    country_code=country_code
                    )
                holidays.append(holiday) # append the Holiday object to the holidays list
            except KeyError as e:
                # Raise an error if a require fieldis missing in the API response
                raise APIResponseError(f"Missing holiday field: {e}") # Raise an error if a require fieldis missing in the API response
        
        return holidays # return the list of Holiday objects.
    
    

