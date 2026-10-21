import streamlit as st
import pandas as pd
import time
import hashlib
import secrets
import db as database
from i18n import _  # <--- Added Translation Engine

# Keep in sync with app.py and sidebar.py
ADMIN_USERS = {"admin", "johnny"}


def fetch_all_users():
    """Fetch all users using the centralised DB connection."""
    try:
        conn = database.get_conn()
        df = pd.read_sql_query(
            "SELECT id, username, email, plan, created_at, is_active FROM users",
            conn.connection if hasattr(conn, 'connection') else None
        )
        return df
    except Exception:
        # pd.read_sql_query needs a raw connection, use it directly
        try:
            import sqlite3
            raw = sqlite3.connect('users.db')
            df = pd.read_sql_query(
                "SELECT id, username, email, plan, created_at, is_active FROM users", raw
            )
            raw.close()
            return df
        except Exception as e:
            st.error(f"{_('Database error:')} {e}")
            return pd.DataFrame()


def reset_user_password(target_username: str, new_password: str) -> bool:
    """Reset a user's password with proper PBKDF2 hashing."""
    try:
        conn = database.get_conn()
        new_salt = secrets.token_hex(32)
        new_hash = hashlib.pbkdf2_hmac(
            'sha256', new_password.encode('utf-8'),
            new_salt.encode('utf-8'), iterations=260_000
        ).hex()
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
            (new_hash, new_salt, target_username)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"{_('Failed to update password:')} {e}")
        return False


def update_user_plan(target_username: str, new_plan: str) -> bool:
    """Update a user's subscription plan."""
    try:
        conn = database.get_conn()
        conn.execute(
            "UPDATE users SET plan = ? WHERE username = ?",
            (new_plan.lower(), target_username)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"{_('Failed to update plan:')} {e}")
        return False


def update_user_username(old_username: str, new_username: str):
    """Rename a user, checking for duplicates first."""
    try:
        conn = database.get_conn()
        existing = conn.execute(
            "SELECT username FROM users WHERE username = ?", (new_username,)
        ).fetchone()
        if existing:
            return False, _("Username is already taken by another account.")
        conn.execute(
            "UPDATE users SET username = ? WHERE username = ?",
            (new_username, old_username)
        )
        conn.commit()
        return True, _("Success")
    except Exception as e:
        return False, str(e)


