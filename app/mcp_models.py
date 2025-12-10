# app/mcp_models.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class MCPQueryParams(BaseModel):
    collection: str
    query_texts: List[str]
    n_results: int = 5

class MCPAddTextsParams(BaseModel):
    collection: str
    ids: List[str]
    documents: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]   # vorher: str geändert zu Union[str, int]
    method: str
    params: Dict[str, Any]