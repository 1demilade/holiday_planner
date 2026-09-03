"""
file_service.py

This handles the file-handling. 
Users need to be able to save fovourite countries, holiday guides and comparison results.
"""

import json  # Converts Python lists and dictionaries to/from JSON text.
from pathlib import Path  # Handles file and folder paths safely on Windows and other systems.
from typing import Any  # Used when a value can contain different object types.

class FileService:
	"""Persist favourites, cultural guides, and comparisons as JSON records."""

	def __init__(self, data_dir: str | Path | None = None):

		# When no folder is supplied, find the project-level data folder from this file.
		self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent / "data"

		# mkdir also makes the service work with a new or temporary data folder.
		self.data_dir.mkdir(parents=True, exist_ok=True)

		# These names are kept as .txt because that is how the project data files are named,
		# but their contents are JSON and must be read with json.load/json.dump.
		self.favourites_file = self.data_dir / "favourites.txt"
		self.guides_file = self.data_dir / "guides.txt"
		self.comparisons_file = self.data_dir / "comparisons.txt"

	def save_favourite(self, country_code: str, holidays: list[Any] | None = None, year: int | None = None, country_name: str | None = None) -> None:
		"""Save a country schedule once for each ISO code and year."""
		if not isinstance(country_code, str) or not country_code.strip(): # check for empty string or non-string input
			raise TypeError("country_code must be a non-empty string")
		code = country_code.strip().upper()

		# Read the complete list first because adding a record must preserve old records.
		records = self._read_json(self.favourites_file)

		# The year is part of the duplicate check. Calling this method twice for the
		# same country and year does nothing, which prevents duplicate saved entries.
		if any(
			record["code"].upper() == code
			and record.get("year") == year
			for record in records
		):
			return
		
        # Build a JSON-compatible dictionary directly from the supplied country values.
		record = {"name": country_name or code, "code": code}
		record["year"] = year
		record["holidays"] = [self._holiday_to_dict(item) for item in (holidays or [])]
		records.append(record)

		# Write the whole updated list back to the file. This is simpler than trying to append a single record to a JSON list.
		self._write_json(self.favourites_file, records)

	def get_favourites(self) -> list[dict[str, Any]]:
		"""Return all saved favourite country records."""
		return self._read_json(self.favourites_file)

	def get_favourite_details(self) -> list[dict[str, Any]]:
		"""Return saved countries with their persisted holiday schedules."""
		records = self._read_json(self.favourites_file)
		# Older saved records may not have a holidays key. Add an empty list so the UI
		# can safely loop over every record without special-case KeyError handling.
		for record in records:
			record.setdefault("holidays", [])
		return records

	def remove_favourite(self, country_code: str, year: int | None = None) -> bool:
		"""Remove a favourite by ISO code and year."""
		# use uppercase input so "ng" and "NG" refer to the same saved country.
		code = country_code.strip().upper()
		records = self._read_json(self.favourites_file)
		# keep every record except the one matching both the country and year.
		remaining = [
			record for record in records
		if not (record["code"].upper() == code and record.get("year") == year)
		]
		# comparing lengths tells the caller whether anything was actually removed.
		removed = len(remaining) != len(records)
		if removed:
			# do not rewrite the file when nothing changed
			self._write_json(self.favourites_file, remaining)
		return removed

	def save_guide(self, holiday_name: str, country_code: str, guide: str) -> None:
		"""Save a cultural guide with its holiday and country context."""
		# A guide is unique for one holiday in one country. So we prevent the same
		# guide from being saved repeatedly when the save button is clicked again
		guides = self._read_json(self.guides_file)
		code = country_code.strip().upper()
		if any(
			item.get("holiday_name", "").strip().casefold() == holiday_name.strip().casefold()
			and item.get("country_code", "").upper() == code
			for item in guides
		):
			return
		guides.append({
			"holiday_name": holiday_name,
			"country_code": code,
			"guide": guide,
		})
		self._write_json(self.guides_file, guides)

	def get_guides(self) -> list[dict[str, str]]:
		"""Return saved cultural guides in insertion order."""
		return self._read_json(self.guides_file)

	def save_comparison(self, comparison: Any) -> None:
		"""Save a ComparisonResult, including its holiday details."""
		# ComparisonResult contains Python objects, so convert it before json.dump can use it.
		comparisons = self._read_json(self.comparisons_file)
		record = self._comparison_to_dict(comparison)
		# Sort the country pair so NG vs US and US vs NG count as the same comparison.
		comparison_key = (
			tuple(sorted((record["country_a"].upper(), record["country_b"].upper()))),
			record["year"],
		)
		if any(
			(
				tuple(sorted((item["country_a"].upper(), item["country_b"].upper()))),
				item.get("year"),
			) == comparison_key
			for item in comparisons
		):
			return
		comparisons.append(record)
		self._write_json(self.comparisons_file, comparisons)

	def get_comparisons(self) -> list[dict[str, Any]]:
		"""Return saved comparison results in insertion order."""
		# the UI reads these dictionaries to rebuild the same tables shown for live comparisons
		return self._read_json(self.comparisons_file)

	@staticmethod
	def _holiday_to_dict(holiday: Any) -> dict[str, Any]:
		# Store every Holiday field needed to display a saved schedule later
		return {
			"name": holiday.name,
			"date": holiday.date,
			"holiday_type": holiday.holiday_type,
			"country_code": holiday.country_code,
		}

	def _comparison_to_dict(self, comparison: Any) -> dict[str, Any]:
		# A comparison has four holiday collections
        # Overlapping dates are pairs
		# Each pair becomes a two-item JSON list
		return {
			"country_a": comparison.country_a,
			"country_b": comparison.country_b,
			"year": comparison.year,
			"shared_holidays": [self._holiday_to_dict(item) for item in comparison.shared_holidays],
			"overlapping_dates": [
				[self._holiday_to_dict(first), self._holiday_to_dict(second)]
				for first, second in comparison.overlapping_dates
			],
			"country_a_only": [self._holiday_to_dict(item) for item in comparison.country_a_only],
			"country_b_only": [self._holiday_to_dict(item) for item in comparison.country_b_only],
		}

	@staticmethod
	def _read_json(path: Path) -> list[dict[str, Any]]:
		# Empty files are treated as an empty collection, which supports the initial
		# blank data files included in the project.
		if not path.exists() or not path.read_text(encoding="utf-8").strip():
			return []
		
		with path.open("r", encoding="utf-8") as file:
			data = json.load(file)

		# every service file must contain a list. A dictionary or string means the file has the wrong structure and should be inspected before continuing.
		if not isinstance(data, list):
			raise ValueError(f"Expected a list of records in {path.name}")
		return data

	@staticmethod
	def _write_json(path: Path, records: list[dict[str, Any]]) -> None:
		# "w" replaces the old JSON with the updated list
		with path.open("w", encoding="utf-8") as file:
			json.dump(records, file, indent=2, ensure_ascii=True)
			file.write("\n")
