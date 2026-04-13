import streamlit as st
import pandas as pd
import backend as bk
import styles as ui
import auth
import monitoring
import sidebar      # Module 1
import setting      # Module 2
import subscription # Module 3 
import api_connect  # Module 4 
import translation
from config import AppConfig
import logger as log_setup
import logging
import admin 

# 1. SETUP
cfg = AppConfig.load()
log_setup.setup_logging()
system_logger = logging.getLogger("app")
st.set_page_config(page_title=cfg.APP_TITLE, page_icon="📊", layout="wide")
ui.apply_custom_css()

# 2. STATE MANAGEMENT
if 'df' not in st.session_state: st.session_state.df = None
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'monitor' not in st.session_state: st.session_state.monitor = monitoring.RealTimeMonitor()
if 'analysis_in_progress' not in st.session_state: st.session_state.analysis_in_progress = False
if 'last_uploaded_filename' not in st.session_state: st.session_state.last_uploaded_filename = None
if 'data_source' not in st.session_state: st.session_state.data_source = "upload"

auth_sys = auth.AuthSystem()

# 3. AUTH (LOGIN SCREEN)
if not st.session_state.logged_in:
    # Initialize the memory state to show the login form first
    if 'auth_view' not in st.session_state:
        st.session_state.auth_view = 'login'

    col1, col2, col3 = st.columns([1, 1.2, 1]) # Made center column slightly wider for the form
    with col2:
        # --- VIEW: LOGIN FORM ---
        if st.session_state.auth_view == 'login':
            st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🔐 Login</h2>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Log In", use_container_width=True):
                    success, user = auth_sys.login(u, p)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user
                        st.rerun()
                    else: 
                        st.error("Invalid credentials")
            
            # Button to switch to Register view
            if st.button("Don't have an account? Register here", use_container_width=True):
                st.session_state.auth_view = 'register'
                st.rerun()

        # --- VIEW: REGISTER FORM ---
        elif st.session_state.auth_view == 'register':
            st.markdown("<h2 style='text-align: center; color: #5d5fef;'>📝 Create Account</h2>", unsafe_allow_html=True)
            
            with st.form("reg_form"):
                e = st.text_input("Email")
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                p2 = st.text_input("Retype Password", type="password")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if p != p2:
                        st.error("⚠️ Passwords do not match! Please try again.")
                    elif len(p) == 0:
                        st.warning("⚠️ Password cannot be empty.")
                    else:
                        s, m = auth_sys.register(e, u, p)
                        if s: 
                            st.success("🎉 Created! Redirecting to Login...")
                            system_logger.info(f"New user: {u}")
                            
                            # THE REDIRECT LOGIC
                            import time
                            time.sleep(1.5) # Wait 1.5 seconds so they can read the success message
                            st.session_state.auth_view = 'login' # Flip the view back to Login
                            st.rerun() # Refresh the page instantly
                        else: 
                            st.error(m)
            
            # Button to switch back to Login view manually
            if st.button("Already have an account? Log In", use_container_width=True):
                st.session_state.auth_view = 'login'
                st.rerun()
    
    st.stop()

# 4. RENDER SIDEBAR
selected = sidebar.show_sidebar()

# --- ROUTING LOGIC (Clean & Modular) ---

# --- ROUTING LOGIC ---

if selected == "Admin":
    # Double security check to prevent people from forcing their way in
    current_user = st.session_state.user_info.get('username')
    if current_user == "admin" or current_user == "johnny":
        admin.show()
    else:
        st.error("🔒 Access Denied. Administrator privileges required.")
    st.stop()

if selected == "Customer":
    # Double security check
    current_user = st.session_state.user_info.get('username')
    if current_user == "admin" or current_user == "johnny":
        admin.show()  # Still calls admin.py, but the tab is named Customer!
    else:
        st.error("🔒 Access Denied. Administrator privileges required.")
    st.stop()

if selected == "Settings":
    setting.show()
    st.stop()

if selected == "Subscription":
    subscription.show()
    st.stop()

if selected == "API Connect":
    api_connect.show()
    # If analysis finishes in the API module, we fall through to the dashboard results below.
    if not st.session_state.analysis_done:
        st.stop()

