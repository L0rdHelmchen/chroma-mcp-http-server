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

    # Neu: MCP-konformes Error-Result statt HTTP 400
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
