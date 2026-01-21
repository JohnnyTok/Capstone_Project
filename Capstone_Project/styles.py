import streamlit as st

def apply_custom_css():
    st.markdown("""
<style>
    /* --- 1. GLOBAL FONTS & THEME --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* --- 2. PREMIUM SIDEBAR STYLING --- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1C24 0%, #111217 100%);
        border-right: 1px solid #2b2d35;
    }

    /* --- 3. GLASSMORPHISM PROFILE CARD (Matches sidebar.py) --- */
    .profile-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 12px;
        margin-top: 10px;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .profile-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(93, 95, 239, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }

    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 16px;
        color: #111;
        box-shadow: 0 0 10px rgba(255,255,255,0.1);
    }

    .user-info h4 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #fff;
        letter-spacing: 0.5px;
    }

    .user-info p {
        margin: 0;
        font-size: 10px;
        font-weight: 700;
        opacity: 0.9;
    }

    /* --- 4. BADGE COLORS --- */
    .badge-premium { color: #FFD700; text-shadow: 0 0 10px rgba(255, 215, 0, 0.3); }
    .badge-basic { color: #00C853; }
    .badge-free { color: #A0A0A0; }

    /* --- 5. COMPACT LAYOUT SETTINGS --- */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.8rem !important;
    }

    /* --- 6. METRIC CARDS --- */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        padding: 15px !important;
        border-radius: 10px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #555;
        transform: translateY(-2px);
    }
    
    /* --- 7. BUTTON STYLING --- */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s;
    }
    
    /* --- 8. HIDE STREAMLIT BRANDING --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- 9. VERDICT BOX --- */
    .verdict-box {
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def show_sidebar_header():
    """
    Renders a consistent, styled sidebar header
    """
    st.markdown("""
    <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #2b2d35; margin-bottom: 20px;">
        <h2 style="
            margin: 0; 
            font-family: 'Inter', sans-serif; 
            font-weight: 800; 
            font-size: 24px;
            background: -webkit-linear-gradient(45deg, #5d5fef, #a259ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        ">
            AI Evaluator
        </h2>
        <p style="
            color: #888; 
            font-size: 11px; 
            margin: 5px 0 0 0; 
            font-weight: 600; 
            letter-spacing: 2px;
            text-transform: uppercase;
        ">
            Pro Dashboard v2.0
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_footer():
    st.markdown("""
    <div style="
        position: fixed; 
        bottom: 10px; 
        right: 10px; 
        color: #444; 
        font-size: 11px; 
        font-family: 'Inter', sans-serif;
    ">
        Powered by VADER & FastAPI
    </div>
    """, unsafe_allow_html=True)

# --- UTILITY FUNCTIONS (Kept from your original file) ---

def show_status_card(status, message, icon="ℹ️"):
    color_map = {"success": "#4CAF50", "warning": "#FF9800", "error": "#F44336", "info": "#2196F3"}
    color = color_map.get(status, "#2196F3")
    st.markdown(f"""
    <div style="background-color: rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}; 
        border-left: 4px solid {color}; padding: 12px; border-radius: 6px; margin: 10px 0; color: white;">
        <strong>{icon} {status.title()}:</strong> {message}
    </div>
    """, unsafe_allow_html=True)

def show_loading_spinner(message="Processing..."):
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 20px; background-color: #1e1e1e; border-radius: 8px;">
        <span style="color: white;">🔄 {message}</span>
    </div>
    """, unsafe_allow_html=True)