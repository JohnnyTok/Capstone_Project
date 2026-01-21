import streamlit as st
from streamlit_option_menu import option_menu
import styles as ui
import logging

# Setup logger
logger = logging.getLogger("app")

def show_sidebar():
    """
    Renders the sidebar and returns the selected menu option.
    """
    with st.sidebar:
        # 1. Header (Logo/Title)
        ui.show_sidebar_header()
        
        # 2. Enhanced Profile Card (MOVED TO TOP)
        if st.session_state.user_info:
            plan = st.session_state.user_info.get('plan', 'free').upper()
            username = st.session_state.user_info.get('username', 'User')
            
            # Dynamic Colors based on Plan
            if plan == 'PREMIUM':
                avatar_bg = "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)"
                badge_class = "badge-premium"
            elif plan == 'BASIC':
                avatar_bg = "linear-gradient(135deg, #00C853 0%, #69F0AE 100%)"
                badge_class = "badge-basic"
            else:
                avatar_bg = "#607D8B"
                badge_class = "badge-free"
            
            # Render Profile Card
            st.markdown(f"""
            <div class="profile-card" style="margin-bottom: 20px;">
                <div class="avatar" style="background: {avatar_bg};">
                    {username[:2].upper()}
                </div>
                <div class="user-info">
                    <h4>{username}</h4>
                    <p class="{badge_class}">{plan} PLAN</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 3. Navigation Menu
        # I've tweaked the styles here to blend better with the new dark gradient
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "API Connect", "Subscription", "Settings", "Logout"], 
            icons=["speedometer2", "cloud-download", "credit-card", "gear", "box-arrow-right"], 
            menu_icon="cast", 
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#a259ff", "font-size": "18px"}, 
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin": "8px", 
                    "border-radius": "10px",
                    "color": "#e0e0e0",
                    "--hover-color": "#262730"
                },
                "nav-link-selected": {
                    "background-color": "#5d5fef", 
                    "color": "white",
                    "font-weight": "600",
                    "box-shadow": "0 4px 15px rgba(93, 95, 239, 0.4)"
                },
            }
        )
        
        # 4. Handle Logout Logic
        if selected == "Logout":
            st.session_state.logged_in = False
            st.session_state.user_info = None
            logger.info("User logged out")
            st.rerun()
            
        return selected