def show():
    st.markdown(f"""
    <div style="margin-bottom:1.5rem">
        <span style="font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#94A3B8;font-weight:500">{_('Admin Panel')}</span>
        <h1 style="color:#F1F5F9;margin:0.2rem 0 0.3rem">{_('Customer Management')}</h1>
        <p style="color:#94A3B8;margin:0">{_('Monitor registered users and manage account access.')}</p>
    </div>
    """, unsafe_allow_html=True)

    df_users = fetch_all_users()

    if df_users.empty:
        st.info(_("No customers found. The database might be empty."))
        return

    # Tag admins
    df_users['role'] = df_users['username'].apply(
        lambda x: 'Admin' if str(x).lower() in ADMIN_USERS else 'Customer'
    )
    df_users['plan'] = df_users['plan'].str.lower().fillna('free')
    
    # Translate status tags directly since they are just for display
    df_users['status'] = df_users['is_active'].apply(
        lambda x: f"✅ {_('Active')}" if x else f"❌ {_('Inactive')}"
    )

    # --- Metrics ---
    total = len(df_users)
    premium = len(df_users[df_users['plan'] == 'premium'])
    basic = len(df_users[df_users['plan'] == 'basic'])
    free = len(df_users[df_users['plan'] == 'free'])

    def draw_metric_card(icon, title, value):
        return f"""
        <div style="background-color: #FFFFFF; padding: 16px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #E2E8F0;">
            <div style="font-size: 14px; font-weight: 600; color: #64748B; margin-bottom: 4px;">{icon} {title}</div>
            <div style="font-size: 28px; font-weight: 700; color: #0F172A;">{value}</div>
        </div>
        """

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(draw_metric_card("👥", _('Total Users'), total), unsafe_allow_html=True)
    with c2:
        st.markdown(draw_metric_card("💎", _('Premium'), premium), unsafe_allow_html=True)
    with c3:
        st.markdown(draw_metric_card("📈", _('Basic'), basic), unsafe_allow_html=True)
    with c4:
        st.markdown(draw_metric_card("🆓", _('Free'), free), unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown(f"### 📋 {_('Customer Database')}")

    col_plan, col_status, col_search = st.columns([1, 1, 2])
    with col_plan:
        plan_filter = st.selectbox(
            _("Filter by Plan:"), 
            ["All Plans", "Premium", "Basic", "Free"], 
            format_func=lambda x: _(x) # Translates options visually
        )
    with col_status:
        role_filter = st.selectbox(
            _("Filter by Role:"), 
            ["All Roles", "Admin", "Customer"], 
            format_func=lambda x: _(x) # Translates options visually
        )
    with col_search:
        search_query = st.text_input(_("🔍 Search by Username or Email:"))

    filtered = df_users.copy()
    if plan_filter != "All Plans":
        filtered = filtered[filtered['plan'] == plan_filter.lower()]
    if role_filter != "All Roles":
        filtered = filtered[filtered['role'] == role_filter]
    if search_query:
        mask = (
            filtered['username'].str.contains(search_query, case=False, na=False) |
            filtered['email'].str.contains(search_query, case=False, na=False)
        )
        filtered = filtered[mask]

    display = filtered[['username', 'email', 'plan', 'role', 'status', 'created_at']].reset_index(drop=True)
    display.insert(0, 'No.', range(1, len(display) + 1))

    st.caption(_("Click any row to manage that user."))
    selection_event = st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "No.": st.column_config.NumberColumn(_("No."), width="small"),
            "role": st.column_config.TextColumn(_("Role"), width="small"),
            "status": st.column_config.TextColumn(_("Status"), width="small"),
            "plan": st.column_config.TextColumn(_("Plan")),
            "username": _("Username"),
            "email": _("Email"),
            "created_at": st.column_config.TextColumn(_("Joined")),
        }
    )

    if not selection_event.selection.rows:
        return

    selected_row_index = selection_event.selection.rows[0]
    target_user = display.iloc[selected_row_index]['username']
    current_plan = display.iloc[selected_row_index]['plan']

    st.markdown("---")
    st.markdown(f"### ⚙️ {_('Manage User:')} `{target_user}`")

    tab1, tab2, tab3 = st.tabs([_("👤 Edit Username"), _("🔄 Change Plan"), _("🔑 Reset Password")])

    with tab1:
        with st.form("edit_username_form"):
            st.info(_("Change the username for this account."))
            new_username = st.text_input(_("New Username"), value=target_user)
            if st.form_submit_button(_("Update Username"), type="primary"):
                if len(new_username) < 3:
                    st.warning("⚠️ " + _("Username must be at least 3 characters."))
                elif new_username.lower() == target_user.lower():
                    st.info(_("Please enter a different username."))
                else:
                    success, msg = update_user_username(target_user, new_username)
                    if success:
                        st.success(f"✅ {_('Username changed to')} '{new_username}'")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")

    with tab2:
        with st.form("change_plan_form"):
            st.info(f"{_('Current Plan:')} **{current_plan.upper()}**")
            plan_options = ["free", "basic", "premium"]
            default_idx = plan_options.index(current_plan) if current_plan in plan_options else 0
            
            # Using format_func to translate visually but keep English logically
            new_plan = st.selectbox(
                _("Select New Plan:"), 
                ["Free", "Basic", "Premium"], 
                index=default_idx,
                format_func=lambda x: _(x)
            )
            
            if st.form_submit_button(_("Update Plan"), type="primary"):
                if new_plan.lower() == current_plan.lower():
                    st.warning(f"{target_user} {_('is already on the')} {new_plan} {_('plan.')}")
                else:
                    if update_user_plan(target_user, new_plan):
                        st.success(f"✅ {_('Plan updated to')} {new_plan} {_('for')} '{target_user}'")
                        time.sleep(1.5)
                        st.rerun()

    with tab3:
        with st.form("reset_password_form"):
            st.warning(_("This will immediately change the user's password."))
            new_pass = st.text_input(_("New Password"), type="password")
            confirm_pass = st.text_input(_("Confirm New Password"), type="password")
            if st.form_submit_button(_("Reset Password"), type="primary"):
                if len(new_pass) < 8:
                    st.warning("⚠️ " + _("Password must be at least 8 characters."))
                elif new_pass != confirm_pass:
                    st.error("⚠️ " + _("Passwords do not match."))
                else:
                    if reset_user_password(target_user, new_pass):
                        st.success(f"✅ {_('Password reset for')} '{target_user}'")
                        time.sleep(1.5)
                        st.rerun()