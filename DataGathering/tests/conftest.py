import pytest
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Sets default environment variables"""
    with patch.dict(os.environ, {
        "FASTAPI_URL": "http://mock-api",
        "RABBITMQ_HOST": "mock-host",
        "API_KEY": "mock-key",
        "PUSHGATEWAY_URL": "",
        "LOG_LEVEL": "DEBUG"
    }):
        yield


@pytest.fixture
def mock_rest_client():
    """Mock RestClient"""
    with patch("DataGathering.Utils.DataProcessor.RestClient") as MockClient:
        client_instance = MockClient.return_value
        yield client_instance


@pytest.fixture
def data_processor(mock_rest_client):
    """Returns mock DataProcessor"""
    with patch("DataGathering.Utils.DataProcessor.setup_logging"), \
            patch("DataGathering.Utils.DataProcessor.MetricsManager"):
        from DataGathering.Utils.DataProcessor import DataProcessor
        processor = DataProcessor()
        # Default params
        processor.run_id = 1
        processor.provider_id = 1
        return processor