"""
app.py

This is the main entry point for the Streamlit application. 
It provides a user interface for exploring public holidays and 
cultural information for different countries.
"""

import streamlit as st
import pandas as pd
from services.holiday_api import HolidayAPIClient
from services.comparison_service import ComparisonService
from services.culture_service import CultureGuideGenerator
import os
from dotenv import load_dotenv


st.set_page_config(page_title="Global Holiday Planner", page_icon="📅", layout="wide")

def get_flag_emoji(country_code: str) -> str:
    country_code = (country_code or "").strip().upper()
    if len(country_code) != 2 or not country_code.isascii() or not country_code.isalpha():
        return "🌐"
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in country_code)

# High-Contrast Light Theme Fix
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

load_dotenv() # Load the environment variables from the .env file

api_key = os.getenv("GEMINI_API_KEY")

api_client = HolidayAPIClient()
culture_generator = CultureGuideGenerator(api_key)

tab1, tab2 = st.tabs(["📊 Country Explorer", "⚖️ Cross-Country Comparison"])

with tab1:
    c1, c2 = st.columns([1, 3])
    with c1:
        raw_country = st.text_input("Country Code (ISO)", value="NG", max_chars=2)
        flag = get_flag_emoji(raw_country)
        st.markdown(f"**Region:** {flag} `{raw_country.upper()}`")
        year = st.number_input("Year", value=2026, min_value=1900, max_value=2099)
        run = st.button("🚀 Fetch Holidays", width="stretch")

    with c2:
        if run or "holidays" in st.session_state:
            try:
                if run:
                    st.session_state.holidays = api_client.get_holidays(raw_country, year)
                    st.session_state.selected_country = raw_country
                    st.session_state.selected_year = year

                holidays = st.session_state.holidays
                c_code = st.session_state.selected_country
                c_year = st.session_state.selected_year
                c_flag = get_flag_emoji(c_code)

                col_m1, col_m2 = st.columns(2)
                col_m1.metric(f"Total Holidays ({c_code.upper()})", len(holidays))
                col_m2.metric("Year", c_year)
                
                st.divider()
                st.subheader(f"📅 {c_flag} {c_code.upper()} Schedule")
                
                df = pd.DataFrame([
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
                selected_holiday = st.selectbox("Select a holiday to inspect:", holiday_names)
                
                if st.button("📖 Get Cultural Guide", width="stretch"):
                    with st.spinner("Generating cultural insights with Gemini..."):
                        guide = culture_generator.get_cultural_guide(selected_holiday, c_code)
                        st.write_stream(guide)

            except Exception as e:
                st.error(f"⚠️ {str(e)}")

with tab2:
    ca, cb, cy = st.columns(3)
    c_a = ca.text_input("Country A", value="NG", max_chars=2)
    c_b = cb.text_input("Country B", value="US", max_chars=2)
    comp_yr = cy.number_input("Year", value=2026, min_value=1900, max_value=2099, key="t2_y")
    
    flag_a = get_flag_emoji(c_a)
    flag_b = get_flag_emoji(c_b)
    
    if st.button("🔄 Compare Schedules", width="stretch"):
        try:
            h_a = api_client.get_holidays(c_a, comp_yr)
            h_b = api_client.get_holidays(c_b, comp_yr)
            res = ComparisonService().compare(h_a, h_b)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("🤝 Shared Holidays", len(res.shared_holidays))
            m2.metric(f"Exclusive to {flag_a} {c_a.upper()}", len(res.country_a_only))
            m3.metric(f"Exclusive to {flag_b} {c_b.upper()}", len(res.country_b_only))
            
            st.divider()
            st.subheader("🤝 Shared Holidays")
            shared = [
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
        except Exception as e:
            st.error(f"⚠️ {str(e)}")












#python -m streamlit run app.py