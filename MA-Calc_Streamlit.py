import streamlit as st
import yfinance as yf
import time

st.set_page_config(page_title="DCA Dashboard", layout="centered")

st.title("📊 Market DCA Dashboard")

# ========= 输入 =========
ticker_symbol = st.text_input("Ticker", "VOO")

# ========= 数据获取（带cache + 重试） =========
@st.cache_data(ttl=300)
def fetch_data(ticker):
    for _ in range(3):
        df = yf.download(ticker, period="5y", interval="1d")
        if df is not None and not df.empty:
            return df
        time.sleep(1)
    return None

run = st.button("Run Analysis")

if run:

    with st.spinner("Fetching market data..."):

        df = fetch_data(ticker_symbol)

        if df is None or 'Close' not in df:
            st.error("❌ Failed to fetch data. Try again.")
            st.stop()

        close = df['Close'].squeeze()

        if len(close) < 200:
            st.error("❌ Not enough data for MA200.")
            st.stop()

        # ========= MA =========
        ma50 = float(close.rolling(50).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])
        price = float(close.iloc[-1])

        # ========= 回撤 =========
        rolling_max = close.cummax()
        dd_pct = abs(float(((close - rolling_max) / rolling_max).iloc[-1]))

        # ========= 趋势 =========
        above_200 = price > ma200
        death_cross = ma50 < ma200

        # ========= VIX =========
        vix_df = fetch_data("^VIX")

        if vix_df is None:
            st.warning("⚠️ VIX unavailable")
            vix = 20
        else:
            vix = round(float(vix_df['Close'].squeeze().iloc[-1]), 2)

        # ========= DCA =========
        base = 2000

        if dd_pct < 0.05:
            extra = 0
        elif dd_pct < 0.10:
            extra = 500
        elif dd_pct < 0.15:
            extra = 1000
        elif dd_pct < 0.20:
            extra = 2000
        else:
            extra = 3000

        # VIX 调整
        if vix < 15:
            extra *= 0.8
        elif vix < 20:
            extra *= 1.0
        elif vix < 30:
            extra *= 1.2
        else:
            extra *= 1.5

        # MA 调整
        if not above_200:
            extra *= 0.7

        dca = int(base + extra)

        # ========= 状态灯 =========
        if dd_pct < 0.05:
            state = "🟢 Normal"
        elif dd_pct < 0.10:
            state = "🟡 Add Slowly"
        elif dd_pct < 0.15:
            state = "🟠 Good Opportunity"
        else:
            state = "🔴 Strong Buy Zone"

        if not above_200:
            state += " (Trend Weak)"

        if death_cross:
            state += " ⚠️"

    # ========= UI =========
    st.divider()

    st.subheader("📈 Market Overview")
    st.write(f"**Ticker:** {ticker_symbol}")
    st.write(f"**Price:** {price:.2f}")

    st.subheader("📊 Indicators")
    st.write(f"MA50: {ma50:.2f}")
    st.write(f"MA200: {ma200:.2f}")

    st.subheader("📉 Market Condition")
    st.write(f"Drawdown: {-dd_pct*100:.2f}%")
    st.write(f"VIX: {vix}")
    st.write(state)

    st.subheader("💰 DCA Decision")
    st.success(f"${dca}")

    # ========= 额外提示 =========
    st.info("💡 Tip: Use DCA primarily to rebalance your portfolio.")
