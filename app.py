import streamlit as st
from config import TABLE_CONFIG
from helpers import (
    get_google_sheets_data,
    get_google_sheet_date_data,
    get_airtable_data,
)
import time
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Lolas Production dashboard", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Get secrets
AIRTABLE_API_KEY = st.secrets["AIRTABLE"]["PERSONAL_ACCESS_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE"]["BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE"]["TABLE_NAME"]
GOOGLE_SHEET_NAME = st.secrets["GOOGLE_SHEET"]["NAME"]

# Auto refresh table every 1 minute smoothly
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()
    st.session_state["refresh_needed"] = False

if time.time() - st.session_state["last_refresh"] > 60:
    st.session_state["last_refresh"] = time.time()
    st.session_state["refresh_needed"] = True

if st.session_state.get("refresh_needed"):
    st.session_state["refresh_needed"] = False
    # Fetch all data from Airtable and Google Sheets
    for config in filter(lambda x: isinstance(x, dict), TABLE_CONFIG):
        print(f"Config type: {type(config)}")  # Debug statement
        airtable_view = config.get("airtable_view")
        google_sheet_source = config.get("google_sheet_source")
        
        if airtable_view:
            st.session_state[airtable_view] = get_airtable_data(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, airtable_view)
        
        if google_sheet_source:
            st.session_state[google_sheet_source] = get_google_sheets_data(GOOGLE_SHEET_NAME, google_sheet_source)

    st.rerun()

# Sidebar navigation
st.sidebar.header("Navigation")
st.sidebar.markdown("<style>div.row-widget.stRadio > div{flex-direction: column;}</style>", unsafe_allow_html=True)
section = st.sidebar.radio("Go to", ["Dashboard", "Reports", "Charts and Graphs", "Maps, Tables, and Cards", "Settings"])

# Dashboard layout
if section == "Dashboard":
    st.header("Production Dashboard")

    # Semi-circle progress chart for estimated production
    estimated_production = 500
    produced = 300
    progress = (produced / estimated_production) * 100

    col1, col2 = st.columns(2)  # Create two columns for layout balance
    with col1:
        with st.container():
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            fig_progress = go.Figure(go.Indicator(
                mode="gauge+number",
                value=produced,
                title={'text': "Estimated Production"},
                gauge={
                    'axis': {'range': [0, estimated_production]},
                    'bar': {'color': "lightblue"},
                    'bordercolor': "lightgray",
                    'borderwidth': 2,
                    'steps': [],
                    'threshold': {'line': {'color': "salmon", 'width': 4}, 'thickness': 0.75, 'value': estimated_production},
                },
            ))
            fig_progress.update_layout(height=200)  # Reduce size
            fig_progress.update_layout(transition_duration=500)  # Add animation
            st.plotly_chart(fig_progress, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        with st.container():
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="Current Production", value=f"{produced} / {estimated_production}", delta_color="normal")  # New card next to progress chart
            st.markdown("</div>", unsafe_allow_html=True)

    # Product cards with metrics using containers
    st.subheader("Product Metrics")
    with st.container():
        col3, col4, col5 = st.columns(3)
        with col3:
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="Highest Selling Product", value="Chocolate Cake", delta_color="normal", help="This is the best seller!")
            st.markdown("</div>", unsafe_allow_html=True)
        with col4:
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="Lowest Selling Product", value="Vanilla Cupcake", delta_color="normal", help="This is the least popular item.")
            st.markdown("</div>", unsafe_allow_html=True)
        with col5:
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="Total Sales", value="$650", delta_color="normal", help="Total sales amount.")
            st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        col6, col7 = st.columns(2)
        with col6:
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="Total Products", value="3", delta_color="normal", help="Total number of different products.")
            st.markdown("</div>", unsafe_allow_html=True)
        with col7:
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="Orders Today", value="80", delta_color="normal", help="Total orders received today.")
            st.markdown("</div>", unsafe_allow_html=True)

    # Additional fake metrics
    with st.container():
        col8, col9, col10 = st.columns(3)
        with col8:
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="Customer Satisfaction", value="95%", delta_color="normal", help="Percentage of happy customers.")
            st.markdown("</div>", unsafe_allow_html=True)
        with col9:
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="Average Order Value", value="$8.25", delta_color="normal", help="Average revenue per order.")
            st.markdown("</div>", unsafe_allow_html=True)
        with col10:
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.metric(label="New Customers This Month", value="25", delta_color="normal", help="Number of new customers acquired this month.")
            st.markdown("</div>", unsafe_allow_html=True)

    # Subscriber or order trend card with a small line chart
    data_trend = {
        'Days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        'Orders': [50, 70, 60, 90, 80]
    }
    fig_trend = px.line(data_trend, x='Days', y='Orders', title='Order Trend Over the Week')
    fig_trend.update_traces(line=dict(color='lightcoral'))
    fig_trend.update_layout(height=300)  # Increase size
    with st.container():
        st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
        st.plotly_chart(fig_trend)
        st.markdown("</div>", unsafe_allow_html=True)

    # Expandable section for detailed reports
    with st.expander("Detailed Reports", expanded=False):
        st.write("Here you can include detailed reports and additional insights.")

    if st.button("Print Table"):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# Charts and Graphs section
