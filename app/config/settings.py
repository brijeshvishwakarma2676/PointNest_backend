from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DATABASE: str
    SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE: int
    REFRESH_TOKEN_EXPIRE: int = 7  # Days

    APP_NAME: str = "PointNest"
    VERSION: str = "1.0.0"
    PORT: int = 8000
    IS_PROD: bool = False
    POINTS_PER_RUPEE: int = 10  # 10 points = 1 INR (override in .env)

    # Outbound Email Service (Vercel Integration)
    EMAIL_SERVICE_URL: str = "https://email-service-gamma-steel.vercel.app/api/v1/send"
    EMAIL_SERVICE_API_KEY: str = "pointnest-secure-email-key-2026"
    STATIC_OTP: str = ""


    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"

    class Config:
        env_file = ".env"


settings = Settings()
