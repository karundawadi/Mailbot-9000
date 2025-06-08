import pytest
from unittest.mock import patch, MagicMock
from configparser import ConfigParser
from mailbot.mail.imapclientwrapper import ImapClientWrapper

@pytest.fixture
def config():
    cfg = ConfigParser()
    cfg["IMAP"] = {
        "port": "993",
        "server": "imap.example.com",
        "username": "user@example.com",
        "password": "password123"
    }
    return cfg


@pytest.fixture
def client(config):
    return ImapClientWrapper(config)


@patch("mailbot.mail.imapclientwrapper.IMAP4_SSL")
def test_create_client_success(mock_imap_ssl, client):
    mock_instance = MagicMock()
    mock_imap_ssl.return_value = mock_instance

    client.initialize()

    mock_imap_ssl.assert_called_once_with("imap.example.com", 993)
    assert client.imap_client is mock_instance


@patch("mailbot.mail.imapclientwrapper.IMAP4_SSL")
def test_create_client_exception(mock_imap_ssl, client, capsys):
    mock_imap_ssl.side_effect = Exception("Connection error")

    client.initialize()

    captured = capsys.readouterr()
    assert "Failed to create IMAP client" in captured.out
    assert client.imap_client is None


@patch("mailbot.mail.imapclientwrapper.IMAP4_SSL")
def test_connect_success(mock_imap_ssl, client):
    mock_instance = MagicMock()
    mock_imap_ssl.return_value = mock_instance

    client.initialize()

    mock_instance.login.assert_called_once_with("user@example.com", "password123")


def test_connect_without_create_client_raises(client):
    # Call the private __connect() method to simulate connection attempt without client
    with pytest.raises(Exception, match="IMAP client not created"):
        client._ImapClientWrapper__connect()


@patch("mailbot.mail.imapclientwrapper.IMAP4_SSL")
def test_disconnect_success(mock_imap_ssl, client):
    mock_instance = MagicMock()
    mock_imap_ssl.return_value = mock_instance

    client.initialize()
    client.disconnect()

    mock_instance.logout.assert_called_once()


def test_disconnect_without_create_client_raises(client):
    with pytest.raises(Exception, match="IMAP client not created"):
        client.disconnect()
