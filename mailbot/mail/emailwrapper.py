from mail.utils import extract_best_body

class EmailWrapper:
    def __init__(self, subject: str, body: str, sender: str, recipient: str, date: str, message_id: str):
        self.subject = subject
        self.body = extract_best_body(body)
        self.sender = sender
        self.recipient = recipient
        self.date = date
        self.message_id = message_id