import streamlit as st
from config import TABLE_CONFIG
from helpers import (
    get_google_sheets_data,
    get_google_sheet_date_data,
    get_airtable_data,
    total_baking,
    online_shops,
    highlight_vegan_rows,
    generate_pivot_table,
)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from datetime import datetime

# Get secrets
AIRTABLE_API_KEY = st.secrets["AIRTABLE"]["PERSONAL_ACCESS_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE"]["BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE"]["TABLE_NAME"]
# GOOGLE_SHEET_CREDENTIALS_FILE = st.secrets["GOOGLE_SHEET"]["CREDENTIALS_FILE"]
GOOGLE_SHEET_NAME = st.secrets["GOOGLE_SHEET"]["NAME"]

# ---- STREAMLIT APP ----
st.sidebar.title("Select a Table Configuration")
selected_table = st.sidebar.selectbox("Choose a table:", list(TABLE_CONFIG.keys()))

st.title(selected_table)
config = TABLE_CONFIG[selected_table]

# Fetch Airtable Data
reg_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][0], AIRTABLE_API_KEY)
reg_total_2nd = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][1], AIRTABLE_API_KEY)
skinny_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][2], AIRTABLE_API_KEY)
thin_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][3], AIRTABLE_API_KEY)
slim_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][4], AIRTABLE_API_KEY)
low_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][5], AIRTABLE_API_KEY)
low_total_2nd = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][6], AIRTABLE_API_KEY)

# Fetch Google Sheets Data
sheets_df = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_NAME, config["sheet_range"])

# Add Animated Date & Time
st.subheader("Current Date")
datetime_placeholder = st.empty()
if "time_sheet_range" in config:
    selected_date = get_google_sheet_date_data(
        config["google_sheet_name"],
        # GOOGLE_SHEET_CREDENTIALS_FILE,
        GOOGLE_SHEET_NAME,
        config["time_sheet_range"]
    )
else:
    selected_date = "No Date Configured"

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f'<div class="date-header" style="display: inline-block;">{selected_date}</div>', unsafe_allow_html=True)
with col2:
    if st.button("Refresh Data", key="refresh_button"):
        st.session_state["refresh_trigger"] = time.time()
tables = None


def generate_tables(selected_table):
    if selected_table == "Total Baking - Cakes":
        df = total_baking(reg_total, reg_total_2nd, skinny_total, thin_total, slim_total, low_total, low_total_2nd, sheets_df)     
    elif selected_table ==  "ONLINE + SHOPS":
        df = online_shops(reg_total, reg_total_2nd, sheets_df)
    return df

if "refresh_trigger" in st.session_state and st.session_state["refresh_trigger"] is not None and time.time() - st.session_state["refresh_trigger"] < 2:
    st.session_state["refresh_trigger"] = None  # Reset trigger
    tables = generate_tables(selected_table)

# Auto refresh table every 1 minute smoothly
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

if time.time() - st.session_state["last_refresh"] > 60:
    st.session_state["last_refresh"] = time.time()
    tables = generate_tables(selected_table)    
    
generate_tables(selected_table)


if st.button("Print Table"):
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
