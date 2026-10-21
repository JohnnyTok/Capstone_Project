import sqlite3
import hashlib
import secrets
import re
import logging
import streamlit as st
import time
import styles as ui
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthSystem:
    """
    Advanced user authentication system with security features
    """
    def __init__(self, db_path: str = "users.db", session_timeout: int = 3600):
        self.db_path = db_path
        self.session_timeout = session_timeout
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_table()
        
        # Rate limiting configuration
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        
        # Password policy configuration
        self.min_password_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        self.require_special_chars = False
    
    def create_table(self) -> None:
        """Create the users table if it doesn't exist"""
        try:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    plan TEXT DEFAULT 'free',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    failed_login_attempts INTEGER DEFAULT 0,
                    last_failed_login TIMESTAMP,
                    session_token TEXT,
                    session_expires TIMESTAMP
                )
            ''')
            # Create indexes for performance
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_email ON users(email)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_session_token ON users(session_token)')
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating database table: {e}")
            raise
    
    def _generate_salt(self) -> str:
        return secrets.token_hex(32)
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password using PBKDF2-HMAC-SHA256 (stronger than plain SHA-256)."""
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations=260_000
        )
        return dk.hex()
    
    def _validate_password(self, password: str) -> Tuple[bool, str]:
        if len(password) < self.min_password_length:
            return False, f"Password must be at least {self.min_password_length} characters"
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if self.require_lowercase and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if self.require_numbers and not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        if self.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        return True, ""
    
    def _validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_account_locked(self, username: str) -> bool:
        cursor = self.conn.execute(
            "SELECT failed_login_attempts, last_failed_login FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        if result:
            failed_attempts, last_failed = result
            if failed_attempts >= self.max_login_attempts and last_failed:
                last_failed_time = datetime.fromisoformat(last_failed)
                lockout_end = last_failed_time + timedelta(seconds=self.lockout_duration)
                if datetime.now() < lockout_end:
                    return True
        return False

    def _increment_failed_attempts(self, username: str) -> None:
        self.conn.execute(
            "UPDATE users SET failed_login_attempts = failed_login_attempts + 1, last_failed_login = ? WHERE username = ?",
            (datetime.now().isoformat(), username)
        )
        self.conn.commit()

    def _reset_failed_attempts(self, username: str) -> None:
        self.conn.execute(
            "UPDATE users SET failed_login_attempts = 0, last_failed_login = NULL WHERE username = ?",
            (username,)
        )
        self.conn.commit()

    def register(self, email: str, username: str, password: str) -> Tuple[bool, str]:
        """Register a new user"""
        try:
            if not self._validate_email(email):
                return False, "Invalid email format"
            if len(username) < 3:
                return False, "Username must be at least 3 characters"
            is_valid, error_msg = self._validate_password(password)
            if not is_valid:
                return False, error_msg
            
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            
            # Default plan is 'free'
            self.conn.execute(
                "INSERT INTO users (email, username, password_hash, salt, plan) VALUES (?, ?, ?, ?, 'free')",
                (email, username, password_hash, salt)
            )
            self.conn.commit()
            logger.info(f"New user registered: {username}")
            return True, "Registration successful"
        except sqlite3.IntegrityError:
            return False, "Username or email already exists"
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, "Server error"

    def login(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Login a user and return their info (including plan)."""
        if self._is_account_locked(username):
            return False, "locked"

        cursor = self.conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        # Always hash to prevent timing attacks that reveal whether a username exists
        dummy_salt = "0" * 64
        candidate_hash = self._hash_password(password, user['salt'] if user else dummy_salt)

        if not user or candidate_hash != user['password_hash']:
            self._increment_failed_attempts(username)
            return False, None

        if not user['is_active']:
            return False, None

        self._reset_failed_attempts(username)

        # ✨ THE MAGIC FIX: Check if last_login is empty BEFORE we update it!
        is_first_time = (user['last_login'] is None)

        # Create session
        session_token = secrets.token_urlsafe(32)
        session_expires = datetime.now() + timedelta(seconds=self.session_timeout)

        self.conn.execute(
            "UPDATE users SET last_login = ?, session_token = ?, session_expires = ? WHERE username = ?",
            (datetime.now().isoformat(), session_token, session_expires.isoformat(), username)
        )
        self.conn.commit()

        # Return user info including PLAN and our accurate first_login flag
        return True, {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'plan': user['plan'],
            'created_at': user['created_at'],
            'first_login': is_first_time, # <--- Now strictly True for brand new accounts!
            'session_token': session_token,
        }

    def update_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change the password for an existing user.
        Verifies the old password before updating.
        """
        cursor = self.conn.execute(
            "SELECT password_hash, salt FROM users WHERE username = ?", (username,)
        )
        user = cursor.fetchone()
        if not user:
            return False, "User not found."

        old_hash = self._hash_password(old_password, user['salt'])
        if old_hash != user['password_hash']:
            return False, "Current password is incorrect."

        is_valid, error_msg = self._validate_password(new_password)
        if not is_valid:
            return False, error_msg

        new_salt = self._generate_salt()
        new_hash = self._hash_password(new_password, new_salt)
        self.conn.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
            (new_hash, new_salt, username)
        )
        self.conn.commit()
        logger.info(f"Password updated for user: {username}")
        return True, "Password updated successfully."

    def get_lockout_remaining(self, username: str) -> int:
        """Return seconds remaining in lockout, or 0 if not locked."""
        cursor = self.conn.execute(
            "SELECT failed_login_attempts, last_failed_login FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        if result:
            failed_attempts, last_failed = result
            if failed_attempts >= self.max_login_attempts and last_failed:
                last_failed_time = datetime.fromisoformat(last_failed)
                lockout_end = last_failed_time + timedelta(seconds=self.lockout_duration)
                remaining = (lockout_end - datetime.now()).total_seconds()
                return max(0, int(remaining))
        return 0

    def logout(self, username: str) -> bool:
        """Clear user session"""
        try:
            self.conn.execute(
                "UPDATE users SET session_token = NULL, session_expires = NULL WHERE username = ?",
                (username,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    def update_user_plan(self, username: str, new_plan: str) -> bool:
        """
        Update a user's subscription plan (free/basic/premium)
        """
        try:
            self.conn.execute(
                "UPDATE users SET plan = ? WHERE username = ?",
                (new_plan.lower(), username)
            )
            self.conn.commit()
            logger.info(f"User {username} upgraded to {new_plan}")
            return True
        except Exception as e:
            logger.error(f"Failed to update plan: {e}")
            return False

    def close_connection(self) -> None:
        if self.conn:
            self.conn.close()

# Initialize Global Instance
auth_system = AuthSystem()

# --- CONVENIENCE FUNCTIONS ---

def register_user(email: str, username: str, password: str):
    return auth_system.register(email, username, password)

def login_user(username: str, password: str):
    return auth_system.login(username, password)

def logout_user(username: str):
    return auth_system.logout(username)

def upgrade_user_plan(username: str, new_plan: str) -> bool:
    """Convenience function to update user plan"""
    return auth_system.update_user_plan(username, new_plan)

# ── NEW UI FUNCTION ──────────────────────────────────────────────────────────

def show_auth_screen():
    """
    Renders the Login and Registration screens and handles the authentication state.
    Stops the Streamlit app execution if the user is not logged in.
    """
    if not st.session_state.logged_in:
        ui.apply_auth_only_css()
        if 'auth_view' not in st.session_state:
            st.session_state.auth_view = 'login'

        left, right = st.columns([0.92, 1.08], gap="large")

        with left:
            if st.session_state.auth_view == 'login':
                st.markdown("""
                <div class="auth-shell">
                    <div class="auth-copy">
                        <div class="auth-brand-chip">AI Evaluator Pro</div>
                        <div class="auth-title">Welcome Back</div>
                        <div class="auth-subtitle">Secure sign-in for your AI product intelligence workspace.</div>
                        <div class="auth-trust-row">
                            <span>Sentiment AI</span><span>Secure access</span><span>Live insights</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.form("login_form"):
                    u = st.text_input("Username")
                    p = st.text_input("Password", type="password")
                    if st.form_submit_button("Sign In with AI-Auth", use_container_width=True):
                        # Use the globally initialized auth_system
                        success, user = auth_system.login(u, p)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user_info = user
                            st.rerun()
                        elif user == "locked":
                            remaining = auth_system.get_lockout_remaining(u)
                            mins = remaining // 60
                            secs = remaining % 60
                            st.error(f"🔒 Account locked. Try again in {mins}m {secs}s.")
                        else:
                            st.error("❌ Invalid username or password.")

                if st.button("Don't have an account? Register here", use_container_width=True):
                    st.session_state.auth_view = 'register'
                    st.rerun()

            elif st.session_state.auth_view == 'register':
                st.markdown("""
                <div class="auth-shell">
                    <div class="auth-copy">
                        <div class="auth-brand-chip">AI Evaluator Pro</div>
                        <div class="auth-title">Create Account</div>
                        <div class="auth-subtitle">Start analyzing reviews with your AI-powered dashboard.</div>
                        <div class="auth-trust-row">
                            <span>Fast setup</span><span>Review intelligence</span><span>Private workspace</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.form("reg_form"):
                    e = st.text_input("Work Email")
                    u = st.text_input("Username")
                    p = st.text_input("Password", type="password")
                    p2 = st.text_input("Retype Password", type="password")
                    if st.form_submit_button("Create Account", use_container_width=True):
                        if p != p2:
                            st.error("⚠️ Passwords do not match!")
                        elif not p:
                            st.warning("⚠️ Password cannot be empty.")
                        else:
                            # Use the globally initialized auth_system
                            s, m = auth_system.register(e, u, p)
                            if s:
                                st.success("🎉 Account created! Redirecting to login...")
                                logger.info(f"New user registered: {u}")
                                time.sleep(1.5)
                                st.session_state.auth_view = 'login'
                                st.rerun()
                            else:
                                st.error(m)

                if st.button("Already have an account? Log In", use_container_width=True):
                    st.session_state.auth_view = 'login'
                    st.rerun()

        with right:
            st.markdown("""
            <div class="auth-visual">
                <div class="auth-orbit auth-orbit-one"></div>
                <div class="auth-orbit auth-orbit-two"></div>
                <div class="auth-device">
                    <div class="auth-device-bar"><span></span><span></span><span></span></div>
                    <div class="auth-login-card">
                        <div class="auth-avatar"></div>
                        <div class="auth-password-line"></div>
                        <div class="auth-password-line short"></div>
                    </div>
                </div>
                <div class="auth-shield"><div class="auth-shield-lock"></div></div>
                <div class="auth-leaf-group"><span></span><span></span><span></span></div>
            </div>
            """, unsafe_allow_html=True)

        # Stop execution here if not logged in
        st.stop()

# --- CONVENIENCE FUNCTIONS ---

def register_user(email: str, username: str, password: str):
    return auth_system.register(email, username, password)

def login_user(username: str, password: str):
    return auth_system.login(username, password)

def logout_user(username: str):
    return auth_system.logout(username)

def upgrade_user_plan(username: str, new_plan: str) -> bool:
    """Convenience function to update user plan"""
    return auth_system.update_user_plan(username, new_plan)