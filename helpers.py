import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import os
from datetime import datetime, timedelta
import time
import threading
import numpy as np
# Function to fetch data from Google Sheets
def get_google_sheets_data(sheet_name, credentials_file, spreadsheet_name, sheet_range):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open(spreadsheet_name)
        values = spreadsheet.worksheet(sheet_name).get_values(sheet_range)
        return pd.DataFrame(values[1:], columns=values[0]) if values else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching Google Sheets data: {e}")
        return pd.DataFrame()

def get_google_sheet_date_data(sheet_name, credentials_file, spreadsheet_name, sheet_range):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open(spreadsheet_name)
        values = spreadsheet.worksheet(sheet_name).get_values(sheet_range)
        return values[0][0] if values and values[0] else "No Date Available"
    except Exception as e:
        st.error(f"Error fetching Google Sheets date: {e}")
        return "No Date Available"

def get_airtable_data(base_id, table_name, view_name, api_key):
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"view": view_name}
    all_records = []

    try:
        while url:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            records = data.get("records", [])
            all_records.extend(records)
            url = data.get("offset", None)  # Check if there's an offset for pagination
            if url:
                url = f"https://api.airtable.com/v0/{base_id}/{table_name}?offset={url}"  # Update URL for next batch

        if not all_records:
            return pd.DataFrame({"Message": ["No Data"]})
        df = pd.DataFrame([record["fields"] for record in all_records])
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching Airtable data: {e}")
        return pd.DataFrame({"Message": ["No Data"]})


