import pytest
import json
from unittest.mock import patch, mock_open, MagicMock, ANY
from src.mail_system import MailMessage, MailManager

def test_mail_message_init():
    # Test default values
    msg = MailMessage("sender", "recipient", "subject", "body")
    assert msg.sender == "sender"
    assert msg.recipient == "recipient"
    assert msg.subject == "subject"
    assert msg.body == "body"
    assert msg.read is False
    assert msg.msg_id == 0
    assert msg.timestamp is not None

    # Test custom values
    msg2 = MailMessage("s", "r", "subj", "b", "2023-01-01", True, 5)
    assert msg2.sender == "s"
    assert msg2.recipient == "r"
    assert msg2.subject == "subj"
    assert msg2.body == "b"
    assert msg2.timestamp == "2023-01-01"
    assert msg2.read is True
    assert msg2.msg_id == 5

def test_mail_message_to_dict():
    msg = MailMessage("s", "r", "subj", "b", "2023-01-01", True, 5)
    expected = {
        'sender': "s",
        'recipient': "r",
        'subject': "subj",
        'body': "b",
        'timestamp': "2023-01-01",
        'read': True,
        'msg_id': 5,
    }
    assert msg.to_dict() == expected

def test_mail_message_from_dict():
    data = {
        'sender': "s",
        'recipient': "r",
        'subject': "subj",
        'body': "b",
        'timestamp': "2023-01-01",
        'read': True,
        'msg_id': 5,
    }
    msg = MailMessage.from_dict(data)
    assert msg.sender == "s"
    assert msg.recipient == "r"
    assert msg.subject == "subj"
    assert msg.body == "b"
    assert msg.timestamp == "2023-01-01"
    assert msg.read is True
    assert msg.msg_id == 5

@patch('os.makedirs')
@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='[]')
def test_mail_manager_send_mail(mock_file, mock_exists, mock_makedirs):
    mock_exists.return_value = True

    # Send first mail
    success = MailManager.send_mail("Alice", "Bob", "Hello Bob")
    assert success is True

    # Verify save was called
    mock_file.assert_called()
    handle = mock_file()
    # Check that it was called with 'w' at least once
    mock_file.assert_any_call(ANY, 'w')

    # Verify content saved (last call to write)
    calls = [call.args[0] for call in handle.write.call_args_list]
    full_content = "".join(calls)
    saved_data = json.loads(full_content)
    assert len(saved_data) == 1
    assert saved_data[0]['sender'] == "Alice"
    assert saved_data[0]['recipient'] == "Bob"
    assert saved_data[0]['msg_id'] == 1

@patch('src.mail_system.MailManager._load_mailbox')
def test_mail_manager_get_unread_count(mock_load):
    mock_load.return_value = [
        {'read': False},
        {'read': True},
        {'read': False}
    ]
    count = MailManager.get_unread_count("Bob")
    assert count == 2

@patch('src.mail_system.MailManager._load_mailbox')
def test_mail_manager_get_all_mail(mock_load):
    mock_data = [{'msg_id': 1}, {'msg_id': 2}]
    mock_load.return_value = mock_data
    assert MailManager.get_all_mail("Bob") == mock_data

@patch('src.mail_system.MailManager._load_mailbox')
def test_mail_manager_get_unread_mail(mock_load):
    mock_load.return_value = [
        {'msg_id': 1, 'read': False},
        {'msg_id': 2, 'read': True},
        {'msg_id': 3, 'read': False}
    ]
    unread = MailManager.get_unread_mail("Bob")
    assert len(unread) == 2
    assert unread[0]['msg_id'] == 1
    assert unread[1]['msg_id'] == 3

@patch('src.mail_system.MailManager._load_mailbox')
@patch('src.mail_system.MailManager._save_mailbox')
def test_mail_manager_mark_read(mock_save, mock_load):
    mock_load.return_value = [
        {'msg_id': 1, 'read': False},
        {'msg_id': 2, 'read': False}
    ]
    MailManager.mark_read("Bob", 1)

    # Verify save was called with updated data
    mock_save.assert_called_once()
    saved_messages = mock_save.call_args[0][1]
    assert saved_messages[0]['read'] is True
    assert saved_messages[1]['read'] is False

@patch('src.mail_system.MailManager._load_mailbox')
@patch('src.mail_system.MailManager._save_mailbox')
def test_mail_manager_mark_all_read(mock_save, mock_load):
    mock_load.return_value = [
        {'msg_id': 1, 'read': False},
        {'msg_id': 2, 'read': False}
    ]
    MailManager.mark_all_read("Bob")

    mock_save.assert_called_once()
    saved_messages = mock_save.call_args[0][1]
    assert all(m['read'] is True for m in saved_messages)

@patch('src.mail_system.MailManager._load_mailbox')
@patch('src.mail_system.MailManager._save_mailbox')
def test_mail_manager_delete_mail(mock_save, mock_load):
    mock_load.return_value = [
        {'msg_id': 1},
        {'msg_id': 2}
    ]

    # Delete existing
    success = MailManager.delete_mail("Bob", 1)
    assert success is True
    mock_save.assert_called_once()
    assert len(mock_save.call_args[0][1]) == 1
    assert mock_save.call_args[0][1][0]['msg_id'] == 2

    mock_save.reset_mock()

    # Delete non-existing
    success = MailManager.delete_mail("Bob", 99)
    assert success is False
    mock_save.assert_not_called()
