import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from DataGathering.Utils.Provider import Provider


@pytest.fixture
def mock_pika():
    """Mock RabbitMQ"""
    with patch("DataGathering.Utils.Provider.pika") as mock_pika_lib:
        mock_connection = MagicMock()
        mock_channel = MagicMock()

        mock_pika_lib.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        yield mock_channel


@pytest.fixture
def provider_instance():
    with patch("os.getenv") as mock_env:
        mock_env.return_value = "mock_value"

        p = Provider(
            name="TestProv",
            endpoint="http://external.api",
            endpoint_auth=None,
            target_date=date(2024, 1, 1),
            params={},
            description="desc",
            timestamp_pth="ts",
            data_pth="val",
            units_pth=None,
            value_key_pth=None
        )
        return p


def test_provider_full_run(provider_instance, mock_pika):
    """
    Simulates provider run:
    """

    mock_client = MagicMock()

    mock_client.get.side_effect = [
        {"data": "some_raw_data"},
        [],
        [{"id": 10, "name": "TestProv", "endpoint": "http://external.api"}]
    ]

    mock_client.post.side_effect = [
        {"id": 10, "name": "TestProv", "endpoint": "http://external.api"},
        {"id": 55, "status": "STARTED", "provider_id": 10, "run_timestamp": date(2024, 1, 1), "params": "", "data_type": "", "target_date": date(2024, 1, 1), "message": "some message"},
        {"status": "ok"}
    ]

    provider_instance.rest_client = mock_client

    provider_instance.run()


    args, _ = mock_client.get.call_args_list[0]

    assert args[0] == "http://external.api"
    assert mock_client.post.call_args_list[0][1]['json']['name'] == "TestProv"

    assert mock_pika.basic_publish.called

    call_args = mock_pika.basic_publish.call_args[1]
    import json
    body = json.loads(call_args['body'])

    assert body['run_id'] == 55
    assert body['provider_name'] == "TestProv"