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
import json
import streamlit.components.v1 as components
from google.oauth2.service_account import Credentials

# Function to fetch data from Google Sheets
def get_google_sheets_data(sheet_name, spreadsheet_name, sheet_range):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])  
        client = gspread.authorize(creds)
        spreadsheet = client.open(spreadsheet_name)
        values = spreadsheet.worksheet(sheet_name).get_values(sheet_range)
        return pd.DataFrame(values[1:], columns=values[0]) if values else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching Google Sheets data: {e}")
        return pd.DataFrame()

def get_google_sheet_date_data(sheet_name, spreadsheet_name, sheet_range):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])  

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

    
    
def highlight_vegan_rows(df):
    if "Sponge Flavour 1" not in df.columns:
        st.error("Column 'Sponge Flavour 1' not found in the dataset.")
        return df

    def highlight_row(row):
        if isinstance(row["Sponge Flavour 1"], str) and "Vegan" in row["Sponge Flavour 1"]:
            return ['background-color: #10B981; color: white; font-weight: bold;'] * len(row)
        return ['background-color: #F9FAFB;' if idx % 2 == 0 else 'background-color: #FFFFFF;' for idx in range(len(row))]

    return df.style.apply(highlight_row, axis=1)\
        .set_table_styles([
            {"selector": "thead th", "props": [("background", "#FFFFFF"), 
                                               ("color", "#111827"), 
                                               ("font-weight", "600"), 
                                               ("text-align", "left"), 
                                               ("padding", "14px"), 
                                               ("border-bottom", "2px solid #E5E7EB")]},
            {"selector": "td", "props": [("border-bottom", "1px solid #E5E7EB"), 
                                         ("padding", "12px"), 
                                         ("text-align", "left")]},
            {"selector": "tbody tr:hover", "props": [("background", "#F3F4F6")]},
            {"selector": "tbody tr.vegan", "props": [("background", "#10B981"), 
                                                     ("color", "white"), 
                                                     ("font-weight", "bold")]}
        ])\
        .set_properties(**{"border": "none", "padding": "12px", "background-color": "#FFFFFF", "color": "#374151"})

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

def generate_pivot_table(df, name):

    df_json = json.dumps(df.to_dict(orient="records"))

    html_code = f"""
        <script src="https://cdn.tailwindcss.com"></script>
        <div class="relative w-full">
            <table class="min-w-full text-sm text-left text-gray-500 dark:text-gray-400 border border-gray-300 dark:border-gray-700" style="table-layout: auto;">
                <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400 border-b border-gray-300 dark:border-gray-700">
                    <tr>
                        <th scope="col" class="px-4 py-2 min-w-[50px]">Index</th>
                        <!-- Header columns will be inserted dynamically by JavaScript -->
                    </tr>
                </thead>
                <tbody id="tableBody" class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 divide-y divide-gray-300 dark:divide-gray-700">
                    <!-- Table rows will be inserted dynamically by JavaScript -->
                </tbody>
            </table>
        </div>

        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                var tableData = {df_json}; // Pass DataFrame data into JavaScript

                // Get column names dynamically from the first record
                var columns = Object.keys(tableData[0]);

                // Dynamically create table headers
                var theadRow = document.querySelector('thead tr');
                columns.forEach(function(column) {{
                    var th = document.createElement('th');
                    th.scope = 'col';
                    th.className = 'px-4 py-2 min-w-[150px]';
                    th.innerText = column;
                    theadRow.appendChild(th);
                }});

                // Dynamically create table rows
                var tableBody = document.getElementById("tableBody");
                tableData.forEach(function(row, index) {{
                    var tr = document.createElement("tr");
                    if (row["Sponge Flavour 1"] && row["Sponge Flavour 1"].toLowerCase().includes("vegan")) {{
                        tr.className = "bg-green-200 dark:bg-green-800 border border-gray-300 dark:border-gray-700 hover:bg-green-300 dark:hover:bg-green-900 whitespace-nowrap";
                    }} else {{
                        tr.className = "odd:bg-white odd:dark:bg-gray-900 even:bg-gray-50 even:dark:bg-gray-800 border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 whitespace-nowrap";
                    }}

                    // Add index column
                    tr.innerHTML = `<td class="px-4 py-2 text-center">${{index + 1}}</td>`;
                    Object.values(row).forEach(function(cell) {{
                        var td = document.createElement("td");
                        td.className = "px-4 py-2";
                        td.innerText = cell || "0"; // Fallback value for empty cells
                        tr.appendChild(td);
                    }});
                    tableBody.appendChild(tr);
                }});
            }});
        </script>
    """

    # Calculate the height dynamically based on the number of rows
    row_count = len(df)  # Number of rows in the table
    row_height = 35  # Height for each row (you can adjust this value)
    header_height = 100  # Height for the header

    # Set the height dynamically based on row count
    table_height = header_height + (row_count * row_height)

    # Set a minimum height (to avoid too small a height)
    table_height = max(table_height, 100)  # Ensure it is at least 600px

    components.html(html_code, height=table_height)

    save_thread = threading.Thread(target=auto_save_versions, args=(df, name), daemon=True)
    save_thread.start()
    
def refresh_data():
    """Periodically refresh data every 5 minutes."""
    while True:
        st.rerun()
        time.sleep(300)  # 300 seconds = 5 minutes

refresh_thread = threading.Thread(target=refresh_data, daemon=True)
refresh_thread.start()