if section == "Charts and Graphs":
    st.header("Charts and Graphs")
    chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Pie Chart", "Scatter Plot"])
    
    if chart_type == "Bar Chart":
        data_bar = {'Products': ['Cake', 'Cupcake', 'Cookie'], 'Sales': [300, 150, 200]}
        fig_bar = px.bar(data_bar, x='Products', y='Sales', title='Sales by Product', color='Sales', color_continuous_scale='pastel')
        fig_bar.update_layout(height=300)  # Increase size
        with st.container():
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.plotly_chart(fig_bar)
            st.markdown("</div>", unsafe_allow_html=True)
    
    elif chart_type == "Pie Chart":
        data_pie = {'Products': ['Cake', 'Cupcake', 'Cookie'], 'Sales': [300, 150, 200]}
        fig_pie = px.pie(data_pie, values='Sales', names='Products', title='Sales Distribution', color='Sales', color_discrete_sequence=px.colors.pastel)
        fig_pie.update_layout(height=300)  # Increase size
        with st.container():
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.plotly_chart(fig_pie)
            st.markdown("</div>", unsafe_allow_html=True)
    
    elif chart_type == "Scatter Plot":
        data_scatter = {'Weight': [1, 2, 3, 4, 5], 'Price': [10, 15, 13, 17, 20]}
        fig_scatter = px.scatter(data_scatter, x='Weight', y='Price', title='Price vs Weight', color='Price', color_continuous_scale='pastel')
        fig_scatter.update_layout(height=300)  # Increase size
        with st.container():
            st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
            st.plotly_chart(fig_scatter)
            st.markdown("</div>", unsafe_allow_html=True)

# Maps, Tables, and Cards section
if section == "Maps, Tables, and Cards":
    st.header("Maps, Tables, and Cards")
    st.subheader("Data Table")
    st.write("Here you can display data in a table format.")
    
    # Example data table
    data_table = {
        'Product': ['Cake', 'Cupcake', 'Cookie'],
        'Sales': [300, 150, 200]
    }
    with st.container():
        st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
        st.table(data_table)
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Data Cards")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
        st.metric(label="Total Sales", value="$650")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
        st.metric(label="Total Products", value="3")
        st.markdown("</div>", unsafe_allow_html=True)

    # Additional fake cards
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
        st.metric(label="Average Delivery Time", value="30 mins")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div style='border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); padding: 10px;'>", unsafe_allow_html=True)
        st.metric(label="Refund Rate", value="2%")
        st.markdown("</div>", unsafe_allow_html=True)
