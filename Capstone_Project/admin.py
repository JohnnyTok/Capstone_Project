import streamlit as st
import pandas as pd
import sqlite3
import time

def fetch_all_users():
    """Connects to the SQLite database and fetches user data."""
    try:
        conn = sqlite3.connect('users.db') 
        query = "SELECT username, email, plan FROM users" 
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def reset_user_password(target_username, new_password):
    """Updates the user's password in the database."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, target_username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Failed to update password: {e}")
        return False

def update_user_plan(target_username, new_plan):
    """Updates the user's subscription plan in the database."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET plan = ? WHERE username = ?", (new_plan.lower(), target_username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Failed to update plan: {e}")
        return False

def update_user_username(old_username, new_username):
    """Changes a user's username, ensuring the new name isn't already taken."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Security Check: Does the new username already exist?
        c.execute("SELECT username FROM users WHERE username = ?", (new_username,))
        if c.fetchone() is not None:
            conn.close()
            return False, "Username is already taken by another account."
            
        # If it's available, perform the update
        c.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
        conn.commit()
        conn.close()
        return True, "Success"
    except Exception as e:
        st.error(f"Failed to update username: {e}")
        return False, str(e)

def show():
    st.markdown("## 👑 Customer Management")
    st.markdown("Monitor registered users and manage account access.")

    df_users = fetch_all_users()

    if not df_users.empty:
        # --- 0. DYNAMIC STATUS/ROLE GENERATION ---
        # Automatically tag known admins. (Add any other admin usernames to this list if needed)
        admin_usernames = ['admin', 'johnny']
        df_users['status'] = df_users['username'].apply(
            lambda x: 'Admin' if str(x).lower() in admin_usernames else 'Customer'
        )

        # --- 1. METRICS DASHBOARD ---
        total_users = len(df_users)
        df_users['plan'] = df_users['plan'].str.lower()
        
        premium_users = len(df_users[df_users['plan'] == 'premium'])
        basic_users = len(df_users[df_users['plan'] == 'basic'])

        c1, c2, c3 = st.columns(3)
        c1.metric("👥 Total Users", total_users)
        c2.metric("💎 Premium", premium_users)
        c3.metric("📈 Basic", basic_users)

        st.markdown("---")
        
        # --- 2. FILTER & SEARCH CONTROLS ---
        st.markdown("### 📋 Customer Database")
        
        # Updated layout to 3 columns to fit the new Status filter
        col_plan, col_status, col_search = st.columns([1, 1, 2])
        with col_plan:
            plan_filter = st.selectbox(
                "Filter by Plan:",
                ["All Plans", "Premium", "Basic"]
            )
        with col_status:
            status_filter = st.selectbox(
                "Filter by Role:",
                ["All Roles", "Admin", "Customer"]
            )
        with col_search:
            search_query = st.text_input("🔍 Search by Username or Email:")
            
        # --- APPLY FILTERS ---
        filtered_df = df_users.copy()
        
        # Apply Plan Filter
        if plan_filter != "All Plans":
            filtered_df = filtered_df[filtered_df['plan'] == plan_filter.lower()]
            
        # Apply Status Filter
        if status_filter != "All Roles":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
        # Apply Search Filter
        if search_query:
            mask = filtered_df['username'].str.contains(search_query, case=False, na=False) | \
                   filtered_df['email'].str.contains(search_query, case=False, na=False)
            filtered_df = filtered_df[mask]

        filtered_df = filtered_df.reset_index(drop=True)
        filtered_df.insert(0, 'No.', range(1, len(filtered_df) + 1))

        st.markdown("*(Click on any row below to edit that user)*")
        
        # --- 3. INTERACTIVE DATAFRAME ---
        selection_event = st.dataframe(
            filtered_df, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",           
            selection_mode="single-row", 
            column_config={
                "No.": st.column_config.NumberColumn("No.", width="small"),
                "status": st.column_config.TextColumn("Role", width="small"), # Added the new Status column here
                "username": "Username",
                "email": "Email Address",
                "plan": st.column_config.TextColumn("Subscription Plan")
            }
        )

        # --- 4. DYNAMIC CUSTOMER EDIT PANEL ---
        if len(selection_event.selection.rows) > 0:
            selected_row_index = selection_event.selection.rows[0]
            target_user = filtered_df.iloc[selected_row_index]['username']
            current_plan = filtered_df.iloc[selected_row_index]['plan']
            
            st.markdown("---")
            st.markdown(f"### ⚙️ Manage User: `{target_user}`")
            
            tab1, tab2, tab3 = st.tabs(["👤 Edit Username", "🔄 Change Subscription Plan", "🔑 Reset Password"])
            
            # -- TAB 1: EDIT USERNAME --
            with tab1:
                with st.form("edit_username_form"):
                    st.info("Transferring this account? Change the username below.")
                    new_username = st.text_input("New Username", value=target_user)
                    
                    submit_username = st.form_submit_button("Update Username", type="primary")
                    
                    if submit_username:
                        if len(new_username) < 3:
                            st.warning("⚠️ Username must be at least 3 characters long.")
                        elif new_username.lower() == target_user.lower():
                            st.info("⚠️ Please enter a different username to update.")
                        else:
                            success, message = update_user_username(target_user, new_username)
                            if success:
                                st.success(f"✅ Username successfully changed from '{target_user}' to '{new_username}'!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(f"⚠️ {message}")

            # -- TAB 2: CHANGE PLAN --
            with tab2:
                with st.form("change_plan_form"):
                    st.info(f"Current Plan: **{str(current_plan).upper()}**")
                    
                    default_index = 0 if current_plan.lower() == 'basic' else 1
                    new_plan = st.selectbox("Select New Plan:", ["Basic", "Premium"], index=default_index)
                    
                    submit_plan = st.form_submit_button("Update Plan", type="primary")
                    
                    if submit_plan:
                        if new_plan.lower() == current_plan.lower():
                            st.warning(f"⚠️ {target_user} is already on the {new_plan} plan.")
                        else:
                            success = update_user_plan(target_user, new_plan)
                            if success:
                                st.success(f"✅ Plan successfully updated to {new_plan} for '{target_user}'!")
                                time.sleep(1.5)
                                st.rerun()

            # -- TAB 3: RESET PASSWORD --
            with tab3:
                with st.form("reset_password_form"):
                    new_pass = st.text_input("New Password", type="password")
                    confirm_pass = st.text_input("Confirm New Password", type="password")
                    
                    submit_reset = st.form_submit_button("Reset Password", type="primary")
                    
                    if submit_reset:
                        if len(new_pass) < 4:
                            st.warning("⚠️ Password must be at least 4 characters long.")
                        elif new_pass != confirm_pass:
                            st.error("⚠️ Passwords do not match!")
                        else:
                            success = reset_user_password(target_user, new_pass)
                            if success:
                                st.success(f"✅ Password successfully updated for '{target_user}'!")
                                time.sleep(1.5) 
                                st.rerun()
                        
    else:
        st.info("No customers found. The database might be empty.")
