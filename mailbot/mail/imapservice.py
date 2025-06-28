from imaplib import IMAP4_SSL
from configparser import ConfigParser
from typing import Optional
from mail.imapclientwrapper import ImapClientWrapper
from re import search
from email import message_from_bytes
from mail.emailwrapper import EmailWrapper
from cache.cache import ImportanceLevel
from loguru import logger

class ImapService:
    def __init__(self, config: ConfigParser):
        self.client_wrapper = ImapClientWrapper(config)
        self.imap_client: IMAP4_SSL = self.client_wrapper.initialize()
        self.most_important_folder = config["IMAP"]["most_important_folder"]
        self.medium_important_folder = config["IMAP"]["medium_important_folder"]
        self.less_important_folder = config["IMAP"]["less_important_folder"]
    
    def get_mailbox_list(self) -> list:
        try:
            _, mailboxes = self.imap_client.list()
            return [self.__decode_mailbox_name(mailbox) for mailbox in mailboxes]
        except Exception as e:
            logger.info(f"Failed to retrieve mailbox list: {e}")
            return []
    
    def __decode_mailbox_name(self, mailbox_name: bytes) -> str:
        try:
            decoded = mailbox_name.decode('utf-8')
            match = search(r'"([^"]+)"\s*$', decoded)
            if match:
                return match.group(1)
            return decoded
        except Exception as e:
            logger.info(f"Failed to decode mailbox name '{mailbox_name}': {e}")
            return ""
    
    def __select_mailbox(self, mailbox_name: str) -> None:
        status, _ = self.imap_client.select(f'"{mailbox_name}"')
        if status != 'OK':
            raise Exception(f"Failed to select mailbox '{mailbox_name}': {status}")
    
    def __format_email_ids(self, email_ids: list) -> list:
        if not email_ids or not email_ids[0]:
            return []
        if isinstance(email_ids[0], bytes):
            ids = email_ids[0].decode('utf-8').split()
            return [email_id.strip() for email_id in ids]
        return []
    
    def fetch_email_ids(self, mailbox_name: str) -> list:
        try:
            if not self.imap_client or not self.imap_client.noop()[0] == 'OK':
                self.imap_client = self.client_wrapper.initialize()
            self.__select_mailbox(mailbox_name)
            _, email_ids = self.imap_client.search(None, 'UNSEEN')
            formatted_ids = self.__format_email_ids(email_ids)
            logger.info(f"Found {len(formatted_ids)} unseen emails in {mailbox_name}")
            return formatted_ids
        except Exception as e:
            logger.info(f"Failed to fetch emails: {e}")
            return []
    
    def __fetch_raw_email(self, email_id: str) -> bytes:
        # Method 1: Standard Body fetch
        logger.debug(f"Attempting to fetch email ID {email_id} with (RFC822)")
        status, data = self.imap_client.fetch(str(email_id), '(RFC822)')            
        if status != 'OK':
            logger.warning(f"Failed to fetch email ID {email_id} with (RFC822). Status: {status}")
            raise Exception(f"Failed to fetch email with ID {email_id}: {status}")
        
        # Validate the fetch response
        if not data or len(data) == 0:
            logger.warning(f"No data returned for email ID {email_id} with (RFC822).")
            raise Exception(f"No data returned for email ID {email_id}")
        
        # Handle different response formats
        raw_email = None
        
        # Check if we got the expected tuple format
        if isinstance(data[0], tuple) and len(data[0]) >= 2:
            raw_email = data[0][1]
        
        # Handle the case where we get bytes response like b'5974 ()'
        elif isinstance(data[0], bytes):
            response_str = data[0].decode('utf-8')
            if '()' in response_str:                    
                # Try BODY.PEEK[]
                logger.debug(f"Attempting to fetch email ID {email_id} with (BODY.PEEK[])")
                status2, data2 = self.imap_client.fetch(str(email_id), '(BODY.PEEK[])')
                if status2 == 'OK' and data2:
                    if isinstance(data2[0], tuple) and len(data2[0]) >= 2:
                        raw_email = data2[0][1]
                
                # If still no luck, try BODY[]
                if raw_email is None:
                    status3, data3 = self.imap_client.fetch(str(email_id), '(BODY[])')
                    if status3 == 'OK' and data3:
                        if isinstance(data3[0], tuple) and len(data3[0]) >= 2:
                            raw_email = data3[0][1]
                
                # If still no luck, try FLAGS to see if email exists
                if raw_email is None:
                    status4, data4 = self.imap_client.fetch(str(email_id), '(FLAGS)')
                    if status4 != 'OK':
                        raise Exception(f"Email ID {email_id} may not exist or may have been deleted")
                    else:
                        raise Exception(f"Email ID {email_id} exists but content could not be retrieved")
        
        if raw_email is None:
            raise Exception(f"Could not extract email content for ID {email_id}")
        
        # Ensure raw_email is bytes
        if not isinstance(raw_email, bytes):
            raise Exception(f"Expected bytes, got {type(raw_email)} for email ID {email_id}")
        
        return raw_email

    def __construct_email(self, msg, body) -> EmailWrapper:
        return EmailWrapper(
            subject=msg.get('Subject', 'No Subject'),
            body=body,
            sender=msg.get('From', 'Unknown Sender'),
            recipient=msg.get('To', 'Unknown Recipient'),
            date=msg.get('Date', 'Unknown Date'),
            message_id=msg.get('Message-ID', 'No Message ID')
        )

    def __extract_email_body(self, msg) -> str:
        body = ""
        
        try:
            if msg.is_multipart():
                # Handle multipart messages
                for part in msg.walk():
                    try:
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition", ""))
                        
                        # Skip attachments
                        if "attachment" in content_disposition:
                            continue
                        
                        # Look for text/plain parts first
                        if content_type == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload is not None and isinstance(payload, bytes):
                                body = payload.decode('utf-8', errors='replace')
                                break
                            elif payload is not None and isinstance(payload, str):
                                body = payload
                                break
                        # Fall back to text/html if no plain text found
                        elif content_type == "text/html" and not body:
                            payload = part.get_payload(decode=True)
                            if payload is not None and isinstance(payload, bytes):
                                body = payload.decode('utf-8', errors='replace')
                            elif payload is not None and isinstance(payload, str):
                                body = payload
                    except Exception as part_error:
                        logger.info(f"Error processing email part: {part_error}")
                        continue
            else:
                # Handle simple (non-multipart) messages
                try:
                    payload = msg.get_payload(decode=True)
                    if payload is not None and isinstance(payload, bytes):
                        body = payload.decode('utf-8', errors='replace')
                    elif payload is not None and isinstance(payload, str):
                        body = payload
                    else:
                        # Try without decode=True
                        payload = msg.get_payload()
                        if isinstance(payload, str):
                            body = payload
                except Exception as payload_error:
                    logger.info(f"Error getting payload: {payload_error}")
                    # Last resort - try to get payload as string
                    try:
                        body = str(msg.get_payload())
                    except:
                        body = "Could not extract email body"
        
        except Exception as e:
            logger.info(f"Error extracting email body: {e}")
            body = "Error extracting email body"
        
        return body
    
    def fetch_email(self, email_id: str) -> Optional[EmailWrapper]:
        try:
            if not self.imap_client or not self.imap_client.noop()[0] == 'OK':
                self.imap_client = self.client_wrapper.initialize()
            raw_email = self.__fetch_raw_email(email_id)            
            msg = message_from_bytes(raw_email)
            body = self.__extract_email_body(msg)
            return self.__construct_email(msg, body)
        except Exception as e:
            logger.exception(f"Failed to fetch email with ID {email_id}: {e}")
            return None

    def __importance_level_to_str(self, importance: ImportanceLevel) -> str:
        if importance == ImportanceLevel.LEAST_IMPORTANT:
            return self.less_important_folder
        elif importance == ImportanceLevel.MEDIUM_IMPORTANT:
            return self.medium_important_folder
        elif importance == ImportanceLevel.MOST_IMPORTANT:
            return self.most_important_folder
        else:
            raise Exception("In correct importance level passed. Please check if importance level is correct.")

    def move_to_folder_and_mark_read(self, email_id: str, importance: ImportanceLevel) -> None:
        try:
            folder_to_move = self.__importance_level_to_str(importance)
            if not folder_to_move:
                raise ValueError(f"{folder_to_move} is not configured in the config file.")
            self.mark_email_as_read(email_id)
            self.imap_client.copy(email_id, f'"{folder_to_move}"')
            self.mark_email_as_deleted(email_id)
            self.imap_client.expunge()
            logger.info(f"Email with ID {email_id} moved to {folder_to_move}.")
        except Exception as e:
            logger.info(f"Failed to move email with ID {email_id} to folder: {e}. Email is marked unread")
            self.mark_email_as_unread(email_id)
    
    def move_to_folder_and_mark_unread(self, email_id: str, importance: ImportanceLevel) -> None:
        try:
            folder_to_move = self.__importance_level_to_str(importance)
            if not folder_to_move:
                raise ValueError(f"{folder_to_move} is not configured in the config file.")
            self.mark_email_as_unread(email_id)
            self.imap_client.copy(email_id, f'"{folder_to_move}"')
            self.mark_email_as_read(email_id)
            self.mark_email_as_deleted(email_id)
            self.imap_client.expunge()
            logger.info(f"Email with ID {email_id} moved to {folder_to_move}.")
        except Exception as e:
            logger.info(f"Failed to move email with ID {email_id} to folder: {e}. Email is marked unread")
            self.mark_email_as_unread(email_id)

    def mark_email_as_read(self, email_id: str) -> None:
        try:
            self.imap_client.store(email_id, '+FLAGS', ('\\Seen',))
            logger.info(f"Email with ID {email_id} marked as read.")
        except Exception as e:
            logger.info(f"Failed to mark email with ID {email_id} as read: {e}")

    def mark_email_as_deleted(self, email_id: str) -> None:
        try:
            self.imap_client.store(email_id, '+FLAGS', '\\Deleted')            
            logger.info(f"Email with ID {email_id} marked as deleted.")
        except Exception as e:
            logger.info(f"Failed to mark email with ID {email_id} as deleted: {e}")

    def mark_email_as_unread(self, email_id: str) -> None:
        try:
            self.imap_client.store(email_id, '-FLAGS', ('\\Seen',))
            logger.info(f"Email with ID {email_id} marked as unread.")
        except Exception as e:
            logger.info(f"Failed to mark email with ID {email_id} as unread: {e}")

    def shutdown(self) -> None:
        try:
            self.imap_client.logout()
            logger.info("Disconnected from IMAP server.")
        except Exception as e:
            logger.info(f"Failed to disconnect: {e}")