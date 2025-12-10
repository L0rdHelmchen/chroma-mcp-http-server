# app/main.py
from fastapi import FastAPI
from app.routes import router
from app.config import settings

app = FastAPI(title="Chroma MCP HTTP/SSE Server")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
    )
