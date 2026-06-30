from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Shop Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://shop:shop123@localhost:5432/shop_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Order timeout
    ORDER_TIMEOUT_MINUTES: int = 30

    # Cache TTL (seconds)
    CACHE_TTL_HOT_PRODUCTS: int = 600
    CACHE_TTL_PRODUCT_DETAIL: int = 600
    CACHE_TTL_CATEGORY_TREE: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
