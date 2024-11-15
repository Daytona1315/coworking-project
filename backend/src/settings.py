from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    server_port: int
    server_host: str

    db_url: str

    jwt_secret: str
    jwt_algorithm: str = 'HS256'
    jwt_expiration: int = 3600


settings = Settings(
    _env_file='.env',
    _env_file_encoding='utf-8',
)
