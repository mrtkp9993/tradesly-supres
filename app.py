import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="tradesly: Support / Resistance", page_icon=":chart_with_upwards_trend:", layout="wide")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.sidebar.image("assets/banner.webp", use_column_width=True)
st.header("tradesly: Support / Resistance")

st.markdown("""Calculate support and resistance levels for a given ticker.
            """)

st.divider()

st.sidebar.markdown("""
## Our Paid Apps
* [tradeslyFX Forex AI Roboadvisor](https://play.google.com/store/apps/details?id=com.tradesly.tradeslyfx)
* [tradeslyPro Cryptocurrency AI Roboadvisor](https://play.google.com/store/apps/details?id=com.tradesly.tradeslypro)
            """)

st.sidebar.divider()

# Get stock code
stock_code = st.sidebar.text_input("Enter stock code", value="AAPL")

# Lookback period
lookback_period = st.sidebar.slider("Lookback period", min_value=5, max_value=252, value=20)

# Analyze button
analyze_button = st.sidebar.button("Analyze")

if analyze_button:
    with st.spinner("Get data..."):
        df = yf.download(stock_code, period="2y")

    if df.shape[0] == 0 or df.shape[1] < 6:
        st.error(f"No data found for {stock_code}.")

    with st.spinner("Calculate support and resistance levels..."):
        highs = df['High'].rolling(lookback_period).max()
        lows = df['Low'].rolling(lookback_period).min()

        diff = highs - lows
        levels = np.array([0, 0.236, 0.382, 0.5, 0.618, 0.786, 1, 1.618])

        fib_levels = lows.values.reshape(-1, 1) + diff.values.reshape(-1, 1) * levels
        last_levels = fib_levels[-1, :]

        colors = ['#787b86', '#f23645', '#ff9800', '#4caf50', '#089981', '#00bcd4', '#787b86', '#2962ff']

        # Volume profile for last 60 days
        df2 = df.tail(60)
        price_bins = np.linspace(df2['Low'].min(), df2['High'].max(), 50)
        volume_profile = []

        for i in range(len(price_bins)-1):
            bin_mask = (df2['Close'] > price_bins[i]) & (df2['Close'] <= price_bins[i+1])
            volume_profile.append(df2['Volume'][bin_mask].sum())

        current_price = df2['Close'].iloc[-1]
        support_idx = np.argmax(volume_profile[:np.digitize(current_price, price_bins)])
        resistance_idx = np.argmax(volume_profile[np.digitize(current_price, price_bins):]) + np.digitize(current_price, price_bins)

        support_price = price_bins[support_idx]
        resistance_price = price_bins[resistance_idx]

    with st.spinner("Plotting..."):
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.8, 0.2],
            subplot_titles=("Fibonacci Retracement", "Volume Profile"),
            horizontal_spacing=0.02  # Add horizontal spacing here
        )

        fig.add_trace(go.Candlestick(x=df.index[-60:],
                                            open=df['Open'][-60:],
                                            high=df['High'][-60:],
                                            low=df['Low'][-60:],
                                            close=df['Close'][-60:],
                                            name=f"{stock_code} OHLC"),
                        row=1, col=1)
        for i in range(len(levels)):
            fig.add_trace(go.Scatter(x=df.index[-60:], y=fib_levels[-60:, i],
                                    line=dict(color=colors[i], width=1),
                                    name=f'Fibonacci {levels[i]}',
                                    opacity=0.8))
        # add bar chart as volume profile
        fig.add_trace(go.Bar(x=volume_profile, y=price_bins,
                            marker=dict(color='blue'),
                            name='Volume Profile',
                            orientation='h',
                            opacity=0.5),
                    row=1, col=2)
        # add support and resistance lines as horizontal lines to the bar chart
        fig.add_trace(go.Scatter(x=[0, max(volume_profile)],
                                    y=[support_price, support_price],
                                    line=dict(color='green', width=1),
                                    name='Support',
                                    opacity=0.8),
                        row=1, col=2)
        fig.add_trace(go.Scatter(x=[0, max(volume_profile)],
                                    y=[resistance_price, resistance_price],
                                    line=dict(color='red', width=1),
                                    name='Resistance',
                                    opacity=0.8),
                        row=1, col=2)

        fig.update_layout(xaxis_rangeslider_visible=False,
                        title=f"Fibonacci Retracement and Volume Profile for {stock_code}",
                        margin=dict(l=10, r=10, t=50, b=10),
                            legend=dict(
                orientation="h",  # Horizontal orientation
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Fibonacci Retracement Levels")
        st.table(pd.DataFrame(fib_levels[-1, :], index=levels, columns=["Price"]))

    with col2:
        st.subheader("Volume Profile")
        # support and resistance price
        st.table(pd.DataFrame({"Price": [support_price, resistance_price]}, index=["Support", "Resistance"]))