# 5. DASHBOARD (Main View)
if selected == "Dashboard":
    st.markdown(f"## 📊 Dashboard")
    
    # Uploader in Main Area
    st.markdown("### 📂 Load Data")
    uploaded_file = st.file_uploader("Upload CSV File", type="csv", help="Limit 200MB per file")
    
    analyze_btn = False
    
    if uploaded_file:
        try:
            if st.session_state.last_uploaded_filename != uploaded_file.name:
                st.session_state.analysis_done = False
                st.session_state.df = None
                st.session_state.last_uploaded_filename = uploaded_file.name
                st.session_state.data_source = "upload"
            
            if st.session_state.df is None or st.session_state.data_source != "upload":
                df = bk.load_data(uploaded_file)
                if df is not None:
                    plan = st.session_state.user_info.get('plan', 'free')
                    row_limit = 10 if plan == 'free' else 500 if plan == 'basic' else 1000000
                    if len(df) > row_limit:
                        st.toast(f"Limit Reached: Truncating to {row_limit} rows", icon="⚠️")
                        df = df.head(row_limit)
                    df.index += 1
                    st.session_state.df = df
                    st.session_state.data_source = "upload"
            
            analyze_btn = st.button("🚀 Run Analysis", type="primary")
            
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        if st.session_state.data_source != 'api':
            st.info("👆 Upload a CSV file above to begin analysis.")

    # Run Analysis
    if analyze_btn:
        with st.spinner("Analyzing..."):
            df = st.session_state.df
            # Calls backend which uses translation automatically
            scores, labels = bk.analyze_sentiment_batch(
                df['Review'].astype(str).tolist(), 
                cfg.DEFAULT_POSITIVE_THRESHOLD, 
                cfg.DEFAULT_NEGATIVE_THRESHOLD
            )
            st.session_state.df['Sentiment Score'] = scores
            st.session_state.df['Sentiment Label'] = labels
            if len(scores) > 0: st.session_state.monitor.update(sum(scores)/len(scores))
            st.session_state.analysis_done = True
            st.rerun()

# 6. RESULTS DISPLAY
if st.session_state.analysis_done and st.session_state.df is not None:
    df = st.session_state.df
    metrics = bk.calculate_metrics(df)
    
    st.markdown("---")
    c1, c2 = st.columns([1, 2])
    with c1:
        pct = metrics['positive_percentage']
        bg, msg = ("#4CAF50", "Excellent") if pct > 70 else ("#FF9800", "Average") if pct > 50 else ("#F44336", "Poor")
        st.markdown(f"<div class='verdict-box' style='background-color:{bg}'><h3>{msg}</h3></div>", unsafe_allow_html=True)
    with c2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Positive", f"{metrics['positive_percentage']:.1f}%")
        m2.metric("Negative", f"{metrics['negative_percentage']:.1f}%")
        m3.metric("Neutral", f"{metrics['neutral_percentage']:.1f}%")

    t1, t2, t3 = st.tabs(["Charts", "Monitor", "Data"])
    with t1:
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(bk.plot_sentiment_distribution(df), use_container_width=True)
        with c2: st.plotly_chart(bk.plot_score_histogram(df, cfg.DEFAULT_POSITIVE_THRESHOLD, cfg.DEFAULT_NEGATIVE_THRESHOLD), use_container_width=True)
    with t2:
        if st.session_state.user_info.get('plan') == 'premium':
            st.plotly_chart(st.session_state.monitor.create_live_chart(), use_container_width=True)
        else:
            st.warning("🔒 Monitor is Premium only."); st.markdown("[Upgrade](#subscription)")
    with t3:
        st.dataframe(df)
        plan = st.session_state.user_info.get('plan', 'free')
        if plan == 'free': st.error("🔒 Export locked.")
        else:
            r_gen = bk.ReportGenerator()
            c_x1, c_x2 = st.columns(2)
            with c_x1: st.download_button("PDF Report", r_gen.generate_pdf_report(df, metrics), "report.pdf")
            with c_x2:
                if plan == 'premium': st.download_button("Excel Report", r_gen.generate_excel_report(df, metrics), "report.xlsx")
                else: st.button("Excel (Premium)", disabled=True)

ui.show_footer()
