"""
RealmsMUD Account System
========================
Manages player accounts with multi-character support.
"""

import os
import json
import hashlib
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

ACCOUNTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'lib', 'accounts')


class Account:
    """Represents a player account that can have multiple characters."""
    
    def __init__(self, account_name: str):
        self.account_name = account_name.lower()
        self.password_hash = ''
        self.created_at = datetime.now().isoformat()
        self.last_login = datetime.now().isoformat()
        self.characters: List[str] = []  # Character names
        self.settings = {
            'email': None,
            'max_chars': 8
        }
        self.shared = {
            'bank_gold': 0,
            'storage': []
        }
        self.reset_tokens = []  # list of {token, created_at}
        self.is_admin = False
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storage."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return self.password_hash == self.hash_password(password)
    
    def set_password(self, password: str):
        """Set a new password."""
        self.password_hash = self.hash_password(password)
    
    def add_character(self, char_name: str) -> bool:
        """Add a character to this account."""
        if len(self.characters) >= self.settings.get('max_chars', 8):
            return False
        if char_name not in self.characters:
            self.characters.append(char_name)
        return True
    
    def remove_character(self, char_name: str) -> bool:
        """Remove a character from this account."""
        if char_name in self.characters:
            self.characters.remove(char_name)
            return True
        return False
    
    def to_dict(self) -> dict:
        """Serialize account to dictionary."""
        return {
            'account_name': self.account_name,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'characters': self.characters,
            'settings': self.settings,
            'shared': self.shared,
            'reset_tokens': self.reset_tokens,
            'is_admin': self.is_admin
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Account':
        """Create account from dictionary."""
        account = cls(data.get('account_name', 'unknown'))
        account.password_hash = data.get('password_hash', '')
        account.created_at = data.get('created_at', datetime.now().isoformat())
        account.last_login = data.get('last_login', datetime.now().isoformat())
        account.characters = data.get('characters', [])
        account.settings = data.get('settings', {'email': None, 'max_chars': 8})
        account.shared = data.get('shared', {'bank_gold': 0, 'storage': []})
        account.reset_tokens = data.get('reset_tokens', [])
        account.is_admin = data.get('is_admin', False)
        return account
    
    def save(self):
        """Save account to file."""
        os.makedirs(ACCOUNTS_DIR, exist_ok=True)
        filepath = os.path.join(ACCOUNTS_DIR, f'{self.account_name}.json')
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, account_name: str) -> Optional['Account']:
        """Load account from file."""
        filepath = os.path.join(ACCOUNTS_DIR, f'{account_name.lower()}.json')
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception:
            return None
    
    @staticmethod
    def exists(account_name: str) -> bool:
        """Check if an account exists."""
        filepath = os.path.join(ACCOUNTS_DIR, f'{account_name.lower()}.json')
        return os.path.exists(filepath)


