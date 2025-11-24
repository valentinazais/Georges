import streamlit as st
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simplified Market Dashboard", layout="wide")

# Define principal assets
ASSETS = {
    'Bonds': ['^IRX', '^FVX', '^TNX', '^TYX'],  # 3M, 5Y, 10Y, 30Y Treasury yields
    'Indices': ['^GSPC', '^DJI', '^IXIC'],  # S&P 500, Dow Jones, Nasdaq
    'Commodities': ['CL=F', 'GC=F', 'NG=F']  # Crude Oil, Gold, Natural Gas
}

def fetch_data(tickers, period='1y'):
    raw_data = yf.download(tickers, period=period, progress=False)
    try:
        data = raw_data['Adj Close']
    except KeyError:
        data = raw_data['Close']
    data = data.dropna(how='all')
    return data

def compute_returns(data):
    returns = data.pct_change().dropna()
    return returns

def plot_heatmap(corr_matrix, title):
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)
    ax.set_title(title)
    st.pyplot(fig)

def main():
    st.title("Simplified Market Dashboard")
    
    for asset_class, tickers in ASSETS.items():
        st.header(asset_class)
        
        data = fetch_data(tickers)
        if not data.empty:
            # Graph: Line chart of prices
            st.subheader("Price Chart")
            st.line_chart(data)
            
            # Correlation heatmap
            st.subheader("Correlation Heatmap")
            returns = compute_returns(data)
            if not returns.empty and len(returns.columns) > 1:
                corr_matrix = returns.corr()
                plot_heatmap(corr_matrix, f"{asset_class} Correlation")
            else:
                st.warning("Insufficient data for correlation.")
        else:
            st.warning(f"No data for {asset_class}.")

if __name__ == "__main__":
    main()
