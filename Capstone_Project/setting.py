import streamlit as st
import time
import styles as ui

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
        
        # Read-only User Info
        if st.session_state.user_info:
            user = st.session_state.user_info
            
            # Profile Header
            c_av, c_det = st.columns([1, 4])
            with c_av:
                st.markdown(f"""
                <div style="width: 80px; height: 80px; border-radius: 50%; background-color: #5d5fef; display: flex; align-items: center; justify-content: center; font-size: 30px; font-weight: bold; color: white;">
                    {user['username'][:2].upper()}
                </div>
                """, unsafe_allow_html=True)
            with c_det:
                st.markdown(f"### {user['username']}")
                st.caption(f"Member since: {user.get('created_at', '2025-01-01')}")
                st.caption(f"Plan: **{user.get('plan', 'free').upper()}**")

            st.divider()
            
            # Change Password Form
            st.markdown("#### 🔐 Security")
            with st.form("change_pass"):
                c_p1, c_p2 = st.columns(2)
                with c_p1: st.text_input("New Password", type="password")
                with c_p2: st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Update Password"):
                    st.toast("Password updated successfully", icon="🔒")

            # Danger Zone
            st.markdown("#### 🚨 Danger Zone")
            if st.button("Delete Account", type="secondary"):
                st.error("Please contact support to delete your account.")