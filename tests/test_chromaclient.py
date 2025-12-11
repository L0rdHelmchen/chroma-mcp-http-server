# tests/test_chromaclient.py
import pytest
from unittest.mock import Mock, patch
from app.chromaclient import get_chroma_client


class TestChromaClient:
    """Test cases for ChromaDB client functions."""

    @patch('app.chromaclient.chromadb.HttpClient')
    @patch('app.chromaclient.Settings')
    def test_get_chroma_client_creation(self, mock_settings, mock_http_client):
        """Test ChromaDB client creation with correct parameters."""
        # Arrange
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance

        host = "localhost"
        port = 8000
        ssl = False

        # Act
        result = get_chroma_client(host, port, ssl)

        # Assert
        mock_settings.assert_called_once()
        mock_http_client.assert_called_once_with(
            host=host,
            port=port,
            ssl=ssl,
            settings=mock_settings_instance
        )
        assert result == mock_client_instance

    @patch('app.chromaclient.chromadb.HttpClient')
    @patch('app.chromaclient.Settings')
    def test_get_chroma_client_with_ssl(self, mock_settings, mock_http_client):
        """Test ChromaDB client creation with SSL enabled."""
        # Arrange
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance

        host = "secure-host.com"
        port = 443
        ssl = True

        # Act
        result = get_chroma_client(host, port, ssl)

        # Assert
        mock_http_client.assert_called_once_with(
            host=host,
            port=port,
            ssl=ssl,
            settings=mock_settings_instance
        )
        assert result == mock_client_instance

    @patch('app.chromaclient.chromadb.HttpClient')
    @patch('app.chromaclient.Settings')
    def test_get_chroma_client_different_ports(self, mock_settings, mock_http_client):
        """Test ChromaDB client creation with different port values."""
        # Arrange
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance

        test_cases = [
            ("localhost", 8000, False),
            ("example.com", 9000, True),
            ("192.168.1.1", 5000, False),
        ]

        for host, port, ssl in test_cases:
            # Act
            result = get_chroma_client(host, port, ssl)

            # Assert
            mock_http_client.assert_called_with(
                host=host,
                port=port,
                ssl=ssl,
                settings=mock_settings_instance
            )
            assert result == mock_client_instance

    @patch('app.chromaclient.chromadb.HttpClient')
    @patch('app.chromaclient.Settings')
    def test_get_chroma_client_settings_initialization(self, mock_settings, mock_http_client):
        """Test that Settings is properly initialized."""
        # Arrange
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance

        # Act
        get_chroma_client("localhost", 8000, False)

        # Assert
        mock_settings.assert_called_once_with()

    @patch('app.chromaclient.chromadb.HttpClient')
    @patch('app.chromaclient.Settings')
    def test_get_chroma_client_exception_handling(self, mock_settings, mock_http_client):
        """Test exception handling when client creation fails."""
        # Arrange
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance
        mock_http_client.side_effect = Exception("Connection failed")

        # Act & Assert
        with pytest.raises(Exception, match="Connection failed"):
            get_chroma_client("localhost", 8000, False)

    @patch('app.chromaclient.chromadb.HttpClient')
    @patch('app.chromaclient.Settings')
    def test_get_chroma_client_settings_exception(self, mock_settings, mock_http_client):
        """Test exception handling when Settings creation fails."""
        # Arrange
        mock_settings.side_effect = Exception("Settings error")

        # Act & Assert
        with pytest.raises(Exception, match="Settings error"):
            get_chroma_client("localhost", 8000, False)

    def test_get_chroma_client_parameter_types(self):
        """Test parameter type validation."""
        with patch('app.chromaclient.chromadb.HttpClient') as mock_http_client:
            with patch('app.chromaclient.Settings') as mock_settings:
                mock_client_instance = Mock()
                mock_http_client.return_value = mock_client_instance
                mock_settings_instance = Mock()
                mock_settings.return_value = mock_settings_instance

                # Test with string host, int port, bool ssl
                result = get_chroma_client("localhost", 8000, True)
                assert result == mock_client_instance

                # Verify the correct types were passed
                call_args = mock_http_client.call_args
                assert isinstance(call_args.kwargs['host'], str)
                assert isinstance(call_args.kwargs['port'], int)
                assert isinstance(call_args.kwargs['ssl'], bool)


class TestChromaClientIntegration:
    """Integration-style tests for ChromaDB client."""

    @patch('app.chromaclient.chromadb.HttpClient')
    def test_client_mock_operations(self, mock_http_client):
        """Test mock client operations to ensure interface compatibility."""
        # Arrange
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_http_client.return_value = mock_client

        # Act
        client = get_chroma_client("localhost", 8000, False)

        # Test collection operations
        collection = client.get_collection("test_collection")
        assert collection == mock_collection

        collection2 = client.get_or_create_collection("test_collection")
        assert collection2 == mock_collection

        # Verify method calls
        client.get_collection.assert_called_once_with("test_collection")
        client.get_or_create_collection.assert_called_once_with("test_collection")

    @patch('app.chromaclient.chromadb.HttpClient')
    def test_client_query_interface(self, mock_http_client):
        """Test query interface compatibility."""
        # Arrange
        mock_client = Mock()
        mock_collection = Mock()
        mock_query_result = {
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"key": "value"}, {"key2": "value2"}]],
            "distances": [[0.1, 0.2]]
        }
        mock_collection.query.return_value = mock_query_result
        mock_client.get_collection.return_value = mock_collection
        mock_http_client.return_value = mock_client

        # Act
        client = get_chroma_client("localhost", 8000, False)
        collection = client.get_collection("test_collection")
        result = collection.query(
            query_texts=["test query"],
            n_results=5
        )

        # Assert
        assert result == mock_query_result
        mock_collection.query.assert_called_once_with(
            query_texts=["test query"],
            n_results=5
        )

    @patch('app.chromaclient.chromadb.HttpClient')
    def test_client_add_interface(self, mock_http_client):
        """Test add documents interface compatibility."""
        # Arrange
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_http_client.return_value = mock_client

        # Act
        client = get_chroma_client("localhost", 8000, False)
        collection = client.get_or_create_collection("test_collection")
        collection.add(
            ids=["id1"],
            documents=["document content"],
            metadatas=[{"key": "value"}]
        )

        # Assert
        mock_collection.add.assert_called_once_with(
            ids=["id1"],
            documents=["document content"],
            metadatas=[{"key": "value"}]
        )