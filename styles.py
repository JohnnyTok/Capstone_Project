import streamlit as st
from streamlit_option_menu import option_menu
import logging
from html import escape

# Setup logger
logger = logging.getLogger("app")

def apply_custom_css():
    # --- ORIGINAL DARK MODE CSS (Always loads as the base) ---
    st.markdown("""
<style>
    /* --- 1. GLOBAL FONTS & THEME --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        background-color: #121824 !important;
        color: #FFFFFF !important;
    }

    /*
      NOTE:
      Your auth (login/register) page should use a separate color theme.
      That theme is applied via apply_auth_only_css() only when logged_in=False.
    */

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #F1F5F9 !important;
        margin-top: 0.4rem !important;
        margin-bottom: 0.6rem !important;
    }

    h1 { font-size: 42px !important; font-weight: 900 !important; letter-spacing: -0.03em !important; }
    h2 { font-size: 30px !important; font-weight: 800 !important; }
    h3 { font-size: 24px !important; font-weight: 700 !important; }
    h4 { font-size: 18px !important; font-weight: 700 !important; }

    .hero-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        margin-bottom: 0.4rem !important;
    }

    .hero-subtitle {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        color: #475569 !important;
        margin-top: 0 !important;
        margin-bottom: 1rem !important;
        line-height: 1.55 !important;
    }

    .auth-panel {
        background: linear-gradient(145deg, #1F293D 0%, rgba(31, 41, 61, 0.95) 100%);
        border: 1px solid rgba(245, 158, 11, 0.2);
        border-radius: 32px;
        padding: 36px 36px 28px;
        box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
        margin-bottom: 1.5rem;
        backdrop-filter: blur(16px);
    }

    .auth-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 38px !important;
        font-weight: 900 !important;
        color: #1E293B !important;
        margin-bottom: 0.4rem !important;
    }

    .auth-subtitle {
        font-family: 'Inter', sans-serif !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #E8F1FF !important;
        margin-bottom: 0.85rem !important;
        line-height: 1.6 !important;
    }

    .auth-note {
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        color: #475569 !important;
        opacity: 0.95 !important;
        margin-bottom: 0.75rem !important;
    }

    .auth-illustration-card {
        background: linear-gradient(180deg, rgba(18, 24, 36, 0.88), rgba(31, 41, 61, 0.98));
        border: 1px solid rgba(245, 158, 11, 0.16);
        border-radius: 32px;
        padding: 28px 24px;
        min-height: 390px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 18px;
        box-shadow: 0 28px 60px rgba(0, 0, 0, 0.32);
    }

    .auth-illustration-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #E8F1FF !important;
        margin-bottom: 0.6rem !important;
    }

    .auth-illustration-copy {
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        color: #475569 !important;
        line-height: 1.65 !important;
    }

    .auth-illustration-hero {
        border-radius: 28px;
        background: radial-gradient(circle at top left, rgba(245, 158, 11, 0.16), transparent 28%),
                    linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(31, 41, 61, 0.9));
        padding: 26px;
        display: flex;
        flex-direction: column;
        gap: 18px;
        min-height: 240px;
    }

    .auth-lock-icon {
        width: 64px;
        height: 64px;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        background: rgba(245, 158, 11, 0.16);
        color: #F59E0B;
        box-shadow: 0 18px 40px rgba(245, 158, 11, 0.15);
    }

    .auth-illustration-panel {
        display: grid;
        gap: 12px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(245, 158, 11, 0.14);
        border-radius: 24px;
        padding: 18px;
    }

    .auth-panel-row {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        font-family: 'Inter', sans-serif !important;
        color: #475569 !important;
        font-size: 13px !important;
    }

    .auth-panel-row span:first-child {
        color: #F59E0B !important;
    }

    .auth-panel-badge {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        border-radius: 999px;
        padding: 8px 14px;
        font-family: 'Inter', sans-serif !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        background: rgba(245, 158, 11, 0.12);
        color: #F59E0B !important;
        width: fit-content;
        margin-top: 8px;
    }

    .auth-switch {
        margin-top: 16px !important;
        text-align: center !important;
        color: #FDE68A !important;
        font-size: 14px !important;
    }

    .auth-secondary {
        color: #F59E0B !important;
        font-weight: 700 !important;
        text-decoration: none !important;
    }

    .auth-secondary:hover {
        color: #F59E0B !important;
    }

    section[data-testid="stAppViewContainer"],
    .main .block-container {
        background-color: #121824 !important;
        color: #475569 !important;
        max-width: 1220px !important;
        margin: 0 auto !important;
        padding-left: 32px !important;
        padding-right: 32px !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #1F293D !important;
        border-right: 1px solid rgba(245, 158, 11, 0.18) !important;
        color: #475569 !important;
    }

    .stButton>button {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 14px 18px !important;
        font-weight: 700 !important;
        box-shadow: 0 18px 35px rgba(0, 0, 0, 0.18) !important;
    }

    .stButton>button:hover {
        background-color: #F59E0B !important;
        color: #FFFFFF !important;
    }

    .stTextInput>div>div>input,
    .stTextInput>div>div>div>input {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        border: 1px solid rgba(245, 158, 11, 0.18) !important;
        border-radius: 16px !important;
        padding: 14px !important;
    }

    .stTextInput>label {
        color: #FFFFFF !important;
    }

    .section-heading {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        margin-bottom: 0.75rem !important;
        color: #334155 !important;
    }

    .pricing-hero {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 36px !important;
        font-weight: 800 !important;
        margin-bottom: 0.4rem !important;
        color: #1E293B !important;
    }

    .pricing-plan {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 22px !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        color: #334155 !important;
    }

    .pricing-price {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 44px !important;
        font-weight: 800 !important;
        margin: 0.4rem 0 0.75rem 0 !important;
        color: #1E293B !important;
    }

    .text-secondary {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        color: #475569 !important;
        line-height: 1.55 !important;
    }

    .micro-text {
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        color: #475569 !important;
        line-height: 1.4 !important;
    }

    p, span, div, label {
        font-size: 16px !important;
        line-height: 1.65 !important;
    }

    .main .block-container,
    .main .block-container p,
    .main .block-container span,
    .main .block-container div,
    .main .block-container label,
    .main .block-container li,
    .main .block-container small,
    .main .block-container [data-testid="stMarkdownContainer"],
    .main .block-container [data-testid="stWidgetLabel"],
    .main .block-container [data-testid="stFileUploader"] * {
        color: #475569 !important;
    }

    .main .block-container input,
    .main .block-container textarea,
    .main .block-container [contenteditable="true"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
    }

    .main .block-container input::placeholder,
    .main .block-container textarea::placeholder {
        color: #475569 !important;
        opacity: 1 !important;
    }

    section[data-testid="stAppViewContainer"],
    .main .block-container {
        background-color: #121824 !important;
        color: #475569 !important;
    }

    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3,
    .main .block-container h4,
    .main .block-container h5,
    .main .block-container h6,
    .main .block-container .pricing-hero,
    .main .block-container .pricing-price,
    .main .block-container .hero-title {
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        opacity: 1 !important;
    }

    .main .block-container .section-heading,
    .main .block-container .pricing-plan {
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
        opacity: 1 !important;
    }

    .main .block-container .text-secondary,
    .main .block-container .micro-text,
    .main .block-container p,
    .main .block-container li,
    .main .block-container label {
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 50% 4%, rgba(245, 158, 11, 0.18), transparent 28%),
            linear-gradient(180deg, #1F293D 0%, #151D2E 100%) !important;
        border-right: 1px solid rgba(245, 158, 11, 0.18) !important;
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }

    .sidebar-brand {
        position: relative;
        overflow: hidden;
        text-align: left;
        padding: 18px 16px;
        margin: 0 0 18px;
        border-radius: 8px;
        background:
            radial-gradient(circle at 86% 18%, rgba(245, 158, 11, 0.24), transparent 28%),
            linear-gradient(145deg, rgba(22, 27, 38, 0.94), rgba(11, 15, 25, 0.92));
        border: 1px solid rgba(245, 158, 11, 0.24);
        box-shadow: 0 18px 34px rgba(0, 0, 0, 0.24);
    }

    .sidebar-brand-mark {
        width: 38px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        margin-bottom: 14px;
        background: linear-gradient(135deg, #F59E0B, #FDE68A);
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        font-weight: 900 !important;
        box-shadow: 0 12px 22px rgba(245, 158, 11, 0.25);
    }

    .sidebar-brand h2 {
        margin: 0 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        line-height: 1.1 !important;
        letter-spacing: 0 !important;
    }

    .sidebar-brand p {
        margin: 8px 0 0 !important;
        color: #FDE68A !important;
        -webkit-text-fill-color: #FDE68A !important;
        font-size: 11px !important;
        font-weight: 800 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase;
    }

    section[data-testid="stSidebar"] .nav-link {
        color: #E8F1FF !important;
        -webkit-text-fill-color: #E8F1FF !important;
    }

    section[data-testid="stSidebar"] .nav-link.active,
    section[data-testid="stSidebar"] .nav-link.active span,
    section[data-testid="stSidebar"] .nav-link.active i {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }

    .profile-card {
        position: relative;
        overflow: hidden;
        background: linear-gradient(145deg, rgba(31, 41, 61, 0.98), rgba(18, 24, 36, 0.98));
        border: 1px solid rgba(245, 158, 11, 0.34);
        border-radius: 8px;
        padding: 14px 14px 14px 12px;
        margin: 10px 0 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: all 0.25s ease;
        box-shadow: 0 14px 28px rgba(0, 0, 0, 0.22);
    }

    .profile-card::before {
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 4px;
        background: linear-gradient(180deg, #FBBF24, #D97706);
    }

    .profile-card:hover {
        background: linear-gradient(145deg, #1E293B, #121824);
        border-color: #F59E0B;
        transform: translateY(-2px);
        box-shadow: 0 14px 28px rgba(245, 158, 11, 0.18);
    }

    .avatar {
        width: 46px;
        height: 46px;
        min-width: 46px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 15px;
        color: #FFFFFF !important;
        background: linear-gradient(135deg, #F59E0B, #D97706);
        box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.12), 0 10px 22px rgba(245, 158, 11, 0.22);
        letter-spacing: 0;
    }

    .user-info {
        min-width: 0;
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 3px;
    }

    .user-label {
        color: #CBD5E1 !important;
        -webkit-text-fill-color: #CBD5E1 !important;
        font-size: 10px !important;
        font-weight: 700 !important;
        line-height: 1.1 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .user-info h4 {
        margin: 0 !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        letter-spacing: 0 !important;
        line-height: 1.2 !important;
        max-width: 130px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .user-info p {
        width: fit-content;
        margin: 4px 0 0 !important;
        padding: 4px 9px;
        border-radius: 999px;
        font-size: 10px !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
    }

    .badge-premium {
        color: #FDE68A !important;
        -webkit-text-fill-color: #FDE68A !important;
        background: rgba(245, 158, 11, 0.16) !important;
        border-color: rgba(245, 158, 11, 0.36) !important;
    }
    .badge-basic {
        color: #FDBA74 !important;
        -webkit-text-fill-color: #FDBA74 !important;
        background: rgba(217, 119, 6, 0.14) !important;
        border-color: rgba(217, 119, 6, 0.28) !important;
    }
    .badge-free {
        color: #E2E8F0 !important;
        -webkit-text-fill-color: #E2E8F0 !important;
    }

    .subscription-page {
        margin-bottom: 16px;
    }

    .dashboard-hero {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 300px;
        gap: 24px;
        align-items: stretch;
        padding: 30px 34px;
        margin-bottom: 20px;
        border-radius: 8px;
        background:
            radial-gradient(circle at 92% 18%, rgba(124, 148, 128, 0.2), transparent 18%),
            linear-gradient(135deg, #FFFDF8 0%, #F4E7D8 100%);
        border: 1px solid rgba(170, 132, 92, 0.22);
        box-shadow: 0 18px 38px rgba(95, 70, 45, 0.12);
    }

    .dashboard-kicker {
        display: inline-flex;
        width: fit-content;
        padding: 6px 12px;
        border-radius: 999px;
        background: #1F293D;
        color: #FDE68A !important;
        -webkit-text-fill-color: #FDE68A !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 16px;
    }

    .main .block-container .dashboard-hero h1 {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-size: 38px !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
        line-height: 1.12 !important;
        margin: 0 0 10px !important;
    }

    .main .block-container .dashboard-hero p {
        max-width: 680px;
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        line-height: 1.6 !important;
        margin: 0 !important;
    }

    .dashboard-hero-panel {
        display: flex;
        align-items: center;
        gap: 14px;
        min-height: 124px;
        padding: 18px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid rgba(170, 132, 92, 0.18);
    }

    .hero-panel-number {
        width: 54px;
        height: 54px;
        min-width: 54px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: linear-gradient(135deg, #B8895B, #FDE68A);
        color: #1F293D !important;
        -webkit-text-fill-color: #1F293D !important;
        font-weight: 900 !important;
        box-shadow: 0 14px 26px rgba(184, 137, 91, 0.22);
    }

    .main .block-container .dashboard-hero-panel strong {
        display: block;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-size: 15px !important;
        font-weight: 900 !important;
        line-height: 1.2 !important;
    }

    .main .block-container .dashboard-hero-panel span {
        display: block;
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        line-height: 1.35 !important;
        margin-top: 5px;
    }

    .dashboard-control-panel,
    .dashboard-empty-state {
        border-radius: 8px;
        background: linear-gradient(145deg, #FFFDF8 0%, #F4E7D8 100%);
        border: 1px solid rgba(170, 132, 92, 0.22);
        box-shadow: 0 18px 38px rgba(95, 70, 45, 0.1);
    }

    .dashboard-control-panel {
        padding: 22px 24px 24px;
        margin-bottom: 18px;
    }

    .dashboard-empty-state {
        display: flex;
        gap: 18px;
        align-items: center;
        padding: 24px;
        margin: 18px 0 8px;
    }

    .page-hero {
        display: block;
        padding: 30px 34px;
        margin-bottom: 20px;
        border-radius: 8px;
        background:
            radial-gradient(circle at 92% 18%, rgba(124, 148, 128, 0.2), transparent 18%),
            linear-gradient(135deg, #FFFDF8 0%, #F4E7D8 100%);
        border: 1px solid rgba(170, 132, 92, 0.22);
        box-shadow: 0 18px 38px rgba(95, 70, 45, 0.12);
    }

    .page-kicker {
        display: inline-flex;
        width: fit-content;
        padding: 6px 12px;
        border-radius: 999px;
        background: #1F293D;
        color: #FDE68A !important;
        -webkit-text-fill-color: #FDE68A !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 16px;
    }

    .main .block-container .page-hero h1 {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-size: 36px !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
        line-height: 1.12 !important;
        margin: 0 0 10px !important;
    }

    .main .block-container .page-hero p {
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        line-height: 1.6 !important;
        margin: 0 !important;
    }

    .hero-mini-stack {
        display: grid;
        gap: 10px;
    }

    .hero-mini-stack div {
        padding: 16px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid rgba(170, 132, 92, 0.18);
        box-shadow: 0 10px 20px rgba(95, 70, 45, 0.08);
    }

    .main .block-container .hero-mini-stack strong {
        display: block;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-size: 22px !important;
        font-weight: 900 !important;
        line-height: 1.1 !important;
    }

    .main .block-container .hero-mini-stack span {
        display: block;
        margin-top: 6px;
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .surface-card {
        border-radius: 8px;
        padding: 24px;
        background: linear-gradient(145deg, #FFFDF8 0%, #F4E7D8 100%);
        border: 1px solid rgba(170, 132, 92, 0.22);
        box-shadow: 0 18px 38px rgba(95, 70, 45, 0.1);
    }

    .api-connect-card,
    .api-info-card,
    .settings-card {
        min-height: 100%;
    }

    .info-step {
        display: grid;
        grid-template-columns: 32px 1fr;
        column-gap: 12px;
        row-gap: 2px;
        align-items: center;
        padding: 13px 0;
        border-bottom: 1px solid rgba(170, 132, 92, 0.18);
    }

    .info-step:last-child {
        border-bottom: 0;
    }

    .info-step span {
        grid-row: span 2;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #1F293D;
        color: #FDE68A !important;
        -webkit-text-fill-color: #FDE68A !important;
        font-weight: 900 !important;
    }

    .main .block-container .info-step strong {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-size: 14px !important;
        font-weight: 900 !important;
        line-height: 1.2 !important;
    }

    .main .block-container .info-step small {
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        line-height: 1.35 !important;
    }

    .profile-management-card {
        display: flex;
        align-items: center;
        gap: 18px;
        padding: 22px;
        border-radius: 8px;
        background:
            radial-gradient(circle at 88% 16%, rgba(184, 137, 91, 0.18), transparent 24%),
            linear-gradient(135deg, rgba(255, 253, 248, 0.86), rgba(244, 231, 216, 0.92));
        border: 1px solid rgba(170, 132, 92, 0.22);
        box-shadow: 0 16px 28px rgba(95, 70, 45, 0.1);
    }

    .profile-avatar-large {
        width: 82px;
        height: 82px;
        min-width: 82px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #F59E0B, #D97706);
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        box-shadow: 0 18px 34px rgba(184, 137, 91, 0.24);
    }

    .profile-summary {
        min-width: 0;
    }

    .profile-eyebrow {
        color: #6E4D32 !important;
        -webkit-text-fill-color: #6E4D32 !important;
        font-size: 12px !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .main .block-container .profile-summary h3 {
        margin: 4px 0 10px !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
    }

    .profile-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .main .block-container .profile-meta-row span {
        padding: 7px 10px;
        border-radius: 999px;
        background: rgba(31, 41, 61, 0.08);
        border: 1px solid rgba(31, 41, 61, 0.08);
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-size: 12px !important;
        font-weight: 800 !important;
    }

    .main .block-container .settings-card h3,
    .main .block-container .settings-card h4,
    .main .block-container .settings-card p,
    .main .block-container .settings-card span:not(.feature-icon),
    .main .block-container .settings-card label,
    .main .block-container .settings-card [data-testid="stMarkdownContainer"],
    .main .block-container .settings-card [data-testid="stMarkdownContainer"] * {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        opacity: 1 !important;
    }

    .main .block-container .settings-card .stTextInput > label,
    .main .block-container .settings-card .stTextInput label,
    .main .block-container .settings-card .stTextArea > label,
    .main .block-container .settings-card .stSelectbox > label {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-weight: 800 !important;
    }

    .main .block-container .settings-card input,
    .main .block-container .settings-card textarea,
    .main .block-container .settings-card .stTextInput input {
        background: #FFFFFF !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        border-color: rgba(170, 132, 92, 0.3) !important;
    }

    .main .block-container .settings-card div[data-testid="stAlert"] {
        background: #FFF7ED !important;
        border: 1px solid rgba(184, 137, 91, 0.24) !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
    }

    .main .block-container .settings-card div[data-testid="stAlert"] *,
    .main .block-container .settings-card div[data-testid="stAlert"] p {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
    }

    .empty-icon {
        width: 64px;
        height: 64px;
        min-width: 64px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #1F293D;
        color: #FDE68A !important;
        -webkit-text-fill-color: #FDE68A !important;
        font-weight: 900 !important;
        letter-spacing: 0.04em;
        box-shadow: 0 14px 26px rgba(31, 41, 61, 0.18);
    }

    .main .block-container .dashboard-empty-state h3 {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        font-size: 20px !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
        margin: 0 0 8px !important;
    }

    .main .block-container .dashboard-empty-state p {
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        line-height: 1.55 !important;
        margin: 0 0 14px !important;
    }

    .empty-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .main .block-container .empty-steps span {
        padding: 7px 10px;
        border-radius: 999px;
        background: rgba(184, 137, 91, 0.12);
        color: #6E4D32 !important;
        -webkit-text-fill-color: #6E4D32 !important;
        font-size: 12px !important;
        font-weight: 800 !important;
    }

    .subscription-header {
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 0;
        background:
            radial-gradient(circle at 92% 18%, rgba(124, 148, 128, 0.24), transparent 16%),
            linear-gradient(135deg, #FFFDF8 0%, #F4E7D8 100%);
        border: 1px solid rgba(245, 158, 11, 0.22);
        border-radius: 8px;
        padding: 30px 34px;
        margin-bottom: 18px;
        box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
    }

    .subscription-header::after {
        content: "";
        position: absolute;
        right: 28px;
        top: 22px;
        width: 72px;
        height: 72px;
        border-radius: 24px;
        background: linear-gradient(135deg, #F59E0B, #14B8A6);
        opacity: 0.18;
        transform: rotate(12deg);
    }

    .subscription-kicker {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        padding: 6px 12px;
        border-radius: 999px;
        background: #1F293D;
        color: #FDE68A !important;
        -webkit-text-fill-color: #FDE68A !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 18px;
    }

    .main .block-container .subscription-hero {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 38px !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
        line-height: 1.15 !important;
        margin: 0 0 0.55rem !important;
    }

    .subscription-subtitle {
        max-width: 680px;
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        line-height: 1.55 !important;
        margin: 0 !important;
    }

    .subscription-hero-stats {
        display: grid;
        grid-template-columns: repeat(3, minmax(78px, 1fr));
        gap: 10px;
        min-width: 290px;
    }

    .subscription-hero-stats div {
        min-height: 82px;
        border-radius: 8px;
        padding: 14px 12px;
        background: rgba(255, 255, 255, 0.58);
        border: 1px solid rgba(170, 132, 92, 0.18);
        text-align: center;
        box-shadow: 0 10px 20px rgba(95, 70, 45, 0.08);
    }

    .main .block-container .subscription-hero-stats strong {
        display: block;
        color: #1F293D !important;
        -webkit-text-fill-color: #1F293D !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 22px !important;
        font-weight: 900 !important;
        line-height: 1.1 !important;
    }

    .main .block-container .subscription-hero-stats span {
        display: block;
        margin-top: 6px;
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        font-size: 11px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .subscription-card {
        background: linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid rgba(245, 158, 11, 0.38);
        border-top: 6px solid #F59E0B;
        border-radius: 8px;
        padding: 26px 30px 28px;
        min-height: 430px;
        text-align: left;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.14);
    }

    .subscription-card-basic {
        background: linear-gradient(145deg, #FFFFFF 0%, #FFF7ED 100%);
    }

    .subscription-card-premium {
        background: radial-gradient(circle at top right, rgba(20, 184, 166, 0.16), transparent 34%),
                    linear-gradient(145deg, #FFFFFF 0%, #ECFEFF 100%);
        border-color: rgba(20, 184, 166, 0.42);
        border-top-color: #14B8A6;
        box-shadow: 0 18px 36px rgba(20, 184, 166, 0.14);
    }

    .subscription-card-topline {
        width: fit-content;
        margin: 0 0 10px;
        padding: 6px 12px;
        border-radius: 999px;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background: #1F293D;
        border: 1px solid rgba(15, 23, 42, 0.12);
        font-size: 12px !important;
        font-weight: 800 !important;
    }

    .subscription-card-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 10px;
    }

    .subscription-plan-icon {
        width: 46px;
        height: 46px;
        min-width: 46px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: linear-gradient(135deg, #F59E0B, #FDE68A);
        color: #1F293D !important;
        -webkit-text-fill-color: #1F293D !important;
        font-weight: 900 !important;
        box-shadow: 0 12px 24px rgba(184, 137, 91, 0.22);
    }

    .subscription-plan-icon.premium {
        background: linear-gradient(135deg, #7C9480, #DDE7CF);
    }

    .main .block-container .subscription-plan {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        letter-spacing: 0.1em !important;
        margin: 0 !important;
    }

    .main .block-container .subscription-price {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 40px !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
        margin-top: 18px !important;
    }

    .subscription-price span {
        color: #D97706 !important;
        -webkit-text-fill-color: #D97706 !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        margin-left: 4px;
    }

    .subscription-card-copy {
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        line-height: 1.5 !important;
        margin: 12px 0 0 !important;
    }

    .subscription-card hr {
        border: 0;
        border-top: 1px solid rgba(15, 23, 42, 0.12);
        margin: 24px 0;
        width: 100%;
    }

    .subscription-features {
        text-align: left;
        list-style-type: none;
        padding: 0;
        margin: 0;
        max-width: none;
        display: grid;
        gap: 10px;
    }

    .main .block-container .subscription-features li {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        line-height: 1.35 !important;
        background: rgba(15, 23, 42, 0.04);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 8px;
        padding: 9px 11px;
    }

    .main .block-container .subscription-card .subscription-features li span:not(.feature-icon),
    .main .block-container .subscription-card .subscription-price,
    .main .block-container .subscription-card .subscription-plan {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
    }

    .feature-icon {
        width: 22px;
        height: 22px;
        min-width: 22px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-weight: 900 !important;
        line-height: 1 !important;
    }

    .feature-icon.good {
        background: #86EFAC;
    }

    .feature-icon.bad {
        background: #FDA4AF;
    }

    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    div[data-testid="stVerticalBlock"] > div {
        gap: 0.85rem !important;
    }

    /* Fix corrupted selectors/properties to ensure theme is applied */
    section[data-testid="stForm"], div[data-testid="stForm"] {
        border: 1px solid rgba(170, 132, 92, 0.28) !important;
        border-radius: 8px !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        background: #FFFDF8 !important;
        padding: 24px !important;
    }

    div[data-testid="stExpander"] > div,
    div[data-testid="stTab"] {
        background-color: #121824 !important;
        color: #FFFFFF !important;
    }

    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stNumberInput > label,
    .stDateInput > label {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        font-weight: 900 !important;
    }

    .stButton > button {
        border-radius: 12px !important;
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid #1E293B !important;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.22) !important;
        min-height: 50px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        text-transform: none !important;
        letter-spacing: 0.02em !important;
    }

    .stButton > button:hover {
        background-color: #F59E0B !important;
        border-color: #F59E0B !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .stDownloadButton > button {
        border-radius: 10px !important;
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid #1E293B !important;
    }

    .stDownloadButton > button:hover {
        background-color: #F59E0B !important;
        border-color: #F59E0B !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .stButton > button:active,
    .stFormSubmitButton > button:active,
    .stDownloadButton > button:active {
        background-color: #D97706 !important;
        border-color: #D97706 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    div[data-testid="stMetric"] {
        padding: 15px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(245, 158, 11, 0.22) !important;
        box-shadow: 0 8px 18px rgba(245, 158, 11, 0.12) !important;
        background-color: #1F293D !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stMetric"] * {
        color: #FFFFFF !important;
    }

    div[data-testid="stMetric"]:hover {
        border-color: #F59E0B !important;
    }

    .metrics-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .custom-metric {
        flex: 1;
        border-radius: 18px;
        padding: 22px 20px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
        color: #FFFFFF;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.25s ease;
    }

    .custom-metric:hover {
        transform: translateY(-3px);
    }

    .custom-metric.positive {
        background: linear-gradient(135deg, #16A34A 0%, #14532D 100%);
        color: #FFFFFF;
    }

    .custom-metric.negative {
        background: linear-gradient(135deg, #DC2626 0%, #7F1D1D 100%);
    }

    .custom-metric.neutral {
        background: linear-gradient(135deg, #F97316 0%, #9A3412 100%);
        color: #FFFFFF;
    }

    .custom-metric .metric-title {
        font-size: 14px;
        font-weight: 600;
        opacity: 0.95;
        margin-bottom: 10px;
    }

    .custom-metric .metric-value {
        font-size: 32px;
        font-weight: 800;
        line-height: 1.1;
    }

    .stDataFrame > div,
    .stDataFrame th,
    .stDataFrame td,
    table {
        color: #FFFFFF !important;
        border-color: rgba(245, 158, 11, 0.24) !important;
    }

    .stDataFrame th,
    .stDataFrame td {
        background-color: #1F293D !important;
    }

    .stTable {
        background-color: #1F293D !important;
        color: #FFFFFF !important;
    }

    .stTabs [role="tab"] {
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
    }

    .stTabs [role="tab"][aria-selected="true"] {
        background-color: #F97316 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .stTabs [role="tab"] p,
    .stTabs [role="tab"] span {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
        font-weight: 800 !important;
    }

    .stAlert {
        border-radius: 16px !important;
        background-color: #FFFBEB !important;
        border: 1px solid rgba(217, 119, 6, 0.34) !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }

    /* Main workspace theme only. Sidebar navigation and auth-specific styles are left untouched. */
    .stApp,
    section[data-testid="stAppViewContainer"],
    .main,
    .main .block-container {
        background: #F6EFE7 !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
    }

    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3,
    .main .block-container h4,
    .main .block-container h5,
    .main .block-container h6,
    .main .block-container p,
    .main .block-container li,
    .main .block-container label,
    .main .block-container span:not(.feature-icon),
    .main .block-container [data-testid="stMarkdownContainer"],
    .main .block-container [data-testid="stMarkdownContainer"] * {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        opacity: 1 !important;
    }

    .main .block-container .text-secondary,
    .main .block-container .micro-text,
    .main .block-container .section-heading,
    .main .block-container small,
    .main .block-container [data-testid="stWidgetLabel"] * {
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
    }

    .main .block-container section[data-testid="stForm"],
    .main .block-container div[data-testid="stForm"],
    .main .block-container div[data-testid="stAlert"],
    .main .block-container div[data-testid="stExpander"] > div,
    .main .block-container div[data-testid="stMetric"],
    .main .block-container div[data-testid="stFileUploader"],
    .main .block-container div[data-testid="stStatusWidget"],
    .main .block-container div[data-testid="stTabs"] [role="tabpanel"],
    .subscription-header,
    .subscription-card {
        background: linear-gradient(145deg, #FFFDF8 0%, #F4E7D8 100%) !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        border: 1px solid rgba(170, 132, 92, 0.24) !important;
        box-shadow: 0 18px 38px rgba(95, 70, 45, 0.12) !important;
    }

    .main .block-container div[data-testid="column"],
    .main .block-container div[data-testid="stHorizontalBlock"] {
        background: transparent !important;
        box-shadow: none !important;
        border: 0 !important;
    }

    .subscription-card-premium {
        border-color: rgba(124, 148, 128, 0.36) !important;
        border-top-color: #7C9480 !important;
    }

    .subscription-card-basic {
        border-top-color: #B8895B !important;
    }

    .main .block-container .subscription-hero,
    .main .block-container .subscription-subtitle,
    .main .block-container .subscription-plan,
    .main .block-container .subscription-price,
    .main .block-container .subscription-price span,
    .main .block-container .subscription-card .subscription-features li span:not(.feature-icon) {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
    }

    .subscription-card-topline {
        background: #EFE0CE !important;
        border-color: rgba(170, 132, 92, 0.3) !important;
        color: #6E4D32 !important;
        -webkit-text-fill-color: #6E4D32 !important;
    }

    .main .block-container .subscription-price span {
        color: #9A6A3D !important;
        -webkit-text-fill-color: #9A6A3D !important;
    }

    .main .block-container .subscription-features li {
        background: rgba(255, 255, 255, 0.54) !important;
        border-color: rgba(170, 132, 92, 0.16) !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
    }

    .feature-icon,
    .feature-icon.good,
    .feature-icon.bad {
        -webkit-text-fill-color: #2F3440 !important;
        color: #2F3440 !important;
    }

    .main .block-container input,
    .main .block-container textarea,
    .main .block-container select,
    .main .block-container [contenteditable="true"],
    .main .block-container .stSelectbox div[data-baseweb="select"] > div {
        background-color: #F8FAFC !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        border-color: rgba(170, 132, 92, 0.3) !important;
    }

    .main .block-container .stSelectbox div[data-baseweb="select"] span {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
    }

    .main .block-container input[type="password"] {
        background-color: #F8FAFC !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
    }

    .main .block-container [data-testid="stForm"] {
        background: #FFFDF8 !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        border: 1px solid rgba(170, 132, 92, 0.24) !important;
        border-radius: 8px !important;
        box-shadow: 0 14px 28px rgba(95, 70, 45, 0.1) !important;
        padding: 22px 24px !important;
    }

    .main .block-container [data-testid="stForm"] *,
    .main .block-container [data-testid="stForm"] label,
    .main .block-container [data-testid="stForm"] p,
    .main .block-container [data-testid="stForm"] span,
    .main .block-container [data-testid="stForm"] div[data-testid="stWidgetLabel"],
    .main .block-container [data-testid="stForm"] div[data-testid="stWidgetLabel"] * {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        opacity: 1 !important;
    }

    .main .block-container [data-testid="stForm"] label,
    .main .block-container [data-testid="stForm"] div[data-testid="stWidgetLabel"] p {
        font-weight: 800 !important;
    }

    .main .block-container [data-testid="stForm"] [data-testid="stAlert"] {
        background: #FFF7ED !important;
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
        border: 1px solid rgba(184, 137, 91, 0.28) !important;
        border-radius: 8px !important;
    }

    .main .block-container [data-testid="stForm"] input,
    .main .block-container [data-testid="stForm"] textarea {
        background: #FFFFFF !important;
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        border: 1px solid rgba(170, 132, 92, 0.34) !important;
    }

    .main .block-container [data-testid="stForm"] .stFormSubmitButton > button,
    .main .block-container [data-testid="stForm"] .stFormSubmitButton > button * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .main .block-container .account-helper {
        margin: 0 0 14px !important;
        padding: 12px 14px !important;
        border-radius: 8px !important;
        background: #FFFBEB !important;
        border: 2px solid #D97706 !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        font-size: 14px !important;
        font-weight: 900 !important;
        line-height: 1.45 !important;
    }

    .main .block-container .account-field-label {
        margin: 0 0 6px !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        font-size: 14px !important;
        font-weight: 900 !important;
        line-height: 1.25 !important;
    }

    .main .block-container [data-testid="stForm"] .stTextInput > label,
    .main .block-container [data-testid="stForm"] .stTextInput label,
    .main .block-container [data-testid="stForm"] [data-testid="stWidgetLabel"],
    .main .block-container [data-testid="stForm"] [data-testid="stWidgetLabel"] * {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        font-weight: 900 !important;
        opacity: 1 !important;
    }

    .main .block-container .stTextInput,
    .main .block-container .stSelectbox,
    .main .block-container .stFileUploader,
    .main .block-container .stSlider,
    .main .block-container .stRadio,
    .main .block-container .stCheckbox {
        background: #FFFDF8 !important;
        border: 1px solid rgba(170, 132, 92, 0.2) !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }

    .main .block-container .stTextInput input,
    .main .block-container .stTextArea textarea {
        color: #2F3440 !important;
        -webkit-text-fill-color: #2F3440 !important;
    }

    .main .block-container input::placeholder,
    .main .block-container textarea::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 1 !important;
    }

    .stTabs [role="tab"] {
        background: #FFFDF8 !important;
        color: #6B6259 !important;
        -webkit-text-fill-color: #6B6259 !important;
        border: 1px solid rgba(170, 132, 92, 0.18) !important;
    }

    .stTabs [role="tab"][aria-selected="true"] {
        background: #B8895B !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .main .block-container .stAlert,
    .main .block-container div[data-testid="stAlert"],
    .main .block-container div[data-testid="stAlert"] > div,
    .main .block-container div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
        background: #FFFBEB !important;
        background-color: #FFFBEB !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        border-color: rgba(217, 119, 6, 0.38) !important;
    }

    .main .block-container .stAlert *,
    .main .block-container div[data-testid="stAlert"] *,
    .main .block-container div[data-testid="stAlert"] p,
    .main .block-container div[data-testid="stAlert"] span {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }

    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}

    .verdict-box {
        padding: 20px;
        border-radius: 14px;
        text-align: center;
        color: #FFFFFF;
        box-shadow: 0 18px 38px rgba(95, 70, 45, 0.12);
        margin-bottom: 20px;
        background-color: #FFFDF8;
        border: 1px solid rgba(170, 132, 92, 0.24);
    }
</style>
""", unsafe_allow_html=True)

    # --- NEW DYNAMIC THEME OVERRIDE (LIGHT MODE) ---
    is_dark = True 
    
    # Check if a user is logged in and what their preference is
    if 'user_info' in st.session_state and st.session_state.user_info:
        prefs = st.session_state.user_info.get('preferences', {})
        # Handle stringified JSON if it hasn't been parsed yet
        if isinstance(prefs, str):
            import json
            try: 
                prefs = json.loads(prefs)
            except: 
                prefs = {}
                
        is_dark = prefs.get('dark_mode', True)

    # Inject Light Mode Overrides if Dark Mode is toggled off
    if not is_dark:
        st.markdown("""
        <style>
            /* Force the main Streamlit app background to be light */
            .stApp {
                background-color: #F8FAFC !important;
                color: #0F172A !important;
            }
            
            /* Override your custom surface cards to be white with dark text */
            .surface-card, .profile-card, .subscription-card, .dashboard-hero, .auth-shell {
                background-color: #FFFFFF !important;
                color: #0F172A !important;
                border: 1px solid #E2E8F0 !important;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            }
            
            /* Make headings and text dark everywhere */
            h1, h2, h3, h4, p, span, label, li, small {
                color: #0F172A !important;
                -webkit-text-fill-color: #0F172A !important;
            }
            
            /* Update Sidebar background to be lighter */
            section[data-testid="stSidebar"] {
                background-color: #FFFFFF !important;
                background: #FFFFFF !important;
                border-right: 1px solid #E2E8F0 !important;
            }
            
            /* Sidebar text and active links */
            section[data-testid="stSidebar"] .nav-link {
                color: #475569 !important;
                -webkit-text-fill-color: #475569 !important;
            }

            section[data-testid="stSidebar"] .nav-link.active {
                background: linear-gradient(135deg, #FDE68A 0%, #F59E0B 100%) !important;
                color: #111827 !important;
            }
            
            /* Main background fixes */
            section[data-testid="stAppViewContainer"],
            .main .block-container {
                background-color: #F8FAFC !important;
                background: #F8FAFC !important;
            }
            
            /* Fix input fields for light mode */
            .stTextInput input, .stSelectbox div[data-baseweb="select"], textarea {
                background-color: #FFFFFF !important;
                color: #0F172A !important;
                -webkit-text-fill-color: #0F172A !important;
                border: 1px solid #CBD5E1 !important;
            }

            /* Fix metric cards for light mode */
            div[data-testid="stMetric"] {
                background-color: #FFFFFF !important;
                border: 1px solid #E2E8F0 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
            }
            div[data-testid="stMetric"] * {
                color: #0F172A !important;
                -webkit-text-fill-color: #0F172A !important;
            }
            
            /* Fix DataFrames/Tables */
            .stDataFrame th,
            .stDataFrame td,
            .stTable {
                background-color: #FFFFFF !important;
                color: #0F172A !important;
                border-color: #E2E8F0 !important;
            }
            
            /* Fix tabs in light mode */
            .stTabs [role="tab"] {
                background: #FFFFFF !important;
                border-color: #CBD5E1 !important;
            }
            
            /* Fix profile card inside light mode */
            .profile-card {
                background: #FFFFFF !important;
                border: 1px solid #E2E8F0 !important;
            }
            .profile-card .user-label {
                color: #64748B !important;
                -webkit-text-fill-color: #64748B !important;
            }
            .profile-card h4 {
                color: #0F172A !important;
                -webkit-text-fill-color: #0F172A !important;
            }
        </style>
        """, unsafe_allow_html=True)


