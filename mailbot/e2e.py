import configparser
from typing import Optional

from mail.imapservice import ImapService
from mail.emailwrapper import EmailWrapper
from llm.ollamallm.llm import LLM
from cache.cache import Cache, ImportanceLevel
from prompt.importance_evaluator import ImportanceEvaulator
from loguru import logger


def process_mailbox(imapService, cacheService, llm, mailbox: str, max_retries: int = 2):
    attempts = 0
    while attempts <= max_retries:
        email_ids = imapService.fetch_email_ids(mailbox)
        logger.info(f"Processing {len(email_ids)} email(s) from {mailbox} (Attempt {attempts + 1})")
        failed = False

        for email_id in email_ids:
            email_data: Optional[EmailWrapper] = imapService.fetch_email(email_id)
            if not email_data:
                logger.warning(f"Failed to fetch email ID {email_id}. Restarting and retrying whole mailbox...")
                failed = True
                break  # Exit this pass and restart everything

            importance_level: Optional[ImportanceLevel] = cacheService.exists(email_data)
            if importance_level:
                logger.info(f'Email "{email_data.subject}" already marked as {importance_level.value}')
                imapService.move_to_folder_and_mark_unread(email_id, importance_level)
                continue

            prompt = ImportanceEvaulator(email_data)
            llm_response = llm.generate(prompt)

            if llm_response["importance"] > 0 and llm_response["confidence"] > 0:
                importance = (
                    ImportanceLevel.MOST_IMPORTANT
                    if llm_response["importance"] > 0.75 else
                    ImportanceLevel.MEDIUM_IMPORTANT
                    if llm_response["importance"] > 0.4 else
                    ImportanceLevel.LEAST_IMPORTANT
                )
                cacheService.add_record(email_data, importance, llm_response["reasoning"])
                logger.info(f'Email "{email_data.subject}" cached and moved to {importance.value}')
                imapService.move_to_folder_and_mark_unread(email_id, importance)

        if not failed:
            break  # Completed mailbox without any fetch failure
        else:
            imapService.restart()
            attempts += 1

    if attempts > max_retries:
        logger.error(f"Failed to process mailbox {mailbox} after {max_retries} retries.")


def process_emails(config: configparser.ConfigParser):
    imapService = ImapService(config)
    cacheService = Cache(config)
    llm = LLM(config)

    most_important_folder = config["IMAP"]["most_important_folder"]
    medium_important_folder = config["IMAP"]["medium_important_folder"]
    less_important_folder = config["IMAP"]["less_important_folder"]

    exception_list = [
        most_important_folder, medium_important_folder, less_important_folder,
        "Important", "Sent", "Drafts", "Trash", "Spam", "Junk", "Archive"
    ]

    try:
        mailbox_list = imapService.get_mailbox_list()
        for mailbox in mailbox_list:
            if mailbox in exception_list:
                logger.info(f"{mailbox} is in the exception list. Skipping...")
                continue

            process_mailbox(imapService, cacheService, llm, mailbox)

    except Exception as e:
        logger.exception(f"Unexpected error during processing: {e}")

    finally:
        imapService.shutdown()


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    process_emails(config)
