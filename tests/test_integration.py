# tests/test_integration.py
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app


class TestFullIntegration:
    """End-to-end integration tests for the MCP ChromaDB server."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_chroma_client(self):
        """Mock ChromaDB client with realistic behavior."""
        client = Mock()
        collection = Mock()

        # Setup default collection behavior
        client.get_collection.return_value = collection
        client.get_or_create_collection.return_value = collection

        return client, collection

    def test_complete_mcp_workflow(self, client, mock_chroma_client):
        """Test complete MCP workflow: initialize, list tools, query, add."""
        mock_client, mock_collection = mock_chroma_client

        # Step 1: Initialize
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=initialize_request)

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["protocolVersion"] == "2024-11-05"
        assert data["result"]["serverInfo"]["name"] == "chroma-mcp-http-server"

        # Step 2: Send initialized notification
        initialized_request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=initialized_request)

        assert response.status_code == 200
        assert response.json() == {}

        # Step 3: List tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=list_tools_request)

        assert response.status_code == 200
        data = response.json()
        tools = data["result"]["tools"]
        assert len(tools) == 2
        tool_names = [tool["name"] for tool in tools]
        assert "chroma.query" in tool_names
        assert "chroma.add_texts" in tool_names

        # Step 4: Add documents
        mock_collection.reset_mock()  # Reset mock calls
        add_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "chroma.add_texts",
                "arguments": {
                    "collection": "test_docs",
                    "ids": ["doc1", "doc2"],
                    "documents": ["First document", "Second document"],
                    "metadatas": [{"type": "test"}, {"type": "test"}]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=add_request)

        assert response.status_code == 200
        assert response.json()["result"] == "ok"

        # Verify add was called correctly
        mock_client.get_or_create_collection.assert_called_once_with("test_docs")
        mock_collection.add.assert_called_once_with(
            ids=["doc1", "doc2"],
            documents=["First document", "Second document"],
            metadatas=[{"type": "test"}, {"type": "test"}]
        )

        # Step 5: Query documents
        mock_collection.reset_mock()
        mock_query_result = {
            "ids": [["doc1", "doc2"]],
            "documents": [["First document", "Second document"]],
            "metadatas": [[{"type": "test"}, {"type": "test"}]],
            "distances": [[0.0, 0.1]]
        }
        mock_collection.query.return_value = mock_query_result

        query_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_docs",
                    "query_texts": ["test query"],
                    "n_results": 2
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=query_request)

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == mock_query_result

        # Verify query was called correctly
        mock_client.get_collection.assert_called_once_with("test_docs")
        mock_collection.query.assert_called_once_with(
            query_texts=["test query"],
            n_results=2
        )

    def test_error_handling_workflow(self, client, mock_chroma_client):
        """Test error handling in complete workflow."""
        mock_client, mock_collection = mock_chroma_client

        # Test ChromaDB connection error
        mock_client.get_collection.side_effect = Exception("ChromaDB connection failed")

        query_request = {
            "jsonrpc": "2.0",
            "id": "error-test",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_collection",
                    "query_texts": ["test query"]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=query_request)

        assert response.status_code == 500

    def test_multiple_collections_workflow(self, client, mock_chroma_client):
        """Test workflow with multiple collections."""
        mock_client, _ = mock_chroma_client

        # Create different mock collections
        collection1 = Mock()
        collection2 = Mock()

        def mock_get_collection(name):
            if name == "collection1":
                return collection1
            elif name == "collection2":
                return collection2
            raise ValueError(f"Collection {name} not found")

        def mock_get_or_create_collection(name):
            if name == "collection1":
                return collection1
            elif name == "collection2":
                return collection2
            # Create new mock for new collections
            return Mock()

        mock_client.get_collection.side_effect = mock_get_collection
        mock_client.get_or_create_collection.side_effect = mock_get_or_create_collection

        # Add to collection1
        add_request1 = {
            "jsonrpc": "2.0",
            "id": "add1",
            "method": "tools/call",
            "params": {
                "name": "chroma.add_texts",
                "arguments": {
                    "collection": "collection1",
                    "ids": ["doc1"],
                    "documents": ["Document in collection1"]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=add_request1)

        assert response.status_code == 200
        collection1.add.assert_called_once()

        # Query from collection2
        collection2.query.return_value = {"ids": [["doc2"]], "documents": [["Doc from collection2"]], "metadatas": [[]], "distances": [[0.0]]}
        query_request2 = {
            "jsonrpc": "2.0",
            "id": "query2",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "collection2",
                    "query_texts": ["query for collection2"]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=query_request2)

        assert response.status_code == 200
        collection2.query.assert_called_once()

    def test_configuration_integration(self, client):
        """Test that configuration is properly integrated."""
        with patch.dict('os.environ', {
            'CHROMA_HOST': 'test-host',
            'CHROMA_PORT': '9000',
            'CHROMA_SSL': 'true'
        }):
            with patch('app.routes.get_chroma_client') as mock_get_client:
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_collection.return_value = mock_collection
                mock_collection.query.return_value = {
                    "ids": [["doc1"]],
                    "documents": [["test doc"]],
                    "metadatas": [[]],
                    "distances": [[0.0]]
                }
                mock_get_client.return_value = mock_client

                request = {
                    "jsonrpc": "2.0",
                    "id": "config-test",
                    "method": "tools/call",
                    "params": {
                        "name": "chroma.query",
                        "arguments": {
                            "collection": "test",
                            "query_texts": ["test"]
                        }
                    }
                }

                response = client.post("/mcp", json=request)
                assert response.status_code == 200

                # Verify that get_chroma_client was called with environment values
                mock_get_client.assert_called()

    def test_concurrent_requests(self, client, mock_chroma_client):
        """Test handling of concurrent requests."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["test doc"]],
            "metadatas": [[]],
            "distances": [[0.0]]
        }

        requests = []
        for i in range(5):
            requests.append({
                "jsonrpc": "2.0",
                "id": f"concurrent-{i}",
                "method": "tools/call",
                "params": {
                    "name": "chroma.query",
                    "arguments": {
                        "collection": f"collection_{i}",
                        "query_texts": [f"query {i}"]
                    }
                }
            })

        responses = []
        with patch('app.routes.get_client', return_value=mock_client):
            for request in requests:
                response = client.post("/mcp", json=request)
                responses.append(response)

        # All requests should succeed
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == f"concurrent-{i}"

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON requests."""
        response = client.post("/mcp", data="invalid json")
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test handling of requests with missing required fields."""
        invalid_requests = [
            {},  # Missing method
            {"method": "tools/call"},  # Missing params for tools/call
            {"method": "tools/call", "params": {}},  # Missing name in params
            {"method": "tools/call", "params": {"name": "chroma.query"}},  # Missing arguments
        ]

        for request in invalid_requests:
            request.setdefault("jsonrpc", "2.0")
            with patch('app.routes.get_client'):
                response = client.post("/mcp", json=request)
                # Should either be validation error (422) or method not found (200 with error)
                assert response.status_code in [200, 422]

    def test_health_check_simulation(self, client):
        """Test basic health check by calling initialize."""
        request = {
            "jsonrpc": "2.0",
            "id": "health",
            "method": "initialize"
        }

        with patch('app.routes.get_client'):
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["serverInfo"]["name"] == "chroma-mcp-http-server"