class AccountManager:
    """Manages account operations."""
    
    @staticmethod
    def create_account(account_name: str, password: str) -> Optional[Account]:
        """Create a new account."""
        if Account.exists(account_name):
            return None
        
        account = Account(account_name)
        account.set_password(password)
        account.save()
        return account
    
    @staticmethod
    def authenticate(account_name: str, password: str) -> Optional[Account]:
        """Authenticate and return account if valid."""
        account = Account.load(account_name)
        if account and account.check_password(password):
            account.last_login = datetime.now().isoformat()
            account.save()
            return account
        return None

    @staticmethod
    def set_email(account: Account, email: str) -> bool:
        """Set account email for password resets."""
        if not email or '@' not in email:
            return False
        account.settings['email'] = email
        account.save()
        return True

    @staticmethod
    def generate_reset_token(account: Account) -> str:
        """Generate and store a password reset token."""
        token = secrets.token_urlsafe(16)
        now = datetime.now().isoformat()
        # Prune old tokens
        from config import Config
        cutoff = datetime.now() - timedelta(hours=Config.PASSWORD_RESET_TTL_HOURS)
        account.reset_tokens = [t for t in account.reset_tokens if datetime.fromisoformat(t.get('created_at', now)) > cutoff]
        account.reset_tokens.append({'token': token, 'created_at': now})
        account.save()
        return token

    @staticmethod
    def send_reset_email(account: Account, token: str) -> bool:
        """Send reset email via SMTP. Returns True if sent."""
        from config import Config
        cfg = Config()
        
        if not cfg.SMTP_HOST or not cfg.SMTP_FROM:
            return False
        if not account.settings.get('email'):
            return False
        
        msg = EmailMessage()
        msg['Subject'] = 'RealmsMUD Password Reset'
        msg['From'] = cfg.SMTP_FROM
        msg['To'] = account.settings['email']
        msg.set_content(
            f"Hello {account.account_name},\n\n"
            f"Use this token to reset your password (valid {cfg.PASSWORD_RESET_TTL_HOURS} hours):\n\n"
            f"{token}\n\n"
            f"You can reset from the login screen by typing:\n"
            f"reset {token} <newpassword>\n\n"
            f"If you did not request this, you can ignore this email."
        )
        
        try:
            server = smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT)
            if cfg.SMTP_TLS:
                server.starttls()
            if cfg.SMTP_USER and cfg.SMTP_PASS:
                server.login(cfg.SMTP_USER, cfg.SMTP_PASS)
            server.send_message(msg)
            server.quit()
            return True
        except Exception:
            return False

    @staticmethod
    def reset_with_token(account_name: str, token: str, new_password: str) -> bool:
        """Reset password using a valid token."""
        account = Account.load(account_name)
        if not account:
            return False
        if len(new_password) < 4:
            return False
        # Validate token
        now = datetime.now()
        from config import Config
        cutoff = now - timedelta(hours=Config.PASSWORD_RESET_TTL_HOURS)
        valid = False
        for t in list(account.reset_tokens):
            try:
                created = datetime.fromisoformat(t.get('created_at'))
            except Exception:
                created = now
            if created < cutoff:
                account.reset_tokens.remove(t)
                continue
            if t.get('token') == token:
                valid = True
                account.reset_tokens.remove(t)
                break
        if not valid:
            account.save()
            return False
        account.set_password(new_password)
        account.save()
        return True

    @staticmethod
    def get_character_info(account: Account) -> List[dict]:
        """Get info about all characters on an account."""
        from player import Player
        """Get info about all characters on an account."""
        from player import Player
        
        char_info = []
        for char_name in account.characters:
            player = Player.load(char_name)
            if player:
                char_info.append({
                    'name': player.name,
                    'class': player.char_class,
                    'level': player.level,
                    'race': getattr(player, 'race', 'Human'),
                    'last_login': getattr(player, 'last_login', 'Unknown')
                })
            else:
                # Character file missing - still show in list
                char_info.append({
                    'name': char_name,
                    'class': '???',
                    'level': 0,
                    'race': '???',
                    'last_login': 'Unknown'
                })
        return char_info
    
    @staticmethod
    def link_character_to_account(player: 'Player', account: Account) -> bool:
        """Link an existing character to an account."""
        if player.name in account.characters:
            return True  # Already linked
        
        if not account.add_character(player.name):
            return False  # Account full
        
        # Update player file with account reference
        player.account_name = account.account_name
        player.save()
        account.save()
        return True
    
    @staticmethod
    def migrate_legacy_player(char_name: str, password: str) -> Optional[Account]:
        """Migrate a legacy player file to account system."""
        from player import Player
        
        # Load the player
        player = Player.load(char_name)
        if not player:
            return None
        
        # Check password against player file
        if not player.check_password(password):
            return None
        
        # Create account with same name as character
        account_name = char_name.lower()
        if Account.exists(account_name):
            # Account already exists - just link
            account = Account.load(account_name)
            if account and account.check_password(password):
                AccountManager.link_character_to_account(player, account)
                return account
            return None
        
        # Create new account
        account = Account(account_name)
        account.set_password(password)
        account.add_character(player.name)
        account.save()
        
        # Update player with account reference
        player.account_name = account_name
        player.save()
        
        return account
    
    @staticmethod
    def delete_character(account: Account, char_name: str) -> bool:
        """Delete a character from an account."""
        if char_name not in account.characters:
            return False
        
        # Remove from account
        account.remove_character(char_name)
        account.save()
        
        # Move player file to deleted folder (don't truly delete)
        players_dir = os.path.join(os.path.dirname(__file__), '..', 'lib', 'players')
        deleted_dir = os.path.join(os.path.dirname(__file__), '..', 'lib', 'deleted')
        os.makedirs(deleted_dir, exist_ok=True)
        
        old_path = os.path.join(players_dir, f'{char_name.lower()}.json')
        new_path = os.path.join(deleted_dir, f'{char_name.lower()}.json')
        
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
        
        return True
    
    @staticmethod
    def rename_character(account: Account, old_name: str, new_name: str) -> bool:
        """Rename a character."""
        from player import Player
        
        if old_name not in account.characters:
            return False
        
        # Check new name is available
        if Player.exists(new_name):
            return False
        
        # Load player
        player = Player.load(old_name)
        if not player:
            return False
        
        # Update player name
        player.name = new_name.capitalize()
        
        # Update account
        idx = account.characters.index(old_name)
        account.characters[idx] = new_name.capitalize()
        account.save()
        
        # Save with new name, delete old file
        players_dir = os.path.join(os.path.dirname(__file__), '..', 'lib', 'players')
        old_path = os.path.join(players_dir, f'{old_name.lower()}.json')
        
        player.save()  # Saves to new name
        
        if os.path.exists(old_path):
            os.remove(old_path)
        
        return True
