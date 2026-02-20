import os
import httpx
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
FRONTEND_URL = os.getenv("FRONTEND_URL")

async def send_reset_email(to_email: str, reset_token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": "Password Reset - Medical LLM Benchmark",
        "html": f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password.</p>
            <p>
              <a href="{reset_link}">
                Click here to reset your password
              </a>
            </p>
            <p>This link will expire in 1 hour.</p>
          </body>
        </html>
        """
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers
            )

        if resp.status_code >= 400:
            print("❌ Email failed:", resp.text)
            return False

        print(f"✅ Reset email sent to {to_email}")
        return True

    except Exception as e:
        print("❌ Email exception:", e)
        return False
