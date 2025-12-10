from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
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


@router.post("/")
@router.post("/mcp")
async def handle_mcp(req: MCPRequest, client=Depends(get_client)):
    # 1) Lifecycle
    if req.method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "chroma-mcp-http-server",
                    "version": "0.1.0",
                },
                "capabilities": {
                    "tools": {
                        "supported": True,
                        "listChanged": True,
                    }
                },
            },
        }

    if req.method == "notifications/initialized":
        # Notification, no response required
        return {}

    # 2) tools/list – advertise tools
    if req.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "tools": [
                    {
                        "name": "chroma.query",
                        "description": "Query documents from a Chroma collection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "collection": {"type": "string"},
                                "query_texts": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "n_results": {
                                    "type": "integer",
                                    "default": 5,
                                },
                            },
                            "required": ["collection", "query_texts"],
                        },
                    },
                    {
                        "name": "chroma.add_texts",
                        "description": "Add documents to a Chroma collection",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "collection": {"type": "string"},
                                "ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "documents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["collection", "ids", "documents"],
                        },
                    },
                ]
            },
        }

    # 3) tools/call – dispatch to your existing logic
    if req.method == "tools/call":
        tool_name = (req.params or {}).get("name")
        args = (req.params or {}).get("arguments") or {}

        if tool_name == "chroma.query":
            params = MCPQueryParams(**args)
            col = client.get_collection(params.collection)
            res = col.query(
                query_texts=params.query_texts,
                n_results=params.n_results,
            )
            return {"jsonrpc": "2.0", "id": req.id, "result": res}

        if tool_name == "chroma.add_texts":
            params = MCPAddTextsParams(**args)
            col = client.get_or_create_collection(params.collection)
            col.add(
                ids=params.ids,
                documents=params.documents,
                metadatas=params.metadatas,
            )
            return {"jsonrpc": "2.0", "id": req.id, "result": "ok"}

    # 4) Fallback: JSON-RPC error
    return JSONResponse(
        status_code=200,
        content={
            "jsonrpc": "2.0",
            "id": req.id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {req.method}",
            },
        },
    )
