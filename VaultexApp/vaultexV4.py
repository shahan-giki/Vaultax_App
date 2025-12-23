import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import feedparser
from datetime import datetime
import pandas as pd
import hashlib
import time

# --- 1. PAGE CONFIGURATION & CUSTOM CSS ---
st.set_page_config(page_title="Vaultex Pro Terminal", layout="wide", page_icon="⚡")

# Enhanced Custom CSS with Smooth Animations
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
        transition: all 0.3s ease;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
        transition: all 0.3s ease;
    }
    
    /* Metrics Styling with Animation */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-family: 'Courier New', monospace;
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Smooth Fade In Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Pulse Animation for Live Data */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .live-indicator {
        animation: pulse 2s infinite;
    }
    
    /* Custom Card Containers */
    .css-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    
    .css-card:hover {
        box-shadow: 0 6px 12px rgba(0,255,0,0.2);
        transform: translateY(-2px);
    }
    
    /* Button Styling with Hover Effects */
    div.stButton > button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,255,0,0.3);
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
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #21262D;
    }
    
    /* Login Container */
    .login-container {
        max-width: 450px;
        margin: 100px auto;
        padding: 40px;
        background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
        border: 2px solid #30363D;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .login-title {
        font-size: 48px;
        font-weight: bold;
        background: linear-gradient(90deg, #00FF00, #00FFFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 10px;
        animation: glow 2s ease-in-out infinite;
    }
    
    @keyframes glow {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.3); }
    }
    
    .login-subtitle {
        color: #8B949E;
        font-size: 14px;
    }
    
    /* Smooth Transitions for All Elements */
    * {
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. USER DATABASE ---
USERS_DB = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest(),
    "trader": hashlib.sha256("trade123".encode()).hexdigest(),
    "demo": hashlib.sha256("demo".encode()).hexdigest()
}

# --- 3. SESSION STATE INITIALIZATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'balance' not in st.session_state:
    st.session_state.balance = 25000.0
if 'holdings' not in st.session_state:
    st.session_state.holdings = {}
if 'log' not in st.session_state:
    st.session_state.log = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['BTC-USD', 'ETH-USD', 'AAPL', 'TSLA']
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# --- 4. LOGIN SYSTEM ---
def login_page():
    """Display login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="login-header">
            <div class="login-title">⚡ VAULTEX</div>
            <div class="login-subtitle">Professional Trading Terminal</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Login Form
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_btn = st.form_submit_button("🚀 LOGIN", use_container_width=True, type="primary")
            with col_btn2:
                demo_btn = st.form_submit_button("🎮 DEMO MODE", use_container_width=True)
            
            if login_btn:
                if username in USERS_DB:
                    hashed_pass = hashlib.sha256(password.encode()).hexdigest()
                    if USERS_DB[username] == hashed_pass:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success("✅ Login Successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Invalid password")
                else:
                    st.error("❌ User not found")
            
            if demo_btn:
                st.session_state.authenticated = True
                st.session_state.username = "demo"
                st.success("✅ Entering Demo Mode!")
                time.sleep(0.5)
                st.rerun()
        
        # Extra options below form
        col_link1, col_link2 = st.columns(2)
        with col_link1:
            if st.button("🔑 Forgot Password?", use_container_width=True, key="forgot_pw"):
                st.info("📧 Password reset link sent to your email!")
        with col_link2:
            if st.button("✍️ Sign Up", use_container_width=True, key="signup_btn"):
                st.info("📝 Registration opening soon!")
        
        # Info section - WITHOUT showing passwords
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #8B949E; font-size: 12px;'>
            <b>Quick Access:</b><br>
            Click "DEMO MODE" for instant access<br><br>
            <b>Available Accounts:</b><br>
            • demo<br>
            • admin<br>
            • trader
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def logout():
    """Logout function"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

# --- 5. CHECK AUTHENTICATION ---
if not st.session_state.authenticated:
    login_page()
    st.stop()

# --- 6. HELPER FUNCTIONS ---
@st.cache_data(ttl=10)  # Cache for 10 seconds for super fast updates
def get_current_price(symbol):
    """Get current price for a symbol with caching"""
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except:
        pass
    return 0.0

def calculate_portfolio_value(holdings, ticker_prices):
    """Calculate total portfolio value"""
    total = 0.0
    for symbol, qty in holdings.items():
        if qty > 0:
            try:
                price = ticker_prices.get(symbol, 0.0)
                total += qty * price
            except:
                pass
    return total

