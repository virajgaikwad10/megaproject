from __future__ import annotations

import requests

from backend import config


def _post_without_proxy(url: str, **kwargs):
    session = requests.Session()
    session.trust_env = False
    return session.post(url, **kwargs)


class NotificationService:
    """Send SMS alerts through Twilio or Fast2SMS."""

    def send_violation_sms(self, phone_number: str, violation: dict) -> str:
        if config.NOTIFICATION_PROVIDER == "twilio":
            return self._send_twilio(phone_number, violation)
        if config.NOTIFICATION_PROVIDER == "fast2sms":
            return self._send_fast2sms(phone_number, violation)
        if config.NOTIFICATION_PROVIDER == "textbelt":
            return self._send_textbelt(phone_number, violation)
        return "disabled"

    def send_test_sms(self, phone_number: str) -> dict:
        message = "Smart Traffic test SMS: notification system is connected."
        if config.NOTIFICATION_PROVIDER == "textbelt":
            response = _post_without_proxy(
                "https://textbelt.com/text",
                data={"phone": phone_number, "message": message, "key": config.TEXTBELT_API_KEY},
                timeout=10,
            )
            return response.json()
        return {"success": False, "error": f"Test endpoint currently supports textbelt, provider={config.NOTIFICATION_PROVIDER}"}

    def _message(self, violation: dict) -> str:
        return (
            f"Traffic violation {violation['violation_id']}: "
            f"{violation['violation_type']} by vehicle {violation['vehicle_id']} "
            f"plate {violation.get('plate_number') or 'unknown'} "
            f"at {violation['date_time']}."
        )

    def _send_twilio(self, phone_number: str, violation: dict) -> str:
        from twilio.rest import Client

        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=self._message(violation),
            from_=config.TWILIO_FROM_NUMBER,
            to=phone_number,
        )
        return "sent"

    def _send_fast2sms(self, phone_number: str, violation: dict) -> str:
        response = _post_without_proxy(
            "https://www.fast2sms.com/dev/bulkV2",
            headers={"authorization": config.FAST2SMS_API_KEY},
            data={
                "route": "q",
                "message": self._message(violation),
                "language": "english",
                "flash": 0,
                "numbers": phone_number,
                "sender_id": config.FAST2SMS_SENDER_ID,
            },
            timeout=10,
        )
        response.raise_for_status()
        return "sent"

    def _send_textbelt(self, phone_number: str, violation: dict) -> str:
        response = _post_without_proxy(
            "https://textbelt.com/text",
            data={
                "phone": phone_number,
                "message": self._message(violation),
                "key": config.TEXTBELT_API_KEY,
            },
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        return "sent" if result.get("success") else "failed"
