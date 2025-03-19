import pandas as pd
import streamlit as st
import time
import numpy as np
from helpers import generate_pivot_table
from config import TABLE_CONFIG
from helpers import (
    get_google_sheets_data,
    get_google_sheet_date_data,
    get_airtable_data,
)
import streamlit.components.v1 as components
import json

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Get secrets
AIRTABLE_API_KEY = st.secrets["AIRTABLE"]["PERSONAL_ACCESS_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE"]["BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE"]["TABLE_NAME"]
GOOGLE_SHEET_CREDENTIALS_FILE = st.secrets["GOOGLE_SHEET"]["CREDENTIALS_FILE"]
GOOGLE_SHEET_NAME = st.secrets["GOOGLE_SHEET"]["NAME"]

config = TABLE_CONFIG["Total Baking - Cakes"]

    
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
        f'<div style="background-color: rgba(150, 110, 255, 0.7); padding: 10px; text-align: center; color: white; font-size: 20px; font-weight: bold; border-radius: 5px; width: 500px; margin-bottom: 20px">BAKING LIST</div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f'<div class="date-header" style="display: inline-block; background-color: rgba(255, 230, 150, 0.7); color: black; padding: 5px; border-radius: 5px; width: 500px; margin-bottom: 20px">{selected_date}</div>',
        unsafe_allow_html=True
    )

# Move the "Refresh Data" button to the sidebar
with st.sidebar:
    if st.button("Refresh Data", key="refresh_button"):
        st.session_state["refresh_trigger"] = time.time()

tables = None

# Fetch Airtable Data
reg_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][0], AIRTABLE_API_KEY)
reg_total_2nd = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][1], AIRTABLE_API_KEY)
skinny_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][2], AIRTABLE_API_KEY)
thin_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][3], AIRTABLE_API_KEY)
slim_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][4], AIRTABLE_API_KEY)
low_total = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][5], AIRTABLE_API_KEY)
low_total_2nd = get_airtable_data(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, config["airtable_views"][6], AIRTABLE_API_KEY)

# Fetch Google Sheets Data
reg_sheet = get_google_sheets_data(config["google_sheet_name"], GOOGLE_SHEET_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, config["sheet_range"])

