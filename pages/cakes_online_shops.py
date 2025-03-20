import pandas as pd
import streamlit as st
import time
from helpers import generate_pivot_table
from config import TABLE_CONFIG
from helpers import (
    get_google_sheets_data,
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

config = TABLE_CONFIG["ONLINE + SHOPS"]
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

reg_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][0], AIRTABLE_API_KEY)
reg_total_2nd = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][1], AIRTABLE_API_KEY)
skinny_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][2], AIRTABLE_API_KEY)
thin_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][3], AIRTABLE_API_KEY)
slim_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][4], AIRTABLE_API_KEY)
low_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][5], AIRTABLE_API_KEY)
low_total_2nd = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][6], AIRTABLE_API_KEY)

# Fetch Google Sheets Data
reg_sheet = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, config["sheet_range"][0])
gf_reg_sheet = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, config["sheet_range"][1])
thin_sheet = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, config["sheet_range"][2])
low_sheet = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, config["sheet_range"][3])
skinny_sheet = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, config["sheet_range"][4])
cheesecake_sheet = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, config["sheet_range"][5])

def online_shops(reg_total, reg_total_2nd, skinny_total, thin_total, slim_total, low_total, low_total_2nd, reg_sheet, gf_reg_sheet, thin_sheet, low_sheet, skinny_sheet, cheesecake_sheet):
    # Select only required columns from Airtable
    required_columns = ["Sponge Flavour 1", "Sponge Size 1", "Sponge QTY 1 - Calculated", "Sponge QTY 2 - Calculated", "Order ID"]
    sheet_required_columns = ["Sponge Flavour 1", "Sponge Size 1", "Total"]
    # Ensure required columns exist in both dataframes
    def column_check(x):
        for col in required_columns:
            if col not in x.columns:
                x[col] = None  # Add missing columns
            if col not in x.columns:
                x[col] = None  # Add missing columns

    # Filter only the required columns
    column_check(reg_total)
    reg_total = reg_total[required_columns]
    reg_total_2nd = reg_total_2nd[required_columns]
    reg_total["Total"] = reg_total["Sponge QTY 1 - Calculated"] 
    reg_total_2nd["Total"] = reg_total_2nd["Sponge QTY 2 - Calculated"]
    reg_total = reg_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Total"]].sum()
    reg_total_2nd = reg_total_2nd.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Total"]].sum()

    reg_sheet["Sponge Flavour 1"] = reg_sheet["Sponge Flavour"]
    reg_sheet["Sponge Size 1"] = reg_sheet["Sponge Size"]
    reg_sheet = reg_sheet[sheet_required_columns]
    
    reg_sheet["Total"] = pd.to_numeric(reg_sheet["Total"], errors="coerce").fillna(0).astype(int)
    merged_df = pd.concat([reg_total, reg_total_2nd])
    merged_df["Total"] = pd.to_numeric(merged_df["Total"], errors="coerce").fillna(0).astype(int)
    merged_df = pd.concat([merged_df, reg_sheet])

    #  Cakes reg Total
    merged_df = merged_df.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Total"]].sum()
    cakes_reg_table = merged_df.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Total",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 
    cakes_reg_table.attrs['name']  = "Cake - Reg Total"
    numeric_cols = cakes_reg_table.columns.difference(["Sponge Flavour 1"])
    cakes_reg_table["Grand Total"] = cakes_reg_table[numeric_cols].sum(axis=1)
    numeric_cols = cakes_reg_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(cakes_reg_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    cakes_reg_table = pd.concat([cakes_reg_table, grand_total_row], ignore_index=True)
    st.markdown(
        '<div class="table-header">Cakes - Reg Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(cakes_reg_table, "Cakes - Reg Sponge Total" )
    
    # Cakes Skinny Total
    column_check(skinny_total)
    skinny_total = skinny_total[required_columns]
    skinny_total = pd.concat([skinny_total, skinny_sheet])
    skinny_total_table = skinny_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Sponge QTY 1 - Calculated",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 
    skinny_total_table.attrs['name']  = "Cakes - Skinny Total"
    numeric_cols = skinny_total_table.columns.difference(["Sponge Flavour 1"])
    skinny_total_table["Grand Total"] = skinny_total_table[numeric_cols].sum(axis=1)
    numeric_cols = skinny_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(skinny_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    skinny_total_table = pd.concat([skinny_total_table, grand_total_row], ignore_index=True)
    st.markdown(
        '<div class="table-header">Cakes - Skinny Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(skinny_total_table, "Cakes - Skinny Sponge Total")
    
    # Cakes Thin Total
    column_check(thin_total)
    thin_total = thin_total[required_columns]
    thin_total = pd.concat([thin_total, thin_sheet])
    thin_total = thin_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Sponge QTY 1 - Calculated"]].sum()
    thin_total_table = thin_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Sponge QTY 1 - Calculated",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 
    print(thin_total_table)
    thin_total_table.attrs['name']  = "Cakes - Thin total"
    numeric_cols = thin_total_table.columns.difference(["Sponge Flavour 1"])
    thin_total_table[numeric_cols] = thin_total_table[numeric_cols].fillna(0).astype(int)
    thin_total_table["Grand Total"] = thin_total_table[numeric_cols].sum(axis=1).astype(int)
    numeric_cols = thin_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(thin_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    thin_total_table = pd.concat([thin_total_table, grand_total_row], ignore_index=True)
    st.markdown(
        '<div class="table-header">Cakes - Thin Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(thin_total_table, "Cakes - Thin Sponge Total")
    
    # Cakes Low Total
    column_check(low_total)
    column_check(low_total_2nd)
    low_total = low_total[required_columns]
    low_total = pd.concat([low_total, low_total_2nd, low_sheet])
    low_total = low_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Sponge QTY 1 - Calculated"]].sum()
    low_total_table = low_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Sponge QTY 1 - Calculated",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 
    low_total_table.attrs['name']  = "Cakes - Thin total"
    numeric_cols = low_total_table.columns.difference(["Sponge Flavour 1"])
    low_total_table[numeric_cols] = low_total_table[numeric_cols].fillna(0).astype(int)
    low_total_table["Grand Total"] = low_total_table[numeric_cols].sum(axis=1).astype(int)
    numeric_cols = low_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(low_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    low_total_table = pd.concat([low_total_table, grand_total_row], ignore_index=True)
    st.markdown(
        '<div class="table-header">Cakes - Low Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(low_total_table, "Cakes - Low Sponge Total")
    return

df = online_shops(reg_total, reg_total_2nd, skinny_total, thin_total, slim_total, low_total, low_total_2nd, reg_sheet, gf_reg_sheet, thin_sheet, low_sheet, skinny_sheet, cheesecake_sheet)  
