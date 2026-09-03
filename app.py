"""
app.py

This is the main entry point for the Streamlit application. 
It provides a user interface for exploring public holidays and 
cultural information for different countries.
"""

# Streamlit builds the web interface, while pandas displays holiday data in tables.
# This import gives the program access to Streamlit widgets and page controls.
import streamlit as st
# This import lets us turn lists of holidays into readable tables.
import pandas as pd

# These services keep the app file focused on user interaction:
# API requests, comparisons, AI guides, and file storage are handled elsewhere.
from services.holiday_api import HolidayAPIClient
# Import the class that compares two lists of Holiday objects.
from services.comparison_service import ComparisonService
# Import the class that asks Gemini to create a cultural explanation.
from services.culture_service import CultureGuideGenerator
# Import the class that reads and writes saved JSON records.
from services.file_service import FileService
# Import Python's operating-system helpers for reading environment variables.
import os
# Import the helper that loads values from the .env file.
from dotenv import load_dotenv


# Configure the browser tab before creating any other Streamlit elements.
st.set_page_config(page_title="Global Holiday Planner", page_icon="📅", layout="wide")


def get_flag_emoji(country_code: str) -> str:
    """Convert a two-letter country code into its matching flag emoji."""
    # User input can contain spaces or lowercase letters, so normalize it first.
    country_code = (country_code or "").strip().upper()
    # Invalid input receives a globe instead of causing an emoji conversion error.
    if len(country_code) != 2 or not country_code.isascii() or not country_code.isalpha():
        return "🌐"
    # Regional indicator letters are consecutive Unicode code points.
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in country_code)

