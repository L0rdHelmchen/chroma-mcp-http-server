# Chroma MCP HTTP Server

A minimal [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes a running [ChromaDB](https://www.trychroma.com/) instance as MCP tools over plain HTTP for clients like Claude Code.

## Features

- HTTP MCP transport (`type: "http"`) compatible with Claude Code.
- Uses `chromadb.HttpClient` to talk to an existing Chroma server (client–server mode).
- Implements the MCP lifecycle:
    - `initialize`
    - `notifications/initialized`
    - basic tool calls: `tools/query`, `tools/add_texts` (extensible).
- Containerized via Docker/Podman for deployment on EC2 or any OCI‑compatible runtime.

Mini Python lesson: The server acts as a thin “adapter layer”: FastAPI receives MCP JSON‑RPC over HTTP, your handlers translate these into Chroma client calls, and return the results in MCP‑compatible JSON. This separation keeps HTTP transport, protocol logic, and vector‑DB access nicely decoupled.

## Architecture

- **FastAPI app** as HTTP server and MCP endpoint (`POST /` and `POST /mcp` for JSON‑RPC, `GET /` and `GET /mcp` for SSE).
- **Configuration** via Pydantic `BaseSettings` (`pydantic-settings`), reading environment variables like `CHROMA_HOST`, `CHROMA_PORT`, `CHROMA_SSL`.
- **Chroma client** created with `chromadb.HttpClient(host, port, ssl=...)`.
- **JSON‑RPC/MCP models** implemented with Pydantic, including:
    - `MCPRequest` (supports both requests and notifications)
    - `MCPQueryParams`, `MCPAddTextsParams`.


## Configuration

Environment variables:

- `CHROMA_HOST` – hostname of the Chroma server (e.g. `chroma-db` in a pod, or an internal DNS).
- `CHROMA_PORT` – Chroma HTTP port (default `8000`).
- `CHROMA_SSL` – `true` or `false` for HTTPS vs HTTP.
- `SERVER_HOST` – bind address for the MCP server (default `0.0.0.0`).
- `SERVER_PORT` – MCP HTTP port (default `8013`).

All values can be overridden via `docker run -e ...` / `podman run -e ...` or your orchestrator.

## Running locally

```bash
# Install dependencies
pip install -e .

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8013

# Verify SSE endpoint
curl -i http://127.0.0.1:8013/mcp
```

You should see a `200 OK` with `content-type: text/event-stream` and a small `event: endpoint` payload.

## Docker / Podman

The image exposes port `8013` and runs the FastAPI app with Uvicorn.

Example with Podman:

```bash
podman run -d \
  --name mcp-chroma \
  -p 8013:8013 \
  -e CHROMA_HOST=chroma-db \
  -e CHROMA_PORT=8000 \
  -e CHROMA_SSL=false \
  ghcr.io/<your-user-or-org>/chroma-mcp-http-server:latest
```

When using AWS ECR, log in first, pull the image, then run it as above.

## Claude Code configuration

In your project (e.g. `~/Documents/VektorDB/.mcp.json`):

```json
{
  "mcpServers": {
    "chroma": {
      "type": "http",
      "url": "http://<ec2ip>>:8013",
      "timeout": 60000
    }
  }
}
```

Then in Claude Code, the server should appear as `connected` under “Manage MCP servers”.

Check can be done by using Terminal curl

Wrong: ❯ curl -i http://<ec-2ip>:8013/mcp

HTTP/1.1 405 Method Not Allowed
date: Thu, 11 Dec 2025 14:19:22 GMT
server: uvicorn
allow: POST
content-length: 31
content-type: application/json

{"detail":"Method Not Allowed"}%

Right: ❯ curl -i \
  -X POST \
  -H "Content-Type: application/json" \
  http://<ec2ip>/mcp \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
  }'

HTTP/1.1 200 OK
date: Thu, 11 Dec 2025 14:20:46 GMT
server: uvicorn
content-length: 194
content-type: application/json

{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","serverInfo":{"name":"chroma-mcp-http-server","version":"0.1.0"},"capabilities":{"tools":{"supported":true,"listChanged":true}}}}%                   

## Supported MCP methods

The server currently handles:

- `initialize` – returns protocol version, server info, and tool capabilities (`tools` supported)
- `notifications/initialized` – accepted as a no‑op notification.
- `tools/query` – queries a Chroma collection with `query_texts` and `n_results`.
- `tools/add_texts` – adds documents and optional metadata to a collection (creating it if needed).

Extending the server with more MCP tools (e.g. `tools/list_collections`, `tools/delete`) follows the same pattern: add Pydantic param models, branch on `req.method` in the handler, and call the appropriate Chroma client APIs.

## Development

- Python ≥ 3.11
- FastAPI + Uvicorn for HTTP server.
- Pydantic v2 + `pydantic-settings` for typed config and request validation.
- `chromadb` (or `chromadb-client`) for talking to your Chroma deployment.

Run tests (if you add them):

```bash
pytest
```

Linting example:

```bash
ruff check .
```


***
