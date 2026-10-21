import streamlit as st
import time
import styles as ui
import db as database
import json
import logging
from i18n import _  # <--- Import our new UI Translator

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# DB HELPERS
# ──────────────────────────────────────────────

def update_username_in_db(old_username: str, new_username: str):
    """Update username, checking for duplicates via the centralised connection."""
    try:
        conn = database.get_conn()
        if conn.execute("SELECT 1 FROM users WHERE username = ?", (new_username,)).fetchone():
            return False, "Username is already taken by another account."
        conn.execute(
            "UPDATE users SET username = ? WHERE username = ?",
            (new_username, old_username)
        )
        conn.commit()
        return True, "Success"
    except Exception as e:
        return False, str(e)


def save_preferences(username: str, prefs: dict) -> bool:
    """Persist user preferences JSON to the database."""
    try:
        conn = database.get_conn()
        conn.execute(
            "UPDATE users SET preferences = ? WHERE username = ?",
            (json.dumps(prefs), username)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Could not save preferences: {e}")
        return False


def load_preferences(username: str) -> dict:
    """Load user preferences from the database."""
    try:
        conn = database.get_conn()
        row = conn.execute(
            "SELECT preferences FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row and row["preferences"]:
            return json.loads(row["preferences"])
    except Exception:
        pass
    return {}


# ──────────────────────────────────────────────
# MAIN PAGE
# ──────────────────────────────────────────────

def show():
    # Notice how we wrap the text strings inside _()
    st.markdown(f"""
    <div class="page-hero settings-hero">
        <div>
            <span class="page-kicker">{_('Workspace Control')}</span>
            <h4>{_('Workspace Settings')}</h4>
            <p1>{_('Personalize your preferences, tune sentiment thresholds, and manage account security.')}</p1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_general, tab_analysis, tab_account = st.tabs([
        f"⚙️ {_('General')}", 
        f"🤖 {_('Analysis Model')}", 
        f"👤 {_('Account')}"
    ])

# ── TAB 1: GENERAL ──────────────────────────
    with tab_general:
        st.markdown(f"#### {_('Application Preferences')}")

        username = st.session_state.user_info.get("username", "") if st.session_state.user_info else ""
        prefs = load_preferences(username)

        c1, c2 = st.columns(2)
        with c1:
            # 1. Define internal English keys
            lang_options = ["English", "Spanish", "French", "German", "Malay"]
            # 2. Get current saved language (default to English)
            current_lang = prefs.get("language", "English")
            
            # 3. Create a selectbox that shows translated names but returns English keys
            lang = st.selectbox(
                _("Language"),
                options=lang_options,
                format_func=lambda x: _(x), # Translates the display text ONLY
                index=lang_options.index(current_lang) if current_lang in lang_options else 0,
                help=_("System interface language")
            )
            
            is_dark = prefs.get("dark_mode", True)
            dark_mode = st.toggle(_("Dark Mode"), value=is_dark, help=_("Toggle between Dark and Light mode"))
            
        with c2:
            tz = st.selectbox(
                _("Time Zone"),
                ["UTC", "Asia/Kuala_Lumpur", "US/Pacific", "Europe/London"],
                index=["UTC", "Asia/Kuala_Lumpur", "US/Pacific", "Europe/London"].index(
                    prefs.get("timezone", "UTC")
                )
            )
            notif = st.toggle(_("Desktop Notifications"), value=prefs.get("notifications", False))

        st.markdown(f"#### 🔔 {_('Notification Preferences')}")
        email_on_complete = st.checkbox(
            _("Email me when analysis completes"),
            value=prefs.get("email_on_complete", True)
        )
        alert_on_spike = st.checkbox(
            _("Alert me on negative sentiment spikes (> 60%)"),
            value=prefs.get("alert_on_spike", True)
        )

        if st.button("💾 " + _("Save General Preferences"), type="primary"):
            new_prefs = {
                **prefs,
                "language": lang, # This safely saves the exact English string
                "timezone": tz,
                "notifications": notif,
                "email_on_complete": email_on_complete,
                "alert_on_spike": alert_on_spike,
                "dark_mode": dark_mode, 
            }
            if save_preferences(username, new_prefs):
                if st.session_state.user_info:
                    st.session_state.user_info["preferences"] = new_prefs
                st.success("✅ " + _("Preferences saved!"))
                time.sleep(0.5)
                st.rerun() 
            else:
                st.error("⚠️ " + _("Could not save preferences. Please try again."))
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 2: ANALYSIS MODEL ────────────────────
    with tab_analysis:
        # ─── 1. SECURE PERMANENT STORAGE ───
        # We use exact uppercase strings to match app.py and backend.py perfectly
        if "pos_threshold" not in st.session_state: 
            st.session_state["pos_threshold"] = 0.2
        if "neg_threshold" not in st.session_state: 
            st.session_state["neg_threshold"] = -0.1
        if "engine" not in st.session_state: 
            st.session_state["engine"] = "VADER"

        st.markdown(f"#### {_('AI Sensitivity Tuning')}")
        st.info(_("These thresholds determine how the AI classifies reviews as Positive or Negative."))

        col_pos, col_neg = st.columns(2)
        with col_pos:
            new_pos = st.slider(
                _("Positive Threshold"), 0.1, 0.9,
                float(st.session_state["pos_threshold"]),
                0.05, help=_("Scores above this are Positive")
            )
        with col_neg:
            new_neg = st.slider(
                _("Negative Threshold"), -0.9, -0.1,
                float(st.session_state["neg_threshold"]),
                0.05, help=_("Scores below this are Negative")
            )

        st.markdown(f"#### 🧪 {_('Sentiment Engine')}")
        plan = st.session_state.user_info.get("plan", "free") if st.session_state.user_info else "free"
        
        # ─── 2. MATCH THE GLOBAL ARCHITECTURE ───
        available_engines = ["VADER"]
        if plan == "premium":
            available_engines.append("RoBERTa")
            
        # UI Translation Mapping
        display_map = {
            "VADER": _("VADER (Rule-Based)"),
            "RoBERTa": _("RoBERTa (Deep Learning) [Premium]")
        }
        
        # Fallback security check
        current_saved_engine = st.session_state["engine"]
        if current_saved_engine not in available_engines:
            current_saved_engine = "VADER"
            
        # Calculate exactly which item should be highlighted on page load
        start_index = available_engines.index(current_saved_engine)
            
        # ─── 3. THE RADIO BUTTON WIDGET ───
        # No 'key=' argument here! This keeps Streamlit from wiping it out on page change.
        selected_engine_ui = st.radio(
            _("Select Sentiment Analysis Engine"), 
            options=available_engines,
            index=start_index,
            format_func=lambda x: display_map[x]
        )

        st.divider()
        
        # ─── 4. THE EXPLICIT SAVE BUTTON ───
        if st.button("💾 " + _("Save Model Parameters"), type="primary", key="final_save_model_parameters_btn"):
            st.session_state["pos_threshold"] = new_pos
            st.session_state["neg_threshold"] = new_neg
            st.session_state["engine"] = selected_engine_ui  # Captures the text directly to memory
            st.session_state.analysis_done = False
            
            st.success(f"✅ {_('Settings Saved! Engine:')} {display_map[selected_engine_ui]} | {_('Pos:')} {new_pos} | {_('Neg:')} {new_neg}")

    # ── TAB 3: ACCOUNT ──────────────────────────
    with tab_account:
        st.markdown(f"#### {_('Profile Management')}")

        if not st.session_state.user_info:
            st.warning(_("No user session found."))
            st.markdown("</div>", unsafe_allow_html=True)
            return

        user = st.session_state.user_info
        current_username = user["username"]

        st.markdown(f"""
        <div class="profile-management-card">
            <div class="profile-avatar-large">{current_username[:2].upper()}</div>
            <div class="profile-summary">
                <span class="profile-eyebrow">{_('Account profile')}</span>
                <h3 style="color:#F1F5F9">{current_username}</h3>
                <div class="profile-meta-row">
                    <span>📧 {user.get('email', '—')}</span>
                    <span>💳 {user.get('plan', 'free').upper()} {_('PLAN')}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── Update Username ──
        st.markdown(f"#### 👤 {_('Update Username')}")
        with st.form("update_username_form"):
            st.caption(_("Changing your username will update your login credentials immediately."))
            new_username = st.text_input(_("New Username"), value=current_username)
            if st.form_submit_button(_("Save Username"), type="primary"):
                if len(new_username) < 3:
                    st.warning("⚠️ " + _("Username must be at least 3 characters."))
                elif new_username.lower() == current_username.lower():
                    st.info(_("Please enter a different username."))
                else:
                    success, message = update_username_in_db(current_username, new_username)
                    if success:
                        st.success("✅ " + _("Username changed!"))
                        st.session_state.user_info["username"] = new_username
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error(f"⚠️ {message}")

        st.markdown("---")

        # ── Change Password ──
        st.markdown(f"#### 🔐 {_('Change Password')}")
        with st.form("change_pass"):
            old_pass = st.text_input(_("Current Password"), type="password")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                new_pass = st.text_input(_("New Password"), type="password")
            with c_p2:
                confirm_pass = st.text_input(_("Confirm New Password"), type="password")

            if st.form_submit_button(_("Update Password"), type="primary"):
                if not old_pass:
                    st.warning("⚠️ " + _("Please enter your current password."))
                elif len(new_pass) < 8:
                    st.warning("⚠️ " + _("New password must be at least 8 characters."))
                elif new_pass != confirm_pass:
                    st.error("⚠️ " + _("New passwords do not match."))
                else:
                    import auth as auth_module
                    auth_sys = auth_module.AuthSystem()
                    success, msg = auth_sys.update_password(current_username, old_pass, new_pass)
                    if success:
                        st.success("✅ " + _("Password updated successfully!"))
                    else:
                        st.error(f"⚠️ {msg}")

        st.markdown("---")

       # ── Danger Zone ──
        st.markdown(f"#### 🚨 {_('Danger Zone')}")
        
        @st.dialog(_("⚠️ Confirm Account Deletion"))
        def confirm_delete_dialog(username_to_delete):
            st.error(_("You are about to permanently delete your account. This action CANNOT be undone."))
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button(_("No, Cancel"), use_container_width=True):
                    st.rerun()
            with c2:
                if st.button(_("Yes, Delete"), type="primary", use_container_width=True):
                    conn = database.get_conn()
                    try:
                        # 1. Clean up user data
                        conn.execute("DELETE FROM analyses WHERE user_id = (SELECT id FROM users WHERE username = ?)", (username_to_delete,))
                        # 2. Delete user
                        conn.execute("DELETE FROM users WHERE username = ?", (username_to_delete,))
                        conn.commit()
                        
                        # 3. Clear session and force return to login
                        for key in ['logged_in', 'user_info', 'df', 'analysis_done', 'data_source', 'monitor', 'show_welcome']:
                            st.session_state.pop(key, None)
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Failed to delete account: {e}")
                        st.error(_("Failed to delete account."))
                    finally:
                        conn.close()

        with st.expander(_("Delete Account")):
            st.warning(_("Account deletion is permanent and cannot be undone."))
            if st.button(_("Delete My Account"), type="primary"):
                confirm_delete_dialog(current_username)