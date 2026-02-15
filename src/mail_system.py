"""
RealmsMUD Mail System
=====================
Allows players to send, read, and manage in-game mail.
Mail is stored in lib/mail/<playername>.json
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger('RealmsMUD.Mail')

MAIL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'mail')


def _ensure_dir():
    os.makedirs(MAIL_DIR, exist_ok=True)


def _mail_path(player_name: str) -> str:
    return os.path.join(MAIL_DIR, f"{player_name.lower()}.json")


class MailMessage:
    def __init__(self, sender: str, recipient: str, subject: str, body: str,
                 timestamp: str = None, read: bool = False, msg_id: int = 0):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.timestamp = timestamp or datetime.now().isoformat()
        self.read = read
        self.msg_id = msg_id

    def to_dict(self) -> Dict:
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'subject': self.subject,
            'body': self.body,
            'timestamp': self.timestamp,
            'read': self.read,
            'msg_id': self.msg_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MailMessage':
        return cls(**data)


class MailManager:
    @staticmethod
    def _load_mailbox(player_name: str) -> List[Dict]:
        _ensure_dir()
        path = _mail_path(player_name)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    @staticmethod
    def _save_mailbox(player_name: str, messages: List[Dict]):
        _ensure_dir()
        path = _mail_path(player_name)
        with open(path, 'w') as f:
            json.dump(messages, f, indent=2)

    @staticmethod
    def send_mail(sender: str, recipient: str, body: str) -> bool:
        messages = MailManager._load_mailbox(recipient)
        next_id = max((m.get('msg_id', 0) for m in messages), default=0) + 1
        msg = MailMessage(
            sender=sender,
            recipient=recipient,
            subject=f"Mail from {sender}",
            body=body,
            msg_id=next_id,
        )
        messages.append(msg.to_dict())
        MailManager._save_mailbox(recipient, messages)
        return True

    @staticmethod
    def get_unread_count(player_name: str) -> int:
        messages = MailManager._load_mailbox(player_name)
        return sum(1 for m in messages if not m.get('read', False))

    @staticmethod
    def get_all_mail(player_name: str) -> List[Dict]:
        return MailManager._load_mailbox(player_name)

    @staticmethod
    def get_unread_mail(player_name: str) -> List[Dict]:
        return [m for m in MailManager._load_mailbox(player_name) if not m.get('read', False)]

    @staticmethod
    def mark_read(player_name: str, msg_id: int):
        messages = MailManager._load_mailbox(player_name)
        for m in messages:
            if m.get('msg_id') == msg_id:
                m['read'] = True
        MailManager._save_mailbox(player_name, messages)

    @staticmethod
    def mark_all_read(player_name: str):
        messages = MailManager._load_mailbox(player_name)
        for m in messages:
            m['read'] = True
        MailManager._save_mailbox(player_name, messages)

    @staticmethod
    def delete_mail(player_name: str, msg_id: int) -> bool:
        messages = MailManager._load_mailbox(player_name)
        before = len(messages)
        messages = [m for m in messages if m.get('msg_id') != msg_id]
        if len(messages) < before:
            MailManager._save_mailbox(player_name, messages)
            return True
        return False
