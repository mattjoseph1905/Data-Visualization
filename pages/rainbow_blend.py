import pandas as pd
import streamlit as st
import time
import numpy as np
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

config = TABLE_CONFIG["NEW: RAINBOW SPONGE - BLEND"]

st.markdown('<div class="page-header">BAKING LIST</div>', unsafe_allow_html=True)

tables = None

thin_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][3], AIRTABLE_API_KEY)
slim_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][4], AIRTABLE_API_KEY)

def rainbow_sponge_blend(thin_total, slim_total):
    required_columns = ["Sponge Size 1", "Sponge QTY 1 - Calculated", "Order ID", "Blue MIX (KG)", "Green MIX (KG)", "Orange MIX (KG)", "Purple MIX (KG)", "Red MIX (KG)", "Yellow MIX (KG)"]
    
    def column_check(x):
        for col in required_columns:
            if col not in x.columns:
                x[col] = None
    
    column_check(thin_total)
    column_check(slim_total)

    mix_columns = ["Blue MIX (KG)", "Green MIX (KG)", "Orange MIX (KG)", "Purple MIX (KG)", "Red MIX (KG)", "Yellow MIX (KG)"]

    for col in mix_columns:
        if col not in thin_total.columns:
            thin_total[col] = 0
        if col not in slim_total.columns:
            slim_total[col] = 0

    thin_total = thin_total.copy()
    slim_total = slim_total.copy()

    thin_conditions = [
        thin_total["Sponge Size 1"] == '7" Round',
        thin_total["Sponge Size 1"] == '9" Round',
        thin_total["Sponge Size 1"] == 'Half 9" Round'
    ]

    slim_conditions = [
        slim_total["Sponge Size 1"] == '7" Round',
        slim_total["Sponge Size 1"] == '9" Round',
        slim_total["Sponge Size 1"] == 'Half 9" Round'
    ]

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

    for col in mix_columns:
        thin_total[col] = np.select(thin_conditions, thin_values)
        slim_total[col] = np.select(slim_conditions, slim_values)
        
    thin_total = thin_total[required_columns]
    slim_total = slim_total[required_columns]

    for col in mix_columns:
        if col not in thin_total.columns:
            thin_total[col] = 0
        if col not in slim_total.columns:
            slim_total[col] = 0
            
    rainbow_blend = pd.concat([thin_total, slim_total], ignore_index=True)

    rainbow_blend.loc[0, "Blue MIX"] = thin_total["Blue MIX (KG)"].max() + slim_total["Blue MIX (KG)"].max()
    rainbow_blend.loc[0, "Green MIX"] = thin_total["Green MIX (KG)"].max() + slim_total["Green MIX (KG)"].max()
    rainbow_blend.loc[0, "Orange MIX"] = thin_total["Orange MIX (KG)"].max() + slim_total["Orange MIX (KG)"].max()
    rainbow_blend.loc[0, "Purple MIX"] = thin_total["Purple MIX (KG)"].max() + slim_total["Purple MIX (KG)"].max()
    rainbow_blend.loc[0, "Red MIX"] = thin_total["Red MIX (KG)"].max() + slim_total["Red MIX (KG)"].max()
    rainbow_blend.loc[0, "Yellow MIX"] = thin_total["Yellow MIX (KG)"].max() + slim_total["Yellow MIX (KG)"].max()

    expected_columns = ["Sponge Size 1", "Blue MIX (KG)", "Green MIX (KG)", "Orange MIX (KG)", "Purple MIX (KG)", "Red MIX (KG)", "Yellow MIX (KG)"]
    rainbow_blend = rainbow_blend[expected_columns]

    rainbow_blend = rainbow_blend.groupby(["Sponge Size 1"], as_index=False).sum().round(1)

    rainbow_blend_table = rainbow_blend.pivot_table(
        index="Sponge Size 1",
        fill_value=0
    ).reset_index() 

    # Adding hierarchical column grouping
    rainbow_blend_table.columns = pd.MultiIndex.from_tuples(
        [('Sponge Size 1', ''), 
         ('MINI', 'Lineitem Quantity'), 
         ('MINI', 'Blue MIX (KG)'), 
         ('MINI', 'Green MIX (KG)'), 
         ('MINI', 'Orange MIX (KG)'), 
         ('MINI', 'Purple MIX (KG)'), 
         ('MINI', 'Red MIX (KG)'), 
         ('MINI', 'Yellow MIX (KG)')]
    )

    numeric_cols = rainbow_blend_table.columns.difference([('Sponge Size 1', '')])
    grand_total_row = pd.DataFrame(rainbow_blend_table[numeric_cols].sum()).T
    grand_total_row.insert(0, ("Sponge Size 1", ""), "Grand Total")  
    rainbow_blend_table = pd.concat([rainbow_blend_table, grand_total_row], ignore_index=True)

    st.markdown('<div class="table-header">ALL RAINBOW BLEND</div>', unsafe_allow_html=True)
    generate_pivot_table(rainbow_blend_table, "rainbow_blend_table")
    return

df = rainbow_sponge_blend(thin_total, slim_total)  
