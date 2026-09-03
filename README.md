# Global Holiday Planner

A Streamlit app for exploring public holidays by country and year, comparing holiday schedules, and saving useful planning data locally.

## Features

- Fetch public holidays for a country using its ISO 3166-1 alpha-2 code, such as `NG`, `US`, or `GB`.
- View holiday names, dates, and categories in a searchable table.
- Compare two countries in the same year to find:
  - Holidays with matching names
  - Holidays occurring on the same date
  - Holidays unique to each country
- Generate short cultural guides for individual holidays with Google Gemini.
- Save favourite country schedules, cultural guides, and comparisons in readable plain-text files.
- Browse and remove saved favourites from the app.

## Requirements

- Python 3.10 or later
- Internet access for the Nager.Date and Gemini API requests
- A Google Gemini API key for the cultural-guide feature

## Installation

1. Create and activate a virtual environment:

	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

	On macOS or Linux, activate it with:

	```bash
	source .venv/bin/activate
	```

2. Install the application dependencies:

	```bash
	python -m pip install streamlit pandas requests python-dotenv google-genai
	```

3. Create a `.env` file in the project root:

	```env
	GEMINI_API_KEY=your_gemini_api_key_here
	```

	`.env` is excluded from version control. Keep the key private and do not commit it.

## Run the app

From the project root, run:

```bash
python -m streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## Using the planner

### Country Explorer

Enter a two-letter country code and year, then select **Fetch Holidays**. From the returned schedule you can save the country-year record as a favourite or select a holiday to generate a cultural guide.

### Cross-Country Comparison

Enter two country codes and a shared year, then select **Compare Schedules**. The results distinguish matching holiday names from date overlaps, since two different holidays can occur on the same date.

### Saved Data

The **Saved Data** tab displays saved favourite schedules, cultural guides, and comparisons. Favourite schedules can be removed from this tab. Duplicate records are ignored when the same country-year, holiday-country guide, or country-pair-year comparison already exists.

## Data and APIs

- Public holiday data is requested from the [Nager.Date API](https://date.nager.at/).
- Cultural guides are generated through the Google Gemini API.
- Saved records are stored locally as plain text in the `data/` directory:
  - `data/favourites.txt`
  - `data/guides.txt`
  - `data/comparisons.txt`

The data files are created automatically when the app starts. They are human-readable, but their contents are application-managed; edit them carefully if you modify them manually.

## Project structure

```text
holiday_planner/
├── app.py                       # Streamlit entry point
├── data/                        # Local saved planner records
├── models/
│   └── holiday.py               # Holiday domain model
├── services/
│   ├── comparison_service.py    # Holiday comparison logic
│   ├── culture_service.py       # Gemini cultural-guide integration
│   ├── file_service.py          # Plain-text persistence
│   └── holiday_api.py           # Nager.Date API client
└── utils/
	 ├── exceptions.py            # Application-specific exceptions
	 └── validators.py            # Country-code and year validation
```

## Troubleshooting

- **Gemini API key is required:** Confirm that `.env` is in the same directory as `app.py` and contains `GEMINI_API_KEY`.
- **No holiday information found:** Check that the country code is a supported two-letter ISO code and that the selected year is valid.
- **API request failed:** Check your internet connection and try again. External API availability can affect results.
- **Saved data is missing:** Confirm that the app can write to the project directory and that the files under `data/` have not been moved or renamed.

## License

No license has been specified for this project.