def total_baking(reg_total, reg_total_2nd, skinny_total, thin_total, slim_total, low_total, low_total_2nd, sheets_df):
    # Select only required columns from Airtable
    required_columns = ["Sponge Flavour 1", "Sponge Size 1", "Sponge QTY 1 - Calculated", "Sponge QTY 2 - Calculated", "Order ID"]
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

    merged_df = pd.concat([reg_total, reg_total_2nd])
    merged_df["Total"] = pd.to_numeric(merged_df["Total"], errors="coerce").fillna(0).astype(int)

    # Pivot table so that "Sponge Size" becomes columns and "Total" is the metric
    df = merged_df.pivot_table(index="Sponge Flavour 1", columns="Sponge Size 1", values="Total", aggfunc="sum", fill_value=0).reset_index()

    # Add Grand Total column
    df["Grand Total"] = df.select_dtypes(include=[np.number]).sum(axis=1)

    # Add Grand Total row
    grand_total_row = df.sum(numeric_only=True)
    grand_total_row["Sponge Flavour 1"] = "Grand Total"
    df = pd.concat([df, grand_total_row.to_frame().T], ignore_index=True)
    st.markdown(
        f'<div style="background-color: #fba0e3; padding: 10px; text-align: center; color: white; font-size: 20px; font-weight: bold; border-radius: 5px; width: 1000px; margin-bottom: 20px">Cakes - Reg Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(df, "Cakes - Reg Sponge Total")
    # Display the grand total in a text box below the first table
    grand_total = merged_df["Total"].sum()
    st.markdown(
        f'<div style="background-color: #fad6a5; padding: 10px; text-align: center; font-size: 18px; font-weight: bold; border-radius: 5px; margin-bottom: 20px">Grand Total: {grand_total}</div>',
        unsafe_allow_html=True
    )
    
    # Cakes Skinny Total
    column_check(skinny_total)
    skinny_total = skinny_total[required_columns]
    skinny_total_table = skinny_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Sponge QTY 1 - Calculated",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 

    # Add Grand Total column
    skinny_total_table["Grand Total"] = skinny_total_table.select_dtypes(include=[np.number]).sum(axis=1)

    # Add Grand Total row
    grand_total_row = skinny_total_table.sum(numeric_only=True)
    grand_total_row["Sponge Flavour 1"] = "Grand Total"
    skinny_total_table = pd.concat([skinny_total_table, grand_total_row.to_frame().T], ignore_index=True)

    skinny_total_table.attrs['name']  = "Cakes - Skinny Total"
    numeric_cols = skinny_total_table.columns.difference(["Sponge Flavour 1"])
    skinny_total_table["Grand Total"] = skinny_total_table[numeric_cols].sum(axis=1)
    numeric_cols = skinny_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(skinny_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    skinny_total_table = pd.concat([skinny_total_table, grand_total_row], ignore_index=True)
    st.markdown(
        f'<div style="background-color: #fba0e3; padding: 10px; text-align: center; color: white; font-size: 20px; font-weight: bold; border-radius: 5px; width: 1000px; margin-bottom: 20px">Cakes - Skinny Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(skinny_total_table, "skinny_Cake - Skinny Sponge Totalotal_table")
    
    # Cakes Slim Total
    column_check(slim_total)
    slim_total = slim_total[required_columns]
    cakes_slim_table = slim_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Sponge QTY 1 - Calculated",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 

    # Add Grand Total column
    cakes_slim_table["Grand Total"] = cakes_slim_table.select_dtypes(include=[np.number]).sum(axis=1)

    # Add Grand Total row
    grand_total_row = cakes_slim_table.sum(numeric_only=True)
    grand_total_row["Sponge Flavour 1"] = "Grand Total"
    cakes_slim_table = pd.concat([cakes_slim_table, grand_total_row.to_frame().T], ignore_index=True)

    cakes_slim_table.attrs['name']  = "Cakes - Slim Total"
    numeric_cols = cakes_slim_table.columns.difference(["Sponge Flavour 1"])
    cakes_slim_table["Grand Total"] = cakes_slim_table[numeric_cols].sum(axis=1)
    numeric_cols = cakes_slim_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(cakes_slim_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    cakes_slim_table = pd.concat([cakes_slim_table, grand_total_row], ignore_index=True)
    st.markdown(
        f'<div style="background-color: #fba0e3; padding: 10px; text-align: center; color: white; font-size: 20px; font-weight: bold; border-radius: 5px; width: 1000px; margin-bottom: 20px">Cakes - Slim Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(cakes_slim_table, "Cakes - Slim Sponge Total")
    
    # Cakes Thin Total
    column_check(thin_total)
    thin_total = thin_total[required_columns]
    thin_total = thin_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Sponge QTY 1 - Calculated"]].sum()
    thin_total_table = thin_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Sponge QTY 1 - Calculated",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 

    # Add Grand Total column
    thin_total_table["Grand Total"] = thin_total_table.select_dtypes(include=[np.number]).sum(axis=1)

    # Add Grand Total row
    grand_total_row = thin_total_table.sum(numeric_only=True)
    grand_total_row["Sponge Flavour 1"] = "Grand Total"
    thin_total_table = pd.concat([thin_total_table, grand_total_row.to_frame().T], ignore_index=True)

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
        f'<div style="background-color: #fba0e3; padding: 10px; text-align: center; color: white; font-size: 20px; font-weight: bold; border-radius: 5px; width: 1000px; margin-bottom: 20px">Cakes - Thin Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(thin_total_table, "Cakes - Thin Sponge Total")
    
    # Cakes Low Total
    column_check(low_total)
    column_check(low_total_2nd)
    low_total = low_total[required_columns]
    low_total = pd.concat([low_total, low_total_2nd])
    low_total = low_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Sponge QTY 1 - Calculated"]].sum()
    low_total_table = low_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Sponge QTY 1 - Calculated",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 

    # Add Grand Total column
    low_total_table["Grand Total"] = low_total_table.select_dtypes(include=[np.number]).sum(axis=1)

    # Add Grand Total row
    grand_total_row = low_total_table.sum(numeric_only=True)
    grand_total_row["Sponge Flavour 1"] = "Grand Total"
    low_total_table = pd.concat([low_total_table, grand_total_row.to_frame().T], ignore_index=True)

    low_total_table.attrs['name']  = "Cakes - Thin total"
    numeric_cols = low_total_table.columns.difference(["Sponge Flavour 1"])
    low_total_table[numeric_cols] = low_total_table[numeric_cols].fillna(0).astype(int)
    low_total_table["Grand Total"] = low_total_table[numeric_cols].sum(axis=1).astype(int)
    numeric_cols = low_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(low_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    low_total_table = pd.concat([low_total_table, grand_total_row], ignore_index=True)
    st.markdown(
        f'<div style="background-color: #fba0e3; padding: 10px; text-align: center; color: white; font-size: 20px; font-weight: bold; border-radius: 5px; width: 1000px; margin-bottom: 20px">Cakes - Low Sponge Total</div>',
        unsafe_allow_html=True
    )
    generate_pivot_table(low_total_table, "Cakes - Low Sponge Total")
    return 

df = total_baking(reg_total, reg_total_2nd, skinny_total, thin_total, slim_total, low_total, low_total_2nd, reg_sheet)    