# Send the CSS string to Streamlit and allow it to be interpreted as HTML/CSS.
# Add CSS so the application has a consistent high-contrast light appearance.
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #F8FAFC !important; color: #0F172A !important; }
    
    /* Typography & Headers */
    h1, h2, h3, label, p, span, .stMarkdown { color: #0F172A !important; font-weight: 600 !important; }
    
    /* Force Light Styling directly on Input Controls */
    .stTextInput input, .stNumberInput input {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        border: 1px solid #94A3B8 !important;
    }

    /* Force parent container background */
    div[data-baseweb="input"], div[data-baseweb="base-input"] {
        background-color: #E2E8F0 !important;
        border-radius: 8px !important;
    }
    
    /* Number Input Buttons (+/-) */
    div[data-testid="stNumberInput"] button {
        background-color: #CBD5E1 !important;
        color: #0F172A !important;
        border: none !important;
    }

    /* Metrics */
    div[data-testid="stMetricValue"] { color: #7C3AED !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #475569 !important; font-weight: 700 !important; }

    /* Tabs Contrast */
    div[data-testid="stTabs"] button {
        color: #475569 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #7C3AED !important;
        border-bottom: 3px solid #7C3AED !important;
    }

    /* Action Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #7C3AED 0%, #C026D3 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }
    .stButton>button:hover { opacity: 0.9 !important; }
</style>
""", unsafe_allow_html=True)

st.title("📅 Public Holiday & Cultural Planner")

# Read values from the local .env file, including the Gemini API key.
load_dotenv()

# Look up the Gemini key that was loaded from the environment.
api_key = os.getenv("GEMINI_API_KEY")

# Create one reusable instance of each service for this Streamlit run.
# The UI calls these objects instead of containing API, comparison, or file logic itself.
api_client = HolidayAPIClient()
culture_generator = CultureGuideGenerator(api_key)
file_service = FileService()

# The three tabs keep all parts of the application together in the user interface.
tab1, tab2, tab3 = st.tabs([
    "📊 Country Explorer",
    "⚖️ Cross-Country Comparison",
    "💾 Saved Data",
])

with tab1:
    # Country Explorer fetches one country's schedule and offers related actions.
    # Split the tab into a narrow input area and a wider results area.
    c1, c2 = st.columns([1, 3])
    with c1:
        # These widgets collect the two values required by the holiday API.
        # The country code is limited to two characters because ISO codes use two letters.
        raw_country = st.text_input("Country Code (ISO)", value="NG", max_chars=2)
        # Calculate a visual flag from whatever code the user has typed.
        flag = get_flag_emoji(raw_country)
        # Show the normalized-looking country code beside its flag.
        st.markdown(f"**Region:** {flag} `{raw_country.upper()}`")
        # Let the user choose which year's public holidays to request.
        year = st.number_input("Year", value=2026, min_value=1900, max_value=2099)
        # This Boolean is True only during the rerun caused by this button click.
        run = st.button("🚀 Fetch Holidays", width="stretch")

    with c2:
        # On every rerun, keep showing the last successful result from session state.
        # This is why users can click Save without losing the fetched schedule.
        if run or "holidays" in st.session_state:
            try:
                if run:
                    # The button click triggers the API request and stores the result for later reruns.
                    st.session_state.holidays = api_client.get_holidays(raw_country, year)
                    st.session_state.selected_country = raw_country
                    st.session_state.selected_year = year

                holidays = st.session_state.holidays
                # Read the selected country and year that were stored with the holidays.
                c_code = st.session_state.selected_country
                c_year = st.session_state.selected_year
                # Convert the stored country code to a flag for the schedule heading.
                c_flag = get_flag_emoji(c_code)

                # Create two metric columns for the result count and selected year.
                col_m1, col_m2 = st.columns(2)
                col_m1.metric(f"Total Holidays ({c_code.upper()})", len(holidays))
                col_m2.metric("Year", c_year)
                
                st.divider()
                st.subheader(f"📅 {c_flag} {c_code.upper()} Schedule")

                favourite_keys = {
                    (favourite["code"].upper(), favourite.get("year"))
                    for favourite in file_service.get_favourite_details()
                }
                # Check both values because the same country may be saved for another year.
                if (c_code.upper(), year) in favourite_keys:
                    # Prevent saving an identical country-year record twice.
                    st.info(f"This country is already saved for {year}.")
                elif st.button("⭐ Save Country as Favourite", width="stretch"):
                    # Save both the country identity and the exact holidays fetched for that year.
                    file_service.save_favourite(
                        c_code.upper(), holidays, year, country_name=c_code.upper()
                    )
                    st.success(f"Saved {c_code.upper()} holidays for {year} to favourites.")
                
                df = pd.DataFrame([
                    # Build one dictionary per Holiday so pandas can create table columns.
                    {
                        "Holiday Name": h.name, 
                        "Date 📅": h.date, 
                        "Category 🏷️": getattr(h, 'holiday_type', 'Public') or "Public"
                    } for h in holidays
                ])
                st.dataframe(df, width="stretch", hide_index=True)

                st.divider()
                st.subheader("✨ Cultural Insights")
                holiday_names = [h.name for h in holidays]
                # Use holiday names as the choices in the cultural-guide selector.
                selected_holiday = st.selectbox("Select a holiday to inspect:", holiday_names)
                
                if st.button("📖 Get Cultural Guide", width="stretch"):
                    with st.spinner("Generating cultural insights with Gemini..."):
                        # The generator yields chunks; joining them creates one complete guide
                        # that can be displayed once and saved as one record.
                        guide = culture_generator.get_cultural_guide(selected_holiday, c_code)
                        st.session_state.generated_guide = "".join(guide)
                        st.session_state.generated_guide_name = selected_holiday
                        st.session_state.generated_guide_country = c_code.upper()

                if "generated_guide" in st.session_state:
                    # Keep the guide visible after the generation button causes a rerun.
                    st.markdown(st.session_state.generated_guide)
                    if st.button("💾 Save Cultural Guide", width="stretch"):
                        # FileService prevents the same holiday-country guide being stored twice.
                        file_service.save_guide(
                            st.session_state.generated_guide_name,
                            st.session_state.generated_guide_country,
                            st.session_state.generated_guide,
                        )
                        st.success("Cultural guide saved.")

            except Exception as e:
                st.error(f"⚠️ {str(e)}")

with tab2:
    # Cross-Country Comparison fetches two schedules, then groups their differences.
    # Use three equal input areas for country A, country B, and the shared year.
    ca, cb, cy = st.columns(3)
    # Collect the first country code from the first input column.
    c_a = ca.text_input("Country A", value="NG", max_chars=2)
    # Collect the second country code from the second input column.
    c_b = cb.text_input("Country B", value="US", max_chars=2)
    # Both API requests use this year so the comparison is meaningful.
    comp_yr = cy.number_input("Year", value=2026, min_value=1900, max_value=2099, key="t2_y")
    
    flag_a = get_flag_emoji(c_a)
    # Calculate the flag for country B as a visual label.
    flag_b = get_flag_emoji(c_b)
    
    compare_clicked = st.button("🔄 Compare Schedules", width="stretch")
    # Reuse the previous result after reruns, for example when Save is clicked.
    if compare_clicked or "comparison_result" in st.session_state:
        try:
            if compare_clicked:
                # Fetch both countries for the selected year before comparing them.
                h_a = api_client.get_holidays(c_a, comp_yr)
                h_b = api_client.get_holidays(c_b, comp_yr)
                res = ComparisonService().compare(h_a, h_b)
                st.session_state.comparison_result = res
            else:
                # No new request is needed when the user is only saving or viewing the result.
                res = st.session_state.comparison_result
            
            m1, m2, m3 = st.columns(3)
            # Show counts for shared and country-specific holidays.
            m1.metric("🤝 Shared Holidays", len(res.shared_holidays))
            m2.metric(f"Exclusive to {flag_a} {c_a.upper()}", len(res.country_a_only))
            m3.metric(f"Exclusive to {flag_b} {c_b.upper()}", len(res.country_b_only))
            
            st.divider()
            st.subheader("🤝 Shared Holidays")
            shared = [
                # Convert each Holiday object into table-friendly values.
                {
                    "Holiday Name": holiday.name,
                    "Date": holiday.date,
                    "Category": holiday.holiday_type or "Public"
                } for holiday in res.shared_holidays
            ]
            if shared:
                st.dataframe(pd.DataFrame(shared), width="stretch", hide_index=True)
            else:
                st.info("No shared holidays found between these countries.")

            st.divider()
            st.subheader("📅 Overlapping Holiday Dates")
            overlaps = [
                # Each overlap is a pair, so display both holiday names on one date row.
                {
                    "Date 📅": a.date, 
                    f"{c_a.upper()} Event": a.name, 
                    f"{c_b.upper()} Event": b.name
                } for a, b in res.overlapping_dates
            ]
            if overlaps:
                st.dataframe(pd.DataFrame(overlaps), width="stretch", hide_index=True)
            else:
                st.info("No exact date overlaps found between these two countries.")

            st.divider()
            st.subheader(f"🇦 {c_a.upper()}-Only Holidays")
            country_a_only = [
                # Convert country A's exclusive Holiday objects into dictionaries.
                {
                    "Holiday Name": holiday.name,
                    "Date": holiday.date,
                    "Category": holiday.holiday_type or "Public"
                } for holiday in res.country_a_only
            ]
            if country_a_only:
                st.dataframe(pd.DataFrame(country_a_only), width="stretch", hide_index=True)
            else:
                st.info(f"No holidays are exclusive to {c_a.upper()}.")

            st.subheader(f"🇧 {c_b.upper()}-Only Holidays")
            country_b_only = [
                # Convert country B's exclusive Holiday objects into dictionaries.
                {
                    "Holiday Name": holiday.name,
                    "Date": holiday.date,
                    "Category": holiday.holiday_type or "Public"
                } for holiday in res.country_b_only
            ]
            if country_b_only:
                st.dataframe(pd.DataFrame(country_b_only), width="stretch", hide_index=True)
            else:
                st.info(f"No holidays are exclusive to {c_b.upper()}.")

            if st.button("💾 Save Current Comparison", width="stretch"):
                # Saving is explicit. FileService ignores the same country-pair and year twice.
                file_service.save_comparison(res)
                st.success("Comparison saved.")
        except Exception as e:
            st.error(f"⚠️ {str(e)}")


with tab3:
    # Saved Data is written after the other tab code, but remains the third tab in the UI.
    st.header("Saved planner data")
    st.caption("Browse and manage your saved holiday planning records.")

    st.divider()
    st.subheader("⭐ Favourite Countries")
    favourite_details = file_service.get_favourite_details()
    st.caption(f"{len(favourite_details)} saved country-year schedules")
    if favourite_details:
        for index, favourite in enumerate(favourite_details):
            favourite_col, remove_col = st.columns([4, 1])
            favourite_year = favourite.get("year")
            year_label = f" - {favourite_year}" if favourite_year else ""
            favourite_col.write(
                f"{get_flag_emoji(favourite['code'])} {favourite['name']} "
                f"({favourite['code']}{year_label})"
            )
            if remove_col.button(
                "×",
                key=f"remove_{favourite['code']}_{favourite_year}",
                help="Remove favourite",
            ):
                file_service.remove_favourite(favourite["code"], favourite_year)
                st.rerun()
            with st.expander("View holiday schedule", expanded=False):
                saved_holidays = [
                    {
                        "Holiday Name": holiday["name"],
                        "Date": holiday["date"],
                        "Category": holiday["holiday_type"] or "Public",
                    }
                    for holiday in favourite.get("holidays", [])
                ]
                if saved_holidays:
                    st.dataframe(pd.DataFrame(saved_holidays), hide_index=True, width="stretch")
                else:
                    st.info("No holiday schedule was saved for this favourite.")
            if index < len(favourite_details) - 1:
                st.divider()
    else:
        st.caption("No favourite countries saved yet.")

    st.divider()
    st.subheader("📖 Saved Cultural Guides")
    saved_guides = file_service.get_guides()
    st.caption(f"{len(saved_guides)} saved guides")
    with st.container(border=True):
        if saved_guides:
            for index, saved_guide in enumerate(saved_guides):
                st.markdown(
                    f"**{saved_guide['holiday_name']} ({saved_guide['country_code']})**"
                )
                st.markdown(saved_guide["guide"])
                if index < len(saved_guides) - 1:
                    st.divider()
        else:
            st.caption("No cultural guides saved yet.")

    st.divider()
    st.subheader("⚖️ Saved Comparisons")
    saved_comparisons = file_service.get_comparisons()
    st.caption(f"{len(saved_comparisons)} saved comparisons")
    with st.container(border=True):
        if saved_comparisons:
            for index, comparison in enumerate(saved_comparisons):
                st.markdown(
                    f"**{comparison['country_a']} vs {comparison['country_b']} ({comparison['year']})**"
                )
                st.write(
                    f"Shared: {len(comparison['shared_holidays'])} | "
                    f"{comparison['country_a']} only: {len(comparison['country_a_only'])} | "
                    f"{comparison['country_b']} only: {len(comparison['country_b_only'])}"
                )
                with st.expander("View comparison details", expanded=False):
                    st.markdown("**Shared Holidays**")
                    shared_saved = [
                        {
                            "Holiday Name": holiday["name"],
                            "Date": holiday["date"],
                            "Category": holiday["holiday_type"] or "Public",
                        }
                        for holiday in comparison["shared_holidays"]
                    ]
                    if shared_saved:
                        st.dataframe(pd.DataFrame(shared_saved), hide_index=True, width="stretch")
                    else:
                        st.info("No shared holidays found.")

                    st.markdown("**Overlapping Holiday Dates**")
                    overlaps_saved = [
                        {
                            "Date": first["date"],
                            f"{comparison['country_a']} Event": first["name"],
                            f"{comparison['country_b']} Event": second["name"],
                        }
                        for first, second in comparison["overlapping_dates"]
                    ]
                    if overlaps_saved:
                        st.dataframe(pd.DataFrame(overlaps_saved), hide_index=True, width="stretch")
                    else:
                        st.info("No exact date overlaps found.")

                    st.markdown(f"**{comparison['country_a']}-Only Holidays**")
                    country_a_saved = [
                        {
                            "Holiday Name": holiday["name"],
                            "Date": holiday["date"],
                            "Category": holiday["holiday_type"] or "Public",
                        }
                        for holiday in comparison["country_a_only"]
                    ]
                    if country_a_saved:
                        st.dataframe(pd.DataFrame(country_a_saved), hide_index=True, width="stretch")
                    else:
                        st.info(f"No holidays are exclusive to {comparison['country_a']}.")

                    st.markdown(f"**{comparison['country_b']}-Only Holidays**")
                    country_b_saved = [
                        {
                            "Holiday Name": holiday["name"],
                            "Date": holiday["date"],
                            "Category": holiday["holiday_type"] or "Public",
                        }
                        for holiday in comparison["country_b_only"]
                    ]
                    if country_b_saved:
                        st.dataframe(pd.DataFrame(country_b_saved), hide_index=True, width="stretch")
                    else:
                        st.info(f"No holidays are exclusive to {comparison['country_b']}.")
                if index < len(saved_comparisons) - 1:
                    st.divider()
        else:
            st.caption("No comparisons saved yet.")












#python -m streamlit run app.py