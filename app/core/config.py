"""Configuration settings for the application."""
import os
from typing import List, Optional
from pydantic import BaseModel

class Settings(BaseModel):
    """Application settings."""
    api_host: str = os.environ.get("API_HOST", "localhost")
    api_port: int = int(os.environ.get("API_PORT", "8000"))
    api_workers: int = int(os.environ.get("API_WORKERS", "1"))
    debug: bool = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")
    api_secret_key: str = os.environ.get("API_SECRET_KEY", "default-secret-key")
    allow_origins: List[str] = []
    
    def __init__(self, **data):
        super().__init__(**data)
        # Parse ALLOW_ORIGINS from environment variable
        allow_origins_str = os.environ.get("ALLOW_ORIGINS", "")
        if allow_origins_str:
            self.allow_origins = [origin.strip() for origin in allow_origins_str.split(",")]
    
    # Azure OpenAI configuration
    azure_openai_api_key: Optional[str] = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
    azure_openai_deployment: str = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    azure_openai_embedding_deployment: str = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
    
    # Policies directory
    policies_dir: str = os.environ.get("POLICIES_DIR", "./policies")
    policies_db_dir: str = os.environ.get("POLICIES_DB_DIR", "./policies/chroma_db")

# Create an instance of Settings
settings = Settings()