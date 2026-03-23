import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="DCA Dashboard", layout="centered")

st.title("📊 Market DCA Dashboard")

# ========= 输入 =========
ticker_symbol = st.text_input("Ticker", "VOO")

run = st.button("Run Analysis")

if run:

    # ========= 下载数据 =========
    df = yf.download(ticker_symbol, period="5y", interval="1d")
    close = df['Close'].squeeze()

    # ========= 计算均线 =========
    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1])
    current_price = float(close.iloc[-1])

    # ========= 计算回撤 =========
    rolling_max = close.cummax()
    dd_pct = abs(float(((close - rolling_max) / rolling_max).iloc[-1]))

    # ========= 趋势 =========
    above_200 = current_price > ma200
    death_cross = ma50 < ma200

    # ========= DCA =========
    base_dca = 2000

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

    # ========= VIX =========
    vix_data = yf.download("^VIX", period="5d", interval="1d")
    vix = round(float(vix_data['Close'].squeeze().iloc[-1]), 2)

    if vix < 15:
        vix_factor = 0.8
    elif vix < 20:
        vix_factor = 1.0
    elif vix < 30:
        vix_factor = 1.2
    else:
        vix_factor = 1.5

    extra *= vix_factor

    if not above_200:
        extra *= 0.7

    dca = int(base_dca + extra)

    # ========= 市场状态 =========
    if dd_pct < 0.05:
        market_state = "🟢 Healthy"
    elif dd_pct < 0.10:
        market_state = "🟡 Pullback"
    elif dd_pct < 0.15:
        market_state = "🟠 Correction"
    else:
        market_state = "🔴 Deep Drawdown"

    if not above_200:
        market_state += " (Below 200MA)"

    if death_cross:
        market_state += " ⚠️ Death Cross"

    # ========= 输出 =========
    st.divider()

    st.subheader("📈 Market Overview")
    st.write(f"**Ticker:** {ticker_symbol}")
    st.write(f"**Price:** {current_price:.2f}")

    st.subheader("📊 Moving Averages")
    st.write(f"MA50: {ma50:.2f}")
    st.write(f"MA200: {ma200:.2f}")

    st.subheader("📉 Trend")
    st.write(f"Above 200MA: {above_200}")
    st.write(f"Death Cross: {death_cross}")

    st.subheader("📉 Drawdown")
    st.write(f"{-dd_pct*100:.2f}%")

    st.subheader("🧠 Market State")
    st.write(market_state)
    st.write(f"VIX: {vix}")

    st.subheader("💰 DCA Suggestion")
    st.success(f"${dca}")