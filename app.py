import streamlit as st
import pandas as pd
import backend as bk
import styles as ui
import auth
import monitoring
import sidebar
import setting
import subscription
import api_connect
import translation
from config import AppConfig
import logger as log_setup
import logging
import urllib.request
import urllib.error
import urllib.parse
import re
import gzip
import time
from html import unescape
import admin
import db as database
from i18n import _
        
# ── 1. SETUP ─────────────────────────────────────────────────────────────────
cfg = AppConfig.load()
log_setup.setup_logging()
system_logger = logging.getLogger("app")
st.set_page_config(page_title=cfg.APP_TITLE, page_icon="📊", layout="wide")
ui.apply_custom_css()

# Run DB migrations on every startup (idempotent)
try:
    database.migrate()
except Exception as _mig_err:
    system_logger.warning(f"DB migration warning: {_mig_err}")

# ── ADMIN HELPER ─────────────────────────────────────────────────────────────
ADMIN_USERS = {"admin", "johnny"}

def is_admin(user_info: dict) -> bool:
    return bool(user_info) and user_info.get("username", "") in ADMIN_USERS

# ── URL REVIEW EXTRACTION HELPERS ────────────────────────────────────────────
def _normalize_link_url(raw_url: str):
    url = (raw_url or "").strip()
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return url

def _extract_page_text_from_url(url: str):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5',
            'Accept-Encoding': 'identity'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get('Content-Type', '')
            encoding = resp.headers.get_content_charset()
            if content_type and not any(t in content_type.lower() for t in ("text/", "html", "xml", "json")):
                return None
            raw_bytes = resp.read(250000)
        if raw_bytes.startswith(b'\x1f\x8b'):
            raw_bytes = gzip.decompress(raw_bytes)
        if not encoding:
            m = re.search(r'charset=["\']?([^;"\' ]+)', content_type, re.I)
            encoding = m.group(1).strip() if m else None
        raw_html = None
        for cand in [encoding, 'utf-8', 'utf-8-sig', 'cp1252', 'latin-1']:
            if not cand:
                continue
            try:
                decoded = raw_bytes.decode(cand, errors='replace')
                if raw_html is None or decoded.count('\ufffd') < raw_html.count('\ufffd'):
                    raw_html = decoded
            except LookupError:
                continue
        if not raw_html or raw_html.count('\ufffd') > max(5, len(raw_html) * 0.02):
            return None
        text = re.sub(r'(?is)<(script|style).*?>.*?</\1>', ' ', raw_html)
        text = re.sub(r'(?s)<[^>]+>', ' ', text)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:20000]
    except Exception:
        return None

def _looks_readable_text(text: str):
    if not text or '\ufffd' in text:
        return False
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return False
    return sum(c.isalnum() for c in chars) / len(chars) >= 0.45

def _build_review_snippets_from_text(text: str):
    if not text:
        return []
    sentences = [
        s.strip() for s in re.split(r'(?<=[.!?])\s+', text)
        if 40 < len(s.strip()) <= 600 and _looks_readable_text(s.strip())
    ]
    if not sentences:
        fb = text[:500].strip()
        return [fb] if _looks_readable_text(fb) else []
    
    # ── THE FIX: RETURN EVERYTHING! ──
    # We removed the [:max_snippets] cap so your subscription logic handles the limits lower down.
    return sentences

def _run_link_sentiment_analysis(snippets):
    df = pd.DataFrame({'Review': snippets})
    df.index += 1
    pos_t = st.session_state.get("pos_threshold", cfg.DEFAULT_POSITIVE_THRESHOLD)
    neg_t = st.session_state.get("neg_threshold", cfg.DEFAULT_NEGATIVE_THRESHOLD)
    
    # ─── 1. GRAB THE ENGINE FROM MEMORY ───
    engine_choice = st.session_state.get("engine", "VADER")

    # ─── 2. PASS THE ENGINE TO THE BACKEND ───
    scores, labels = bk.analyze_sentiment_batch(
        df['Review'].astype(str).tolist(), 
        pos_t, 
        neg_t,
        engine=engine_choice  # <--- THIS IS THE MISSING PIECE!
    )
    
    df['Sentiment Score'] = scores
    df['Sentiment Label'] = labels
    st.session_state.df = df
    st.session_state.analysis_done = True
    st.session_state.data_source = "link"
    if scores:
        st.session_state.monitor.update(sum(scores) / len(scores))

