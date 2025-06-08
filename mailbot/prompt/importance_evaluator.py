from mail.emailwrapper import EmailWrapper
from prompt.prompt import Prompt
from re import findall, DOTALL
from json import loads

# This prompt is custom-built and maynot be suitable for all use cases.
class ImportanceEvaulator(Prompt):
    def __init__(self, email: EmailWrapper):
        self.email_from = email.sender
        self.email_subject = email.subject
        self.email_body = email.body

    def _get_instruction(self) -> str:  
        return (
            "CRITICAL: You MUST respond with ONLY the exact JSON format specified below. "
            "Do NOT add any other fields, explanations, or text outside the JSON.\n\n"
            
            "Your task: Assign an importance score (0.0-1.0) to this email for an individual person.\n\n"

            "Scoring Guidelines:\n"
            "- HIGH (0.8-1.0): Security alerts, account notifications, direct human communication, medical/legal info, calendar invites, job applications\n"
            "- MEDIUM (0.4-0.79): Order confirmations, shipping updates, expiring EXISTING paid services/memberships, appointment reminders\n"
            "- LOW (0.0-0.39): All marketing, promotions, newsletters, deals, offers, advertisements, bulk emails\n\n"
            
            "CRITICAL DISTINCTION:\n"
            "- Expiring membership you ALREADY pay for (gym, subscription) = MEDIUM\n"
            "- Promotional offer to JOIN something new = LOW\n\n"
            
            "STRICT RULES:\n"
            "1. ANY email with promotional keywords (deals, discount, offer, sale, limited time, promo code, bonus points, low stock, savings, % off) = LOW importance\n"
            "2. Emails about YOUR EXISTING paid services expiring = MEDIUM importance\n"
            "3. Promotional offers to join/buy NEW services = LOW importance\n"
            "4. If the primary purpose is to sell or promote anything = LOW importance, even if personalized\n"
            "5. Marketing emails disguised as urgent alerts are still marketing = LOW importance\n"
            "6. Food newsletters, event promotions, reward programs, loyalty programs = LOW importance\n"
            "7. Neighborhood posts/community updates = LOW importance (not urgent personal matters)\n\n"
            
            "RESPONSE FORMAT - FOLLOW EXACTLY:\n"
            "{\n"
            "  \"importance\": 0.XX,\n"
            "  \"confidence\": 0.XX,\n"
            "  \"reasoning\": \"Brief explanation\"\n"
            "}\n\n"
            
            "ONLY return this JSON. NO other text, fields, or explanations."
        )

    def _get_few_shot_example(self) -> str:
        return (
            "EXAMPLES - Learn the patterns:\n\n"
            
            "Promotional/Marketing (LOW):\n"
            "{\n"
            "  \"importance\": 0.1,\n"
            "  \"confidence\": 0.95,\n"
            "  \"reasoning\": \"Promotional email with discount offers\"\n"
            "}\n\n"
            
            "Stock Alert Marketing (LOW):\n"
            "{\n"
            "  \"importance\": 0.1,\n"
            "  \"confidence\": 0.95,\n"
            "  \"reasoning\": \"Marketing email using artificial urgency about low stock\"\n"
            "}\n\n"
            
            "Bonus Points Promotion (LOW):\n"
            "{\n"
            "  \"importance\": 0.1,\n"
            "  \"confidence\": 0.95,\n"
            "  \"reasoning\": \"Promotional offer for loyalty program rewards\"\n"
            "}\n\n"
            
            "Expiring Paid Service (MEDIUM):\n"
            "{\n"
            "  \"importance\": 0.6,\n"
            "  \"confidence\": 0.90,\n"
            "  \"reasoning\": \"Notification about expiring paid membership requiring action\"\n"
            "}\n\n"
            
            "Security Alert (HIGH):\n"
            "{\n"
            "  \"importance\": 0.95,\n"
            "  \"confidence\": 0.98,\n"
            "  \"reasoning\": \"Account security alert requiring immediate verification\"\n"
            "}\n\n"
            
            "Order Confirmation (MEDIUM):\n"
            "{\n"
            "  \"importance\": 0.6,\n"
            "  \"confidence\": 0.90,\n"
            "  \"reasoning\": \"Transactional confirmation of completed purchase\"\n"
            "}\n\n"
            
            "Newsletter/Food Forecast (LOW):\n"
            "{\n"
            "  \"importance\": 0.1,\n"
            "  \"confidence\": 0.95,\n"
            "  \"reasoning\": \"Newsletter content with no actionable information\"\n"
            "}"
        )

    def _get_response_format(self) -> str:
        return (
            "FINAL REMINDER:\n"
            "Return ONLY this exact JSON structure:\n"
            "{\n"
            "  \"importance\": [number 0.0-1.0],\n"
            "  \"confidence\": [number 0.0-1.0],\n"
            "  \"reasoning\": \"[one sentence]\"\n"
            "}\n"
            "NO additional fields or text allowed."
        )

    def get_prompt(self) -> str:
        return (
            f"{self._get_instruction()}\n\n"
            f"{self._get_few_shot_example()}\n\n"
            f"EMAIL TO EVALUATE:\n"
            f"From: {self.email_from}\n"
            f"Subject: {self.email_subject}\n"
            f"Body: {self.email_body[:500]}...\n\n"  # Truncate very long bodies
            f"{self._get_response_format()}\n\n"
            f"REMEMBER: \n"
            f"- Look for promotional keywords: 'deals', 'offers', 'discount', 'limited time', 'bonus points', 'low stock', 'promo code', 'savings', '% off' = ALL LOW\n"
            f"- 'Join now' or 'Sign up' offers = LOW (trying to sell NEW service)\n"
            f"- 'Your membership expires' = MEDIUM (existing service you pay for)\n"
            f"- Neighborhood posts, community updates = LOW (not urgent personal matters)\n"
            f"- Any email trying to sell something = LOW, regardless of personalization\n\n"
            f"Evaluate now (JSON only):"
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
            print(f"Failed to parse response JSON: {e}")
            return {
                "importance": 0.0,
                "confidence": 0.0,
                "reasoning": "Failed to parse response"
            }

    def extract_response(self, response: str) -> dict:
        return self.__create_object(response)