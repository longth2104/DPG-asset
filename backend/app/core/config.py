from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    REDIS_URL: str = "redis://redis:6379"

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "asset-uploads"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_ALLOWED_DOMAIN: str = ""

    SEED_ADMIN_EMAIL: str = ""
    SEED_ADMIN_PASSWORD: str = ""

    HRIS_BASE_URL: str = ""
    HRIS_EMPLOYEES_PATH: str = "/api/v1/api-keys/directory/employees"
    HRIS_API_KEY: str = ""

    RDS_BASE_URL: str = ""
    RDS_CATEGORIES_PATH: str = "/api/v1/categories/tscd"
    RDS_API_KEY: str = ""

    # Inbound key for the e-office (datphuong.vn) integration — the reverse
    # direction from HRIS/RDS above: e-office calls *into* AMS, authenticating
    # with this key as "Authorization: Bearer <key>". Empty disables the
    # integration (all /api/eoffice/* calls 503).
    EOFFICE_API_KEY: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
