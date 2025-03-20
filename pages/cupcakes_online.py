import pandas as pd
import streamlit as st
import time
from helpers import generate_pivot_table
from config import TABLE_CONFIG
from helpers import (
    get_google_sheet_date_data,
    get_airtable_data,
)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



# Get secrets
AIRTABLE_API_KEY = st.secrets["AIRTABLE"]["PERSONAL_ACCESS_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE"]["BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE"]["TABLE_NAME"]
GOOGLE_SHEET_CREDENTIALS_FILE = st.secrets["GOOGLE_SHEET"]["CREDENTIALS_FILE"]
GOOGLE_SHEET_NAME = st.secrets["GOOGLE_SHEET"]["NAME"]


config = TABLE_CONFIG["Total Baking - Cupcakes"]
reg_am = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][1], AIRTABLE_API_KEY)
reg_pm = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][2], AIRTABLE_API_KEY)

# Ensure the "Eligibility" column exists in the DataFrame
if "Eligibility" in reg_am.columns:
    eligibility_am = reg_am["Eligibility"].iloc[0]  # Get the first unique value
    print("Eligibility:", eligibility_am)
else:
    print("Error: 'Eligibility' column not found in DataFrame")

if "Eligibility" in reg_pm.columns:
    eligibility_pm = reg_pm["Eligibility"].iloc[0]
    print("Eligibility:", eligibility_pm)
else:
    print("Error: 'Eligibility' column not found in DataFrame")

    
eligibility_am = str(eligibility_am)
eligibility_pm = str(eligibility_pm)

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

# Load and apply external CSS file
def load_css(file_name):
    with open(file_name, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css("styles.css")

st.markdown('<div class="page-header">CUPCAKE BAKING LIST - ONLINE ONLY</div>', unsafe_allow_html=True)

# Define Columns (Keep Original Layout)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f'''
        <div class="date-header">
            <span class="small-text">AM Delivery on:</span> </br>
            <span class="large-text">{eligibility_am}</span>
        </div>
        ''',
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f'''
        <div class="date-header">
            <span class="small-text">PM Delivery on:</span> </br>
            <span class="large-text">{eligibility_pm}</span>
        </div>
        ''',
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f'''
        <div class="date-header">
            <span class="small-text">Time and Date for Baking List:</span> </br>
            <span class="large-text">{selected_date}</span>
        </div>
        ''',
        unsafe_allow_html=True
    )

tables = None

cupcakes_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][0], AIRTABLE_API_KEY)


def cupcake_total(cupcakes_total):
    # Select only required columns from Airtable
    required_columns = ["Sponge Flavour 1", "Sponge Size 1", "Sponge QTY 1 - Calculated", "Sponge QTY 2 - Calculated", "Lineitem Quantity"]
    
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
    cupcakes_total = cupcakes_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Lineitem Quantity"]].sum()
    
    # Apply CASE-like logic to create a single 'Mix Size' column
    cupcakes_total["Mix Size"] = cupcakes_total.apply(
        lambda row: 0.075 * row["Lineitem Quantity"] if row["Sponge Size 1"] == "Regular Cupcake"
        else 0.02 * row["Lineitem Quantity"] if row["Sponge Size 1"] == "Mini Cupcake"
        else 0, axis=1
    )
    
    # Apply rounding to one decimal place for all relevant numeric columns
    cupcakes_total["Mix Size"] = cupcakes_total["Mix Size"].round(1)

    # Group the data under MINI and REGULAR
    cupcakes_total['Sponge Size 1'] = cupcakes_total['Sponge Size 1'].replace({'Mini Cupcake': 'MINI', 'Regular Cupcake': 'REGULAR'})
    
    cupcakes_total_table = cupcakes_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values=["Lineitem Quantity", "Mix Size"],
        aggfunc="sum",
        fill_value=0
    ).swaplevel(axis=1).sort_index(axis=1).reset_index()
    
    # Select numeric columns for total calculation
    numeric_cols = [col for col in cupcakes_total_table.columns if col != "Sponge Flavour 1" and pd.api.types.is_numeric_dtype(cupcakes_total_table[col])]

    cupcakes_total_table["Grand Total Lineitem Quantity"] = cupcakes_total_table[[col for col in numeric_cols if "Lineitem Quantity" in col]].sum(axis=1)
    cupcakes_total_table["Grand Total Mix Size"] = cupcakes_total_table[[col for col in numeric_cols if "Mix Size" in col]].sum(axis=1)

    # Compute grand total row and round values
    grand_total_row = pd.DataFrame(cupcakes_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    cupcakes_total_table = pd.concat([cupcakes_total_table, grand_total_row], ignore_index=True)
    
    # Flatten MultiIndex columns by joining names with an underscore
    cupcakes_total_table.columns = ['_'.join(col) if isinstance(col, tuple) else col for col in cupcakes_total_table.columns]

    cupcakes_total_table = cupcakes_total_table.round(1)

    st.markdown('<div class="table-header">Total Cupcakes - ONLINE ONLY</div>', unsafe_allow_html=True)
    generate_pivot_table(cupcakes_total_table, "cupcakes_total_table")
        
    return
df = cupcake_total(cupcakes_total) 
