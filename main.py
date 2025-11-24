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
    if not tickers:
        return pd.DataFrame()
    
    raw_data = yf.download(tickers, period=period, progress=False)
    
    if raw_data.empty:
        return pd.DataFrame()
    
    # Handle single vs multiple tickers
    if len(tickers) == 1:
        if 'Adj Close' in raw_data.columns:
            data = raw_data['Adj Close'].to_frame(name=tickers[0])
        else:
            data = raw_data['Close'].to_frame(name=tickers[0])
    else:
        if 'Adj Close' in raw_data.columns.get_level_values(0):
            data = raw_data['Adj Close']
        else:
            data = raw_data['Close']
    
    data = data.dropna(how='all')
    return data

def normalize_data(data):
    # Normalize to start at 100 for better scale comparison
    normalized = pd.DataFrame()
    for col in data.columns:
        first_valid = data[col].first_valid_index()
        if first_valid is not None:
            first_value = data.loc[first_valid, col]
            if first_value != 0:
                normalized[col] = (data[col] / first_value) * 100
            else:
                normalized[col] = data[col]
        else:
            normalized[col] = data[col]
    return normalized

def scale_to_fit(data):
    # Scale each series to 0-100 based on its min and max
    scaled = pd.DataFrame()
    for col in data.columns:
        col_data = data[col].dropna()
        if len(col_data) > 0:
            data_min = col_data.min()
            data_max = col_data.max()
            data_range = data_max - data_min
            if data_range != 0:
                scaled[col] = 100 * (data[col] - data_min) / data_range
            else:
                scaled[col] = data[col]
        else:
            scaled[col] = data[col]
    return scaled

def compute_returns(data):
    returns = data.pct_change().dropna()
    return returns

def plot_heatmap(corr_matrix, title):
    num_assets = len(corr_matrix)
    fig_size = (max(8, num_assets * 0.5), max(6, num_assets * 0.5))
    fig, ax = plt.subplots(figsize=fig_size)
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax, fmt=".2f", 
                annot_kws={"size": 8}, vmin=-1, vmax=1)
    ax.set_title(title)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
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
    
    # Scaling options
    st.sidebar.subheader("Chart Scaling Options")
    normalize = st.sidebar.checkbox("Normalize to 100 (start at same baseline)", value=True)
    scale_fit = st.sidebar.checkbox("Scale to fit 0-100 (for shape comparison)", value=False)
    
    if not selected_classes:
        st.warning("Please select at least one asset class.")
        return
    
    # Initialize session state for ticker selections
    if 'ticker_selections' not in st.session_state:
        st.session_state.ticker_selections = {}
    
    # Display charts in tabs for better organization
    tab_names = ["All Assets"] + selected_classes
    tabs = st.tabs(tab_names)
    
    # All Assets tab
    with tabs[0]:
        st.header("All Assets")
        
        # Collect all selected tickers from individual class selections
        all_selected_tickers = []
        for cls in selected_classes:
            if cls in st.session_state.ticker_selections:
                all_selected_tickers.extend(st.session_state.ticker_selections[cls])
            else:
                all_selected_tickers.extend(ASSET_CLASSES[cls])
        
        all_selected_tickers = list(set(all_selected_tickers))
        
        if all_selected_tickers:
            with st.spinner("Fetching market data..."):
                original_data = fetch_data(all_selected_tickers, period=selected_period)
            
            if not original_data.empty:
                # Rename columns to human-readable names
                original_data.columns = [TICKER_NAMES.get(col, col) for col in original_data.columns]
                
                # Apply transformations
                data = original_data.copy()
                if normalize:
                    data = normalize_data(data)
                if scale_fit:
                    data = scale_to_fit(data)
                
                # Price Chart
                st.subheader("Price/Yields Chart")
                st.line_chart(data, use_container_width=True, height=500)
                
                # Correlation Heatmap
                st.subheader("Correlation Heatmap (Daily Returns)")
                returns = compute_returns(original_data)
                if not returns.empty and len(returns.columns) > 1:
                    corr_matrix = returns.corr()
                    plot_heatmap(corr_matrix, "All Assets Correlation")
                else:
                    st.warning("Insufficient data for correlation heatmap.")
            else:
                st.error("No data available for the selected tickers and period.")
        else:
            st.warning("No tickers selected. Please select tickers in individual asset class tabs.")
    
    # Individual class tabs
    tab_index = 1
    for cls in selected_classes:
        with tabs[tab_index]:
            st.header(cls)
            
            # Ticker selection for this class
            class_tickers = ASSET_CLASSES[cls]
            
            # Default selection
            if cls not in st.session_state.ticker_selections:
                st.session_state.ticker_selections[cls] = class_tickers
            
            selected_tickers = st.multiselect(
                f"Select {cls} tickers to display",
                options=class_tickers,
                default=st.session_state.ticker_selections[cls],
                format_func=lambda x: TICKER_NAMES.get(x, x),
                key=f"select_{cls}"
            )
            
            # Update session state
            st.session_state.ticker_selections[cls] = selected_tickers
            
            if not selected_tickers:
                st.warning(f"Please select at least one ticker for {cls}.")
                tab_index += 1
                continue
            
            with st.spinner(f"Fetching {cls} data..."):
                original_data = fetch_data(selected_tickers, period=selected_period)
            
            if not original_data.empty:
                # Rename columns to human-readable names
                original_data.columns = [TICKER_NAMES.get(col, col) for col in original_data.columns]
                
                # Apply transformations
                data = original_data.copy()
                if normalize:
                    data = normalize_data(data)
                if scale_fit:
                    data = scale_to_fit(data)
                
                # Price Chart
                st.subheader("Price/Yields Chart")
                st.line_chart(data, use_container_width=True, height=500)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Data Points", len(original_data))
                with col2:
                    if len(original_data) > 1:
                        latest = original_data.iloc[-1]
                        previous = original_data.iloc[-2]
                        change = ((latest - previous) / previous * 100).mean()
                        st.metric("Avg Last Change", f"{change:.2f}%")
                with col3:
                    st.metric("Tickers Selected", len(selected_tickers))
                
                # Correlation Heatmap
                if len(selected_tickers) > 1:
                    st.subheader("Correlation Heatmap (Daily Returns)")
                    returns = compute_returns(original_data)
                    if not returns.empty and len(returns.columns) > 1:
                        corr_matrix = returns.corr()
                        plot_heatmap(corr_matrix, f"{cls} Correlation")
                    else:
                        st.warning("Insufficient data for correlation heatmap.")
            else:
                st.error(f"No data available for {cls}.")
        
        tab_index += 1

if __name__ == "__main__":
    main()
