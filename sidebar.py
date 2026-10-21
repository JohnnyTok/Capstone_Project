import streamlit as st
from streamlit_option_menu import option_menu
import styles as ui
import logging
from html import escape
from i18n import _  # Added translation import

# Keep in sync with ADMIN_USERS in app.py
ADMIN_USERS = {"admin", "johnny"}

# Setup logger
logger = logging.getLogger("app")

def show_sidebar():
    """
    Renders the sidebar and returns the selected menu option (Internal Key).
    """
    with st.sidebar:
        ui.show_sidebar_header()
        
        # 2. Enhanced Profile Card
        if st.session_state.user_info:
            plan = st.session_state.user_info.get('plan', 'free').upper()
            username = st.session_state.user_info.get('username', 'User')
            safe_username = escape(str(username))
            safe_initials = escape(str(username)[:2].upper())
            
            if plan == 'PREMIUM':
                avatar_bg = "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)"
                badge_class = "badge-premium"
            elif plan == 'BASIC':
                avatar_bg = "linear-gradient(135deg, #1E293B 0%, #F59E0B 100%)"
                badge_class = "badge-basic"
            else:
                avatar_bg = "#1E293B"
                badge_class = "badge-free"
            
            st.markdown(f"""
            <div class="profile-card">
                <div class="avatar" style="background: {avatar_bg};">
                    {safe_initials}
                </div>
                <div class="user-info">
                    <span class="user-label">{_('Signed in as')}</span>
                    <h4>{safe_username}</h4>
                    <p class="{badge_class}">{plan} {_('PLAN')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- NAVIGATION LOGIC ---
        # 1. Define English keys (Internal Logic)
        menu_options = ["Dashboard", "API Connect", "Subscription", "Settings"]
        menu_icons = ["speedometer2", "cloud-download", "credit-card", "gear"]

        # 2. Handle Admin Addition
        if st.session_state.user_info and st.session_state.user_info.get('username') in ADMIN_USERS:
            menu_options.append("Customer")
            menu_icons.append("shield-lock-fill")

        # 3. Handle Logout Addition
        menu_options.append("Logout")
        menu_icons.append("box-arrow-right")

        # 4. Create a mapping for translations dynamically AFTER all options are added
        menu_map = {opt: _(opt) for opt in menu_options}
        
        # 5. Create the list of labels to show in the UI
        menu_labels = [menu_map[opt] for opt in menu_options]
        
        # 6. Create the reverse lookup map
        label_to_key = {v: k for k, v in menu_map.items()}

        # 7. Navigation Menu
        selected_label = option_menu(
            menu_title=None,
            options=menu_labels, 
            icons=menu_icons, 
            menu_icon="cast", 
            key="sidebar_menu",
            default_index=0,
            styles={
                "container": {
                    "padding": "10px 8px!important",
                    "background": "linear-gradient(180deg, rgba(22,27,38,0.96), rgba(14,20,32,0.98))",
                    "border": "1px solid rgba(245,158,11,0.18)",
                    "border-radius": "8px",
                    "box-shadow": "0 18px 30px rgba(0,0,0,0.22)"
                },
                "icon": {"color": "#FDE68A", "font-size": "18px"}, 
                "nav-link": {
                    "font-size": "15px", 
                    "text-align": "left", 
                    "margin": "6px 0", 
                    "padding": "12px 14px",
                    "border-radius": "8px",
                    "color": "#E8F1FF",
                    "font-weight": "700",
                    "background-color": "transparent",
                    "--hover-color": "rgba(245, 158, 11, 0.14)"
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)", 
                    "color": "#111827",
                    "font-weight": "800",
                    "box-shadow": "0 10px 20px rgba(245, 158, 11, 0.28)"
                }
            }
        )

        # 8. Map the chosen label back to the English key safely using .get()
        selected = label_to_key.get(selected_label, selected_label)
        
        # Fallback in case of a stale state during language swap
        if selected not in menu_options:
            selected = "Dashboard"

        # 9. Handle Logout Logic
        if selected == "Logout":
            # ADDED 'show_welcome' TO THIS LIST!
            for key in ['logged_in', 'user_info', 'df', 'analysis_done',
                        'analysis_in_progress', 'last_uploaded_filename',
                        'data_source', 'auth_view', 'monitor', 'show_welcome']: 
                st.session_state.pop(key, None)
            logger.info("User logged out")
            st.rerun()
            
        return selected