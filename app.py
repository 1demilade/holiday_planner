"""
app.py

"""

# please do not write any code here

# this project was last updated and sent to the group on 31/08 around 7:00 PM
import streamlit as st
import pandas as pd
from services.holiday_api import HolidayAPIClient
from services.comparison_service import ComparisonService

st.set_page_config(page_title="Global Holiday Planner", page_icon="📅", layout="wide")

def get_flag_emoji(country_code: str) -> str:
    country_code = country_code.strip().upper()
    if len(country_code) != 2 or not country_code.isalpha(): 
        return "🌐"
    return chr(ord(country_code[0]) + 127397) + chr(ord(country_code[1]) + 127397)

# High-Contrast Light Theme Fix
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #F8FAFC !important; color: #0F172A !important; }
    
    /* Typography & Headers */
    h1, h2, h3, label, p, span, .stMarkdown { color: #0F172A !important; font-weight: 600 !important; }
    
    /* Fix Input Fields (Light gray box with high-contrast black text) */
    div[data-baseweb="input"] {
        background-color: #E2E8F0 !important;
        border: 2px solid #94A3B8 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input {
        color: #0F172A !important;
        font-weight: 700 !important;
        background-color: transparent !important;
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

api_client = HolidayAPIClient()
tab1, tab2 = st.tabs(["📊 Country Explorer", "⚖️ Cross-Country Comparison"])

with tab1:
    c1, c2 = st.columns([1, 3])
    with c1:
        raw_country = st.text_input("Country Code (ISO)", value="NG", max_chars=2)
        flag = get_flag_emoji(raw_country)
        st.markdown(f"**Region:** `{raw_country.upper()}` {flag}")
        year = st.number_input("Year", value=2026, min_value=1900, max_value=2099)
        run = st.button("🚀 Fetch Holidays", use_container_width=True)

    with c2:
        if run:
            try:
                holidays = api_client.get_holidays(raw_country, year)
                col_m1, col_m2 = st.columns(2)
                col_m1.metric(f"Total Holidays ({raw_country.upper()})", len(holidays))
                col_m2.metric("Year", year)
                
                st.divider()
                st.subheader(f"📅 {raw_country.upper()} Schedule {flag}")
                
                df = pd.DataFrame([
                    {
                        "Holiday Name": h.name, 
                        "Date 📅": h.date, 
                        "Category 🏷️": h.holiday_type or "Public"
                    } for h in holidays
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"⚠️ {str(e)}")

with tab2:
    ca, cb, cy = st.columns(3)
    c_a = ca.text_input("Country A", value="NG", max_chars=2)
    c_b = cb.text_input("Country B", value="US", max_chars=2)
    comp_yr = cy.number_input("Year", value=2026, min_value=1900, max_value=2099, key="t2_y")
    
    flag_a = get_flag_emoji(c_a)
    flag_b = get_flag_emoji(c_b)
    
    if st.button("🔄 Compare Schedules", use_container_width=True):
        try:
            h_a = api_client.get_holidays(c_a, comp_yr)
            h_b = api_client.get_holidays(c_b, comp_yr)
            res = ComparisonService().compare(h_a, h_b)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("🤝 Shared Holidays", len(res.shared_holidays))
            m2.metric(f"Exclusive to {c_a.upper()} {flag_a}", len(res.country_a_only))
            m3.metric(f"Exclusive to {c_b.upper()} {flag_b}", len(res.country_b_only))
            
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
                st.dataframe(pd.DataFrame(overlaps), use_container_width=True, hide_index=True)
            else:
                st.info("No exact date overlaps found between these two countries.")
        except Exception as e:
            st.error(f"⚠️ {str(e)}")