# ── 2. STATE ──────────────────────────────────────────────────────────────────
defaults = {
    'df': None, 'analysis_done': False, 'logged_in': False,
    'user_info': None, 'analysis_in_progress': False,
    'last_uploaded_filename': None, 'data_source': 'upload',
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
if 'monitor' not in st.session_state:
    st.session_state.monitor = monitoring.RealTimeMonitor()

# ── 3. AUTH ───────────────────────────────────────────────────────────────────
auth.show_auth_screen()

# ── 4. SIDEBAR + ROUTING ──────────────────────────────────────────────────────
selected = sidebar.show_sidebar()

# Keep these keys as English, they are your code's "keys"
if selected == "Admin":
    if is_admin(st.session_state.user_info):
        admin.show()
    else:
        st.error(_("🔒 Access Denied."))
    st.stop()

if selected == "Customer": # No underscore here
    if is_admin(st.session_state.user_info):
        admin.show()
    else:
        st.error(_("🔒 Access Denied. Administrator privileges required."))
    st.stop()

if selected == "Settings": # No underscore here
    setting.show()
    st.stop()

if selected == "Subscription": # No underscore here
    subscription.show()
    st.stop()

if selected == "API Connect": # No underscore here
    api_connect.show()
    if not st.session_state.analysis_done:
        st.stop()

if selected == "Settings":
    setting.show()
    st.stop()

# ── 5. DASHBOARD ──────────────────────────────────────────────────────────────
if selected == "Dashboard":  # <--- REMOVE THE _() HERE! IT MUST BE EXACTLY THIS.
    user_info = st.session_state.user_info or {}
    plan = user_info.get("plan", "free")
    username = user_info.get("username", "User")

    import os
    user_id = user_info.get("id", 0)
    save_file = f"user_{user_id}_last_run.pkl"

    # If the app just booted up, check if they have a saved file!
    if not st.session_state.analysis_done and os.path.exists(save_file):
        try:
            st.session_state.df = pd.read_pickle(save_file)
            st.session_state.analysis_done = True
            st.session_state.data_source = "saved"
            st.session_state.last_uploaded_filename = _("Loaded from previous session")
        except Exception as e:
            system_logger.error(f"Could not load previous session: {e}")

# ── 1. Plan row limit info & Hero Title ──
    row_limits = {'free': 10, 'basic': 500, 'premium': _('Unlimited')}
    active_engine = st.session_state.get("engine", "VADER") # Grabs their chosen AI
    
    st.markdown(f"""
    <div class="dashboard-hero">
        <div>
            <span class="dashboard-kicker">{_('Review Intelligence')}</span>
            <h4>{_('Product Insights Dashboard')}</h4>
            <p1>{_('Analyze customer reviews from a product link or CSV upload, then turn sentiment into clear product decisions.')}</p1>
        </div>
        <div class="dashboard-hero-panel">
            <div class="hero-panel-number">🧠</div>
            <div>
                <strong>{_('Active AI:')} {active_engine}</strong>
                <span>{plan.title()} {_('Account')} • {_('Max Rows:')} {row_limits.get(plan, 10)}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Onboarding banner for first-time users ──
    # Unconditionally set to True the first time they load the dashboard this session
    if "show_welcome" not in st.session_state:
        st.session_state["show_welcome"] = user_info.get("first_login", False)

    if st.session_state["show_welcome"]:
        st.info(
            _("👋 **Welcome to AI Evaluator Pro!** Here's how to get started:\n\n"
            "**Step 1** — Paste a product URL *or* upload a CSV with a `Review` column\n\n"
            "**Step 2** — Click **Run Analysis** to generate sentiment insights\n\n"
            "**Step 3** — Download your PDF/Excel report"),
            icon="🚀"
        )
        if st.button(_("Got it, dismiss"), key="dismiss_welcome"):
            st.session_state["show_welcome"] = False
            st.rerun()

    # ── Negative sentiment spike alert ──
    if st.session_state.analysis_done and st.session_state.df is not None:
        prefs = user_info.get("preferences", {})
        if isinstance(prefs, str):
            import json
            try:
                prefs = json.loads(prefs)
            except Exception:
                prefs = {}
        if prefs.get("alert_on_spike", True):
            df_check = st.session_state.df
            if 'Sentiment Label' in df_check.columns:
                neg_pct = (df_check['Sentiment Label'] == 'Negative').mean() * 100
                if neg_pct > 60:
                    st.warning(
                        f"⚠️ **{_('Negative Sentiment Spike Detected:')}** {neg_pct:.1f}% {_('of reviews are negative.')} "
                        f"{_('Immediate product quality review is recommended.')}"
                    )

    # ── Link analysis ──
    st.markdown(f"<p class='section-heading'>🔗 {_('Analyze a Product Link')}</p>", unsafe_allow_html=True)
    link_url = st.text_input(_("Paste the product or review page URL below"),
                             placeholder="https://example.com/product-reviews")
    analyze_link_btn = st.button(_("Analyze Link"), type="primary")

    if analyze_link_btn:
        if not link_url:
            st.warning(_("Please enter a link to analyze."))
        else:
            normalized_url = _normalize_link_url(link_url)
            if not normalized_url:
                st.warning(_("That doesn't look like a valid URL. Try pasting the full address including https://"))
            else:
                progress = st.progress(0, text=_("Fetching page..."))
                page_text = _extract_page_text_from_url(normalized_url)
                progress.progress(40, text=_("Extracting review sentences..."))
                if not page_text:
                    st.warning(_("Could not read that page — it may be private or bot-protected."))
                    progress.empty()
                else:
                    snippets = _build_review_snippets_from_text(page_text)
                    
                    # ── DYNAMIC ROW LIMIT BASED ON PLAN ──
                    if plan == 'premium':
                        row_limit = 1000000  # Essentially unlimited
                    elif plan == 'basic':
                        row_limit = 500
                    else:
                        row_limit = 10

                    if len(snippets) > row_limit:
                        snippets = snippets[:row_limit]
                        st.toast(f"⚠️ {_('Link analysis limited to')} {row_limit} {_('sentences based on your plan.')}", icon="⚠️")
                    # ─────────────────────────────────────────

                    progress.progress(70, text=f"{_('Analyzing')} {len(snippets)} {_('sentences...')}")
                    if not snippets:
                        st.warning(_("Found the page but not enough readable text to analyze."))
                        progress.empty()
                    else:
                        try:
                            _run_link_sentiment_analysis(snippets)
                            progress.progress(100, text=_("Done!"))
                            time.sleep(0.5)
                            progress.empty()
                            st.success(f"✅ {_('Analyzed')} {len(snippets)} {_('sentences from the page. Scroll down to view results.')}")
                            metrics = bk.calculate_metrics(st.session_state.df)
                            bk.save_analysis_history(
                                user_info.get("id", 0), normalized_url, "link", metrics
                            )
                            user_id = user_info.get("id", 0)
                            st.session_state.df.to_pickle(f"user_{user_id}_last_run.pkl")
                            st.rerun()
                        except Exception:
                            system_logger.exception("Link analysis failed")
                            progress.empty()
                            st.warning(_("Could not finish analyzing this link. Please try another page."))

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

 # ── CSV upload ──
    st.markdown(f"<p class='section-heading'>📂 {_('Load Data from CSV')}</p>", unsafe_allow_html=True)

    # Always render the uploader regardless of current state
    uploaded_file = st.file_uploader(_("Upload CSV File"), type=["csv", "xlsx"],
                                     help=_("File must contain a 'Review' column"))

    st.markdown("</div>", unsafe_allow_html=True)

    # Handle the file logic separately
    # Handle the file logic separately
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
                    # ── ROBUST PLAN CHECK ──
                    # Ensure plan is retrieved from the most current user_info
                    current_plan = st.session_state.user_info.get('plan', 'free')
                    
                    # Set a very large number for premium to effectively mean "Unlimited"
                    if current_plan == 'premium':
                        row_limit = 1000000  # Essentially unlimited
                    elif current_plan == 'basic':
                        row_limit = 500
                    else:
                        row_limit = 10
                    
                    # ── Option 2: The "Just In Time" Upgrade Warning ──
                    # Only apply .head() and show warning IF the limit exists
                    if current_plan != 'premium' and len(df) > row_limit:
                        st.warning(
                            f"⚠️ {_('Your file had more than')} {row_limit} {_('rows. We only kept the first')} {row_limit}. "
                            f"**[{_('Upgrade your plan to unlock more rows →')}](#subscription)**"
                        )
                        df = df.head(row_limit)
                    
                    df.index += 1
                    st.session_state.df = df
                    st.session_state.data_source = "upload"
                    st.session_state.analysis_done = False
                else:
                    st.error(_("⚠️ Could not load file. Make sure it has a **'Review'** column with text."))
        except Exception as e:
            st.error(f"{_('File error:')} {e}")

    # Display Analysis UI based on Data in Session State
    if st.session_state.df is not None:
        st.caption(f"✅ **{len(st.session_state.df)} {_('reviews loaded from')}** `{st.session_state.last_uploaded_filename}`")
        analyze_btn = st.button(_("🚀 Run Analysis"), type="primary")
    elif st.session_state.data_source not in ('api', 'link'):
        # Only show the empty state if there's truly nothing loaded
        st.markdown(f"""
        <div class="dashboard-empty-state">
            <div class="empty-icon">CSV</div>
            <div>
                <h6>{_('Upload a CSV to begin analysis.')}</h6>
                <p>{_('Your file should include a <strong>Review</strong> column.')}</p>
                <div class="empty-steps">
                    <span>1. {_('Upload CSV')}</span><span>2. {_('Run Analysis')}</span><span>3. {_('Review Insights')}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        analyze_btn = False

    # ── Run Analysis ──
    if analyze_btn and st.session_state.df is not None:
        total = len(st.session_state.df)
        progress_bar = st.progress(0, text=_("Starting analysis..."))
        reviews = st.session_state.df['Review'].astype(str).tolist()
        pos_t = st.session_state.get("pos_threshold", cfg.DEFAULT_POSITIVE_THRESHOLD)
        neg_t = st.session_state.get("neg_threshold", cfg.DEFAULT_NEGATIVE_THRESHOLD)
        
        # ─── 1. GRAB THE ENGINE FROM MEMORY ───
        engine_choice = st.session_state.get("engine", "VADER")

        chunk = max(1, total // 10)
        all_scores, all_labels = [], []
        for i in range(0, total, chunk):
            batch = reviews[i:i + chunk]
            
            # ─── 2. PASS THE ENGINE TO THE BACKEND ───
            s, l = bk.analyze_sentiment_batch(
                batch, 
                pos_t, 
                neg_t, 
                engine=engine_choice  # <--- THIS IS THE MISSING PIECE!
            )
            
            all_scores.extend(s)
            all_labels.extend(l)
            pct = min(int((i + len(batch)) / total * 100), 99)
            progress_bar.progress(pct, text=f"{_('Analyzed')} {i + len(batch)} / {total} {_('reviews...')}")

        st.session_state.df['Sentiment Score'] = all_scores
        st.session_state.df['Sentiment Label'] = all_labels
        if all_scores:
            st.session_state.monitor.update(sum(all_scores) / len(all_scores))

        metrics = bk.calculate_metrics(st.session_state.df)
        bk.save_analysis_history(
            user_info.get("id", 0),
            st.session_state.last_uploaded_filename or "upload",
            "upload",
            metrics
        )

        user_id = user_info.get("id", 0)
        st.session_state.df.to_pickle(f"user_{user_id}_last_run.pkl")

        progress_bar.progress(100, text=_("Complete!"))
        time.sleep(0.4)
        progress_bar.empty()
        st.session_state.analysis_done = True
        st.rerun()

# ── 6. RESULTS DISPLAY ───────────────────────────────────────────────────────
if st.session_state.analysis_done and st.session_state.df is not None:
    df = st.session_state.df
    metrics = bk.calculate_metrics(df)
    
    # ── NEW SAFETY CHECK ──
    # If metrics is empty, stop drawing the page and show an error
    if not metrics:
        st.error(_("⚠️ Analysis results are incomplete or missing. Please check your data and run the analysis again."))
        st.stop()
    # ──────────────────────
        
    plan = (st.session_state.user_info or {}).get("plan", "free")

    st.markdown("---")
    c1, c2 = st.columns([1, 2])
    with c1:
        # Use .get() so it defaults to 0 instead of crashing if the key is missing
        pct = metrics.get('positive_percentage', 0)
        
        bg = "#16A34A" if pct > 70 else "#F97316" if pct > 50 else "#DC2626"
        msg = _("Excellent") if pct > 70 else _("Average") if pct > 50 else _("Poor")
        st.markdown(
            f"<div class='verdict-box' style='background-color:{bg}'><h3>{msg}</h3></div>",
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(f"""
        <div class="metrics-row">
            <div class="custom-metric positive">
                <div class="metric-title">{_('Positive')}</div>
                <div class="metric-value">{metrics.get('positive_percentage', 0):.1f}%</div>
            </div>
            <div class="custom-metric negative">
                <div class="metric-title">{_('Negative')}</div>
                <div class="metric-value">{metrics.get('negative_percentage', 0):.1f}%</div>
            </div>
            <div class="custom-metric neutral">
                <div class="metric-title">{_('Neutral')}</div>
                <div class="metric-value">{metrics.get('neutral_percentage', 0):.1f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs([f"📊 {_('Charts')}", f"📡 {_('Monitor')}", f"🗃️ {_('Data')}", f"🕐 {_('History')}"])

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(bk.plot_sentiment_distribution(df), use_container_width=True)
        with c2:
            pos_t = st.session_state.get("pos_threshold", cfg.DEFAULT_POSITIVE_THRESHOLD)
            neg_t = st.session_state.get("neg_threshold", cfg.DEFAULT_NEGATIVE_THRESHOLD)
            st.plotly_chart(bk.plot_score_histogram(df, pos_t, neg_t), use_container_width=True)

    with t2:
        if plan == 'premium':
            st.plotly_chart(st.session_state.monitor.create_live_chart(), use_container_width=True)
        else:
            st.warning(_("🔒 Real-time monitor is available on the **Premium** plan."))
            st.markdown(_("[Upgrade your plan →](#subscription)"))

    with t3:
        f1, f2 = st.columns([2, 1])
        with f1:
            search_kw = st.text_input(_("🔍 Search reviews"), placeholder=_("Type a keyword..."))
        with f2:
            label_filter = st.multiselect(
                _("Filter by sentiment"), ["Positive", "Negative", "Neutral"],
                default=["Positive", "Negative", "Neutral"]
            )

        display_df = df.copy()
        if search_kw:
            display_df = display_df[
                display_df['Review'].astype(str).str.contains(search_kw, case=False, na=False)
            ]
        if label_filter:
            display_df = display_df[display_df['Sentiment Label'].isin(label_filter)]

        st.caption(f"{_('Showing')} {len(display_df)} {_('of')} {len(df)} {_('reviews')}")
        st.dataframe(display_df, use_container_width=True)

        if plan == 'free':
            st.error(_("🔒 Export is locked on the Free plan. [Upgrade to download reports →](#subscription)"))
        else:
            r_gen = bk.ReportGenerator()
            cx1, cx2 = st.columns(2)
            with cx1:
                pdf_bytes = r_gen.generate_pdf_report(df, metrics)
                st.download_button(_("📄 Download PDF Report"), pdf_bytes, "sentiment_report.pdf",
                                   mime="application/pdf")
            with cx2:
                if plan == 'premium':
                    xlsx_bytes = r_gen.generate_excel_report(df, metrics)
                    st.download_button(_("📊 Download Excel Report"), xlsx_bytes, "sentiment_report.xlsx",
                                       mime="application/vnd.ms-excel")
                else:
                    st.button(_("📊 Excel Report (Premium only)"), disabled=True)

    with t4:
        user_id = (st.session_state.user_info or {}).get("id", 0)
        history = bk.get_analysis_history(user_id)
        if history:
            hist_df = pd.DataFrame(history)
            hist_df.columns = ["File/Source", "Source", "Reviews", "Positive %",
                                "Negative %", "Avg Score", "Date"]
            hist_df["Date"] = pd.to_datetime(hist_df["Date"]).dt.strftime("%Y-%m-%d %H:%M")
            hist_df["Positive %"] = hist_df["Positive %"].round(1)
            hist_df["Negative %"] = hist_df["Negative %"].round(1)
            hist_df["Avg Score"] = hist_df["Avg Score"].round(3)
            st.dataframe(hist_df, use_container_width=True, hide_index=True)
        else:
            st.info(_("No analysis history yet. Run your first analysis above!"))

ui.show_footer()