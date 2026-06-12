from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = 8000
    REDIS_URL: str = "redis://localhost:6379/0"
    AGENT_API_KEY: str = "demo-key"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 10
    MONTHLY_BUDGET_USD: float = 10.0
    TOKEN_ROUTER_API_KEY: str = ""
    TOKEN_ROUTER_BASE_URL: str = "https://api.tokenrouter.com/v1"
    LLM_MODEL: str = "minimax"

settings = Settings()