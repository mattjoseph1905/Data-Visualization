import streamlit as st
from config import TABLE_CONFIG
from helpers import (
    get_google_sheets_data,
    get_google_sheet_date_data,
    get_airtable_data,
)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
import time


# Get secrets
AIRTABLE_API_KEY = st.secrets["AIRTABLE"]["PERSONAL_ACCESS_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE"]["BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE"]["TABLE_NAME"]
GOOGLE_SHEET_CREDENTIALS_FILE = st.secrets["GOOGLE_SHEET"]["CREDENTIALS_FILE"]
GOOGLE_SHEET_NAME = st.secrets["GOOGLE_SHEET"]["NAME"]


if "refresh_trigger" in st.session_state and st.session_state["refresh_trigger"] is not None and time.time() - st.session_state["refresh_trigger"] < 2:
    st.session_state["refresh_trigger"] = None  # Reset trigger

# Auto refresh table every 1 minute smoothly
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

if time.time() - st.session_state["last_refresh"] > 60:
    st.session_state["last_refresh"] = time.time()
    


if st.button("Print Table"):
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
