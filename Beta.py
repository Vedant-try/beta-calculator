import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Initialize Streamlit App
st.title("Beta Calculator")

# Input fields
st.sidebar.header("Input Fields")
stock_symbol = st.sidebar.text_input("Enter the Stock Symbol (e.g., RELIANCE.NS):", "RELIANCE.NS")
index_symbol = st.sidebar.text_input("Enter the Index Symbol (e.g., ^NSEI):", "^NSEI")
specified_date = st.sidebar.date_input("Enter a specific date (YYYY-MM-DD):", value=datetime.now().date())
num_days = st.sidebar.number_input("Enter the number of days (max 720):", min_value=1, max_value=720, value=30)

if st.sidebar.button("Fetch Data"):
    try:
        # Calculate the start and end dates
        end_date = specified_date
        start_date = end_date - timedelta(days=num_days)

        # Fetch stock data
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
        index_data = yf.download(index_symbol, start=start_date, end=end_date)

        # Process stock data
        if not stock_data.empty:
            stock_df = stock_data.reset_index()
            stock_df['Daily Change (%)'] = ((stock_df['Close'].pct_change()) * 100).round(2)
        else:
            st.error("Failed to fetch stock data. Please check the stock symbol.")
            stock_df = None

        # Process index data
        if not index_data.empty:
            index_df = index_data.reset_index()
            index_df['Daily Change (%)'] = ((index_df['Close'].pct_change()) * 100).round(2)
        else:
            st.error("Failed to fetch index data. Please check the index symbol.")
            index_df = None

        # Merge and align data
        if stock_df is not None and index_df is not None:
            stock_df = stock_df[['Date', 'Close', 'Daily Change (%)']]
            index_df = index_df[['Date', 'Close', 'Daily Change (%)']]

            stock_df.rename(columns={
                'Close': 'Stock Price',
                'Daily Change (%)': 'Stock Daily Change (%)'
            }, inplace=True)

            index_df.rename(columns={
                'Close': 'Index Price',
                'Daily Change (%)': 'Index Daily Change (%)'
            }, inplace=True)

            merged_df = pd.merge(stock_df, index_df, on='Date', how='outer', indicator=True)

            # Part 1: Intersection data
            intersecting_df = merged_df[merged_df['_merge'] == 'both']
            intersecting_df = intersecting_df[['Date', 'Stock Price', 'Stock Daily Change (%)', 'Index Price', 'Index Daily Change (%)']]

            # Part 2: Non-intersecting data
            non_intersecting_df = merged_df[merged_df['_merge'] != 'both']
            non_intersecting_df = non_intersecting_df[['Date', 'Stock Price', 'Index Price']]

            # Display intersection data
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Intersection Data (Aligned Dates)")
                st.dataframe(intersecting_df)

            # Display non-intersecting data
            with col2:
                st.subheader("Non-Intersection Data (Missing Dates)")
                st.dataframe(non_intersecting_df)

            # Beta calculation
            stock_changes = intersecting_df['Stock Daily Change (%)']
            index_changes = intersecting_df['Index Daily Change (%)']

            covariance = stock_changes.cov(index_changes)
            variance = index_changes.var()
            beta = round(covariance / variance, 2)

            st.subheader("Beta Calculation")
            st.write(f"**Beta of the stock ({stock_symbol}) relative to the index ({index_symbol}): {beta}**")

    except Exception as e:
        st.error(f"An error occurred: {e}")
