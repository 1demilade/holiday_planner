"""
file_service.py

Stores application data in human-readable plain-text files.
No JSON is used for the application's local data.
"""

from pathlib import Path
import re
from typing import Any


class FileService:
    """Persist favourites, cultural guides, and comparisons as plain TXT records."""

    def __init__(self, data_dir: str | Path | None = None):
        # One service owns all file locations. That keeps the rest of the app
        # from having to know where its saved data lives
        self.data_dir = (
            Path(data_dir)
            if data_dir
            else Path(__file__).resolve().parent.parent / "data"
        )
		
        ## mkdir also makes a fresh checkout work without a manual setup step
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.favourites_file = self.data_dir / "favourites.txt"
        self.guides_file = self.data_dir / "guides.txt"
        self.comparisons_file = self.data_dir / "comparisons.txt"



    def save_favourite(
        self,
        country_code: str,
        holidays: list[Any] | None = None,
        year: int | None = None,
        country_name: str | None = None,
    ) -> None:
        """Save one country/year schedule in plain text."""

        # Fail early: an empty country code would create a record nobody can find later
        if not isinstance(country_code, str) or not country_code.strip():
            raise TypeError("country_code must be a non-empty string")

        code = country_code.strip().upper()
        records = self.get_favourite_details()

        ## A country can be saved again for a different year, but not for this exact pair
        if any(
            record["code"].upper() == code and record.get("year") == year
            for record in records
        ):
            return

        record = {
            "name": country_name or code,
            "code": code,
            "year": year,
            "holidays": [self._holiday_to_dict(h) for h in (holidays or [])],
        }

        # Read, append, then rewrite: the TXT file is treated like a small database table
        records.append(record)
        self._write_favourites(records)

    def get_favourites(self) -> list[dict[str, Any]]:
        """Return saved favourite countries."""

        return self.get_favourite_details()

    def get_favourite_details(self) -> list[dict[str, Any]]:
        """Read favourite country schedules from the TXT file."""

        # Missing or empty files simply mean that the user has no saved favourites yet
        if not self.favourites_file.exists():
            return []

        text = self.favourites_file.read_text(encoding="utf-8").strip()
        if not text:
            return []

        records = []
        # Each [FAVOURITE] block becomes one dictionary for the UI
        for block in self._split_records(text, "FAVOURITE"):
            fields, holidays = self._parse_record(block)

            if not fields.get("code"):
                # Ignore damaged/incomplete blocks instead of crashing the whole app
                continue

            records.append(
                {
                    "name": fields.get("name", fields["code"]),
                    "code": fields["code"],
                    "year": self._parse_optional_int(fields.get("year")),
                    "holidays": holidays,
                }
            )

        return records

    def remove_favourite(self, country_code: str, year: int | None = None) -> bool:
        """Remove a saved favourite by country code and year."""

        # Normalising here makes "ng", "NG", and " NG " refer to the same record
        code = country_code.strip().upper()
        records = self.get_favourite_details()

        # Keep everything except the one record that matches both parts of the key
        remaining = [
            record
            for record in records
            if not (
                record["code"].upper() == code
                and record.get("year") == year
            )
        ]

        removed = len(remaining) != len(records)

        if removed:
            # Do not touch the file when nothing changed
            self._write_favourites(remaining)

        return removed



    def save_guide(self, holiday_name: str, country_code: str, guide: str) -> None:
        """Save a cultural guide in plain text."""

        code = country_code.strip().upper()
        guides = self.get_guides()

        # casefold lets "Christmas" and "christmas" count as the same holiday
        if any(
            item.get("holiday_name", "").strip().casefold()
            == holiday_name.strip().casefold()
            and item.get("country_code", "").upper() == code
            for item in guides
        ):
            return

        guides.append(
            {
                "holiday_name": holiday_name.strip(),
                "country_code": code,
                "guide": guide,
            }
        )

        # Guides are multiline, so they get their own labelled section in the file
        self._write_guides(guides)

    def get_guides(self) -> list[dict[str, str]]:
        """Read saved cultural guides from the TXT file."""

        # This mirrors get_favourite_details, but guide text needs line breaks preserved
        if not self.guides_file.exists():
            return []

        text = self.guides_file.read_text(encoding="utf-8").strip()
        if not text:
            return []

        guides = []

        for block in self._split_records(text, "GUIDE"):
            fields, guide = self._parse_guide_record(block)

            if fields.get("holiday_name"):
                guides.append(
                    {
                        "holiday_name": fields["holiday_name"],
                        "country_code": fields.get("country_code", ""),
                        "guide": guide,
                    }
                )

        return guides


    def save_comparison(self, comparison: Any) -> None:
        """Save a ComparisonResult in plain text."""

        comparisons = self.get_comparisons()
        record = self._comparison_to_dict(comparison)

        # Sort the pair so A-vs-B and B-vs-A produce the same duplicate key
        comparison_key = (
            tuple(
                sorted(
                    (
                        record["country_a"].upper(),
                        record["country_b"].upper(),
                    )
                )
            ),
            record["year"],
        )

        ## One comparison is identified by its two countries plus its year
        if any(
            (
                tuple(
                    sorted(
                        (
                            item["country_a"].upper(),
                            item["country_b"].upper(),
                        )
                    )
                ),
                item.get("year"),
            )
            == comparison_key
            for item in comparisons
        ):
            return

        comparisons.append(record)
        self._write_comparisons(comparisons)

    def get_comparisons(self) -> list[dict[str, Any]]:
        """Read saved comparisons from the TXT file."""

        # A comparison contains several named lists, so parsing rebuilds the same shape
        if not self.comparisons_file.exists():
            return []

        text = self.comparisons_file.read_text(encoding="utf-8").strip()
        if not text:
            return []

        comparisons = []

        for block in self._split_records(text, "COMPARISON"):
            fields, sections = self._parse_comparison_record(block)

            if not fields.get("country_a") or not fields.get("country_b"):
                # A comparison without both countries is not useful to the caller
                continue

            comparisons.append(
                {
                    "country_a": fields["country_a"],
                    "country_b": fields["country_b"],
                    "year": self._parse_optional_int(fields.get("year")),
                    "shared_holidays": sections["shared_holidays"],
                    "overlapping_dates": sections["overlapping_dates"],
                    "country_a_only": sections["country_a_only"],
                    "country_b_only": sections["country_b_only"],
                }
            )

        return comparisons

    
   

    @staticmethod
    def _holiday_to_dict(holiday: Any) -> dict[str, Any]:
        """Convert a Holiday object into a simple dictionary."""

        # Files store plain values, not Python objects that depend on application code
        return {
            "name": holiday.name,
            "date": holiday.date,
            "holiday_type": holiday.holiday_type,
            "country_code": holiday.country_code,
        }

    def _comparison_to_dict(self, comparison: Any) -> dict[str, Any]:
        """Convert ComparisonResult into a TXT-friendly structure."""

        # Nested holiday objects are flattened before the writer sees them
        return {
            "country_a": comparison.country_a,
            "country_b": comparison.country_b,
            "year": comparison.year,
            "shared_holidays": [
                self._holiday_to_dict(item)
                for item in comparison.shared_holidays
            ],
            "overlapping_dates": [
                [
                    self._holiday_to_dict(first),
                    self._holiday_to_dict(second),
                ]
                for first, second in comparison.overlapping_dates
            ],
            "country_a_only": [
                self._holiday_to_dict(item)
                for item in comparison.country_a_only
            ],
            "country_b_only": [
                self._holiday_to_dict(item)
                for item in comparison.country_b_only
            ],
        }


    def _write_favourites(self, records: list[dict[str, Any]]) -> None:
        # The labels make the hand-written file readable and tell the parser where data starts
        lines = []

        for record in records:
            lines.extend(
                [
                    "[FAVOURITE]",
                    f"name={self._clean_field(record['name'])}",
                    f"code={self._clean_field(record['code'])}",
                    f"year={record.get('year') or ''}",
                    "holidays:",
                ]
            )

            for holiday in record.get("holidays", []):
                # One holiday per line keeps records easy to inspect in a text editor
                lines.append(self._encode_holiday(holiday))

            lines.append("[/FAVOURITE]")
            lines.append("")

        self._write_text(self.favourites_file, lines)

    def _write_guides(self, records: list[dict[str, str]]) -> None:
        lines = []

        for record in records:
            lines.extend(
                [
                    "[GUIDE]",
                    f"holiday_name={self._clean_field(record['holiday_name'])}",
                    f"country_code={self._clean_field(record['country_code'])}",
                    "guide:",
                    # The guide itself is allowed to span as many lines as it needs
                    record.get("guide", "").rstrip(),
                    "[/GUIDE]",
                    "",
                ]
            )

        self._write_text(self.guides_file, lines)

    def _write_comparisons(self, records: list[dict[str, Any]]) -> None:
        lines = []

        for record in records:
            lines.extend(
                [
                    "[COMPARISON]",
                    f"country_a={self._clean_field(record['country_a'])}",
                    f"country_b={self._clean_field(record['country_b'])}",
                    f"year={record.get('year') or ''}",
                    "shared_holidays:",
                ]
            )
            lines.extend(
                self._encode_holiday(h)
                for h in record.get("shared_holidays", [])
            )

            # Sections prevent the four holiday lists from getting mixed together
            lines.append("overlapping_dates:")
            for first, second in record.get("overlapping_dates", []):
                # An overlap is two holidays on one line, with eight known fields
                lines.append(
                    "OVERLAP|"
                    + "|".join(
                        [
                            self._escape(first["name"]),
                            self._escape(first["date"]),
                            self._escape(first["holiday_type"]),
                            self._escape(first["country_code"]),
                            self._escape(second["name"]),
                            self._escape(second["date"]),
                            self._escape(second["holiday_type"]),
                            self._escape(second["country_code"]),
                        ]
                    )
                )

            lines.append("country_a_only:")
            lines.extend(
                self._encode_holiday(h)
                for h in record.get("country_a_only", [])
            )

            lines.append("country_b_only:")
            lines.extend(
                self._encode_holiday(h)
                for h in record.get("country_b_only", [])
            )

            lines.extend(["[/COMPARISON]", ""])

        self._write_text(self.comparisons_file, lines)

    @staticmethod
    def _write_text(path: Path, lines: list[str]) -> None:
        # Always finish with one newline; many command-line tools expect that
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    @staticmethod
    def _split_records(text: str, record_type: str) -> list[str]:
        """Extract record bodies between [TYPE] and [/TYPE]."""

        # DOTALL is important here: a record usually contains many lines
        pattern = rf"\[{record_type}\](.*?)\[/{record_type}\]"
        return re.findall(pattern, text, flags=re.DOTALL)

    def _parse_record(
        self, block: str
    ) -> tuple[dict[str, str], list[dict[str, Any]]]:
        fields = {}
        holidays = []

        in_holidays = False

        for line in block.splitlines():
            line = line.strip()

            if not line:
                continue

            if line == "holidays:":
                # Everything after this marker is expected to be a HOLIDAY record
                in_holidays = True
                continue

            if not in_holidays and "=" in line:
                # split only once so an unexpected '=' inside a value is retained
                key, value = line.split("=", 1)
                fields[key.strip()] = self._unescape(value.strip())
                continue

            if in_holidays:
                holiday = self._decode_holiday(line)
                if holiday:
                    holidays.append(holiday)

        return fields, holidays

    def _parse_guide_record(
        self, block: str
    ) -> tuple[dict[str, str], str]:
        fields = {}
        guide_lines = []
        in_guide = False

        for line in block.splitlines():
            if line.strip() == "guide:":
                # Unlike key=value fields, guide content must keep its original line structure
                in_guide = True
                continue

            if in_guide:
                guide_lines.append(line)
            elif "=" in line:
                key, value = line.split("=", 1)
                fields[key.strip()] = self._unescape(value.strip())

        return fields, "\n".join(guide_lines).strip()

    def _parse_comparison_record(
        self, block: str
    ) -> tuple[dict[str, str], dict[str, list]]:
        fields = {}
        sections = {
            "shared_holidays": [],
            "overlapping_dates": [],
            "country_a_only": [],
            "country_b_only": [],
        }

        current_section = None

        for line in block.splitlines():
            line = line.strip()

            if not line:
                continue

            if line.endswith(":") and line[:-1] in sections:
                # Remember which list future HOLIDAY lines belong to
                current_section = line[:-1]
                continue

            if current_section is None and "=" in line:
                key, value = line.split("=", 1)
                fields[key.strip()] = self._unescape(value.strip())
                continue

            if current_section == "overlapping_dates":
                # Overlaps need a special decoder because each line contains two holidays
                overlap = self._decode_overlap(line)
                if overlap:
                    sections[current_section].append(overlap)
            else:
                holiday = self._decode_holiday(line)
                if holiday and current_section:
                    sections[current_section].append(holiday)

        return fields, sections



    @staticmethod
    def _escape(value: Any) -> str:
        """Escape characters used by the TXT format."""

        value = "" if value is None else str(value)
        # Backslash is escaped first, otherwise the new backslashes would be escaped again
        return (
            value.replace("\\", "\\\\")
            .replace("|", "\\|")
            .replace("\n", "\\n")
        )

    @staticmethod
    def _unescape(value: str) -> str:
        result = []
        escaped = False

        # Walk character by character because a normal split cannot understand escaped pipes
        for char in value:
            if escaped:
                if char == "n":
                    result.append("\n")
                else:
                    result.append(char)
                escaped = False
            elif char == "\\":
                # The next character is literal format data, not a separator
                escaped = True
            else:
                result.append(char)

        if escaped:
            result.append("\\")

        return "".join(result)

    def _encode_holiday(self, holiday: dict[str, Any]) -> str:
        # Field order is part of the format: decoder expects name, date, type, country
        return "HOLIDAY|" + "|".join(
            [
                self._escape(holiday.get("name", "")),
                self._escape(holiday.get("date", "")),
                self._escape(holiday.get("holiday_type", "")),
                self._escape(holiday.get("country_code", "")),
            ]
        )

    def _decode_holiday(self, line: str) -> dict[str, Any] | None:
        if not line.startswith("HOLIDAY|"):
            return None

        # Escaped '|' characters should not split a holiday into extra fields
        parts = self._split_escaped(line[len("HOLIDAY|"):])

        if len(parts) != 4:
            # Treat malformed lines as bad data and let the rest of the file load
            return None

        return {
            "name": parts[0],
            "date": parts[1],
            "holiday_type": parts[2],
            "country_code": parts[3],
        }

    def _decode_overlap(
        self, line: str
    ) -> list[dict[str, Any]] | None:
        if not line.startswith("OVERLAP|"):
            return None

        parts = self._split_escaped(line[len("OVERLAP|"):])

        if len(parts) != 8:
            # Two holidays x four fields each = eight values
            return None

        first = {
            "name": parts[0],
            "date": parts[1],
            "holiday_type": parts[2],
            "country_code": parts[3],
        }
        second = {
            "name": parts[4],
            "date": parts[5],
            "holiday_type": parts[6],
            "country_code": parts[7],
        }

        return [first, second]

    def _split_escaped(self, value: str) -> list[str]:
        parts = []
        current = []
        escaped = False

        # This is the inverse of _escape: split on real pipes, not escaped ones
        for char in value:
            if escaped:
                if char == "n":
                    current.append("\n")
                else:
                    current.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "|":
                parts.append("".join(current))
                current = []
            else:
                current.append(char)

        if escaped:
            current.append("\\")

        parts.append("".join(current))
        return parts

    @staticmethod
    def _clean_field(value: Any) -> str:
        """Keep simple key=value fields on one line."""

        value = "" if value is None else str(value)
        # Newlines would break the one-field-per-line part of the file format
        return value.replace("\n", " ").replace("\r", " ").strip()

    @staticmethod
    def _parse_optional_int(value: str | None) -> int | None:
        if value is None or not value.strip():
            return None

        try:
            return int(value)
        except ValueError:
            # Old or hand-edited files may contain a bad year; represent it as missing
            return None
