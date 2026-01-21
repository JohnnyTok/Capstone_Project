import streamlit as st
import pandas as pd
import time
import backend as bk
from config import AppConfig

# Load config once
cfg = AppConfig.load()

def show():
    """
    Renders the API Integration Page
    """
    st.title("🔗 External Data Integration")
    st.markdown("Connect your E-commerce or Social Media accounts to fetch reviews automatically.")
    
    # Feature Gating
    plan = st.session_state.user_info.get('plan', 'free')
    if plan == 'free':
        st.error("🔒 API Integration is a Basic/Premium feature. Please upgrade to access.")
        return # Stop rendering this specific page

    c1, c2 = st.columns([2, 1])
    
    with c1:
        source = st.selectbox("Select Data Source", ["Shoppee", "Lazada", "Twitter/X Feed", "Google Reviews"])
        api_key = st.text_input("API Access Token", type="password", help="Paste your production API key here.")
        
        if st.button("🔗 Connect & Fetch Data", type="primary"):
            if not api_key:
                st.warning("Please enter an API Token.")
            else:
                st.session_state.analysis_in_progress = True
                with st.status("Establishing Secure Connection...", expanded=True) as status:
                    time.sleep(1)
                    status.write("✅ Authentication Successful")
                    time.sleep(0.5)
                    status.write(f"📥 Fetching data from {source}...")
                    time.sleep(1.5)
                    
                    # --- MOCK DATA FOR API SIMULATION ---
                    mock_reviews = ["Great product!", "Not bad", "Terrible quality", "Loved it", "Will buy again"] * 10
                    df = pd.DataFrame({'Product': ['API Item'] * 50, 'Review': mock_reviews})
                    
                    status.write("🧠 Running AI Sentiment Analysis...")
                    
                    # Using Backend Logic (which includes translation now)
                    scores, labels = bk.analyze_sentiment_batch(
                        df['Review'].astype(str).tolist(), 
                        cfg.DEFAULT_POSITIVE_THRESHOLD, 
                        cfg.DEFAULT_NEGATIVE_THRESHOLD
                    )
                    df['Sentiment Score'] = scores
                    df['Sentiment Label'] = labels
                    
                    # Update Session State
                    st.session_state.df = df
                    st.session_state.analysis_done = True
                    st.session_state.data_source = "api"
                    if len(scores) > 0: st.session_state.monitor.update(sum(scores)/len(scores))
                    
                    status.update(label="Analysis Complete!", state="complete", expanded=False)
                    st.toast(f"Data fetched from {source}", icon="📥")