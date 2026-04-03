import sqlite3
import hashlib
import secrets
import re
import logging
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
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
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
        """Login a user and return their info (including plan)"""
        if self._is_account_locked(username):
            return False, None
            
        cursor = self.conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            self._increment_failed_attempts(username)
            return False, None
            
        if self._hash_password(password, user['salt']) != user['password_hash']:
            self._increment_failed_attempts(username)
            return False, None
            
        if not user['is_active']:
            return False, None
            
        self._reset_failed_attempts(username)
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        session_expires = datetime.now() + timedelta(seconds=self.session_timeout)
        
        self.conn.execute(
            "UPDATE users SET last_login = ?, session_token = ?, session_expires = ? WHERE username = ?",
            (datetime.now().isoformat(), session_token, session_expires.isoformat(), username)
        )
        self.conn.commit()
        
        # Return user info including PLAN
        return True, {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'plan': user['plan'],  # Crucial for the subscription logic
            'session_token': session_token
        }

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
