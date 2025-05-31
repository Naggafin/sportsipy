from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    api_key: str = "default-mcp-key"
    port: int = 5000
    project_path: str = str(Path.cwd())
    
    class Config:
        env_prefix = "MCP_"
        case_sensitive = False

settings = Settings()