def show_sidebar_header():
    """
    Renders a consistent, styled sidebar header
    """
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-mark">AI</div>
        <h2>AI Evaluator</h2>
        <p>Pro Dashboard v2.0</p>
    </div>
    """, unsafe_allow_html=True)

def show_footer():
    st.markdown("""
    <div style="
        position: fixed; 
        bottom: 10px; 
        right: 10px; 
        color: #FFFFFF; 
        font-size: 12px; 
        font-family: 'Poppins', sans-serif;
    ">
        Powered by VADER & FastAPI
    </div>
    """, unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---

def show_status_card(status, message, icon="ℹ️"):
    color_map = {"success": "#F59E0B", "warning": "#D97706", "error": "#D97706", "info": "#F59E0B"}
    color = color_map.get(status, "#F59E0B")
    st.markdown(f"""
    <div style="background-color: rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}; 
        border-left: 4px solid {color}; padding: 12px; border-radius: 6px; margin: 10px 0; color: #FFFFFF;">
        <strong>{icon} {status.title()}:</strong> {message}
    </div>
    """, unsafe_allow_html=True)

def apply_auth_only_css():
    """Auth page-only theme. Called only while logged out."""
    background = "#0B132B"  # Deep Midnight Blue
    card = "#1C2541"        # Slate Gray
    accent = "#6FFFE9"      # Mint Gold
    amber = "#FFB123"       # Rich Amber

    st.markdown(
        f"""
