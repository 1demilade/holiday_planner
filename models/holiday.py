"""
holiday.py

Defines the Holiday class, which represents a public holiday with attributes such as name, 
date, type, and country_code. This class is used to encapsulate holiday data retrieved from 
the Nager.Date API.
"""


class Holiday:
    """Represents a single public holiday as an object."""
    def __init__(self, name, date, holiday_type, country_code):
        self.name = name
        self.date = date
        self.holiday_type = holiday_type
        self.country_code = country_code
        # Create a Holiday object with the provided attributes: name, date, type, and country code.

    def __str__(self):
        """Controls what happens when we use: print(holiday)"""
        return f"{self.name} - {self.date} - {self.holiday_type}"
        # This method returns a string representation of the Holiday object, which includes its name, date, and type. 
        # This is for debugging and logging purposes.

