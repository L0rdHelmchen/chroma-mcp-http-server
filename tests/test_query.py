# tests/test_query.py
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app


class TestQuerySpecific:
    """Specific tests for query functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_chroma_setup(self):
        """Setup mock ChromaDB client with query-specific behavior."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection.return_value = mock_collection
        return mock_client, mock_collection

    def test_basic_query(self, client, mock_chroma_setup):
        """Test basic query functionality."""
        mock_client, mock_collection = mock_chroma_setup

        # Setup mock response
        mock_query_result = {
            "ids": [["doc1", "doc2", "doc3"]],
            "documents": [["First document", "Second document", "Third document"]],
            "metadatas": [[{"author": "Alice"}, {"author": "Bob"}, {"author": "Charlie"}]],
            "distances": [[0.1, 0.3, 0.5]]
        }
        mock_collection.query.return_value = mock_query_result

        request = {
            "jsonrpc": "2.0",
            "id": "basic-query",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "documents",
                    "query_texts": ["search term"],
                    "n_results": 3
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == mock_query_result

        # Verify ChromaDB method calls
        mock_client.get_collection.assert_called_once_with("documents")
        mock_collection.query.assert_called_once_with(
            query_texts=["search term"],
            n_results=3
        )

    def test_multiple_query_texts(self, client, mock_chroma_setup):
        """Test query with multiple query texts."""
        mock_client, mock_collection = mock_chroma_setup

        mock_query_result = {
            "ids": [["doc1", "doc2"], ["doc3", "doc4"]],
            "documents": [["Doc 1", "Doc 2"], ["Doc 3", "Doc 4"]],
            "metadatas": [[{}, {}], [{}, {}]],
            "distances": [[0.1, 0.2], [0.3, 0.4]]
        }
        mock_collection.query.return_value = mock_query_result

        request = {
            "jsonrpc": "2.0",
            "id": "multi-query",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "documents",
                    "query_texts": ["first query", "second query"],
                    "n_results": 2
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        mock_collection.query.assert_called_once_with(
            query_texts=["first query", "second query"],
            n_results=2
        )

    def test_default_n_results(self, client, mock_chroma_setup):
        """Test query with default n_results value."""
        mock_client, mock_collection = mock_chroma_setup

        mock_query_result = {
            "ids": [["doc1", "doc2", "doc3", "doc4", "doc5"]],
            "documents": [["Doc 1", "Doc 2", "Doc 3", "Doc 4", "Doc 5"]],
            "metadatas": [[{}, {}, {}, {}, {}]],
            "distances": [[0.1, 0.2, 0.3, 0.4, 0.5]]
        }
        mock_collection.query.return_value = mock_query_result

        request = {
            "jsonrpc": "2.0",
            "id": "default-results",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "documents",
                    "query_texts": ["search term"]
                    # n_results not specified, should default to 5
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        mock_collection.query.assert_called_once_with(
            query_texts=["search term"],
            n_results=5  # Default value
        )

    def test_large_n_results(self, client, mock_chroma_setup):
        """Test query with large n_results value."""
        mock_client, mock_collection = mock_chroma_setup

        mock_query_result = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        mock_collection.query.return_value = mock_query_result

        request = {
            "jsonrpc": "2.0",
            "id": "large-results",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "documents",
                    "query_texts": ["search term"],
                    "n_results": 1000
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        mock_collection.query.assert_called_once_with(
            query_texts=["search term"],
            n_results=1000
        )

    def test_empty_query_results(self, client, mock_chroma_setup):
        """Test query that returns no results."""
        mock_client, mock_collection = mock_chroma_setup

        empty_result = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        mock_collection.query.return_value = empty_result

        request = {
            "jsonrpc": "2.0",
            "id": "empty-results",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "empty_collection",
                    "query_texts": ["nonexistent term"]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == empty_result

    def test_query_with_special_characters(self, client, mock_chroma_setup):
        """Test query with special characters."""
        mock_client, mock_collection = mock_chroma_setup

        mock_query_result = {
            "ids": [["doc1"]],
            "documents": [["Document with special chars: @#$%^&*()"]],
            "metadatas": [[{}]],
            "distances": [[0.1]]
        }
        mock_collection.query.return_value = mock_query_result

        request = {
            "jsonrpc": "2.0",
            "id": "special-chars",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "special_docs",
                    "query_texts": ["query with @#$%^&*() characters"],
                    "n_results": 1
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        mock_collection.query.assert_called_once_with(
            query_texts=["query with @#$%^&*() characters"],
            n_results=1
        )

    def test_query_collection_not_found(self, client, mock_chroma_setup):
        """Test query when collection doesn't exist."""
        mock_client, _ = mock_chroma_setup
        mock_client.get_collection.side_effect = Exception("Collection not found")

        request = {
            "jsonrpc": "2.0",
            "id": "missing-collection",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "nonexistent_collection",
                    "query_texts": ["search term"]
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=request)

        assert response.status_code == 500

    def test_query_validation_errors(self, client):
        """Test query parameter validation."""
        validation_test_cases = [
            # Missing collection
            {
                "name": "chroma.query",
                "arguments": {
                    "query_texts": ["search term"]
                }
            },
            # Missing query_texts
            {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_collection"
                }
            },
            # Empty query_texts list (should be valid)
            {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_collection",
                    "query_texts": []
                }
            },
            # Invalid n_results type
            {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_collection",
                    "query_texts": ["search"],
                    "n_results": "invalid"
                }
            }
        ]

        for i, params in enumerate(validation_test_cases):
            request = {
                "jsonrpc": "2.0",
                "id": f"validation-{i}",
                "method": "tools/call",
                "params": params
            }

            response = client.post("/mcp", json=request)

            if i == 2:  # Empty query_texts should be valid
                assert response.status_code in [200, 500]  # Depends on ChromaDB mock
            else:
                assert response.status_code == 422  # Validation error

    def test_query_with_unicode_content(self, client, mock_chroma_setup):
        """Test query with Unicode content."""
        mock_client, mock_collection = mock_chroma_setup

        mock_query_result = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Document with émojis =€", "‡c+-‡…¹"]],
            "metadatas": [[{"lang": "en"}, {"lang": "zh"}]],
            "distances": [[0.1, 0.2]]
        }
        mock_collection.query.return_value = mock_query_result

        request = {
            "jsonrpc": "2.0",
            "id": "unicode-query",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "multilingual_docs",
                    "query_texts": ["å~ émojis ="],
                    "n_results": 2
                }
            }
        }

        with patch('app.routes.get_client', return_value=mock_client):
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == mock_query_result

    def test_query_response_format(self, client, mock_chroma_setup):
        """Test that query response follows MCP format."""
        mock_client, mock_collection = mock_chroma_setup

        mock_query_result = {
            "ids": [["doc1"]],
            "documents": [["Test document"]],
            "metadatas": [[{"test": "metadata"}]],
            "distances": [[0.1]]
        }
        mock_collection.query.return_value = mock_query_result

        request = {
            "jsonrpc": "2.0",
            "id": "format-test",
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
            response = client.post("/mcp", json=request)

        assert response.status_code == 200
        data = response.json()

        # Check MCP response format
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "format-test"
        assert "result" in data
        assert data["result"] == mock_query_result