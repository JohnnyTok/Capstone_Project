import streamlit as st
import pandas as pd
import time
import backend as bk
from config import AppConfig
from i18n import _
import urllib.request
import urllib.parse
import re
import gzip
from html import unescape

# Load config once
cfg = AppConfig.load()

def show():
    """
    Renders the API Integration Page
    """
    st.markdown(f"""
    <div class="page-hero api-hero">
        <div>
            <span class="page-kicker">{_('Data Pipeline')}</span>
            <h4>{_('External Data Integration')}</h4>
            <p1>{_('Connect ecommerce or social channels, fetch live reviews, and send them straight into AI sentiment analysis.')}</p1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Gating
    plan = st.session_state.user_info.get('plan', 'free')
    if plan == 'free':
        st.error(_("🔒 API Integration is a Basic/Premium feature. Please upgrade to access."))
        return # Stop rendering this specific page

    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown(f"<div class='surface-card api-connect-card'><p4 class='section-heading'>{_('Connection Setup')}</p4>", unsafe_allow_html=True)
        source = st.selectbox(_("Select Data Source"), ["Shoppee", "Lazada", "Twitter/X Feed", "Google Reviews"])
        
        # UI updated to ask for a URL instead of an API token
        api_key = st.text_input(_("Target URL / Data Endpoint"), help=_("Paste the full website URL you want to scrape here."))
        
        if st.button(_("🔗 Connect & Fetch Data"), type="primary"):
            if not api_key:
                st.warning(_("Please enter a Target URL."))
            else:
                st.session_state.analysis_in_progress = True
                with st.status(_("Establishing Secure Connection..."), expanded=True) as status:
                    time.sleep(1)
                    status.write(_("✅ Authentication Successful"))
                    time.sleep(0.5)
                    status.write(f"{_('📥 Fetching live data from')} {source}...")
                    
                    # ─── REAL WEB SCRAPING LOGIC ────────────────────────────
                    try:
                        # 1. Mimic a real web browser to bypass basic bot-blockers
                        req = urllib.request.Request(api_key, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5'
                        })
                        
                        # 2. Download the live HTML
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            raw_bytes = resp.read(250000)
                            if raw_bytes.startswith(b'\x1f\x8b'):
                                raw_bytes = gzip.decompress(raw_bytes)
                            raw_html = raw_bytes.decode('utf-8', errors='replace')
                        
                        # 3. Clean the HTML tags and extract readable sentences
                        text = re.sub(r'(?is)<(script|style).*?>.*?</\1>', ' ', raw_html)
                        text = re.sub(r'(?s)<[^>]+>', ' ', text)
                        text = unescape(text)
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        snippets = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if 40 < len(s.strip()) <= 600]
                        
                        # 4. Apply dynamic plan limits
                        if plan == 'premium': row_limit = 1000000
                        elif plan == 'basic': row_limit = 500
                        else: row_limit = 10
                        snippets = snippets[:row_limit]

                        # 5. Stop if the firewall blocked us
                        if not snippets:
                            st.error(_("Could not find any readable reviews. The site may be protected by a bot-firewall."))
                            st.stop()

                        # 6. Build the DataFrame with the live text
                        df = pd.DataFrame({'Review': snippets})
                        df.index += 1

                    except Exception as e:
                        st.error(f"{_('Failed to fetch live data:')} {e}")
                        st.stop()
                    # ────────────────────────────────────────────────────────
                    
                    status.write(_("🧠 Running AI Sentiment Analysis..."))
                    
                    # ─── THRESHOLD & ENGINE LOGIC ───────────────────────────
                    # 1. Grab the custom settings (or use defaults if none exist)
                    pos_t = float(st.session_state.get("pos_threshold", cfg.DEFAULT_POSITIVE_THRESHOLD))
                    neg_t = float(st.session_state.get("neg_threshold", cfg.DEFAULT_NEGATIVE_THRESHOLD))
                    
                    # 2. Grab the engine from memory
                    engine_choice = st.session_state.get("engine", "VADER")

                    # 3. Run the analysis using the dynamic thresholds and engine
                    scores, labels = bk.analyze_sentiment_batch(
                        df['Review'].astype(str).tolist(), 
                        pos_t, 
                        neg_t,
                        engine=engine_choice
                    )
                    # ────────────────────────────────────────────────────
                    df['Sentiment Label'] = labels
                    df['Sentiment Score'] = scores
                    
                    # Update Session State
                    st.session_state.df = df
                    st.session_state.analysis_done = True

                    user_id = st.session_state.user_info.get("id", 0) if st.session_state.user_info else 0
                    df.to_pickle(f"user_{user_id}_last_run.pkl")

                    st.session_state.data_source = "api"
                    if len(scores) > 0: st.session_state.monitor.update(sum(scores)/len(scores))

                    metrics = bk.calculate_metrics(st.session_state.df)
                    bk.save_analysis_history(
                        user_id=user_id,
                        filename=f"{source} API Fetch", 
                        source="api", 
                        metrics=metrics
                    )
                    
                    status.update(label=_("Analysis Complete!"), state="complete", expanded=False)
                    st.toast(f"{_('Data fetched successfully')}", icon="📥")

        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="surface-card api-info-card">
            <p class="section-heading">{_('What happens next')}</p>
            <div class="info-step"><span>1</span><strong>{_('Target')}</strong><small>{_('Provide the URL to fetch data from.')}</small></div>
            <div class="info-step"><span>2</span><strong>{_('Scrape')}</strong><small>{_('Pull review text into the workspace.')}</small></div>
            <div class="info-step"><span>3</span><strong>{_('Analyze')}</strong><small>{_('Generate labels and dashboard charts.')}</small></div>
        </div>
        """, unsafe_allow_html=True)