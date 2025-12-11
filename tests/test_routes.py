# tests/test_routes.py
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.routes import router, get_client
from app.main import app


class TestMCPRoutes:
    """Test cases for MCP protocol routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_chroma_client(self):
        """Mock ChromaDB client."""
        return Mock()

    @pytest.fixture
    def mock_collection(self):
        """Mock ChromaDB collection."""
        return Mock()

    def test_initialize_method(self, client):
        """Test initialize method response."""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "method": "initialize"
        }

        with patch('app.routes.get_client'):
            response = client.post("/mcp", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-123"
        assert "result" in data
        assert data["result"]["protocolVersion"] == "2024-11-05"
        assert data["result"]["serverInfo"]["name"] == "chroma-mcp-http-server"
        assert data["result"]["serverInfo"]["version"] == "0.1.0"
        assert data["result"]["capabilities"]["tools"]["supported"] is True

    def test_notifications_initialized(self, client):
        """Test notifications/initialized method."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }

        with patch('app.routes.get_client'):
            response = client.post("/", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data == {}

    def test_tools_list_method(self, client):
        """Test tools/list method response."""
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-456",
            "method": "tools/list"
        }

        with patch('app.routes.get_client'):
            response = client.post("/mcp", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-456"
        assert "result" in data
        assert "tools" in data["result"]

        tools = data["result"]["tools"]
        assert len(tools) == 2

        # Check chroma.query tool
        query_tool = next(tool for tool in tools if tool["name"] == "chroma.query")
        assert query_tool["description"] == "Query documents from a Chroma collection"
        assert "inputSchema" in query_tool
        assert query_tool["inputSchema"]["required"] == ["collection", "query_texts"]

        # Check chroma.add_texts tool
        add_tool = next(tool for tool in tools if tool["name"] == "chroma.add_texts")
        assert add_tool["description"] == "Add documents to a Chroma collection"
        assert "inputSchema" in add_tool
        assert add_tool["inputSchema"]["required"] == ["collection", "ids", "documents"]

    def test_chroma_query_tool_call(self, client, mock_chroma_client, mock_collection):
        """Test chroma.query tool call."""
        # Setup mocks
        mock_query_result = {
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"key": "value"}, None]],
            "distances": [[0.1, 0.2]]
        }
        mock_collection.query.return_value = mock_query_result
        mock_chroma_client.get_collection.return_value = mock_collection

        request_data = {
            "jsonrpc": "2.0",
            "id": "query-test",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_collection",
                    "query_texts": ["test query"],
                    "n_results": 3
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_chroma_client):
            response = client.post("/", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "query-test"
        assert data["result"] == mock_query_result

        # Verify ChromaDB calls
        mock_chroma_client.get_collection.assert_called_once_with("test_collection")
        mock_collection.query.assert_called_once_with(
            query_texts=["test query"],
            n_results=3
        )

    def test_chroma_add_texts_tool_call(self, client, mock_chroma_client, mock_collection):
        """Test chroma.add_texts tool call."""
        mock_chroma_client.get_or_create_collection.return_value = mock_collection

        request_data = {
            "jsonrpc": "2.0",
            "id": "add-test",
            "method": "tools/call",
            "params": {
                "name": "chroma.add_texts",
                "arguments": {
                    "collection": "test_collection",
                    "ids": ["id1", "id2"],
                    "documents": ["doc1", "doc2"],
                    "metadatas": [{"key": "value"}, {"key2": "value2"}]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_chroma_client):
            response = client.post("/mcp", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "add-test"
        assert data["result"] == "ok"

        # Verify ChromaDB calls
        mock_chroma_client.get_or_create_collection.assert_called_once_with("test_collection")
        mock_collection.add.assert_called_once_with(
            ids=["id1", "id2"],
            documents=["doc1", "doc2"],
            metadatas=[{"key": "value"}, {"key2": "value2"}]
        )

    def test_chroma_add_texts_without_metadata(self, client, mock_chroma_client, mock_collection):
        """Test chroma.add_texts tool call without metadata."""
        mock_chroma_client.get_or_create_collection.return_value = mock_collection

        request_data = {
            "jsonrpc": "2.0",
            "id": "add-no-meta",
            "method": "tools/call",
            "params": {
                "name": "chroma.add_texts",
                "arguments": {
                    "collection": "test_collection",
                    "ids": ["id1"],
                    "documents": ["doc1"]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_chroma_client):
            response = client.post("/", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "ok"

        # Verify ChromaDB calls - metadatas should be None
        mock_collection.add.assert_called_once_with(
            ids=["id1"],
            documents=["doc1"],
            metadatas=None
        )

    def test_unknown_tool_call(self, client):
        """Test unknown tool call returns error."""
        request_data = {
            "jsonrpc": "2.0",
            "id": "unknown-test",
            "method": "tools/call",
            "params": {
                "name": "unknown.tool",
                "arguments": {}
            }
        }

        with patch('app.routes.get_client'):
            response = client.post("/mcp", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "unknown-test"
        assert "error" in data
        # Should fall through to method not found

    def test_unknown_method(self, client):
        """Test unknown method returns JSON-RPC error."""
        request_data = {
            "jsonrpc": "2.0",
            "id": "error-test",
            "method": "unknown/method"
        }

        with patch('app.routes.get_client'):
            response = client.post("/", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "error-test"
        assert "error" in data
        assert data["error"]["code"] == -32601
        assert "Method not found" in data["error"]["message"]
        assert "unknown/method" in data["error"]["message"]

    def test_request_without_id(self, client):
        """Test request without ID."""
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize"
        }

        with patch('app.routes.get_client'):
            response = client.post("/mcp", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] is None

    def test_invalid_query_params(self, client, mock_chroma_client):
        """Test chroma.query with invalid parameters."""
        request_data = {
            "jsonrpc": "2.0",
            "id": "invalid-query",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_collection"
                    # Missing required query_texts
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_chroma_client):
            response = client.post("/", json=request_data)

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_invalid_add_texts_params(self, client, mock_chroma_client):
        """Test chroma.add_texts with invalid parameters."""
        request_data = {
            "jsonrpc": "2.0",
            "id": "invalid-add",
            "method": "tools/call",
            "params": {
                "name": "chroma.add_texts",
                "arguments": {
                    "collection": "test_collection"
                    # Missing required ids and documents
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_chroma_client):
            response = client.post("/mcp", json=request_data)

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_chroma_client_exception(self, client, mock_chroma_client):
        """Test handling of ChromaDB client exceptions."""
        mock_chroma_client.get_collection.side_effect = Exception("ChromaDB error")

        request_data = {
            "jsonrpc": "2.0",
            "id": "exception-test",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_collection",
                    "query_texts": ["test query"]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_chroma_client):
            response = client.post("/", json=request_data)

        # The exception should propagate and result in 500 error
        assert response.status_code == 500


class TestGetClientDependency:
    """Test the get_client dependency function."""

    @patch('app.routes.get_chroma_client')
    @patch('app.routes.settings')
    def test_get_client_calls_with_settings(self, mock_settings, mock_get_chroma_client):
        """Test that get_client uses settings correctly."""
        # Setup mock settings
        mock_settings.chroma_host = "test-host"
        mock_settings.chroma_port = 9000
        mock_settings.chroma_ssl = True

        mock_client = Mock()
        mock_get_chroma_client.return_value = mock_client

        # Call the dependency function
        result = get_client()

        # Verify correct calls
        mock_get_chroma_client.assert_called_once_with(
            host="test-host",
            port=9000,
            ssl=True
        )
        assert result == mock_client

    @patch('app.routes.get_chroma_client')
    @patch('app.routes.settings')
    def test_get_client_with_different_settings(self, mock_settings, mock_get_chroma_client):
        """Test get_client with different settings values."""
        # Setup different mock settings
        mock_settings.chroma_host = "localhost"
        mock_settings.chroma_port = 8000
        mock_settings.chroma_ssl = False

        mock_client = Mock()
        mock_get_chroma_client.return_value = mock_client

        # Call the dependency function
        result = get_client()

        # Verify correct calls
        mock_get_chroma_client.assert_called_once_with(
            host="localhost",
            port=8000,
            ssl=False
        )
        assert result == mock_client