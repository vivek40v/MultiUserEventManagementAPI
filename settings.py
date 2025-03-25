import os
from pydantic import Field
from pydantic_settings import BaseSettings


env_check = os.environ.get('environment', 'production')
is_prod = env_check.lower() == 'production'


class Settings(BaseSettings):
    DEBUG: bool = is_prod is False  # Enable debug mode in non-prod environments
    DOCS_URL: str = "/docs" if DEBUG else None,  # Disable docs in production
    REDOC_URL: str = "/redoc" if DEBUG else None,
    OPENAPI_URL: str = "/openapi.json" if DEBUG else None
    INTERNAL_ENDPOINTS: bool = True
    DEBUG_ENDPOINTS: bool = True

    # SOURCE DB
    SOURCE_PG_HOST: str = '127.0.0.1'
    SOURCE_PG_USER: str = 'postgres'
    SOURCE_PG_PASSWORD: str = 'postgres'
    SOURCE_PG_PORT: int = 5430
    SOURCE_PG_READ_ONLY: bool = False
    SOURCE_PG_DBNAME: str = "multiusereventmanagement"

    REDIS_USE: int = 0
    REDIS_IP: str = '127.0.0.1'
    REDIS_PORT: int = 1998
    REDIS_MAX_CONNECTIONS: int = 2
    REDIS_URL: str = f'redis://{REDIS_IP}:{REDIS_PORT}'

    kafka_autocommit: bool = False
    kafka_host: str = '127.0.0.1'
    kafka_port: int = 9092
    kafka_offset: str = "earliest"  # latest
    HEADERS: dict = {'Authorization': '', 'Content-Type': 'application/json'}


    # App
    APP_HOST: str = "127.0.0.1" if not is_prod else "0.0.0.0"
    USE_AUTH: bool = Field(default=True)
    APP_PORT: int = Field(default=8000)
    APP_WORKERS: int = Field(default=1)
    APP_TITLE: str = "My FastAPI App"
    APP_DESCRIPTION: str = "This is a FastAPI application."
    APP_VERSION: str = "1.0.0"


    host_ip: str = "127.0.0.1"
    host_port: int = 8050
    data_path: str = "data"
    logs_path: str = "logs"

    # Email Configuration
    SMTP_SERVER:str = "smtp.example.com"
    SMTP_PORT:int = 587
    SMTP_USERNAME:str = "your_email@example.com"
    SMTP_PASSWORD:str = "your_email_password"

    # Google Maps API Configuration
    GOOGLE_MAPS_API_KEY:str = "your_google_maps_api_key"


settings = Settings(_env_file='.env')  # Init in root directory only
