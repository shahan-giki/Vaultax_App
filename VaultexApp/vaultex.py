
import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import feedparser
from datetime import datetime

# --- 1. PAGE CONFIGURATION & CUSTOM CSS ---
st.set_page_config(page_title="Vaultex Pro Terminal", layout="wide", page_icon="⚡")

# Inject Custom CSS for the "Fintech" Look
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-family: 'Courier New', monospace;
    }
    
    /* Custom Card Containers */
    .css-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Button Styling overrides */
    div.stButton > button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161B22;
        border-radius: 4px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE (WALLET) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 25000.0  # Start with 25k
if 'holdings' not in st.session_state:
    st.session_state.holdings = {}
if 'log' not in st.session_state:
    st.session_state.log = []

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("⚡ Vaultex")
    st.markdown("### Market Controls")
    
    ticker = st.text_input("SYMBOL", value="BTC-USD").upper()
    period = st.selectbox("TIMEFRAME", ["1d", "5d", "1mo", "6mo", "1y"])
    
    st.markdown("---")
    st.markdown("### 💼 Wallet Status")
    
    # Calculate Net Worth
    current_data = yf.Ticker(ticker).history(period="1d")
    current_price = current_data['Close'].iloc[-1] if not current_data.empty else 0
    
    holdings_val = sum(q * current_price for s, q in st.session_state.holdings.items() if s == ticker)
    total_net_worth = st.session_state.balance + holdings_val
    
    c1, c2 = st.columns(2)
    # UPDATED: Changed $ to PKR
    c1.metric("Cash", f"PKR {st.session_state.balance/1000:.1f}K")
    c2.metric("Net Worth", f"PKR {total_net_worth/1000:.1f}K")
    
    st.markdown("---")
    st.info("System Status: 🟢 ONLINE")

# --- 4. MAIN DATA ENGINE ---
try:
    data = yf.Ticker(ticker)
    hist = data.history(period=period)
    
    if hist.empty:
        st.error("Invalid Symbol")
        st.stop()
        
    curr_price = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2]
    price_change = curr_price - prev_close
    pct_change = (price_change / prev_close) * 100
    
    # Determine color for UI
    color = "#00FF00" if price_change >= 0 else "#FF0000"
    
except:
    st.error("Data connection failed.")
    st.stop()

# --- 5. UI LAYOUT ---

# Top Header Stats
col_head1, col_head2, col_head3 = st.columns([2,1,1])
with col_head1:
    st.markdown(f"<h1 style='margin:0; padding:0;'>{ticker}</h1>", unsafe_allow_html=True)
    st.caption(f"Real-Time Market Data • {period.upper()}")

with col_head2:
    # UPDATED: Changed $ to PKR
    st.metric("Last Price", f"PKR {curr_price:,.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")

with col_head3:
    sentiment = "BULLISH 🐂" if price_change > 0 else "BEARISH 🐻"
    st.markdown(f"<div style='text-align:center; padding: 10px; border: 1px solid {color}; color: {color}; border-radius: 5px;'>{sentiment}</div>", unsafe_allow_html=True)

# Main Workspace Tabs
tab1, tab2, tab3 = st.tabs(["📊 CHARTING", "⚡ TRADING CONSOLE", "🧠 INTELLIGENCE"])

# --- TAB 1: CHART ---
with tab1:
    # Plotly with Dark Theme
    fig = go.Figure(data=[go.Candlestick(x=hist.index,
                        open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'],
                        increasing_line_color='#00FF00', decreasing_line_color='#FF0000')])
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: TRADING CONSOLE ---
with tab2:
    col_trade_L, col_trade_R = st.columns([1, 2])
    
    # Left: Order Entry
    with col_trade_L:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Place Order")
        
        trade_type = st.selectbox("Order Type", ["MARKET BUY", "MARKET SELL"])
        qty = st.number_input("Quantity", min_value=1, value=10)
        
        est_total = qty * curr_price
        # UPDATED: Changed $ to PKR
        st.markdown(f"*Est. Total:* PKR {est_total:,.2f}")
        
        if st.button("SUBMIT ORDER", type="primary"):
            timestamp = datetime.now().strftime("%H:%M:%S")
            if "BUY" in trade_type:
                if st.session_state.balance >= est_total:
                    st.session_state.balance -= est_total
                    st.session_state.holdings[ticker] = st.session_state.holdings.get(ticker, 0) + qty
                    st.session_state.log.append(f"🟢 {timestamp} | BUY {qty} {ticker} @ {curr_price:.2f}")
                    st.success("ORDER EXECUTED")
                    st.rerun()
                else:
                    st.error("INSUFFICIENT FUNDS")
            else: # SELL
                if st.session_state.holdings.get(ticker, 0) >= qty:
                    st.session_state.balance += est_total
                    st.session_state.holdings[ticker] -= qty
                    st.session_state.log.append(f"🔴 {timestamp} | SELL {qty} {ticker} @ {curr_price:.2f}")
                    st.success("ORDER EXECUTED")
                    st.rerun()
                else:
                    st.error("INSUFFICIENT POSITION")
        st.markdown('</div>', unsafe_allow_html=True)

    # Right: Order Book / History
    with col_trade_R:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Recent Activity")
        if st.session_state.log:
            for line in reversed(st.session_state.log[-6:]):
                st.code(line, language="bash")
        else:
            st.caption("No trades executed this session.")
        
        st.markdown("---")
        st.subheader("Current Positions")
        if st.session_state.holdings:
            # Simple table for holdings
            # UPDATED: Changed $ to PKR
            hold_data = [{"Asset": k, "Qty": v, "Value": f"PKR {v*curr_price:,.2f}"} for k,v in st.session_state.holdings.items() if v > 0]
            st.dataframe(hold_data, use_container_width=True)
        else:
            st.info("Portfolio is empty.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: INTELLIGENCE ---
with tab3:
    col_vid, col_news = st.columns(2)
    
    with col_vid:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("📺 Video Analysis")
        queries = [f"{ticker} trading strategy", f"{ticker} technical analysis", f"{ticker} news today"]
        for q in queries:
            url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
            # Custom styled link
            st.markdown(f"""
            <a href="{url}" target="_blank" style="text-decoration: none; color: white;">
                <div style="background: #21262D; padding: 10px; margin-bottom: 5px; border-radius: 5px; border-left: 3px solid #FF0000;">
                    ▶️ <b>{q.title()}</b>
                </div>
            </a>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_news:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("📰 Live Wire")
        try:
            rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:5]:
                st.markdown(f"""
                <div style="margin-bottom: 10px; border-bottom: 1px solid #30363D; padding-bottom: 5px;">
                    <a href="{entry.link}" target="_blank" style="text-decoration: none; color: #58A6FF; font-weight: bold;">{entry.title}</a>
                    <div style="font-size: 12px; color: #8B949E;">{entry.published}</div>
                </div>
                """, unsafe_allow_html=True)
        except:
            st.warning("News feed offline.")
            st.markdown('</div>', unsafe_allow_html=True)