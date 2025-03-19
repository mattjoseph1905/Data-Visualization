    
import pandas as pd
import streamlit as st
import time
import numpy as np
from helpers import generate_pivot_table
import streamlit as st
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

st.title("NEW: RAINBOW SPONGE - BLEND")
config = TABLE_CONFIG["NEW: RAINBOW SPONGE - BLEND"]

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
        f'<div class="date-header" style="display: inline-block; background-color: rgba(255, 230, 150, 0.7); color: black; padding: 5px; border-radius: 5px; width: 500px; margin-bottom: 20px">RAINBOW BLEND</div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f'<div class="date-header" style="display: inline-block; background-color: rgba(255, 230, 150, 0.7); color: black; padding: 5px; border-radius: 5px; width: 500px; margin-bottom: 20px">{selected_date}</div>',
        unsafe_allow_html=True
    )
tables = None

thin_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][3], AIRTABLE_API_KEY)
slim_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][4], AIRTABLE_API_KEY)

    
def rainbow_sponge_blend(thin_total, slim_total):
       # Select only required columns from Airtable
    required_columns = ["Sponge Size 1", "Sponge QTY 1 - Calculated", "Order ID", "Blue MIX (KG)", "Green MIX (KG)", "Orange MIX (KG)", "Purple MIX (KG)", "Red MIX (KG)", "Yellow MIX (KG)"]
    # Ensure required columns exist in both dataframes
    def column_check(x):
        for col in required_columns:
            if col not in x.columns:
                x[col] = None  # Add missing columns
            if col not in x.columns:
                x[col] = None  # Add missing columns
    
    
    # Cakes Thin Total
    column_check(thin_total)
    column_check(slim_total)

    # Ensure all mix columns exist
    mix_columns = ["Blue MIX (KG)", "Green MIX (KG)", "Orange MIX (KG)", "Purple MIX (KG)", "Red MIX (KG)", "Yellow MIX (KG)"]

    for col in mix_columns:
        if col not in thin_total.columns:
            thin_total[col] = 0
        if col not in slim_total.columns:
            slim_total[col] = 0

    # Ensure DataFrames are copies (to avoid SettingWithCopyWarning)
    thin_total = thin_total.copy()
    slim_total = slim_total.copy()

    # Define conditions separately for thin_total
    thin_conditions = [
        thin_total["Sponge Size 1"] == '7" Round',
        thin_total["Sponge Size 1"] == '9" Round',
        thin_total["Sponge Size 1"] == 'Half 9" Round'
    ]

    # Define conditions separately for slim_total
    slim_conditions = [
        slim_total["Sponge Size 1"] == '7" Round',
        slim_total["Sponge Size 1"] == '9" Round',
        slim_total["Sponge Size 1"] == 'Half 9" Round'
    ]

    # Define values separately for each DataFrame
    thin_values = [
        0.23 * thin_total["Sponge QTY 1 - Calculated"],
        0.40 * thin_total["Sponge QTY 1 - Calculated"],
        0.20 * thin_total["Sponge QTY 1 - Calculated"]
    ]

    slim_values = [
        0.23 * slim_total["Sponge QTY 1 - Calculated"],
        0.40 * slim_total["Sponge QTY 1 - Calculated"],
        0.20 * slim_total["Sponge QTY 1 - Calculated"]
    ]
    
    # Apply separately to each DataFrame
    for col in mix_columns:
        thin_total[col] = np.select(thin_conditions, thin_values)
        slim_total[col] = np.select(slim_conditions, slim_values)
        
    print(thin_total, slim_total)
    print("Updated thin_total columns:", thin_total.columns)
    print("Updated slim_total columns:", slim_total.columns)
    
    thin_total = thin_total[required_columns]
    slim_total = slim_total[required_columns]
    
    # Ensure all mix columns exist in thin_total and slim_total
    mix_columns = ["Blue MIX (KG)", "Green MIX (KG)", "Orange MIX (KG)", "Purple MIX (KG)", "Red MIX (KG)", "Yellow MIX (KG)"]

    for col in mix_columns:
        if col not in thin_total.columns:
            thin_total[col] = 0  # Add missing column with default value
        if col not in slim_total.columns:
            slim_total[col] = 0  # Add missing column with default value
            
     # Concatenate the results ensuring all columns are present
    rainbow_blend = pd.concat([thin_total, slim_total], ignore_index=True)


    # Manually compute mix totals
    rainbow_blend.loc[0, "Blue MIX"] = thin_total["Blue MIX (KG)"].max() + slim_total["Blue MIX (KG)"].max()
    rainbow_blend.loc[0, "Green MIX"] = thin_total["Green MIX (KG)"].max() + slim_total["Green MIX (KG)"].max()
    rainbow_blend.loc[0, "Orange MIX"] = thin_total["Orange MIX (KG)"].max() + slim_total["Orange MIX (KG)"].max()
    rainbow_blend.loc[0, "Purple MIX"] = thin_total["Purple MIX (KG)"].max() + slim_total["Purple MIX (KG)"].max()
    rainbow_blend.loc[0, "Red MIX"] = thin_total["Red MIX (KG)"].max() + slim_total["Red MIX (KG)"].max()
    rainbow_blend.loc[0, "Yellow MIX"] =thin_total["Yellow MIX (KG)"].max() + slim_total["Yellow MIX (KG)"].max()

    # Ensure columns exist before pivoting
    expected_columns = ["Sponge Size 1", "Blue MIX (KG)", "Green MIX (KG)", "Orange MIX (KG)", "Purple MIX (KG)", "Red MIX (KG)", "Yellow MIX (KG)"]
    rainbow_blend = rainbow_blend[expected_columns]

    # Group by sponge size and sum mix values
    rainbow_blend = rainbow_blend.groupby(["Sponge Size 1"], as_index=False).sum()
    print(rainbow_blend)
    # Debugging
    print("Rainbow Blend DataFrame before pivot:")
    print(rainbow_blend.head())
    print("Columns:", rainbow_blend.columns)
    
    rainbow_blend_table = rainbow_blend.pivot_table(
        index="Sponge Size 1",
        fill_value=0
    ).reset_index() 
    rainbow_blend_table.attrs['name']  = "Cakes - Thin total"
    numeric_cols = rainbow_blend_table.columns
    
    # Identify numeric columns excluding text-based ones
    numeric_cols = rainbow_blend_table.select_dtypes(include=['number']).columns

    # Convert only numeric columns to integers
    numeric_cols = rainbow_blend_table.columns.difference(["Sponge Size 1"])
    grand_total_row = pd.DataFrame(rainbow_blend_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Size 1", "Grand Total")  
    rainbow_blend_table = pd.concat([rainbow_blend_table, grand_total_row], ignore_index=True)

    st.subheader(f"ALL RAINBOW BLEND")
    generate_pivot_table(rainbow_blend_table, "rainbow_blend_table")
    return
df = rainbow_sponge_blend(thin_total, slim_total)  
