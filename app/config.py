# app/config.py
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    chroma_host: str = " chroma-db" # ChromaDB server hostname
    chroma_port: int = 8000
    chroma_ssl: bool = False

    # MCP HTTP/SSE Server
    server_host: str = "0.0.0.0"
    server_port: int = 8013 # MCP server port

    class Config:
        env_file = ".env"

settings = Settings()
