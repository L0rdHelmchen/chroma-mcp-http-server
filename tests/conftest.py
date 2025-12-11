# tests/conftest.py
"""
Global pytest configuration and shared fixtures.
"""
import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_chroma_client():
    """Create a mock ChromaDB client."""
    client = Mock()
    collection = Mock()

    # Setup default behavior
    client.get_collection.return_value = collection
    client.get_or_create_collection.return_value = collection

    # Default query response
    collection.query.return_value = {
        "ids": [["doc1"]],
        "documents": [["Test document"]],
        "metadatas": [[{}]],
        "distances": [[0.1]]
    }

    return client, collection


@pytest.fixture
def mock_settings():
    """Create mock settings with test values."""
    settings = Mock(spec=Settings)
    settings.chroma_host = "test-host"
    settings.chroma_port = 8000
    settings.chroma_ssl = False
    settings.server_host = "0.0.0.0"
    settings.server_port = 8013
    return settings


@pytest.fixture
def clean_env():
    """Provide a clean environment for tests."""
    # Save original environment
    original_env = dict(os.environ)

    # Clear relevant environment variables
    env_vars_to_clear = [
        "CHROMA_HOST", "CHROMA_PORT", "CHROMA_SSL",
        "SERVER_HOST", "SERVER_PORT"
    ]

    for var in env_vars_to_clear:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_mcp_requests():
    """Provide sample MCP request data for testing."""
    return {
        "initialize": {
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize"
        },
        "tools_list": {
            "jsonrpc": "2.0",
            "id": "tools-1",
            "method": "tools/list"
        },
        "query_tool": {
            "jsonrpc": "2.0",
            "id": "query-1",
            "method": "tools/call",
            "params": {
                "name": "chroma.query",
                "arguments": {
                    "collection": "test_collection",
                    "query_texts": ["test query"],
                    "n_results": 5
                }
            }
        },
        "add_texts_tool": {
            "jsonrpc": "2.0",
            "id": "add-1",
            "method": "tools/call",
            "params": {
                "name": "chroma.add_texts",
                "arguments": {
                    "collection": "test_collection",
                    "ids": ["doc1"],
                    "documents": ["Test document"]
                }
            }
        }
    }


@pytest.fixture
def sample_chroma_responses():
    """Provide sample ChromaDB response data for testing."""
    return {
        "empty_query": {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        },
        "single_result": {
            "ids": [["doc1"]],
            "documents": [["Single test document"]],
            "metadatas": [[{"type": "test"}]],
            "distances": [[0.1]]
        },
        "multiple_results": {
            "ids": [["doc1", "doc2", "doc3"]],
            "documents": [["First doc", "Second doc", "Third doc"]],
            "metadatas": [[{"type": "test"}, {"type": "test"}, {"type": "test"}]],
            "distances": [[0.1, 0.3, 0.5]]
        }
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location/name."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark unit tests (default for most tests)
        if not any(marker.name in ["integration", "slow"] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


@pytest.fixture(autouse=True)
def patch_get_client():
    """Automatically patch get_client dependency in routes for all tests."""
    with patch('app.routes.get_client') as mock:
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_client.get_or_create_collection.return_value = mock_collection
        mock.return_value = mock_client
        yield mock_client, mock_collection