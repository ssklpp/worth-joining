from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SPEC 3장 환경 변수. `.env`에서 읽고, 같은 이름의 환경 변수가 있으면 그것이 우선한다."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    database_url_sync: str
    test_database_url: str = ""
    db_ssl_verify: bool = True

    # 비어 있으면 해당 수집기는 경고 후 건너뛴다(SPEC 3장)
    data_go_kr_service_key: str = ""
    seoul_opendata_key: str = ""
    opendart_api_key: str = ""
    juso_search_key: str = ""
    juso_coord_key: str = ""
    saramin_access_key: str = ""


settings = Settings()