# --- 7. SIDEBAR CONTROLS ---
with st.sidebar:
    # User info at top
    st.markdown(f"""
    <div style='background: #21262D; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 3px solid #00FF00;'>
        <div style='font-size: 12px; color: #8B949E;'>Logged in as</div>
        <div style='font-size: 18px; font-weight: bold; color: #00FF00;'>👤 {st.session_state.username.upper()}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.title("⚡ Vaultex")
    st.markdown("### Market Controls")
    
    ticker = st.text_input("SYMBOL", value="BTC-USD", key="ticker_input").upper()
    period = st.selectbox("TIMEFRAME", ["15m", "1h", "1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"])
    
    # Auto-refresh toggle with dynamic intervals
    if period in ["15m", "1h", "1d"]:
        refresh_interval = 10  # 10 seconds for ultra-short timeframes
        auto_refresh = st.checkbox("🔄 Live Mode (10s)", value=True)
    elif period == "5d":
        refresh_interval = 30  # 30 seconds for short timeframes
        auto_refresh = st.checkbox("🔄 Auto-Refresh (30s)", value=False)
    else:
        refresh_interval = 300  # 5 minutes for longer timeframes
        auto_refresh = st.checkbox("🔄 Auto-Refresh (5m)", value=False)
    
    st.markdown("---")
    st.markdown("### 💼 Wallet Status")
    
    # Add Funds Button
    if st.button("💳 Add Funds", use_container_width=True, type="secondary"):
        st.session_state.show_add_funds = True
    
    # Add Funds Modal
    if 'show_add_funds' not in st.session_state:
        st.session_state.show_add_funds = False
    
    if st.session_state.show_add_funds:
        with st.form("add_funds_form"):
            st.markdown("### 💳 Add Funds")
            
            amount = st.number_input("Amount (PKR)", min_value=100, max_value=1000000, value=5000, step=100)
            
            st.text_input("Card Number", placeholder="1234 5678 9012 3456", max_chars=19)
            
            col_exp, col_cvv = st.columns(2)
            with col_exp:
                st.text_input("Expiry", placeholder="MM/YY", max_chars=5)
            with col_cvv:
                st.text_input("CVV", placeholder="123", max_chars=3, type="password")
            
            st.text_input("Cardholder Name", placeholder="JOHN DOE")
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.form_submit_button("✅ ADD FUNDS", use_container_width=True, type="primary"):
                    st.session_state.balance += amount
                    st.session_state.show_add_funds = False
                    st.success(f"✅ PKR {amount:,} added to wallet!")
                    time.sleep(0.5)
                    st.rerun()
            with col_cancel:
                if st.form_submit_button("❌ CANCEL", use_container_width=True):
                    st.session_state.show_add_funds = False
                    st.rerun()
    
    # Calculate portfolio value with fresh data
    ticker_prices = {}
    for symbol in st.session_state.holdings.keys():
        ticker_prices[symbol] = get_current_price(symbol)
    
    holdings_val = calculate_portfolio_value(st.session_state.holdings, ticker_prices)
    total_net_worth = st.session_state.balance + holdings_val
    profit_loss = total_net_worth - 25000.0
    pl_pct = (profit_loss / 25000.0) * 100
    
    # Live update indicator
    if auto_refresh and period in ["15m", "1h", "1d"]:
        refresh_time_remaining = int(refresh_interval - (time.time() - st.session_state.last_refresh))
        st.markdown(f'<div style="text-align: center; color: #00FF00; font-size: 11px; margin-bottom: 10px;">🔴 LIVE • Next update in {refresh_time_remaining}s</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("Cash", f"PKR {st.session_state.balance/1000:.1f}K")
    c2.metric("Net Worth", f"PKR {total_net_worth/1000:.1f}K")
    
    # P/L with live indicator
    pl_color = "#00FF00" if profit_loss >= 0 else "#FF0000"
    st.markdown(f"""
    <div style='background: rgba(0,255,0,0.05); padding: 12px; border-radius: 8px; border-left: 3px solid {pl_color}; margin: 10px 0;'>
        <div style='font-size: 11px; color: #8B949E;'>Total P/L {' 🔴 LIVE' if auto_refresh and period in ["15m", "1h", "1d"] else ''}</div>
        <div style='font-size: 24px; font-weight: bold; color: {pl_color}; font-family: "Courier New", monospace;'>
            PKR {profit_loss:,.0f}
        </div>
        <div style='font-size: 14px; color: {pl_color};'>{pl_pct:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Watchlist with live prices
    st.markdown("### 👁️ Watchlist")
    for sym in st.session_state.watchlist[:4]:
        price = get_current_price(sym)
        if st.button(f"{sym}: PKR {price:.2f}", key=f"watch_{sym}"):
            st.rerun()
    
    st.markdown("---")
    st.markdown('<div class="live-indicator">🟢 LIVE</div>', unsafe_allow_html=True)
    
    # Action buttons
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.balance = 25000.0
            st.session_state.holdings = {}
            st.session_state.log = []
            st.rerun()
    
    with col_b:
        if st.button("🚪 Logout", use_container_width=True):
            logout()

# --- 8. AUTO-REFRESH LOGIC ---
# Map period to interval for better granularity (only for short timeframes)
interval_map = {
    "15m": ("1d", "1m"),  # 15 minutes of 1-minute data
    "1h": ("1d", "2m"),   # 1 hour of 2-minute data
    "1d": ("1d", "5m"),   # 1 day of 5-minute data
    "5d": ("5d", "15m"),  # 5 days of 15-minute data
    "1mo": ("1mo", None), # 1 month - default
    "3mo": ("3mo", None), # 3 months - default
    "6mo": ("6mo", None), # 6 months - default
    "1y": ("1y", None),   # 1 year - default
    "5y": ("5y", None)    # 5 years - default
}

if auto_refresh:
    current_time = time.time()
    if period in ["15m", "1h", "1d"]:
        refresh_time = 10  # 10 seconds for ultra-fast
    elif period == "5d":
        refresh_time = 30  # 30 seconds
    else:
        refresh_time = 300  # 5 minutes
    
    if current_time - st.session_state.last_refresh > refresh_time:
        st.session_state.last_refresh = current_time
        st.rerun()

# --- 9. MAIN DATA ENGINE ---
try:
    with st.spinner(f"📡 Loading {ticker} data..."):
        # Get the appropriate period and interval
        data_period, data_interval = interval_map.get(period, (period, None))
        data = yf.Ticker(ticker)
        
        # For 15m, get only last 15 minutes of data
        if period == "15m":
            hist = data.history(period="1d", interval="1m")
            if not hist.empty:
                # Get last 15 periods (15 minutes of 1-min data)
                hist = hist.tail(15)
        # For 1h, get only last hour of data
        elif period == "1h":
            hist = data.history(period="1d", interval="2m")
            if not hist.empty:
                # Get last 30 periods (1 hour of 2-min data)
                hist = hist.tail(30)
        # For short timeframes with custom intervals
        elif data_interval:
            hist = data.history(period=data_period, interval=data_interval)
        # For longer timeframes, use default
        else:
            hist = data.history(period=period)
    
    if hist.empty:
        st.error("❌ Invalid Symbol or No Data Available")
        st.stop()
        
    curr_price = float(hist['Close'].iloc[-1])
    prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else curr_price
    price_change = curr_price - prev_close
    pct_change = (price_change / prev_close) * 100 if prev_close != 0 else 0
    
    # Additional metrics
    high_52w = float(hist['High'].max())
    low_52w = float(hist['Low'].min())
    avg_volume = float(hist['Volume'].mean())
    
    color = "#00FF00" if price_change >= 0 else "#FF0000"
    
except Exception as e:
    st.error(f"❌ Data connection failed: {str(e)}")
    st.stop()

# --- 10. UI LAYOUT ---

# Top Header Stats
col_head1, col_head2, col_head3, col_head4 = st.columns([2,1,1,1])
with col_head1:
    st.markdown(f"<h1 style='margin:0; padding:0;'>{ticker}</h1>", unsafe_allow_html=True)
    # Show data granularity for short timeframes only
    if period in ["15m", "1h", "1d", "5d"]:
        _, interval = interval_map.get(period, (period, None))
        if interval:
            live_badge = ' 🔴 LIVE' if auto_refresh and period in ["15m", "1h", "1d"] else ''
            st.caption(f"Real-Time Market Data • {period.upper()} • {interval} intervals{live_badge}")
        else:
            st.caption(f"Real-Time Market Data • {period.upper()}")
    else:
        st.caption(f"Real-Time Market Data • {period.upper()}")

with col_head2:
    st.metric("Last Price", f"PKR {curr_price:,.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")

with col_head3:
    st.metric("52W High", f"PKR {high_52w:,.2f}")
    st.metric("52W Low", f"PKR {low_52w:,.2f}")

with col_head4:
    sentiment = "BULLISH 🐂" if price_change > 0 else "BEARISH 🐻"
    st.markdown(f"<div style='text-align:center; padding: 10px; border: 1px solid {color}; color: {color}; border-radius: 5px;'>{sentiment}</div>", unsafe_allow_html=True)
    st.metric("Avg Volume", f"{avg_volume/1e6:.1f}M")

# Main Workspace Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 CHARTING", "⚡ TRADING CONSOLE", "🧠 INTELLIGENCE", "📈 ANALYTICS"])

# --- TAB 1: CHART ---
with tab1:
    chart_col1, chart_col2 = st.columns([3, 1])
    
    with chart_col1:
        chart_type = st.radio("Chart Type", ["Candlestick", "Line", "Area"], horizontal=True)
    
    with chart_col2:
        # Show number of data points
        st.caption(f"📊 {len(hist)} data points")
    
    fig = go.Figure()
    
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'], 
            high=hist['High'],
            low=hist['Low'], 
            close=hist['Close'],
            increasing_line_color='#00FF00', 
            decreasing_line_color='#FF0000',
            name=ticker
        ))
    elif chart_type == "Line":
        fig.add_trace(go.Scatter(
            x=hist.index, 
            y=hist['Close'],
            mode='lines',
            line=dict(color='#00FF00', width=2),
            name='Close Price'
        ))
    else:  # Area
        fig.add_trace(go.Scatter(
            x=hist.index, 
            y=hist['Close'],
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.2)',
            line=dict(color='#00FF00', width=2),
            name='Close Price'
        ))
    
    # Add volume bar chart
    fig.add_trace(go.Bar(
        x=hist.index,
        y=hist['Volume'],
        name='Volume',
        marker_color='rgba(88, 166, 255, 0.3)',
        yaxis='y2'
    ))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False,
        yaxis=dict(title='Price (PKR)'),
        yaxis2=dict(title='Volume', overlaying='y', side='right', showgrid=False),
        hovermode='x unified',
        transition={'duration': 500},
        # Better x-axis formatting for different timeframes
        xaxis=dict(
            title='Time',
            tickformat='%H:%M' if period in ["15m", "1h", "1d"] else '%b %d' if period in ["5d", "1mo"] else '%Y-%m'
        )
    )
    st.plotly_chart(fig, use_container_width=True, key="main_chart")

