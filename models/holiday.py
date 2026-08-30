class Holiday:
    """Represents a single public holiday as an object."""
    def __init__(self, name, date, holiday_type, country_code):
        self.name = name
        self.date = date
        self.holiday_type = holiday_type
        self.country_code = country_code

    def __str__(self):
        """Controls what happens when we use: print(holiday)"""
        return f"{self.name} - {self.date} - {self.holiday_type}"

