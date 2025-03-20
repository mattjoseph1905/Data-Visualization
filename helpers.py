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
    # Check if DataFrame is empty
    if df.empty:
        st.markdown(
            """
            <div class="flex items-center justify-center text-gray-500 dark:text-gray-300 text-lg font-semibold py-10">
                Oops! No data available.
            </div>
            """,
            unsafe_allow_html=True
        )
        return  # Exit function if there is no data or the total sum is 0

    df_json = json.dumps(df.to_dict(orient="records"))
    html_code = f"""
        <script src="https://cdn.tailwindcss.com"></script>
        
        <div class="relative w-full min-w-full overflow-x-auto p-4">
            <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400 border border-gray-300 dark:border-gray-700 
                         shadow-lg rounded-lg bg-white dark:bg-gray-800 transition-transform duration-300">
                <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400 border-b border-gray-300 dark:border-gray-700">
                    <tr>
                        <th scope="col" class="px-4 py-2">Index</th>
                        <!-- Dynamic column headers will be added via JavaScript -->
                    </tr>
                </thead>
                <tbody id="tableBody" class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 divide-y divide-gray-300 dark:divide-gray-700">
                    <!-- Table rows will be inserted dynamically via JavaScript -->
                </tbody>
            </table>
        </div>

        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                var tableData = {df_json};

                // Check if the only row is Grand Total
                var onlyGrandTotal = tableData.length === 1 && tableData[0]["Sponge Flavour 1"] === "Grand Total";

                if (onlyGrandTotal) {{
                    tableData = [{{ "Sponge Flavour 1": "Oops! No data" }}]; // Replace with "Oops! No data"
                }}

                // Get column names dynamically
                var columns = Object.keys(tableData[0]);

                // Append dynamic headers
                var theadRow = document.querySelector('thead tr');
                columns.forEach(function(column) {{
                    var th = document.createElement('th');
                    th.scope = 'col';
                    th.className = 'px-4 py-2 text-center';
                    th.innerText = column;
                    theadRow.appendChild(th);
                }});

                // Populate table rows dynamically
                var tableBody = document.getElementById("tableBody");
                tableData.forEach(function(row, index) {{
                    var tr = document.createElement("tr");

                    // Apply alternating grey & white row colors
                    tr.className = index % 2 === 0 
                        ? "bg-white dark:bg-gray-900 transition-transform duration-200 hover:scale-105 hover:shadow-md"
                        : "bg-gray-100 dark:bg-gray-800 transition-transform duration-200 hover:scale-105 hover:shadow-md";

                    // Apply Vegan row full green
                    if (row["Sponge Flavour 1"] && row["Sponge Flavour 1"].toLowerCase().includes("vegan")) {{
                        tr.classList.add("bg-green-200", "dark:bg-green-800", "hover:bg-green-300", "dark:hover:bg-green-900", "font-semibold");
                    }}

                    // Apply bold styling to Grand Total row (only if it's not the only row)
                    if (row["Sponge Flavour 1"] === "Grand Total" && !onlyGrandTotal) {{
                        tr.classList.add("font-bold");
                    }}

                    // Add index column (skip if showing "Oops! No data")
                    if (!onlyGrandTotal) {{
                        tr.innerHTML = `<td class="px-4 py-2 text-center font-semibold">${{index + 1}}</td>`;
                    }} else {{
                        tr.innerHTML = `<td class="px-4 py-2 text-center font-semibold" colspan="${{columns.length}}">Oops! No data</td>`;
                    }}

                    Object.keys(row).forEach(function(column) {{
                        if (onlyGrandTotal) return; // Skip adding normal cells if only showing "Oops! No data"

                        var td = document.createElement("td");
                        td.className = "px-4 py-2 text-gray-600 dark:text-gray-200 text-center";

                        // Apply bold styling to Grand Total column
                        if (column === "Grand Total" && !onlyGrandTotal) {{
                            td.classList.add("font-bold");
                        }}

                        td.innerText = row[column] || "0"; // Handle empty cells
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
    print(row_count)
    # Set a minimum height (to avoid too small a height)
    table_height = max(table_height, 300)  # Ensure it is at least 300px
    
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
