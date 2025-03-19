import pandas as pd
import streamlit as st
import time
from helpers import generate_pivot_table
from config import TABLE_CONFIG
from helpers import (
    get_google_sheet_date_data,
    get_airtable_data,
    get_google_sheets_data
)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



# Get secrets
AIRTABLE_API_KEY = st.secrets["AIRTABLE"]["PERSONAL_ACCESS_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE"]["BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE"]["TABLE_NAME"]
GOOGLE_SHEET_CREDENTIALS_FILE = st.secrets["GOOGLE_SHEET"]["CREDENTIALS_FILE"]
GOOGLE_SHEET_NAME = st.secrets["GOOGLE_SHEET"]["NAME"]


st.title("Total Baking - Cupcakes")
config = TABLE_CONFIG["WITH STORES Total Baking - Cupcakes"]

# Add Animated Date & Time
st.subheader("Current Date")
datetime_placeholder = st.empty()
if "time_sheet_range" in config:
    selected_date = get_google_sheet_date_data(
        config["google_sheet_name"],
        GOOGLE_SHEET_CREDENTIALS_FILE,
        GOOGLE_SHEET_NAME,
        config["time_sheet_range"]
    )
else:
    selected_date = "No Date Configured"

col1, col2 = st.columns(2, vertical_alignment="center", border=False)
with col1:
    st.markdown(
        f'<div class="date-header" style="display: inline-block; background-color: rgba(255, 230, 150, 0.7); color: black; padding: 5px; border-radius: 5px; width: 500px; margin-bottom: 20px">CUPCAKES (ONLINE + SHOPS)</div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f'<div class="date-header" style="display: inline-block; background-color: rgba(255, 230, 150, 0.7); color: black; padding: 5px; border-radius: 5px; width: 500px; margin-bottom: 20px">{selected_date}</div>',
        unsafe_allow_html=True
    )
tables = None

cupcakes_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][0], AIRTABLE_API_KEY)
cupcake_sheet = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, config["sheet_range"][0])


def cupcake_total(cupcakes_total, cupcake_sheet):
    # Select only required columns from Airtable
    required_columns = ["Sponge Flavour 1", "Sponge Size 1", "Sponge QTY 1 - Calculated", "Sponge QTY 2 - Calculated", "Lineitem Quantity"]
    sheet_required_columns = ["Sponge Flavour 1", "Sponge Size 1", "Lineitem Quantity"]
    cupcake_sheet = cupcake_sheet[sheet_required_columns]
    cupcake_sheet["Lineitem Quantity"] = pd.to_numeric(cupcake_sheet["Lineitem Quantity"], errors="coerce").fillna(0).astype(int)
    

    # Ensure required columns exist in both dataframes
    def column_check(x):
        for col in required_columns:
            if col not in x.columns:
                x[col] = None  # Add missing columns
            if col not in x.columns:
                x[col] = None  # Add missing columns

    # Filter only the required columns
    column_check(cupcakes_total)
    cupcakes_total = cupcakes_total[required_columns]
    cupcakes_total["Lineitem Quantity"] = pd.to_numeric(cupcakes_total["Lineitem Quantity"], errors="coerce").fillna(0).astype(int)
    cupcakes_total = pd.concat([cupcakes_total, cupcake_sheet])
    cupcakes_total = cupcakes_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Lineitem Quantity"]].sum()
    
    # Apply CASE-like logic to create a single 'Mix Size' column
    # cupcakes_total["Mix Size"] = cupcakes_total.apply(
    #     lambda row: 0.075 * row["Lineitem Quantity"] if row["Sponge Size 1"] == "Regular Cupcake"
    #     else 0.02 * row["Lineitem Quantity"] if row["Sponge Size 1"] == "Mini Cupcake"
    #     else 0, axis=1
    # )
    
    # Apply rounding to one decimal place for all relevant numeric columns
    # cupcakes_total["Mix Size"] = cupcakes_total["Mix Size"]

    cupcakes_total_table = cupcakes_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Lineitem Quantity",
        aggfunc="sum",
        fill_value=0
    )
    
    # Select numeric columns for total calculation
    numeric_cols = [col for col in cupcakes_total_table.columns if col != "Sponge Flavour 1" and pd.api.types.is_numeric_dtype(cupcakes_total_table[col])]

    cupcakes_total_table["Grand Total Lineitem Quantity"] = cupcakes_total_table[[col for col in numeric_cols if "Lineitem Quantity" in col]].sum(axis=1)
    # cupcakes_total_table["Grand Total Mix Size"] = cupcakes_total_table[[col for col in numeric_cols if "Mix Size" in col]].sum(axis=1)

    # Compute grand total row and round values
    grand_total_row = pd.DataFrame(cupcakes_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    cupcakes_total_table = pd.concat([cupcakes_total_table, grand_total_row], ignore_index=True)
    

    st.subheader(f"Total Cupcakes - ONLINE ONLY")
    generate_pivot_table(cupcakes_total_table, "cupcakes_total_table" )
    
    return
df = cupcake_total(cupcakes_total, cupcake_sheet) 
