from os import path
from configparser import ConfigParser
from enum import Enum
from csv import DictWriter, DictReader
from datetime import datetime
from mail.emailwrapper import EmailWrapper
from hashlib import sha256
from typing import Optional

# Define an Enum for clarity and type safety for importance levels
class ImportanceLevel(Enum):
    LEAST_IMPORTANT = "least_important"
    MEDIUM_IMPORTANT = "medium_important"
    MOST_IMPORTANT = "most_important"
    SCAM = "scam"

class Cache:
    def __init__(self, config: ConfigParser):

        if not config["CACHE"]["cache_file"]:
            raise ValueError("Cache file path is not specified in the configuration.")
        
        self.cache_file_path = path.join(
            self.__get_current_base_dir(),
            config["CACHE"]["cache_file"]
        )

        self.fieldnames = [
            'sender',
            'importance_level',
            'email_subject',
            'email_subject_hash',
            'reasoning',
            'time_added'
        ]
        self.__ensure_file()

    def __get_current_base_dir(self) -> str:
        """Get the current base directory of the script."""
        return path.dirname(path.abspath(__file__))
    
    def __ensure_file(self) -> None:
        """Create the CSV file with headers if it doesn't exist."""
        if not path.exists(self.cache_file_path):
            try:
                with open(self.cache_file_path, 'w', newline='') as file:
                    writer = DictWriter(file, fieldnames=self.fieldnames)
                    writer.writeheader()
            except Exception as e:
                raise Exception(f"Failed to create cache file: {e}")
    
    def __get_current_time(self) -> str:
        """Get the current time in a suitable format for the cache."""
        return datetime.now().isoformat()

    def add_record(self, email: EmailWrapper, importance_level: ImportanceLevel, reasoning: str) -> None:
        """Add a record to the cache."""
        row = {
            'sender': email.sender,
            'importance_level': importance_level.value,
            'email_subject': email.subject,
            'email_subject_hash': sha256(email.subject.encode('utf-8')).hexdigest(),
            'reasoning': reasoning,
            'time_added': self.__get_current_time()
        }
        try:
            with open(self.cache_file_path, 'a', newline='') as file:
                writer = DictWriter(file, fieldnames=self.fieldnames)
                writer.writerow(row)
        except Exception as e:
            raise Exception(f"Failed to add record to cache: {e}")
    
    def __evaluate_row(self, row) -> Optional[ImportanceLevel]:
        try:
            return ImportanceLevel(row['importance_level'])
        except ValueError:
            return None

    def exists(self, email: EmailWrapper) -> Optional[ImportanceLevel]:
        subject_hash = sha256(email.subject.encode('utf-8')).hexdigest()
        with open(self.cache_file_path, 'r', newline='') as file:
            reader = DictReader(file) 
            for row in reader:
                if row['email_subject_hash'] == subject_hash:
                    return self.__evaluate_row(row)
                
                if row['sender'] == email.sender:
                    return self.__evaluate_row(row)
        return None