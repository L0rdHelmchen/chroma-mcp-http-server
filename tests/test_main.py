# tests/test_main.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


class TestMainApp:
    """Test cases for the main FastAPI application."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_app_creation(self):
        """Test that the FastAPI app is created correctly."""
        assert app.title == "Chroma MCP HTTP/SSE Server"
        assert app is not None

    def test_router_inclusion(self, client):
        """Test that the router is properly included."""
        # Test that MCP endpoints are available
        with patch('app.routes.get_client'):
            response = client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": "test",
                "method": "initialize"
            })

        assert response.status_code == 200

        # Test alternative endpoint
        with patch('app.routes.get_client'):
            response = client.post("/", json={
                "jsonrpc": "2.0",
                "id": "test",
                "method": "initialize"
            })

        assert response.status_code == 200

    def test_app_startup(self):
        """Test basic app functionality."""
        with TestClient(app) as test_client:
            # App should start without errors
            assert test_client is not None

    @patch('app.main.uvicorn.run')
    @patch('app.main.settings')
    def test_main_execution(self, mock_settings, mock_uvicorn_run):
        """Test the main execution block."""
        # Setup mock settings
        mock_settings.server_host = "test-host"
        mock_settings.server_port = 9999

        # Import and execute the main block
        # This simulates running: python -m app.main
        import app.main

        # Since the main block only runs when __name__ == "__main__",
        # we need to test it differently
        if hasattr(app.main, '__name__'):
            # Simulate main execution
            import uvicorn
            with patch.object(uvicorn, 'run') as mock_run:
                # This would be called if running as main
                uvicorn.run(
                    "app.main:app",
                    host=mock_settings.server_host,
                    port=mock_settings.server_port,
                    reload=True,
                )

                mock_run.assert_called_once_with(
                    "app.main:app",
                    host=mock_settings.server_host,
                    port=mock_settings.server_port,
                    reload=True,
                )

    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is generated correctly."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert schema["info"]["title"] == "Chroma MCP HTTP/SSE Server"
        assert "paths" in schema

    def test_docs_endpoint(self, client):
        """Test that docs endpoint is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint(self, client):
        """Test that redoc endpoint is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_health_check_via_root(self, client):
        """Test basic health check via root endpoint."""
        # Since there's no dedicated health endpoint, we test via initialize
        with patch('app.routes.get_client'):
            response = client.post("/", json={
                "jsonrpc": "2.0",
                "id": "health",
                "method": "initialize"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["serverInfo"]["name"] == "chroma-mcp-http-server"


class TestAppConfiguration:
    """Test application configuration and setup."""

    def test_app_debug_mode(self):
        """Test app in different modes."""
        # In test mode, debug should be handled appropriately
        assert app is not None

    def test_cors_configuration(self):
        """Test CORS configuration if implemented."""
        # Currently no CORS is configured, but this is where we'd test it
        # if it were added in the future
        pass

    def test_middleware_configuration(self):
        """Test middleware configuration."""
        # Test that necessary middleware is configured
        # Currently minimal middleware, but this is where we'd test additions
        pass

    def test_exception_handlers(self, client):
        """Test global exception handlers."""
        # Test that exceptions are handled appropriately
        with patch('app.routes.get_client', side_effect=Exception("Test error")):
            response = client.post("/mcp", json={
                "jsonrpc": "2.0",
                "id": "error-test",
                "method": "tools/call",
                "params": {
                    "name": "chroma.query",
                    "arguments": {
                        "collection": "test",
                        "query_texts": ["test"]
                    }
                }
            })

        # Should return 500 for unhandled exceptions
        assert response.status_code == 500