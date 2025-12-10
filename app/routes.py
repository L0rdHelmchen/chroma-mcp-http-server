# app/routes.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Callable, Dict, Any
from app.mcp_models import MCPRequest, MCPQueryParams, MCPAddTextsParams
from app.config import settings
from app.chromaclient import get_chroma_client

router = APIRouter()


def get_client():
    return get_chroma_client(
        host=settings.chroma_host,
        port=settings.chroma_port,
        ssl=settings.chroma_ssl,
    )

# --- MCP JSON-RPC: POST / und POST /mcp ---

@router.post("/")
@router.post("/mcp")
async def handle_mcp(req: MCPRequest, client=Depends(get_client)):
    if req.method == "tools/query":
        params = MCPQueryParams(**req.params)
        col = client.get_collection(params.collection)
        res = col.query(
            query_texts=params.query_texts,
            n_results=params.n_results,
        )
        return {"jsonrpc": "2.0", "id": req.id, "result": res}

    if req.method == "tools/add_texts":
        params = MCPAddTextsParams(**req.params)
        col = client.get_or_create_collection(params.collection)
        col.add(
            ids=params.ids,
            documents=params.documents,
            metadatas=params.metadatas,
        )
        return {"jsonrpc": "2.0", "id": req.id, "result": "ok"}

    raise HTTPException(status_code=400, detail="Unknown method")


# --- SSE: GET / und GET /mcp ---

@router.get("/")
@router.get("/mcp")
async def sse_stream():
    async def event_generator():
        yield "event: endpoint\ndata: {}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")