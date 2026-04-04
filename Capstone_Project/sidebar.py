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
        
        # 2. Enhanced Profile Card
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

        # --- ADMIN LOGIC INTEGRATION ---
        # We define the default lists first
        menu_options = ["Dashboard", "API Connect", "Subscription", "Settings"]
        menu_icons = ["speedometer2", "cloud-download", "credit-card", "gear"]

        # Check if the logged-in user is the Admin, then add the Admin tab to the lists
        if st.session_state.user_info:
            current_user = st.session_state.user_info.get('username')
            if current_user == "admin" or current_user == "johnny":
                menu_options.append("Customer")
                menu_icons.append("shield-lock-fill")

        # Finally, add the Logout button at the very bottom
        menu_options.append("Logout")
        menu_icons.append("box-arrow-right")
        # -------------------------------

        # 3. Navigation Menu (Keeping YOUR nice custom styles!)
        selected = option_menu(
            menu_title=None,
            options=menu_options, 
            icons=menu_icons, 
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
