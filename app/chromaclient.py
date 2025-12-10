# app/chromaclient.py
import chromadb
from chromadb.config import Settings

def get_chroma_client(host: str, port: int, ssl: bool):
    return chromadb.HttpClient(
        host=host,
        port=port,
        ssl=ssl,
        settings=Settings()
    )
