"""
file_service.py
"""

from pathlib import Path

data_folder = Path(__file__).resolve().parent.parent / "data"


def load_lines(file_name):
    file_path = data_folder / file_name

    if not file_path.exists():
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def save_lines(file_name, items):
    file_path = data_folder / file_name

    with open(file_path, "w", encoding="utf-8") as file:
        for item in items:
            file.write(f"{item}\n")


def load_favourites():
    return load_lines("favourites.txt")


def save_favourites(favourites):
    save_lines("favourites.txt", favourites)


def load_guides():
    return load_lines("guides.txt")


def save_guides(guides):
    save_lines("guides.txt", guides)


def load_comparisons():
    return load_lines("commparisons.txt")


def save_comparisons(comparisons):
    save_lines("commparisons.txt", comparisons)
