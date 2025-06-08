import configparser

from mail.imapservice import ImapService
from mail.emailwrapper import EmailWrapper
from llm.ollamallm.llm import LLM
from cache.cache import Cache, ImportanceLevel
from prompt.importance_evaluator import ImportanceEvaulator
from typing import Optional

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    imapService = ImapService(config)
    cacheService = Cache(config)
    most_important_folder = config["IMAP"]["most_important_folder"]
    medium_important_folder = config["IMAP"]["medium_important_folder"]
    less_important_folder = config["IMAP"]["less_important_folder"]
    llm = LLM(config)
    mailbox_list = imapService.get_mailbox_list()
    exception_list = [f"{most_important_folder}", f"{medium_important_folder}", f"{less_important_folder}"]
    for mailbox in mailbox_list:
        if mailbox in exception_list:
            print(mailbox, "is in the exception list. Skipping...")
            continue
        email_ids = imapService.fetch_email_ids(mailbox)
        for email_id in email_ids:
            email_data: EmailWrapper = imapService.fetch_email(email_id)
            importance_level: Optional[ImportanceLevel] = cacheService.exists(email_data)
            if importance_level:
                print(f'Email with subject {email_data.subject} already evaluated and marked as {importance_level.value}')
                imapService.move_to_folder_and_mark_unread(email_id, importance_level)
                continue
            prompt = ImportanceEvaulator(email_data)
            llm_response = llm.generate(prompt)
            if llm_response["importance"] > 0 and llm_response["confidence"] > 0:
                importance = ImportanceLevel.MOST_IMPORTANT if llm_response["importance"] > 0.75 else ImportanceLevel.MEDIUM_IMPORTANT if llm_response["importance"] > 0.4 else ImportanceLevel.LEAST_IMPORTANT
                cacheService.add_record(email_data, importance, llm_response["reasoning"])
                print(f'Email with subject {email_data.subject} added to cache and moved to {importance.value}')
                imapService.move_to_folder_and_mark_unread(email_id, importance)
    imapService.shutdown()