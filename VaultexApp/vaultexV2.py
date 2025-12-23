import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import feedparser
from datetime import datetime
import pandas as pd
import hashlib

# --- 1. PAGE CONFIGURATION & CUSTOM CSS ---
st.set_page_config(page_title="Vaultex Pro Terminal", layout="wide", page_icon="⚡")

# Enhanced Custom CSS
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
    
    /* Button Styling */
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
    
    /* Login Container */
    .login-container {
        max-width: 450px;
        margin: 100px auto;
        padding: 40px;
        background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
        border: 2px solid #30363D;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
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
        margin-bottom: 10px;
    }
    
    .login-subtitle {
        color: #8B949E;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. USER DATABASE (In production, use proper database) ---
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
                        st.rerun()
                    else:
                        st.error("❌ Invalid password")
                else:
                    st.error("❌ User not found")
            
            if demo_btn:
                st.session_state.authenticated = True
                st.session_state.username = "demo"
                st.success("✅ Entering Demo Mode!")
                st.rerun()
        
        # Info section
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #8B949E; font-size: 12px;'>
            <b>Demo Credentials:</b><br>
            Username: <code>demo</code> | Password: <code>demo</code><br><br>
            <b>Admin Access:</b><br>
            Username: <code>admin</code> | Password: <code>admin123</code>
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
def calculate_portfolio_value(holdings, ticker_prices):
    """Calculate total portfolio value"""
    total = 0
    for symbol, qty in holdings.items():
        if qty > 0:
            try:
                price = ticker_prices.get(symbol, 0)
                total += qty * price
            except:
                pass
    return total

def get_current_price(symbol):
    """Get current price for a symbol"""
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
    except:
        pass
    return 0

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
    
    ticker = st.text_input("SYMBOL", value="BTC-USD").upper()
    period = st.selectbox("TIMEFRAME", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"])
    
    st.markdown("---")
    st.markdown("### 💼 Wallet Status")
    
    # Calculate portfolio value
    ticker_prices = {}
    for symbol in st.session_state.holdings.keys():
        ticker_prices[symbol] = get_current_price(symbol)
    
    holdings_val = calculate_portfolio_value(st.session_state.holdings, ticker_prices)
    total_net_worth = st.session_state.balance + holdings_val
    profit_loss = total_net_worth - 25000.0
    pl_pct = (profit_loss / 25000.0) * 100
    
    c1, c2 = st.columns(2)
    c1.metric("Cash", f"PKR {st.session_state.balance/1000:.1f}K")
    c2.metric("Net Worth", f"PKR {total_net_worth/1000:.1f}K")
    
    st.metric("Total P/L", f"PKR {profit_loss:,.0f}", f"{pl_pct:+.2f}%")
    
    st.markdown("---")
    
    # Watchlist
    st.markdown("### 👁️ Watchlist")
    for sym in st.session_state.watchlist[:4]:
        price = get_current_price(sym)
        if st.button(f"{sym}: PKR {price:.2f}", key=f"watch_{sym}"):
            ticker = sym
            st.rerun()
    
    st.markdown("---")
    st.info("System Status: 🟢 ONLINE")
    
    # Reset Portfolio
    if st.button("🔄 Reset Portfolio", type="secondary"):
        st.session_state.balance = 25000.0
        st.session_state.holdings = {}
        st.session_state.log = []
        st.rerun()
    
    # Logout Button
    if st.button("🚪 LOGOUT", type="secondary"):
        logout()

# --- 8. MAIN DATA ENGINE ---
try:
    data = yf.Ticker(ticker)
    hist = data.history(period=period)
    
    if hist.empty:
        st.error("Invalid Symbol or No Data Available")
        st.stop()
        
    curr_price = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else curr_price
    price_change = curr_price - prev_close
    pct_change = (price_change / prev_close) * 100 if prev_close != 0 else 0
    
    # Additional metrics
    high_52w = hist['High'].max()
    low_52w = hist['Low'].min()
    avg_volume = hist['Volume'].mean()
    
    color = "#00FF00" if price_change >= 0 else "#FF0000"
    
except Exception as e:
    st.error(f"Data connection failed: {str(e)}")
    st.stop()

# --- 9. UI LAYOUT ---

# Top Header Stats
col_head1, col_head2, col_head3, col_head4 = st.columns([2,1,1,1])
with col_head1:
    st.markdown(f"<h1 style='margin:0; padding:0;'>{ticker}</h1>", unsafe_allow_html=True)
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
    chart_type = st.radio("Chart Type", ["Candlestick", "Line", "Area"], horizontal=True)
    
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
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

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
            limit_price = st.number_input("Limit Price (PKR)", min_value=0.01, value=float(curr_price), step=0.01)
        else:
            limit_price = curr_price
        
        est_total = qty * limit_price
        st.markdown(f"**Est. Total:** PKR {est_total:,.2f}")
        
        # Show available balance/position
        if "BUY" in trade_type:
            st.caption(f"Available Cash: PKR {st.session_state.balance:,.2f}")
        else:
            current_position = st.session_state.holdings.get(ticker, 0)
            st.caption(f"Current Position: {current_position} units")
        
        if st.button("SUBMIT ORDER", type="primary"):
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if "BUY" in trade_type:
                if st.session_state.balance >= est_total:
                    st.session_state.balance -= est_total
                    st.session_state.holdings[ticker] = st.session_state.holdings.get(ticker, 0) + qty
                    st.session_state.log.append(f"🟢 {timestamp} | BUY {qty} {ticker} @ PKR {limit_price:.2f}")
                    st.success("✅ ORDER EXECUTED")
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
        yaxis_title="Frequency"
    )
    
    st.plotly_chart(fig_dist, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"⚡ Vaultex Pro Terminal • User: {st.session_state.username} • Market data provided by Yahoo Finance")