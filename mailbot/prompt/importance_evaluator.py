from mail.emailwrapper import EmailWrapper
from prompt.prompt import Prompt
from re import findall, DOTALL
from json import loads
from loguru import logger

# This prompt is custom-built and maynot be suitable for all use cases.
class ImportanceEvaulator(Prompt):
    def __init__(self, email: EmailWrapper):
        self.email_from = email.sender
        self.email_subject = email.subject
        self.email_body = email.body

    def _get_instruction(self) -> str:
        return (
            "Respond ONLY with the following JSON format. No extra text.\n\n"
            "Task: Assign an importance score (0.0-1.0) to this email for an individual. If the email is a scam or phishing attempt, set importance to -1.\n\n"
            "Scoring:\n"
            "- HIGH (0.8-1.0): Security alerts, account notifications, direct human communication, medical/legal info, calendar invites, job applications\n"
            "- MEDIUM (0.4-0.79): Order confirmations, shipping updates, expiring EXISTING paid services/memberships, appointment reminders\n"
            "- LOW (0.0-0.39): Marketing, promotions, newsletters, deals, offers, advertisements, bulk emails\n"
            "- SCAM/PHISHING (-1): Any email that is a scam, phishing, or malicious attempt.\n\n"
            "Scam/Phishing Detection:\n"
            "- If the sender address and the content (e.g., signature, reply-to, URLs) do not match or look suspicious, mark as SCAM (-1).\n"
            "- If sender claims to be a known company but uses a generic or mismatched email domain, mark as SCAM.\n"
            "- If the email requests sensitive info, login, payment, or urgent action with suspicious links, mark as SCAM.\n"
            "- If sender is unknown and content is generic, threatening, or too good to be true, mark as SCAM.\n"
            "- If sender and content mismatch in any way typical of phishing, mark as SCAM.\n\n"
            "Rules:\n"
            "- Promotional keywords (deals, discount, offer, sale, limited time, promo code, bonus points, low stock, savings, % off) = LOW\n"
            "- Expiring EXISTING paid service = MEDIUM\n"
            "- Promotional offers to join/buy NEW service = LOW\n"
            "- If selling or promoting anything = LOW, even if personalized\n"
            "- Marketing disguised as urgent = LOW\n"
            "- Food/newsletters/events/rewards/loyalty/community = LOW\n"
            "- If the email is a scam, phishing, or malicious, set importance to -1 and reasoning to 'Likely scam or phishing'.\n\n"
            "Format:\n"
            "{\n  \"importance\": 0.XX,\n  \"confidence\": 0.XX,\n  \"reasoning\": \"Brief explanation\"\n}\n\n"
            "Return ONLY this JSON."
        )

    def _get_few_shot_example(self) -> str:
        return (
            "Examples:\n"
            "Promotional/Marketing (LOW): {\"importance\": 0.1, \"confidence\": 0.95, \"reasoning\": \"Promotional email with discount offers\"}\n"
            "Expiring Paid Service (MEDIUM): {\"importance\": 0.6, \"confidence\": 0.90, \"reasoning\": \"Notification about expiring paid membership\"}\n"
            "Security Alert (HIGH): {\"importance\": 0.95, \"confidence\": 0.98, \"reasoning\": \"Account security alert\"}\n"
            "Order Confirmation (MEDIUM): {\"importance\": 0.6, \"confidence\": 0.90, \"reasoning\": \"Transactional confirmation of purchase\"}\n"
            "Newsletter (LOW): {\"importance\": 0.1, \"confidence\": 0.95, \"reasoning\": \"Newsletter, no action needed\"}\n"
            "Scam/Phishing (JUNK): {\"importance\": -1, \"confidence\": 0.99, \"reasoning\": \"Likely scam or phishing attempt\"}"
        )

    def _get_response_format(self) -> str:
        return (
            "Return ONLY this JSON structure:\n"
            "{\"importance\": [0.0-1.0 or -1 for scam], \"confidence\": [0.0-1.0], \"reasoning\": \"[one sentence]\"}"
        )

    def get_prompt(self) -> str:
        return (
            f"{self._get_instruction()}\n\n"
            f"{self._get_few_shot_example()}\n\n"
            f"EMAIL TO EVALUATE:\nFrom: {self.email_from}\nSubject: {self.email_subject}\nBody: {self.email_body[:500]}...\n\n"
            f"{self._get_response_format()}\n"
        )
    
    def __create_object(self, response: str) -> dict:
        try:
            match = findall(r"<answer>\s*({.*?})\s*</answer>", response, flags=DOTALL)

            if not match:
                # Fallback: extract JSON from code block like ```json\n{...}\n```}`
                match = findall(r"```(?:json)?\s*({.*?})\s*```", response, flags=DOTALL)
            
            if not match:
                # Final fallback: any JSON-looking block in the response
                match = findall(r"{\s*\"importance\".*?}", response, flags=DOTALL)

            if not match:
                raise ValueError("No valid JSON found in response.")
            extracted_answer = match[0].strip()
            obj = loads(extracted_answer)
            return {
                "importance": obj.get("importance", 0.0),
                "confidence": obj.get("confidence", 0.0),
                "reasoning": obj.get("reasoning", "Missing reasoning.")
            }
        except Exception as e:
            logger.info(f"Failed to parse response JSON: {e}")
            return {
                "importance": 0.0,
                "confidence": 0.0,
                "reasoning": "Failed to parse response"
            }

    def extract_response(self, response: str) -> dict:
        return self.__create_object(response)