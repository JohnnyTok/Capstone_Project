import streamlit as st
import time
import styles as ui
import sqlite3

def update_username_in_db(old_username, new_username):
    """Updates the username in the database and checks for duplicates."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Security Check: Does the new username already exist?
        c.execute("SELECT username FROM users WHERE username = ?", (new_username,))
        if c.fetchone() is not None:
            conn.close()
            return False, "Username is already taken by another account."
            
        # If available, update the database
        c.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
        conn.commit()
        conn.close()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def show():
    """
    Renders the Settings Page UI
    """
    st.title("⚙️ System Configuration")
    st.markdown("Manage your application preferences and analysis parameters.")

    # Create Tabs for better organization
    tab_general, tab_analysis, tab_account = st.tabs(["General", "Analysis Model", "Account"])

    # --- TAB 1: GENERAL SETTINGS ---
    with tab_general:
        st.subheader("Application Preferences")
        
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Language", ["English (Default)", "Spanish", "French", "German"], help="System interface language")
            st.toggle("Enable Dark Mode", value=True, disabled=True, help="Dark mode is enforced by corporate policy.")
        with c2:
            st.selectbox("Time Zone", ["UTC", "Asia/Kuala_Lumpur", "US/Pacific", "Europe/London"])
            st.toggle("Desktop Notifications", value=False)

        st.markdown("### 🔔 Notification Settings")
        st.checkbox("Email me when analysis completes", value=True)
        st.checkbox("Alert me on negative sentiment spikes", value=True)

        if st.button("Save General Preferences", type="primary"):
            with st.spinner("Saving..."):
                time.sleep(0.8)
                st.toast("Preferences saved successfully!", icon="✅")

    # --- TAB 2: ANALYSIS MODEL ---
    with tab_analysis:
        st.subheader("AI Sensitivity Tuning")
        st.info("Adjusting these thresholds determines how the AI classifies reviews as Positive or Negative.")
        
        # Sliders for thresholds
        col_pos, col_neg = st.columns(2)
        with col_pos:
            st.slider("Positive Threshold", 0.1, 0.9, 0.2, 0.05, help="Scores above this are Positive")
        with col_neg:
            st.slider("Negative Threshold", -0.9, -0.1, -0.1, 0.05, help="Scores below this are Negative")
            
        st.markdown("### 🧪 Model Configuration")
        st.radio("Sentiment Engine", ["VADER (Rule-Based)", "RoBERTa (Deep Learning) [Premium]", "GPT-4o [Enterprise]"], index=0)
        
        st.divider()
        if st.button("Update Model Parameters", type="primary"):
            with st.spinner("Re-calibrating model..."):
                time.sleep(1)
                st.toast("Model parameters updated!", icon="🤖")

    # --- TAB 3: ACCOUNT ---
    with tab_account:
        st.subheader("Profile Management")
        
        if st.session_state.user_info:
            user = st.session_state.user_info
            current_username = user['username']
            
            # Profile Header
            c_av, c_det = st.columns([1, 4])
            with c_av:
                st.markdown(f"""
                <div style="width: 80px; height: 80px; border-radius: 50%; background-color: #5d5fef; display: flex; align-items: center; justify-content: center; font-size: 30px; font-weight: bold; color: white;">
                    {current_username[:2].upper()}
                </div>
                """, unsafe_allow_html=True)
            with c_det:
                st.markdown(f"### {current_username}")
                st.caption(f"Member since: {user.get('created_at', '2025-01-01')}")
                # Updated the default plan from 'free' to 'basic' to match your system rules!
                st.caption(f"Plan: **{user.get('plan', 'basic').upper()}**")

            st.divider()
            
            # --- NEW: UPDATE PROFILE FORM ---
            st.markdown("#### 👤 Update Username")
            with st.form("update_username_form"):
                st.info("Changing your username will update your login credentials.")
                new_username = st.text_input("New Username", value=current_username)
                
                submit_username = st.form_submit_button("Save Username", type="primary")
                
                if submit_username:
                    if len(new_username) < 3:
                        st.warning("⚠️ Username must be at least 3 characters long.")
                    elif new_username.lower() == current_username.lower():
                        st.info("⚠️ Please enter a different username.")
                    else:
                        success, message = update_username_in_db(current_username, new_username)
                        if success:
                            st.success(f"✅ Username successfully changed to '{new_username}'!")
                            
                            # Update the Streamlit memory so the whole app (and sidebar) changes instantly
                            st.session_state.user_info['username'] = new_username
                            
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(f"⚠️ {message}")

            st.markdown("---")
            
            # Change Password Form
            st.markdown("#### 🔐 Security")
            with st.form("change_pass"):
                c_p1, c_p2 = st.columns(2)
                with c_p1: st.text_input("New Password", type="password")
                with c_p2: st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Update Password"):
                    st.toast("Password updated successfully", icon="🔒")

            st.markdown("---")
            
            # Danger Zone
            st.markdown("#### 🚨 Danger Zone")
            if st.button("Delete Account", type="secondary"):
                st.error("Please contact support to delete your account.")