# --- TAB 2: TRADING CONSOLE ---
with tab2:
    col_trade_L, col_trade_R = st.columns([1, 2])
    
    with col_trade_L:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Place Order")
        
        trade_type = st.selectbox("Order Type", ["MARKET BUY", "MARKET SELL", "LIMIT BUY", "LIMIT SELL"])
        qty = st.number_input("Quantity", min_value=1, value=10, step=1)
        
        # Limit order price
        if "LIMIT" in trade_type:
            limit_price = st.number_input("Limit Price (PKR)", min_value=0.01, value=float(curr_price), step=0.01, format="%.2f")
        else:
            limit_price = curr_price
        
        est_total = qty * limit_price
        st.markdown(f"**Est. Total:** PKR {est_total:,.2f}")
        
        # Show available balance/position
        if "BUY" in trade_type:
            st.caption(f"💰 Available Cash: PKR {st.session_state.balance:,.2f}")
        else:
            current_position = st.session_state.holdings.get(ticker, 0)
            st.caption(f"📦 Current Position: {current_position} units")
        
        if st.button("SUBMIT ORDER", type="primary", use_container_width=True):
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if "BUY" in trade_type:
                if st.session_state.balance >= est_total:
                    st.session_state.balance -= est_total
                    st.session_state.holdings[ticker] = st.session_state.holdings.get(ticker, 0) + qty
                    st.session_state.log.append(f"🟢 {timestamp} | BUY {qty} {ticker} @ PKR {limit_price:.2f}")
                    st.success("✅ ORDER EXECUTED")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("❌ INSUFFICIENT FUNDS")
            else:  # SELL
                if st.session_state.holdings.get(ticker, 0) >= qty:
                    st.session_state.balance += est_total
                    st.session_state.holdings[ticker] -= qty
                    if st.session_state.holdings[ticker] == 0:
                        del st.session_state.holdings[ticker]
                    st.session_state.log.append(f"🔴 {timestamp} | SELL {qty} {ticker} @ PKR {limit_price:.2f}")
                    st.success("✅ ORDER EXECUTED")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("❌ INSUFFICIENT POSITION")
        
        st.markdown('</div>', unsafe_allow_html=True)

    with col_trade_R:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Recent Activity")
        if st.session_state.log:
            for line in reversed(st.session_state.log[-8:]):
                st.code(line, language="bash")
        else:
            st.caption("No trades executed this session.")
        
        st.markdown("---")
        st.subheader("Current Positions")
        if st.session_state.holdings:
            position_data = []
            for symbol, qty in st.session_state.holdings.items():
                if qty > 0:
                    price = get_current_price(symbol)
                    value = qty * price
                    position_data.append({
                        "Asset": symbol,
                        "Quantity": qty,
                        "Current Price": f"PKR {price:,.2f}",
                        "Total Value": f"PKR {value:,.2f}"
                    })
            
            if position_data:
                df = pd.DataFrame(position_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Portfolio is empty.")
        else:
            st.info("Portfolio is empty.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: INTELLIGENCE ---
with tab3:
    col_vid, col_news = st.columns(2)
    
    with col_vid:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("📺 Video Analysis")
        queries = [
            f"{ticker} trading strategy",
            f"{ticker} technical analysis",
            f"{ticker} news today",
            f"{ticker} price prediction"
        ]
        for q in queries:
            url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
            st.markdown(f"""
            <a href="{url}" target="_blank" style="text-decoration: none; color: white;">
                <div style="background: #21262D; padding: 10px; margin-bottom: 5px; border-radius: 5px; border-left: 3px solid #FF0000; transition: all 0.3s ease;">
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
            if feed.entries:
                for entry in feed.entries[:6]:
                    st.markdown(f"""
                    <div style="margin-bottom: 10px; border-bottom: 1px solid #30363D; padding-bottom: 5px;">
                        <a href="{entry.link}" target="_blank" style="text-decoration: none; color: #58A6FF; font-weight: bold;">{entry.title}</a>
                        <div style="font-size: 12px; color: #8B949E;">{entry.published if 'published' in entry else 'Recent'}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent news available.")
        except Exception as e:
            st.warning("News feed temporarily offline.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: ANALYTICS ---
with tab4:
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("📊 Technical Indicators")
        
        # Calculate Simple Moving Averages
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        
        # RSI Calculation
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        current_rsi = hist['RSI'].iloc[-1] if not hist['RSI'].isna().all() else 50
        
        col_a, col_b = st.columns(2)
        col_a.metric("SMA 20", f"PKR {hist['SMA_20'].iloc[-1]:,.2f}" if not hist['SMA_20'].isna().all() else "N/A")
        col_b.metric("SMA 50", f"PKR {hist['SMA_50'].iloc[-1]:,.2f}" if not hist['SMA_50'].isna().all() else "N/A")
        
        st.metric("RSI (14)", f"{current_rsi:.2f}")
        
        # RSI Signal
        if current_rsi > 70:
            st.warning("⚠️ Overbought - Consider Selling")
        elif current_rsi < 30:
            st.success("✅ Oversold - Consider Buying")
        else:
            st.info("ℹ️ Neutral Zone")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_right:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("💰 Performance Metrics")
        
        # Calculate returns
        period_return = ((curr_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
        volatility = hist['Close'].pct_change().std() * 100
        
        st.metric("Period Return", f"{period_return:+.2f}%")
        st.metric("Volatility", f"{volatility:.2f}%")
        st.metric("Total Volume", f"{hist['Volume'].sum()/1e9:.2f}B")
        
        # Portfolio Performance
        if st.session_state.holdings:
            st.markdown("---")
            st.markdown("**Portfolio Performance**")
            initial_value = 25000.0
            current_value = st.session_state.balance + holdings_val
            portfolio_return = ((current_value - initial_value) / initial_value) * 100
            
            st.metric("Portfolio Return", f"{portfolio_return:+.2f}%")
            st.metric("Total Trades", len(st.session_state.log))
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Price distribution chart
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("📉 Price Distribution")
    
    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(
        x=hist['Close'],
        nbinsx=30,
        marker_color='#00FF00',
        opacity=0.7,
        name='Price Distribution'
    ))
    
    fig_dist.update_layout(
        template="plotly_dark",
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        xaxis_title="Price (PKR)",
        yaxis_title="Frequency",
        transition={'duration': 500}
    )
    
    st.plotly_chart(fig_dist, use_container_width=True, key="dist_chart")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
current_time = datetime.now().strftime("%I:%M:%S %p")
st.caption(f"⚡ Vaultex Pro Terminal • User: {st.session_state.username} • {current_time} • Market data by Yahoo Finance")