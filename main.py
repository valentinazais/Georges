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
    'Currencies': ['EURUSD=X', 'GBPUSD=X', 'JPYUSD=X', 'CNYUSD=X'],  # EUR/USD, GBP/USD, JPY/USD, CNY/USD
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
    'JPYUSD=X': 'JPY/USD',
    'CNYUSD=X': 'CNY/USD',
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
    # Normalize to start at 100 for better scale comparison
    return (data / data.iloc[0]) * 100

def compute_returns(data):
    returns = data.pct_change().dropna()
    return returns

def plot_heatmap(corr_matrix, title):
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax, fmt=".2f", annot_kws={"size": 8})
    ax.set_title(title)
    st.pyplot(fig)

def main():
    st.title("Simplified Market Dashboard")
    st.markdown("An intuitive dashboard for tracking market assets. Select options in the sidebar to customize.")

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
    
    # Custom tickers input
    custom_tickers = st.sidebar.text_input("Add Custom Tickers (comma-separated, e.g., AAPL, TSLA)")
    custom_tickers_list = [t.strip() for t in custom_tickers.split(',') if t.strip()]
    
    # Normalize option
    normalize = st.sidebar.checkbox("Normalize Charts (start at 100 for scale comparison)", value=True)
    
    # Collect all selected tickers
    all_tickers = []
    for cls in selected_classes:
        all_tickers.extend(ASSET_CLASSES[cls])
    all_tickers.extend(custom_tickers_list)
    all_tickers = list(set(all_tickers))  # Remove duplicates
    
    if not all_tickers:
        st.warning("Please select at least one asset class or add custom tickers.")
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
    tabs = st.tabs(selected_classes + (["Custom"] if custom_tickers_list else []))
    
    tab_index = 0
    for cls in selected_classes:
        with tabs[tab_index]:
            st.header(cls)
            class_tickers = [t for t in all_tickers if t in ASSET_CLASSES[cls]]
            class_data = data[[TICKER_NAMES.get(t, t) for t in class_tickers]]
            
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
    
    # Custom tab if any
    if custom_tickers_list:
        with tabs[tab_index]:
            st.header("Custom Tickers")
            custom_data = data[[TICKER_NAMES.get(t, t) for t in custom_tickers_list]]
            
            if not custom_data.empty:
                st.subheader("Price Chart")
                st.line_chart(custom_data, use_container_width=True)
                
                st.subheader("Correlation Heatmap")
                returns = compute_returns(custom_data)
                if not returns.empty and len(returns.columns) > 1:
                    corr_matrix = returns.corr()
                    plot_heatmap(corr_matrix, "Custom Tickers Correlation")
                else:
                    st.warning("Insufficient data for correlation heatmap.")
            else:
                st.warning("No data for custom tickers.")

if __name__ == "__main__":
    main()
