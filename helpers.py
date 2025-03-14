import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import json
from google.oauth2.service_account import Credentials

# Function to fetch data from Google Sheets
def get_google_sheets_data(sheet_name, credentials_file, spreadsheet_name, sheet_range):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict)
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

        df = pd.DataFrame([record["fields"] for record in all_records]) if all_records else pd.DataFrame()
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching Airtable data: {e}")
        return pd.DataFrame()


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

    sheets_df["Sponge Flavour 1"] = sheets_df["Sponge Flavour"]
    sheets_df["Sponge Size 1"] = sheets_df["Sponge Size"]
    sheets_df = sheets_df[sheet_required_columns]

    merged_df = pd.concat([reg_total, reg_total_2nd])
    numeric_columns = ["Total"]
    for col in numeric_columns:
        merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce").fillna(0)

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

    st.subheader(f"cakes_reg_table")
    generate_pivot_table(cakes_reg_table)
    st.subheader(f"skinny_total_table")
    generate_pivot_table(skinny_total_table)
    st.subheader(f"thin_total_table")
    generate_pivot_table(thin_total_table)
    st.subheader(f"cakes_slim_table")
    generate_pivot_table(cakes_slim_table)
    
    return 

def online_shops(reg_total, reg_total_2nd, sheets_df):
    # Select only required columns from Airtable
    required_columns = ["Sponge Flavour 1", "Sponge Size 1", "Sponge QTY 1 - Calculated", "Sponge QTY 2 - Calculated", "Order ID"]
    sheet_required_columns = ["Sponge Flavour 1", "Sponge Size 1", "Total"]
    # Ensure required columns exist in both dataframes
    for col in required_columns:
        if col not in reg_total.columns:
            reg_total[col] = None  # Add missing columns
        if col not in reg_total_2nd.columns:
            reg_total_2nd[col] = None  # Add missing columns

    # Filter only the required columns
    reg_total = reg_total[required_columns]
    reg_total_2nd = reg_total_2nd[required_columns]
    reg_total["Total"] = reg_total["Sponge QTY 1 - Calculated"]
    reg_total_2nd["Total"] = reg_total_2nd["Sponge QTY 2 - Calculated"]
    reg_total = reg_total.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Total"]].sum()
    reg_total_2nd = reg_total_2nd.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Total"]].sum()

    sheets_df["Sponge Flavour 1"] = sheets_df["Sponge Flavour"]
    sheets_df["Sponge Size 1"] = sheets_df["Sponge Size"]
    sheets_df = sheets_df[sheet_required_columns]
    
    merged_df = pd.concat([reg_total, reg_total_2nd, sheets_df])
    numeric_columns = ["Total"]
    for col in numeric_columns:
        merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce").fillna(0)

    merged_df = merged_df.groupby(["Sponge Flavour 1", "Sponge Size 1"], as_index=False)[[ "Total"]].sum()
        # Generate Pivot Table
    pivot_table = merged_df.pivot_table(
        index="Sponge Flavour 1",
        columns="Sponge Size 1",
        values="Total",
        aggfunc="sum",
        fill_value=0
    ).reset_index()  # Reset index to make 'Sponge Flavour 1' a column

    numeric_cols = [col for col in pivot_table.columns if col != "Sponge Flavour 1"]

    pivot_table[numeric_cols] = pivot_table[numeric_cols].fillna(0).astype(int)

    # Add "Grand Total" column (row-wise total)
    pivot_table["Grand Total"] = pivot_table[numeric_cols].sum(axis=1).astype(int)

    # Add Grand Total Column (sum across rows)
    numeric_cols = pivot_table.columns.difference(["Sponge Flavour 1"])
    
    # Add Grand Total Row (sum across columns)
    grand_total_row = pd.DataFrame(pivot_table[numeric_cols].sum()).T
    grand_total_row.insert(0, "Sponge Flavour 1", "Grand Total")  # Ensure Grand Total row has a label

    # Append Grand Total Row
    pivot_table = pd.concat([pivot_table, grand_total_row], ignore_index=True)

    return pivot_table

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

def generate_pivot_table(pivot_table):
    # Apply styling after pivoting
    styled_pivot = highlight_vegan_rows(pivot_table)
    st.dataframe(styled_pivot)
