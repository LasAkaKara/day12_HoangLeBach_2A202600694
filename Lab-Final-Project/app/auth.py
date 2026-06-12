from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from .config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or api_key != settings.AGENT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return "user_123"
