from configparser import ConfigParser
from imaplib import IMAP4_SSL

# This code defines an IMAP client that connects to an IMAP server using credentials from a configuration file.
# This is only responsible for creating the client, connecting to the server, and disconnecting from it.
class ImapClientWrapper:
    def __init__(self, config: ConfigParser):
        self.imap_port: int = int(config["IMAP"]["port"])
        self.imap_server: str = config["IMAP"]["server"]
        self.imap_username: str = config["IMAP"]["username"]
        self.imap_password: str = config["IMAP"]["password"]
        self.imap_client: IMAP4_SSL = None

    def __create_client(self) -> None:
        try:
            self.imap_client = IMAP4_SSL(self.imap_server, self.imap_port)
            print("IMAP client created successfully.")
        except Exception as e:
            print(f"Failed to create IMAP client. Detailed error: {e}")
    
    def __connect(self) -> None:
        if self.imap_client is None:
            raise Exception("IMAP client not created. Call create_client() first.")
        try:
            login_status, _ = self.imap_client.login(self.imap_username, self.imap_password)
            if login_status != 'OK':
                raise Exception("Login failed.")
            print("Connected to IMAP server.")
        except Exception as e:
            print(f"Failed to connect: {e}")
    
    def initialize(self) -> IMAP4_SSL:
        self.__create_client()
        if self.imap_client is None:
            return None
        self.__connect()
        return self.imap_client

    
    def disconnect(self) -> None:
        if self.imap_client is None:
            raise Exception("IMAP client not created. Call create_client() first.")
        try:
            self.imap_client.logout()
            print("Disconnected from IMAP server.")
        except Exception as e:
            print(f"Failed to disconnect: {e}")

    def get_client(self) -> IMAP4_SSL:
        if self.imap_client is None:
            raise Exception("IMAP client not created. Call create_client() first.")
        return self.imap_client