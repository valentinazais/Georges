import streamlit as st
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simplified Market Dashboard", layout="wide")

# Expanded asset classes with more tickers
ASSET_CLASSES = {
    'Bonds': ['^IRX', '^FVX', '^TNX', '^TYX'],  # 3M, 5Y, 10Y, 30Y Treasury yields
    'Indices': ['^GSPC', '^DJI', '^IXIC', '^RUT'],  # S&P 500, Dow Jones, Nasdaq, Russell 2000
    'Commodities': ['CL=F', 'GC=F', 'NG=F', 'SI=F'],  # Crude Oil, Gold, Natural Gas, Silver
    'Currencies': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCNY=X'],  # EUR/USD, GBP/USD, USD/JPY, USD/CNY
    'Crypto': ['BTC-USD', 'ETH-USD', 'SOL-USD']  # Bitcoin, Ethereum, Solana
}

# Human-readable names for tickers
TICKER_NAMES = {
    '^IRX': '3M Treasury Yield',
    '^FVX': '5Y Treasury Yield',
    '^TNX': '10Y Treasury Yield',
    '^TYX': '30Y Treasury Yield',
    '^GSPC': 'S&P 500',
    '^DJI': 'Dow Jones',
    '^IXIC': 'Nasdaq',
    '^RUT': 'Russell 2000',
    'CL=F': 'Crude Oil',
    'GC=F': 'Gold',
    'NG=F': 'Natural Gas',
    'SI=F': 'Silver',
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'USDCNY=X': 'USD/CNY',
    'BTC-USD': 'Bitcoin',
    'ETH-USD': 'Ethereum',
    'SOL-USD': 'Solana'
}

# Available periods for selection
PERIODS = ['1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max']

def fetch_data(tickers, period='1y'):
    raw_data = yf.download(tickers, period=period, progress=False)
    try:
        data = raw_data['Adj Close']
    except KeyError:
        data = raw_data['Close']
    data = data.dropna(how='all')
    # Rename columns to human-readable names
    data = data.rename(columns={ticker: TICKER_NAMES.get(ticker, ticker) for ticker in data.columns})
    return data

def normalize_data(data):
    # Normalize to start at 100 for better scale comparison, handling potential NaNs
    first_row = data.iloc[0]
    if first_row.isna().any():
        data = data.fillna(method='ffill').fillna(method='bfill')  # Simple fill for normalization
    return (data / data.iloc[0]) * 100

def compute_returns(data):
    returns = data.pct_change().dropna()
    return returns

def plot_heatmap(corr_matrix, title):
    num_assets = len(corr_matrix)
    fig_size = (max(8, num_assets * 0.5), max(6, num_assets * 0.5))
    fig, ax = plt.subplots(figsize=fig_size)
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax, fmt=".2f", annot_kws={"size": 8})
    ax.set_title(title)
    st.pyplot(fig)

def main():
    st.title("Simplified Market Dashboard")
    st.markdown("An intuitive dashboard for tracking market assets. Select options in the sidebar to customize. View all selected assets in the 'All Assets' tab or per category.")

    # Sidebar for user inputs
    st.sidebar.header("Dashboard Settings")
    
    # Period selection
    selected_period = st.sidebar.selectbox("Select Time Window", PERIODS, index=3)  # Default to 1y
    
    # Asset class selection
    selected_classes = st.sidebar.multiselect(
        "Select Asset Classes",
        list(ASSET_CLASSES.keys()),
        default=list(ASSET_CLASSES.keys())[:3]  # Default to first 3
    )
    
    # Normalize option
    normalize = st.sidebar.checkbox("Normalize Charts (start at 100 for scale comparison)", value=True)
    
    # Collect all selected tickers
    all_tickers = []
    for cls in selected_classes:
        all_tickers.extend(ASSET_CLASSES[cls])
    all_tickers = list(set(all_tickers))  # Remove duplicates
    
    if not all_tickers:
        st.warning("Please select at least one asset class.")
        return
    
    # Fetch data
    with st.spinner("Fetching market data..."):
        data = fetch_data(all_tickers, period=selected_period)
    
    if data.empty:
        st.error("No data available for the selected tickers and period.")
        return
    
    # Normalize if selected
    if normalize:
        data = normalize_data(data)
    
    # Display charts in tabs for better organization
    tab_names = ["All Assets"] + selected_classes
    tabs = st.tabs(tab_names)
    
    # All Assets tab
    with tabs[0]:
        st.header("All Assets")
        if not data.empty:
            # Price Chart
            st.subheader("Price/Yields Chart")
            st.line_chart(data, use_container_width=True)
            
            # Correlation Heatmap
            st.subheader("Correlation Heatmap")
            returns = compute_returns(data)
            if not returns.empty and len(returns.columns) > 1:
                corr_matrix = returns.corr()
                plot_heatmap(corr_matrix, "All Assets Correlation (Daily Returns)")
            else:
                st.warning("Insufficient data for correlation heatmap.")
        else:
            st.warning("No data available.")
    
    # Individual class tabs
    tab_index = 1
    for cls in selected_classes:
        with tabs[tab_index]:
            st.header(cls)
            class_tickers = [t for t in all_tickers if t in ASSET_CLASSES[cls]]
            class_names = [TICKER_NAMES.get(t, t) for t in class_tickers]
            class_data = data[class_names]  # Select by renamed columns
            
            if not class_data.empty:
                # Price Chart
                st.subheader("Price/Yields Chart")
                st.line_chart(class_data, use_container_width=True)
                
                # Correlation Heatmap
                st.subheader("Correlation Heatmap")
                returns = compute_returns(class_data)
                if not returns.empty and len(returns.columns) > 1:
                    corr_matrix = returns.corr()
                    plot_heatmap(corr_matrix, f"{cls} Correlation (Daily Returns)")
                else:
                    st.warning("Insufficient data for correlation heatmap.")
            else:
                st.warning(f"No data for {cls}.")
        tab_index += 1

if __name__ == "__main__":
    main()
