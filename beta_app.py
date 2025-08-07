import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime

sns.set(style="whitegrid")

# ====================================
# S&P500 기업명 및 티커 정보 표 제공
# ====================================

@st.cache_data
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url)
    df = table[0]
    df = df[['Symbol', 'Security']]

    # 예외 처리 (Yahoo Finance용 티커로 변환)
    def correct_ticker(ticker):
        mapping = {
            'BRK.B': 'BRK-B',
            'BF.B': 'BF-B'
        }
        return mapping.get(ticker, ticker)

    df['Yahoo_Ticker'] = df['Symbol'].apply(correct_ticker)
    df = df.rename(columns={'Security': 'Company Name', 'Yahoo_Ticker': 'Ticker'})
    df = df[['Company Name', 'Ticker']].sort_values(by='Company Name').reset_index(drop=True)
    return df

# S&P500 종목 불러오기
sp500_info_df = get_sp500_tickers()

# 사용자에게 표 제공
with st.expander("🔍 View S&P 500 Company List (Alphabetical Order)"):
    st.write("You can copy the ticker(s) from this list and paste them into the input box above.")
    st.dataframe(sp500_info_df, use_container_width=True)

# Load beta data
@st.cache_data
def load_betas():
    df = pd.read_excel("beta_timeseries_by_firm_sorted.xlsx", header=[0, 1], index_col=0)
    df.index = pd.to_datetime(df.index)
    return df

beta_df = load_betas()
factor_order = ['Mkt-RF', 'SMB', 'HML', 'CMA', 'RMW']

# Streamlit UI
st.title("Fama-French 5-Factor Beta Dashboard")

mode = st.radio("Select Mode", ["1️⃣ Cross-Section Comparison", "2️⃣ Time-Series Comparison"])

tickers_input = st.text_input("Enter up to 10 tickers (comma-separated)", "AAPL,MSFT,GOOG")
selected_tickers = [t.strip().upper() for t in tickers_input.split(",")[:10]]

available_tickers = beta_df.columns.levels[0].tolist()
valid_tickers = [t for t in selected_tickers if t in available_tickers]

if not valid_tickers:
    st.warning("No valid tickers found.")
    st.stop()

# Cross-section mode
if mode.startswith("1"):
    latest_date = beta_df.index.max()
    st.subheader(f"Cross-Section Beta at {latest_date.date()}")

    latest_betas = beta_df.loc[latest_date, valid_tickers]
    latest_betas = latest_betas.T.loc[:, factor_order]  # firm x factor

    beta_long = latest_betas.reset_index()
    beta_long.columns = ['Ticker', 'Factor', 'Beta']

    # Plot each factor separately
    for factor in factor_order:
        fig, ax = plt.subplots(figsize=(5, 4))  # Smaller size for compact layout
        data = beta_long[beta_long['Factor'] == factor]
        sns.barplot(data=data, x="Ticker", y="Beta", palette="Set2", ax=ax)
        ax.set_title(f"{factor} - Beta")
        ax.axhline(0, color='black', linewidth=1)
        plt.xticks(rotation=45)
        st.pyplot(fig)

# Time-series mode
else:
    st.subheader("5-Year Rolling Beta Trends")
    min_date = pd.to_datetime("today") - pd.DateOffset(years=5)

    for factor in factor_order:
        fig, ax = plt.subplots(figsize=(10, 5))
        for ticker in valid_tickers:
            if (ticker, factor) in beta_df.columns:
                series = beta_df[(ticker, factor)].copy()
                series = series[series.index >= min_date]
                sns.lineplot(x=series.index, y=series.values, label=ticker, marker='o', ax=ax)
        ax.set_title(f"{factor} - 5-Year Rolling Beta")
        ax.set_ylabel("Beta")
        ax.axhline(0, color='black', linestyle='--', linewidth=1)
        ax.legend()
        st.pyplot(fig)

