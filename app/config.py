from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str

    # Security & JWT Token
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email Service Configuration
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"



    FIRST_ADMIN_EMAIL: str 
    FIRST_ADMIN_PASSWORD: str

    # Payment Gateway Configuration (Stripe)
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    BASE_URL: str = "http://127.0.0.1:8000"

    # Dynamic Method to generate verification URL with token
    def get_verification_link(self, token: str) -> str:
        """
        Generates the email verification link with a dynamic token.
        """
        return f"{self.BASE_URL}/users/verify-email?token={token}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()