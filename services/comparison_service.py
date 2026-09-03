"""
comparison_service.py

Contains the logic for comparing the holidays of two countries based on their names and dates. It identifies shared holidays, overlapping dates, and country-specific holidays.
"""

from dataclasses import dataclass
from typing import List
from models.holiday import Holiday

# @dataclass decorator automatically generates special methods like __init__() and 
# __repr__() for the class, making it easier to create classes that primarily 
# store data.

@dataclass
class ComparisonResult:
    """Stores the result of comparing two countries holidays"""
    country_a: str
    country_b: str
    year: int

    shared_holidays: list
    overlapping_dates: list
    country_a_only: list
    country_b_only: list

class ComparisonService:
    """Compares holiday lists from two countries."""
    def compare(self, holidays_a: list, holidays_b: list) -> ComparisonResult:
        # first we handle any empty lists
        if not holidays_a:
            raise ValueError("The first country has no holiday data.")
        if not holidays_b:
            raise ValueError("The second country has no holiday data.")
        
        # extract country information
        country_a = holidays_a[0].country_code
        country_b = holidays_b[0].country_code

        #we are assuming that both lists belong to the same year
        #NOTE:so from the ui we should only select a single year for comparison.
        year = self._extract_year(holidays_a[0])

        #find shared holidays
        shared_holidays = self._find_shared_holidays(holidays_a, holidays_b)

        #find overlapping dates
        overlapping_dates = self._find_overlapping_dates(holidays_a, holidays_b)

        #find country specific holidays
        country_a_only = self._find_country_specific(holidays_a, holidays_b)
        country_b_only = self._find_country_specific(holidays_b, holidays_a)

        return ComparisonResult(country_a=country_a, country_b=country_b, year=year, shared_holidays=shared_holidays, overlapping_dates=overlapping_dates, country_a_only=country_a_only, country_b_only=country_b_only)

    # staticmethod decorator indicates that this method does not depend 
    # on the instance of the class and can be called on the class itself.
    @staticmethod
    def _extract_year(holiday: Holiday) -> int:
        # Extract year from a holiday date
        return int(holiday.date[:4]) # extract the first four characters of the date string and convert to int
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        # Normalize the holiday name to make comparisons case-sensitive and remove any spaces
        return "".join(name.lower().split())

    def _find_shared_holidays(self, holidays_a: List[Holiday], holidays_b: List[Holiday]) -> List[Holiday]:
        # Find holidays that are shared between two countries based on normalized names.
        shared = [] # list to store shared holidays.
        
        # create a set of normalized names of holidays in country b
        normalized_names_of_b = {self._normalize_name(holiday.name) for holiday in holidays_b}
        
        for holiday in holidays_a: # iterate through each holiday in country a
            normalized_name = self._normalize_name(holiday.name) # normalize the hoilday name for comparison
            if normalized_name in normalized_names_of_b: # check if the normalized name exists in country b's normalized names
                shared.append(holiday) # append the holiday to the shared list if it is found in both countries.
        
        return shared # return the list of shared holidays

    def _find_overlapping_dates(self, holidays_a: List[Holiday], holidays_b: List[Holiday]) -> List[tuple]:
        # Find holidays that occur on the same date in both countries.
        
        # create a list to store tuples of overlapping holidays
        overlapping = []
        
        # create a dict where dates point to holiday(s) on that date
        dates_b = {}

        for holiday in holidays_b:
            # How setdefault() works:
            # 1. Look up 'holiday.date' in the 'dates_b' dictionary.
            # 2. If the date isn't in the dictionary yet, create it with a new empty list [] as its value.
            # 3. Add (append) the current 'holiday' object into that date's list.
            dates_b.setdefault(holiday.date, []).append(holiday)

        for holiday_a in holidays_a:
            if holiday_a.date in dates_b: # check if the date of holiday_a exists in the dates_b dictionaries
                for holiday_b in dates_b[holiday_a.date]:
                    overlapping.append((holiday_a, holiday_b)) # append a tuple of the overlapping holidays to the overlapping list.

        return overlapping # return the list of tuples containing overlapping holidays from both countries.

    def _find_country_specific(self, holidays_a: List[Holiday], holidays_b: List[Holiday]) -> List[Holiday]:
        # Find holidays that are specific to one country and not present in the other based on normalized names.
        
        # create a set of normalized names of holidays in country
        names_b = {self._normalize_name(holiday.name) for holiday in holidays_b}
        
        # create a list to store holidays that are specific to country a
        country_specific = []
        
        for holiday in holidays_a:
        
            normalized_name = self._normalize_name(holiday.name)
        
            if normalized_name not in names_b: # if the normalized name of holiday_a is not found in country b;s normalized names, it is specific to country a.
                country_specific.append(holiday)
        
        return country_specific


### Note: There is a difference between same holiday and same date.
### Two holidays can be on the same date but not the same celebration.
