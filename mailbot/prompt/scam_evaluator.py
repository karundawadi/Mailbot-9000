from mail.emailwrapper import EmailWrapper
from prompt.prompt import Prompt
from re import findall, DOTALL
from json import loads

class ScamEvaluator(Prompt):
    def __init__(self, email: EmailWrapper):
        self.email_from = email.sender
        self.email_subject = email.subject
        self.email_body = email.body

    def _get_instruction(self) -> str:
        return (
            "You are a smart email security assistant designed to detect scam or phishing emails.\n"
            "Your task is to classify an email as either a scam (fraudulent, phishing, deceptive) or not.\n\n"

            "Consider an email a **scam** if it includes:\n"
            "- Urgent language prompting quick action (e.g., 'act now', 'your account will be closed')\n"
            "- Requests for sensitive information (passwords, bank info, OTP, SSN)\n"
            "- Fake sender addresses or spoofed domains\n"
            "- Unusual attachments or links to suspicious websites\n"
            "- Promises of rewards, inheritances, lottery winnings, cryptocurrency giveaways\n"
            "- Poor grammar, spelling, and formatting\n\n"

            "**JSON Output Rules:**\n"
            "- 'scam': 1 → Yes, this email is a scam\n"
            "- 'scam': 0 → No, this email is legitimate\n"
            "- Include a 'confidence' score between 0.0 and 1.0\n"
            "- Explain your reasoning clearly in one sentence"
        )

    def _get_few_shot_example(self) -> str:
        return (
            "EXAMPLES:\n\n"

            "Example 1:\n"
            "From: \"Support\" <support@apple.verify-login.com>\n"
            "Subject: Urgent! Confirm your Apple ID\n"
            "Body: Your Apple ID has been locked. Click this link to verify your identity...\n\n"
            "<answer>\n"
            "{\n"
            "  \"scam\": 1,\n"
            "  \"confidence\": 0.97,\n"
            "  \"reasoning\": \"Spoofed domain with phishing link requesting sensitive info.\"\n"
            "}\n"
            "</answer>\n\n"

            "Example 2:\n"
            "From: \"Amazon\" <auto-confirm@amazon.com>\n"
            "Subject: Your order has been shipped\n"
            "Body: Your order #456-123456 will arrive by Tuesday...\n\n"
            "<answer>\n"
            "{\n"
            "  \"scam\": 0,\n"
            "  \"confidence\": 0.93,\n"
            "  \"reasoning\": \"Legitimate transactional email from a known sender with expected content.\"\n"
            "}\n"
            "</answer>\n\n"

            "Example 3:\n"
            "From: \"CryptoGiveaway\" <giveaway@eloncrypto.org>\n"
            "Subject: You’ve won 5 BTC!\n"
            "Body: Click now to claim your crypto prize before it expires...\n\n"
            "<answer>\n"
            "{\n"
            "  \"scam\": 1,\n"
            "  \"confidence\": 0.99,\n"
            "  \"reasoning\": \"Too-good-to-be-true offer with suspicious domain and urgent CTA.\"\n"
            "}\n"
            "</answer>"
        )

    def _get_response_format(self) -> str:
        return (
            "\n\nANALYZE THE FOLLOWING EMAIL:\n"
            "Respond ONLY with valid JSON wrapped in <answer> tags. No extra text.\n\n"

            "REQUIRED FORMAT:\n"
            "<answer>\n"
            "{\n"
            "  \"scam\": 0 or 1,\n"
            "  \"confidence\": 0.XX,\n"
            "  \"reasoning\": \"One clear sentence explaining your decision.\"\n"
            "}\n"
            "</answer>\n\n"

            "RULES:\n"
            "- scam: 0 = NOT SCAM, 1 = SCAM\n"
            "- Return ONLY valid JSON inside <answer> tags\n"
            "- No markdown, no explanation, just JSON"
        )

    def get_prompt(self) -> str:
        return (
            f"{self._get_instruction()}\n\n"
            f"{self._get_few_shot_example()}\n\n"
            f"EMAIL TO ANALYZE:\n"
            f"From: {self.email_from}\n"
            f"Subject: {self.email_subject}\n"
            f"Body: {self.email_body}\n"
            f"{self._get_response_format()}"
        )
    
    def __create_object(self, response: str) -> dict:
        try:
            match = findall(r"<answer>\s*(\{.*?\})\s*</answer>", response, flags=DOTALL)
            if not match:
                raise ValueError("No valid JSON found in response.")
            extracted_answer = match[0].strip()
            obj = loads(extracted_answer)
            return {
                "scam": obj.get("scam", 0),
                "confidence": obj.get("confidence", 0.0),
                "reasoning": obj.get("reasoning", "Missing reasoning.")
            }
        except Exception as e:
            print(f"Failed to parse response JSON: {e}")
            return {
                "scam": 0,
                "confidence": 0.0,
                "reasoning": "Failed to parse response"
            }

    def extract_response(self, response: str) -> dict:
        return self.__create_object(response)
