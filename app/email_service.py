from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.config import settings

# 1. Gmail SMTP Server Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


# 2. Account Verification Email Sending Function
async def send_verification_email(email_to: EmailStr, token: str) -> None:
    # Generate dynamic verification URL with the user token
    verification_link = settings.get_verification_link(token)

    html_content = f"""
    <!DOCTYPE html>
    <html dir="ltr" lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f7; padding: 20px; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
            <h2 style="color: #333333; margin-bottom: 20px;">Welcome! 👋</h2>
            <p style="color: #555555; font-size: 16px; line-height: 1.5;">
                Thank you for registering. Please click the button below to confirm your email address and activate your account:
            </p>
            <div style="margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #28a745; color: #ffffff; padding: 12px 25px; text-decoration: none; font-size: 16px; border-radius: 5px; font-weight: bold; display: inline-block;">
                    Activate Account Now
                </a>
            </div>
            <p style="color: #888888; font-size: 13px;">
                Note: This link is valid for 24 hours only.
            </p>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Confirm and Activate Your Account ✉️️",
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)
