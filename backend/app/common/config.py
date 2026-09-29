from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Consult Support System"

    # 표시용 브랜딩. 공개 저장소라 실제 법인명·자산 URL 은 두지 않는다.
    # 운영 환경에서는 .env 로 덮어쓴다.
    FIRM_NAME: str = "법무법인"
    LAWYER_IMAGE_BASE_URL: str = ""
    DATABASE_URL: str = ""
    OPENAI_API_KEY: str = ""

    SEARCH_TOP_K: int = 100
    SEARCH_SCORE_THRESHOLD: float = 0.015

    GROK_API_URL: str = ""
    DEBUG: bool = False

    ES_HOST: str = "http://localhost:9200"
    EMBEDDING_MODEL_NAME: str = "nlpai-lab/KURE-v1"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()