# tests/test_mcp_models.py
import pytest
from pydantic import ValidationError
from app.mcp_models import MCPQueryParams, MCPAddTextsParams, MCPRequest


class TestMCPQueryParams:
    """Test cases for MCPQueryParams model."""

    def test_valid_query_params(self):
        """Test valid query parameters."""
        params = MCPQueryParams(
            collection="test_collection",
            query_texts=["query text 1", "query text 2"],
            n_results=10
        )
        assert params.collection == "test_collection"
        assert params.query_texts == ["query text 1", "query text 2"]
        assert params.n_results == 10

    def test_default_n_results(self):
        """Test default value for n_results."""
        params = MCPQueryParams(
            collection="test_collection",
            query_texts=["query text"]
        )
        assert params.n_results == 5

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            MCPQueryParams()

        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "collection" in error_fields
        assert "query_texts" in error_fields

    def test_empty_query_texts(self):
        """Test validation with empty query_texts list."""
        params = MCPQueryParams(
            collection="test_collection",
            query_texts=[]
        )
        assert params.query_texts == []

    def test_invalid_types(self):
        """Test validation with invalid types."""
        with pytest.raises(ValidationError):
            MCPQueryParams(
                collection=123,  # Should be string
                query_texts="not a list"  # Should be list
            )


class TestMCPAddTextsParams:
    """Test cases for MCPAddTextsParams model."""

    def test_valid_add_texts_params(self):
        """Test valid add texts parameters."""
        params = MCPAddTextsParams(
            collection="test_collection",
            ids=["id1", "id2"],
            documents=["doc1", "doc2"],
            metadatas=[{"key": "value"}, {"key2": "value2"}]
        )
        assert params.collection == "test_collection"
        assert params.ids == ["id1", "id2"]
        assert params.documents == ["doc1", "doc2"]
        assert params.metadatas == [{"key": "value"}, {"key2": "value2"}]

    def test_optional_metadatas(self):
        """Test that metadatas is optional."""
        params = MCPAddTextsParams(
            collection="test_collection",
            ids=["id1"],
            documents=["doc1"]
        )
        assert params.metadatas is None

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            MCPAddTextsParams(collection="test")

        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "ids" in error_fields
        assert "documents" in error_fields

    def test_mismatched_ids_documents_length(self):
        """Test with mismatched lengths of ids and documents."""
        # This should still validate as the model doesn't enforce length matching
        params = MCPAddTextsParams(
            collection="test_collection",
            ids=["id1"],
            documents=["doc1", "doc2"]  # Different length
        )
        assert len(params.ids) == 1
        assert len(params.documents) == 2

    def test_empty_lists(self):
        """Test with empty lists."""
        params = MCPAddTextsParams(
            collection="test_collection",
            ids=[],
            documents=[]
        )
        assert params.ids == []
        assert params.documents == []


class TestMCPRequest:
    """Test cases for MCPRequest model."""

    def test_valid_request(self):
        """Test valid MCP request."""
        request = MCPRequest(
            jsonrpc="2.0",
            id="test-123",
            method="initialize",
            params={"test": "value"}
        )
        assert request.jsonrpc == "2.0"
        assert request.id == "test-123"
        assert request.method == "initialize"
        assert request.params == {"test": "value"}

    def test_default_jsonrpc(self):
        """Test default jsonrpc value."""
        request = MCPRequest(method="test")
        assert request.jsonrpc == "2.0"

    def test_optional_fields(self):
        """Test optional fields."""
        request = MCPRequest(method="test")
        assert request.id is None
        assert request.params is None

    def test_id_types(self):
        """Test different ID types."""
        # String ID
        request1 = MCPRequest(method="test", id="string-id")
        assert request1.id == "string-id"

        # Integer ID
        request2 = MCPRequest(method="test", id=123)
        assert request2.id == 123

        # None ID
        request3 = MCPRequest(method="test", id=None)
        assert request3.id is None

    def test_missing_method(self):
        """Test validation error when method is missing."""
        with pytest.raises(ValidationError) as exc_info:
            MCPRequest()

        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "method" in error_fields

    def test_invalid_jsonrpc_version(self):
        """Test with invalid jsonrpc version."""
        # The model doesn't enforce jsonrpc version, so this should pass
        request = MCPRequest(jsonrpc="1.0", method="test")
        assert request.jsonrpc == "1.0"


class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_query_params_in_mcp_request(self):
        """Test using query params in MCP request."""
        query_params = {
            "collection": "test_collection",
            "query_texts": ["test query"],
            "n_results": 3
        }

        request = MCPRequest(
            method="tools/call",
            params={
                "name": "chroma.query",
                "arguments": query_params
            }
        )

        # Extract and validate the nested query params
        args = request.params["arguments"]
        validated_params = MCPQueryParams(**args)

        assert validated_params.collection == "test_collection"
        assert validated_params.query_texts == ["test query"]
        assert validated_params.n_results == 3

    def test_add_texts_params_in_mcp_request(self):
        """Test using add texts params in MCP request."""
        add_params = {
            "collection": "test_collection",
            "ids": ["doc1"],
            "documents": ["Document content"]
        }

        request = MCPRequest(
            method="tools/call",
            params={
                "name": "chroma.add_texts",
                "arguments": add_params
            }
        )

        # Extract and validate the nested add params
        args = request.params["arguments"]
        validated_params = MCPAddTextsParams(**args)

        assert validated_params.collection == "test_collection"
        assert validated_params.ids == ["doc1"]
        assert validated_params.documents == ["Document content"]
        assert validated_params.metadatas is None