def total_baking(reg_total, reg_total_2nd, skinny_total, thin_total, slim_total, low_total, low_total_2nd, sheets_df):
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


    merged_df = pd.concat([reg_total, reg_total_2nd])
    merged_df["Total"] = pd.to_numeric(merged_df["Total"], errors="coerce").fillna(0).astype(int)

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
    skinny_total_table.attrs['name']  = "Cakes - Skinny Total"
    numeric_cols = skinny_total_table.columns.difference(["Sponge Flavour 1"])
    skinny_total_table["Grand Total"] = skinny_total_table[numeric_cols].sum(axis=1)
    numeric_cols = skinny_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(skinny_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    skinny_total_table = pd.concat([skinny_total_table, grand_total_row], ignore_index=True)
    
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
    cakes_slim_table.attrs['name']  = "Cakes - Slim Total"
    numeric_cols = cakes_slim_table.columns.difference(["Sponge Flavour 1"])
    cakes_slim_table["Grand Total"] = cakes_slim_table[numeric_cols].sum(axis=1)
    numeric_cols = cakes_slim_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(cakes_slim_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    cakes_slim_table = pd.concat([cakes_slim_table, grand_total_row], ignore_index=True)
    
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
    print(thin_total_table)
    thin_total_table.attrs['name']  = "Cakes - Thin total"
    numeric_cols = thin_total_table.columns.difference(["Sponge Flavour 1"])
    thin_total_table[numeric_cols] = thin_total_table[numeric_cols].fillna(0).astype(int)
    thin_total_table["Grand Total"] = thin_total_table[numeric_cols].sum(axis=1).astype(int)
    numeric_cols = thin_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(thin_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    thin_total_table = pd.concat([thin_total_table, grand_total_row], ignore_index=True)
    
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
    low_total_table.attrs['name']  = "Cakes - Thin total"
    numeric_cols = low_total_table.columns.difference(["Sponge Flavour 1"])
    low_total_table[numeric_cols] = low_total_table[numeric_cols].fillna(0).astype(int)
    low_total_table["Grand Total"] = low_total_table[numeric_cols].sum(axis=1).astype(int)
    numeric_cols = low_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(low_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    low_total_table = pd.concat([low_total_table, grand_total_row], ignore_index=True)

    st.subheader(f"cakes_reg_table")
    generate_pivot_table(cakes_reg_table, "cakes_reg_table" )
    st.subheader(f"skinny_total_table")
    generate_pivot_table(skinny_total_table, "skinny_total_table")
    st.subheader(f"thin_total_table")
    generate_pivot_table(thin_total_table, "thin_total_table")
    st.subheader(f"cakes_slim_table")
    generate_pivot_table(cakes_slim_table, "cakes_slim_table")
    st.subheader(f"low_total_table")
    generate_pivot_table(low_total_table, "low_total_table")
    
    return 

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

    st.subheader(f"cakes_reg_table")
    generate_pivot_table(cakes_reg_table, "cakes_reg_table" )
    st.subheader(f"skinny_total_table")
    generate_pivot_table(skinny_total_table, "skinny_total_table")
    st.subheader(f"thin_total_table")
    generate_pivot_table(thin_total_table, "thin_total_table")
    st.subheader(f"low_total_table")
    generate_pivot_table(low_total_table, "low_total_table")
    
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

def cupcake_total(cupcakes_total):
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
    column_check(cupcakes_total)
    cupcakes_total = cupcakes_total[required_columns]
    cupcakes_total["Total"] = cupcakes_total["Sponge QTY 1 - Calculated"] 
    cupcakes_total = cupcakes_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Total"]].sum()

    #  Cakes reg Total
    cupcakes_total = cupcakes_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Total"]].sum()
    cupcakes_total_table = cupcakes_total.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Total",
        aggfunc="sum",
        fill_value=0
    ).reset_index() 
    cupcakes_total_table.attrs['name']  = "Cake - Reg Total"
    numeric_cols = cupcakes_total_table.columns.difference(["Sponge Flavour 1"])
    cupcakes_total_table["Grand Total"] = cupcakes_total_table[numeric_cols].sum(axis=1)
    numeric_cols = cupcakes_total_table.columns.difference(["Sponge Flavour 1"])
    grand_total_row = pd.DataFrame(cupcakes_total_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  
    cupcakes_total_table = pd.concat([cupcakes_total_table, grand_total_row], ignore_index=True)
    

    st.subheader(f"Total Cupcakes - ONLINE ONLY")
    generate_pivot_table(cupcakes_total_table, "cupcakes_total_table" )
    
    
    
def highlight_vegan_rows(df):
    if "Sponge Flavour 1" not in df.columns:
        st.error("Column 'Sponge Flavour 1' not found in the dataset.")
        return df  # Return unstyled DataFrame to prevent errors

    def highlight_row(row):
        if isinstance(row["Sponge Flavour 1"], str) and "Vegan" in row["Sponge Flavour 1"]:
            return ['background-color: #2e7d32; color: white; font-weight: bold;'] * len(row)
        return ['background-color: #f9f9f9;' if i % 2 == 0 else 'background-color: #ffffff;' for i in range(len(row))]

    return df.style.apply(highlight_row, axis=1)\
            .set_table_styles([
                {"selector": "th", "props": [("font-weight", "bold"), ("background", "#1565c0"), ("color", "white")]}
            ])\
            .set_properties(**{"border": "1px solid #ddd", "text-align": "center", "padding": "10px"})

def save_table_snapshot(table, table_name):
    """Save a snapshot of the table with a timestamp."""
    versions_dir = "versions"
    os.makedirs(versions_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(versions_dir, f"{table_name}_{timestamp}.csv")
    
    table.to_csv(file_path, index=False)

def cleanup_old_snapshots():
    """Delete table snapshots older than 2 days."""
    versions_dir = "versions"
    if not os.path.exists(versions_dir):
        return

    threshold = datetime.now() - timedelta(days=2)
    
    for filename in os.listdir(versions_dir):
        file_path = os.path.join(versions_dir, filename)
        try:
            # Extract timestamp correctly assuming filename format: table_name_YYYY-MM-DD_HH-MM-SS.csv
            timestamp_str = "_".join(filename.split("_")[-2:]).replace(".csv", "")
            file_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
            if file_time < threshold:
                os.remove(file_path)
        except Exception as e:
            st.error(f"Error cleaning up old snapshots: {e}")

def auto_save_versions(pivot_table, name):
    """Automatically save table snapshots every hour."""
    while True:
        save_table_snapshot(pivot_table, name)
        cleanup_old_snapshots()
        time.sleep(3600)  # 1 hour

def generate_pivot_table(pivot_table, name):
    """Generate a pivot table with cleanup and styling."""
    cleanup_old_snapshots()

    # Apply styling after pivoting
    styled_pivot = highlight_vegan_rows(pivot_table)
    st.dataframe(styled_pivot)

    save_thread = threading.Thread(target=auto_save_versions, args=(pivot_table, name), daemon=True)
    save_thread.start()
    
def refresh_data():
    """Periodically refresh data every 5 minutes."""
    while True:
        st.rerun()
        time.sleep(300)  # 300 seconds = 5 minutes

refresh_thread = threading.Thread(target=refresh_data, daemon=True)
refresh_thread.start()