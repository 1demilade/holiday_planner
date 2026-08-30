"""
comparison_service.py

Contains the logic for comparing the holidays of two countries.
"""

from dataclasses import dataclass
from typing import List
from models.holiday import holiday

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

    @staticmethod
    def _extract_year(holiday: Holiday) -> int:
        """Extract year from a holiday date"""
        return int(holiday.date[:4])
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize the hpliday name to make comparisons case-sensitive and remove any spaces"""
        return "".join(name.lower().split())

    def _find_shared_holidays(self, holidays_a: List[Holiday], holidays_b: List[Holiday]) -> List[Holiday]:
        shared = []
        
        # create a set of normalized names of holidays in country b
        normalized_names_of_b = {self._normalize_name(holiday.name) for holiday in holidays_b}
        
        for holiday in holidays_a:
            normalized_name = self._normalize_name(holiday.name)
            if normalized_name in normalized_names_of_b:
                shared.append(holiday)
        
        return shared

    def _find_overlapping_dates(self, holidays_a: List[Holiday], holidays_b: List[Holiday]) -> List[tuple]:
        
        overlapping = []
        
        # create a dict where dates point to holiday(s) on that date
        dates_b = {}

        for holiday in holidays_b:
            dates_b.setdefault(holiday.date, []).append(holiday)

        for holiday_a in holidays_a:
            if holiday_a.date in dates_b:
                for holiday_b in dates_b[holiday_a.date]:
                    overlapping.append((holiday_a, holiday_b))

        return overlapping

    def _find_country_specific(self, holidays_a: List[Holiday], holidays_b: List[Holiday]) -> List[Holiday]:
        
        names_b = {self._normalize_name(holiday.name) for holiday in holidays_b}
        
        country_specific = []
        
        for holiday in holidays_a:
        
            normalized_name = self.normalize_name(holiday.name)
        
            if normalized_name not in names_b:
                country_specific.append(holiday)
        
        return country_specific


### Note: There is a difference between same holiday and same date.
### Two holidays can be one the same date but the same celebration.