<style>
    section[data-testid="stAppViewContainer"],
    .main,
    .main .block-container {{
        background:
            radial-gradient(circle at 12% 18%, rgba(111, 255, 233, 0.2), transparent 24%),
            radial-gradient(circle at 42% 92%, rgba(255, 177, 35, 0.2), transparent 24%),
            linear-gradient(135deg, #08101F 0%, #101A35 48%, #061C24 100%) !important;
        color: #E8F1FF !important;
        max-width: 1180px !important;
    }}

    .main .block-container {{
        min-height: 100vh !important;
        padding: 5.5rem 4rem 3rem !important;
    }}

    header[data-testid="stHeader"],
    section[data-testid="stSidebar"] {{
        display: none !important;
    }}

    div[data-testid="stHorizontalBlock"] {{
        align-items: center !important;
    }}

    .auth-shell {{
        position: relative;
        width: 100%;
        max-width: 440px;
        margin: 0 auto 1.25rem;
        padding: 38px 34px 30px;
        background:
            radial-gradient(circle at 88% 10%, rgba(255, 177, 35, 0.28), transparent 26%),
            linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(221, 245, 241, 0.94));
        border: 1px solid rgba(111, 255, 233, 0.54) !important;
        border-radius: 8px;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.26), 0 0 0 1px rgba(255, 255, 255, 0.55) inset;
        overflow: hidden;
    }}

    .auth-shell::before {{
        content: "";
        position: absolute;
        inset: 0 0 auto;
        height: 5px;
        background: linear-gradient(90deg, {accent}, {amber});
    }}

    .auth-brand-mark {{
        width: 58px;
        height: 58px;
        margin: 0 auto 24px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: {background};
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
        background: linear-gradient(135deg, {accent}, {amber});
        box-shadow: 0 18px 36px rgba(111, 255, 233, 0.18);
    }}

    .auth-copy {{
        text-align: center;
    }}

    .auth-brand-chip {{
        width: fit-content;
        margin: 0 auto 18px !important;
        padding: 7px 12px;
        border-radius: 999px;
        background: #0B132B;
        color: {accent} !important;
        -webkit-text-fill-color: {accent} !important;
        font-size: 12px !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em !important;
        box-shadow: 0 12px 26px rgba(11, 19, 43, 0.18);
    }}

    .auth-title {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 38px !important;
        font-weight: 900 !important;
        color: #0B132B !important;
        -webkit-text-fill-color: #0B132B !important;
        margin-bottom: 10px !important;
        line-height: 1.05 !important;
        text-shadow: none !important;
    }}

    .auth-subtitle {{
        color: #006D77 !important;
        -webkit-text-fill-color: #006D77 !important;
        font-size: 16px !important;
        font-weight: 900 !important;
        line-height: 1.5 !important;
        margin: 0 auto 12px !important;
        max-width: 330px;
    }}

    .auth-description,
    .auth-note {{
        color: #1C2541 !important;
        -webkit-text-fill-color: #1C2541 !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        line-height: 1.65 !important;
        margin: 0 auto !important;
        max-width: 340px;
    }}

    .auth-trust-row {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        margin-top: 20px;
    }}

    .auth-trust-row span {{
        padding: 7px 10px;
        border-radius: 999px;
        background: rgba(11, 19, 43, 0.08);
        border: 1px solid rgba(11, 19, 43, 0.1);
        color: #0B132B !important;
        -webkit-text-fill-color: #0B132B !important;
        font-size: 11px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
    }}

    section[data-testid="stForm"],
    div[data-testid="stForm"] {{
        position: relative;
        max-width: 440px !important;
        margin: 0 auto !important;
        padding: 30px 34px 32px !important;
        border-radius: 8px !important;
        border: 1px solid rgba(111, 255, 233, 0.28) !important;
        background:
            radial-gradient(circle at 92% 4%, rgba(111, 255, 233, 0.18), transparent 24%),
            linear-gradient(180deg, rgba(28, 37, 65, 0.98), rgba(18, 27, 54, 0.98)) !important;
        box-shadow: 0 30px 80px rgba(0, 0, 0, 0.36), 0 0 0 1px rgba(255, 255, 255, 0.04) inset !important;
        overflow: hidden;
    }}

    section[data-testid="stForm"]::before,
    div[data-testid="stForm"]::before {{
        content: "";
        position: absolute;
        inset: 0 0 auto;
        height: 4px;
        background: linear-gradient(90deg, {accent}, {amber});
    }}

    .stTextInput > label,
    .stTextInput label {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 13px !important;
        font-weight: 800 !important;
        letter-spacing: 0 !important;
    }}

    .stTextInput input {{
        min-height: 52px !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.82) !important;
        background: #FFFDF8 !important;
        color: #0B132B !important;
        -webkit-text-fill-color: #0B132B !important;
        caret-color: {accent} !important;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.16) !important;
    }}

    .stTextInput input:focus {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 3px rgba(111, 255, 233, 0.24), 0 14px 28px rgba(0, 0, 0, 0.18) !important;
    }}

    .stFormSubmitButton > button {{
        min-height: 52px !important;
        border-radius: 8px !important;
        background: linear-gradient(135deg, {accent}, {amber}) !important;
        color: {background} !important;
        -webkit-text-fill-color: {background} !important;
        border: 1px solid rgba(255, 255, 255, 0.28) !important;
        box-shadow: 0 16px 34px rgba(111, 255, 233, 0.18), 0 12px 28px rgba(255, 177, 35, 0.14) !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
    }}

    .stButton > button {{
        min-height: 46px !important;
        border-radius: 8px !important;
        background: rgba(232, 241, 255, 0.94) !important;
        color: #0B132B !important;
        -webkit-text-fill-color: #0B132B !important;
        border: 1px solid rgba(111, 255, 233, 0.36) !important;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.18) !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
    }}

    .main .block-container,
    .main .block-container p,
    .main .block-container span,
    .main .block-container div,
    .main .block-container label,
    .main .block-container small,
    .main .block-container [data-testid="stMarkdownContainer"],
    .main .block-container [data-testid="stMarkdownContainer"] * {{
        color: #E8F1FF !important;
        -webkit-text-fill-color: #E8F1FF !important;
        opacity: 1 !important;
    }}

    .main .block-container .auth-title,
    .main .block-container .auth-title * {{
        color: #0B132B !important;
        -webkit-text-fill-color: #0B132B !important;
    }}

    .main .block-container .auth-subtitle,
    .main .block-container .auth-subtitle * {{
        color: #006D77 !important;
        -webkit-text-fill-color: #006D77 !important;
    }}

    .main .block-container .auth-brand-chip,
    .main .block-container .auth-brand-chip * {{
        color: {accent} !important;
        -webkit-text-fill-color: {accent} !important;
    }}

    .main .block-container .stTextInput > label,
    .main .block-container .stTextInput label {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    .main .block-container .auth-description,
    .main .block-container .auth-note,
    .main .block-container .auth-description *,
    .main .block-container .auth-note *,
    .main .block-container .auth-trust-row span,
    .main .block-container .auth-trust-row span * {{
        color: #1C2541 !important;
        -webkit-text-fill-color: #1C2541 !important;
    }}

    .main .block-container input,
    .main .block-container textarea {{
        color: #0B132B !important;
        -webkit-text-fill-color: #0B132B !important;
    }}

    .main .block-container .stFormSubmitButton > button,
    .main .block-container .stFormSubmitButton > button * {{
        color: {background} !important;
        -webkit-text-fill-color: {background} !important;
    }}

    .main .block-container .stButton > button,
    .main .block-container .stButton > button * {{
        color: #0B132B !important;
        -webkit-text-fill-color: #0B132B !important;
    }}

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {{
        filter: brightness(1.06) !important;
        transform: translateY(-1px);
    }}

    .auth-visual {{
        position: relative;
        min-height: 520px;
        border-radius: 8px;
        background:
            radial-gradient(circle at 78% 16%, rgba(111, 255, 233, 0.16), transparent 24%),
            radial-gradient(circle at 18% 88%, rgba(255, 177, 35, 0.16), transparent 26%),
            linear-gradient(145deg, #101A35 0%, #071D2B 56%, #0B132B 100%);
        border: 1px solid rgba(111, 255, 233, 0.2);
        overflow: hidden;
        box-shadow: 0 28px 80px rgba(0, 0, 0, 0.3);
    }}

    .auth-visual::before {{
        content: "Product Review Intelligence";
        position: absolute;
        left: 34px;
        top: 26px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(232, 241, 255, 0.1);
        border: 1px solid rgba(111, 255, 233, 0.22);
        color: #E8F1FF;
        -webkit-text-fill-color: #E8F1FF;
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .auth-visual::after {{
        content: "92% positive sentiment";
        position: absolute;
        right: 34px;
        top: 26px;
        padding: 8px 12px;
        border-radius: 999px;
        background: linear-gradient(135deg, {accent}, {amber});
        color: #0B132B;
        -webkit-text-fill-color: #0B132B;
        font-size: 12px;
        font-weight: 900;
        box-shadow: 0 14px 28px rgba(111, 255, 233, 0.16);
    }}

    .auth-orbit {{
        position: absolute;
        border: 1px solid rgba(111, 255, 233, 0.24);
        border-radius: 50%;
    }}

    .auth-orbit-one {{
        width: 260px;
        height: 260px;
        top: 72px;
        right: 78px;
    }}

    .auth-orbit-two {{
        width: 180px;
        height: 180px;
        left: 70px;
        bottom: 66px;
        border-color: rgba(255, 177, 35, 0.28);
    }}

    .auth-device {{
        position: absolute;
        left: 50%;
        top: 50%;
        width: min(500px, 80%);
        height: 315px;
        transform: translate(-50%, -48%);
        border-radius: 8px;
        border: 1px solid rgba(232, 241, 255, 0.18);
        background:
            linear-gradient(180deg, rgba(232, 241, 255, 0.98), rgba(255, 253, 248, 0.96));
        box-shadow: 0 24px 65px rgba(0, 0, 0, 0.38);
        overflow: hidden;
    }}

    .auth-device-bar {{
        height: 52px;
        border-radius: 8px 8px 0 0;
        background: #FFFFFF;
        display: flex;
        gap: 8px;
        align-items: center;
        padding-left: 20px;
        border-bottom: 1px solid rgba(11, 19, 43, 0.1);
    }}

    .auth-device-bar::after {{
        content: "Review Dashboard";
        margin-left: 10px;
        color: #0B132B;
        -webkit-text-fill-color: #0B132B;
        font-size: 13px;
        font-weight: 900;
    }}

    .auth-device-bar span {{
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: {amber};
    }}

    .auth-device-bar span:nth-child(2) {{
        background: {accent};
    }}

    .auth-device-bar span:nth-child(3) {{
        background: #FFB123;
    }}

    .auth-login-card {{
        position: absolute;
        left: 28px;
        top: 78px;
        width: 280px;
        min-height: 200px;
        transform: none;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 20px 45px rgba(28, 37, 65, 0.25);
        display: flex;
        flex-direction: column;
        align-items: stretch;
        padding: 20px;
    }}

    .auth-avatar {{
        width: 70px;
        height: 70px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, {accent}, {amber});
        color: #0B132B;
        font-weight: 900;
        margin-bottom: 14px;
        border: 0;
        box-shadow: 0 14px 28px rgba(111, 255, 233, 0.24);
    }}

    .auth-avatar::before {{
        content: "4.8";
        font-size: 24px;
        line-height: 1;
    }}

    .auth-avatar::after {{
        content: "rating";
        position: absolute;
        left: 102px;
        top: 27px;
        color: #64748B;
        -webkit-text-fill-color: #64748B;
        font-size: 12px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}

    .auth-password-line {{
        width: 100%;
        height: 18px;
        border-radius: 999px;
        background:
            linear-gradient(90deg, #6FFFE9 0 76%, #E2E8F0 76% 100%);
        margin-bottom: 12px;
        position: relative;
    }}

    .auth-password-line:after {{
        content: "Positive reviews";
        position: absolute;
        inset: -24px auto auto 0;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        color: #0B132B;
        -webkit-text-fill-color: #0B132B;
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 0;
    }}

    .auth-password-line.short {{
        width: 100%;
        opacity: 1;
        background:
            linear-gradient(90deg, #FFB123 0 42%, #E2E8F0 42% 100%);
        margin-top: 20px;
    }}

    .auth-password-line.short:after {{
        content: "Needs attention";
    }}

    .auth-shield {{
        position: absolute;
        left: 54px;
        bottom: 54px;
        width: 184px;
        height: 96px;
        background: rgba(232, 241, 255, 0.94);
        border: 1px solid rgba(111, 255, 233, 0.28);
        border-radius: 8px;
        clip-path: none;
        filter: drop-shadow(0 20px 28px rgba(0, 0, 0, 0.28));
    }}

    .auth-shield::before {{
        content: "Top keyword";
        position: absolute;
        left: 14px;
        top: 12px;
        color: #64748B;
        -webkit-text-fill-color: #64748B;
        font-size: 11px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}

    .auth-shield::after {{
        content: "fast delivery";
        position: absolute;
        left: 14px;
        bottom: 16px;
        color: #0B132B;
        -webkit-text-fill-color: #0B132B;
        font-size: 20px;
        font-weight: 900;
    }}

    .auth-shield-lock {{
        position: absolute;
        right: 14px;
        top: 14px;
        left: auto;
        width: 42px;
        height: 42px;
        transform: none;
        border-radius: 8px;
        background: {accent};
        box-shadow: 0 0 24px rgba(111, 255, 233, 0.3);
    }}

    .auth-shield-lock:before {{
        content: "+";
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #0B132B;
        -webkit-text-fill-color: #0B132B;
        font-size: 24px;
        font-weight: 900;
        border: 0;
    }}

    .auth-shield-lock:after {{
        content: "";
        position: absolute;
        display: none;
    }}

    .auth-leaf-group {{
        position: absolute;
        right: 62px;
        bottom: 62px;
        width: 190px;
        height: 160px;
        padding: 18px;
        border-radius: 8px;
        background: rgba(232, 241, 255, 0.94);
        border: 1px solid rgba(111, 255, 233, 0.28);
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.25);
    }}

    .auth-leaf-group::before {{
        content: "Sentiment mix";
        position: absolute;
        left: 18px;
        top: 14px;
        color: #0B132B;
        -webkit-text-fill-color: #0B132B;
        font-size: 14px;
        font-weight: 900;
    }}

    .auth-leaf-group::after {{
        content: "Positive 92%  •  Neutral 6%";
        position: absolute;
        left: 18px;
        bottom: 16px;
        color: #64748B;
        -webkit-text-fill-color: #64748B;
        font-size: 11px;
        font-weight: 900;
    }}

    .auth-leaf-group span {{
        position: absolute;
        bottom: 48px;
        width: 34px;
        border-radius: 8px 8px 3px 3px;
        background: linear-gradient(180deg, {accent}, #006D77);
        transform-origin: bottom center;
    }}

    .auth-leaf-group span:nth-child(1) {{
        left: 32px;
        height: 62px;
        transform: none;
    }}

    .auth-leaf-group span:nth-child(2) {{
        left: 78px;
        height: 88px;
        background: linear-gradient(180deg, {amber}, #D97706);
    }}

    .auth-leaf-group span:nth-child(3) {{
        left: 124px;
        height: 42px;
        transform: none;
        background: linear-gradient(180deg, #94A3B8, #64748B);
    }}

    @media (max-width: 900px) {{
        .main .block-container {{
            padding: 2rem 1rem 3rem !important;
        }}

        .auth-visual {{
            min-height: 360px;
            margin-top: 1rem;
        }}

        .auth-shell,
        section[data-testid="stForm"],
        div[data-testid="stForm"] {{
            max-width: 100% !important;
        }}

        .auth-shield {{
            left: 44px;
            bottom: 70px;
            transform: scale(0.82);
        }}

        .auth-leaf-group {{
            right: 42px;
            bottom: 48px;
            transform: scale(0.76);
        }}
    }}
</style>
""",
        unsafe_allow_html=True,
    )


def show_loading_spinner(message="Processing..."):
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 20px; background-color: #1F293D; border-radius: 8px; border: 1px solid rgba(245, 158, 11, 0.22);">
        <span style="color: #F59E0B;">🔄 {message}</span>
    </div>
    """, unsafe_allow_html=True)
    