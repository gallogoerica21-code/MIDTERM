import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class BrevoEmailError(Exception):
    """Raised when a Brevo email cannot be configured or delivered."""


def send_password_reset_notification(email):
    api_key = os.environ.get("BREVO_API_KEY")
    sender_email = os.environ.get("BREVO_SENDER_EMAIL")
    recipient_email = os.environ.get("BREVO_NOTIFICATION_EMAIL")

    missing_settings = [
        name
        for name, value in (
            ("BREVO_API_KEY", api_key),
            ("BREVO_SENDER_EMAIL", sender_email),
            ("BREVO_NOTIFICATION_EMAIL", recipient_email),
        )
        if not value
    ]
    if missing_settings:
        raise BrevoEmailError(
            "Missing Brevo settings: " + ", ".join(missing_settings)
        )

    _send_email(
        api_key,
        sender_email,
        {
        "sender": {
            "email": sender_email,
            "name": os.environ.get(
                "BREVO_SENDER_NAME", "Campus Hardware Inventory"
            ),
        },
        "to": [{"email": recipient_email}],
        "subject": "New password reset request",
        "textContent": (
            "A user submitted a password reset request for "
            f"the account registered to {email}.\n\n"
            "Review this request in the application's admin approvals page."
        ),
        },
    )


def send_registration_otp(email, code):
    api_key = os.environ.get("BREVO_API_KEY")
    sender_email = os.environ.get("BREVO_SENDER_EMAIL")

    missing_settings = [
        name
        for name, value in (
            ("BREVO_API_KEY", api_key),
            ("BREVO_SENDER_EMAIL", sender_email),
        )
        if not value
    ]
    if missing_settings:
        raise BrevoEmailError(
            "Missing Brevo settings: " + ", ".join(missing_settings)
        )

    _send_email(
        api_key,
        sender_email,
        {
            "sender": {
                "email": sender_email,
                "name": os.environ.get(
                    "BREVO_SENDER_NAME", "Campus Hardware Inventory"
                ),
            },
            "to": [{"email": email}],
            "subject": "Your account verification code",
            "textContent": (
                f"Your Campus Hardware Inventory account verification code is "
                f"{code}.\n\nThis code expires in 10 minutes. If you did not "
                "request this code, you can ignore this email."
            ),
        },
    )


def _send_email(api_key, sender_email, payload):
    brevo_request = Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(brevo_request, timeout=15) as response:
            if not 200 <= response.status < 300:
                raise BrevoEmailError(
                    f"Brevo returned HTTP status {response.status}."
                )
    except HTTPError as exc:
        raise BrevoEmailError(
            f"Brevo returned HTTP status {exc.code}."
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise BrevoEmailError("Could not reach the Brevo email service.") from exc
