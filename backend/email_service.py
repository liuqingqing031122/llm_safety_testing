import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")  # Your Gmail
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # App password
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

async def send_reset_email(to_email: str, reset_token: str):
    """Send password reset email"""
    
    # Create reset link (update with your frontend URL)
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset - Medical LLM Benchmark"
    message["From"] = FROM_EMAIL
    message["To"] = to_email
    
    # HTML content
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #667eea;">Password Reset Request</h2>
        <p>You requested to reset your password for Medical LLM Safety Benchmark.</p>
        <p>Click the button below to reset your password:</p>
        <a href="{reset_link}" 
           style="display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0;">
          Reset Password
        </a>
        <p style="color: #666;">Or copy and paste this link into your browser:</p>
        <p style="color: #667eea;">{reset_link}</p>
        <p style="color: #999; font-size: 0.9em; margin-top: 30px;">
          This link will expire in 1 hour.<br>
          If you didn't request this, please ignore this email.
        </p>
      </body>
    </html>
    """
    
    # Plain text alternative
    text = f"""
    Password Reset Request
    
    You requested to reset your password for Medical LLM Safety Benchmark.
    
    Click this link to reset your password:
    {reset_link}
    
    This link will expire in 1 hour.
    If you didn't request this, please ignore this email.
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    
    message.attach(part1)
    message.attach(part2)
    
    # Send email
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
        )
        print(f"✅ Reset email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False