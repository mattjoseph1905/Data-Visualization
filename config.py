import os
import streamlit as st

# Airtable Configuration
AIRTABLE_CONFIG = {
    "BASE_ID": st.secrets["AIRTABLE"]["BASE_ID"],
    "TABLE_NAME": st.secrets["AIRTABLE"]["TABLE_NAME"],
    "API_KEY": st.secrets["AIRTABLE"]["PERSONAL_ACCESS_TOKEN"]
}

# Google Sheets Configuration
GOOGLE_SHEET_CONFIG = {
    "SHEET_NAME": st.secrets["GOOGLE_SHEET"]["NAME"]
}

# Table Configurations
TABLE_CONFIG = {
    "Total Baking - Cakes": {
        "airtable_views": ["viwXT63LCBVLAhGWT", "viwwjOlUiBR7OMWVa", "viw1R2f8dIjvCgmsz", "viwptndKSqXkhIMtw","viwYFEuFmr6uCpKMX","viw4Pylyrbiimves9","viwlxNV6rPrgFKEkN"],
        "google_sheet_name": "(7) CAKES SUM & (8) CAKE BAKING",
        "sheet_range": "AB1:AE45",
        "time_sheet_range": "F2:G2"
    },
    "ONLINE + SHOPS": {
        "airtable_views": ["viwXT63LCBVLAhGWT", "viwwjOlUiBR7OMWVa", "viw1R2f8dIjvCgmsz", "viwptndKSqXkhIMtw","viwYFEuFmr6uCpKMX","viw4Pylyrbiimves9","viwlxNV6rPrgFKEkN"],
        "google_sheet_name": "(7) CAKES SUM & (8) CAKE BAKING",
        "sheet_range": ["AB1:AE45", "AG1:AJ13", "AG16:AJ20", "AG23:AJ26", "AG29:AJ30", "AG33:AJ41"],
        "time_sheet_range": "F2:G2"
    },
    "NEW: RAINBOW SPONGE - BLEND": {
        "airtable_views": ["viwXT63LCBVLAhGWT", "viwwjOlUiBR7OMWVa", "viw1R2f8dIjvCgmsz", "viwptndKSqXkhIMtw","viwYFEuFmr6uCpKMX","viw4Pylyrbiimves9","viwlxNV6rPrgFKEkN"], 
    },
    "Total Baking - Cupcakes": {
        "airtable_views": ["viwwzswpoQX0IdGCh"]
    },
    "WITH STORES Total Baking - Cupcakes": {
        "airtable_views": ["viwwzswpoQX0IdGCh"],
        "google_sheet_name": "(6) CUPCAKE PRODUCTION",
        "sheet_range": ["AT80:AV131"],
    },
    "Cheesecakes": {
        "data_sources": ["Source 2", "Source 3"],
        "blend_config": []
    },
    "GF Total Baking - Cupcakes": {
        "data_sources": ["Source 1", "Source 2"],
        "blend_config": [
            {"airtable_field": "Placeholder_Field_5", "sheets_field": "Placeholder_Column_E", "blend_type": "Concatenate"}
        ]
    },
    "GF Total Baking - Cakes": {
        "data_sources": ["Source 3"],
        "blend_config": []
    },
    "RAINBOW SPONGE - 5 LAYER": {
        "data_sources": ["Source 1"],
        "blend_config": []
    },
    "RAINBOW SPONGE - 7 LAYER": {
        "data_sources": ["Source 2"],
        "blend_config": []
    },
    "MIX Total Baking - Cakes": {
        "data_sources": ["Source 1", "Source 2"],
        "blend_config": []
    },
    "TOTAL SPONGE/MIX": {
        "data_sources": ["Source 2", "Source 3"],
        "blend_config": []
    },
    "Cupcake Summary": {
        "data_sources": ["Source 1", "Source 2"],
        "blend_config": []
    },
    "Cake Decorating Summary": {
        "data_sources": ["Source 1", "Source 3"],
        "blend_config": []
    },
    "GF Cupcake Summary": {
        "data_sources": ["Source 2"],
        "blend_config": []
    },
    "FUTURE CAKE DECORATING": {
        "data_sources": ["Source 3"],
        "blend_config": []
    },
    "NATION WIDE PACKING Summary": {
        "data_sources": ["Source 1", "Source 2"],
        "blend_config": []
    },
    "PM NATIONWIDE GF-CAKE BAKING": {
        "data_sources": ["Source 3"],
        "blend_config": []
    },
    "NATIONWIDE CAKE BAKING": {
        "data_sources": ["Source 2"],
        "blend_config": []
    },
    "Tall Cake Summary": {
        "data_sources": ["Source 3"],
        "blend_config": [
            {"airtable_field": "Placeholder_Field_12", "sheets_field": "Placeholder_Column_L", "blend_type": "Sum"}
        ]
    }
}
# App Configuration
APP_CONFIG = {
    "REFRESH_INTERVAL": 60,  # Auto-refresh table every 60 seconds
}
