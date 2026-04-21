import json
import os
import pytest
from datetime import datetime


def load_sample(filename):
    path = os.path.join(os.path.dirname(__file__), 'samples', filename)
    with open(path, 'r') as f:
        return json.load(f)


def test_normalize_openmeteo_columns(data_processor, mock_rest_client):
    """Test column based (OpenMeteo)"""

    raw_data = load_sample("openmeteo_sample.json")

    data_processor.timestamp_pth = "hourly.time"
    data_processor.data_pth = "hourly"
    data_processor.units_pth = "hourly_units"
    data_processor.value_key_pth = None
    data_processor.file_format = "json"

    mock_rest_client.get.side_effect = [
        [{"id": 1, "name": "OpenMeteo", "endpoint": "https://api.open-meteo.com/v1/forecast"}],
        [{"id": 1, "provider_id": 1, "run_timestamp": datetime.now(), "params": {}, "data_type": "RAW",
          "target_date": "2024-01-01", "status": "STARTED", "message": ""}],
    ]

    data_processor.save_json(raw_data)

    assert mock_rest_client.post.call_count == 4

    call_args = mock_rest_client.post.call_args_list[0]
    payload = call_args[1]['json']

    assert payload['run_id'] == 1
    assert payload['name'] == 'temperature_2m'
    assert payload['value'] == '10.5'
    assert payload['unit'] == 'C'


def test_normalize_oilprice_placeholders(data_processor, mock_rest_client):
    """Test placeholder based (OilPrice)"""

    raw_data = load_sample("oilprice_sample.json")

    data_processor.timestamp_pth = "data.prices.created_at"
    data_processor.data_pth = "data.prices"
    data_processor.units_pth = None
    data_processor.value_key_pth = "data.prices.code"
    data_processor.file_format = "json"

    mock_rest_client.get.side_effect = [
        [{"id": 2, "name": "OilPrice", "endpoint": "https://api.oilpriceapi.com/v1/prices/latest"}],
        [{"id": 1, "provider_id": 2, "run_timestamp": datetime.now(), "params": {}, "data_type": "RAW",
          "target_date": "2024-01-01", "status": "STARTED", "message": ""}],
    ]

    data_processor.save_json(raw_data)

    assert mock_rest_client.post.call_count == 2

    posted_data = [call[1]['json'] for call in mock_rest_client.post.call_args_list]

    wti_record = next(d for d in posted_data if "WTI_USD_price" in d['name'])
    assert wti_record['value'] == '75.5'

def test_normalize_oktedam_list(data_processor, mock_rest_client):
    """Test list based (OkteDam)"""

    raw_data = load_sample("okteDam_sample.json")

    data_processor.timestamp_pth = "deliveryStart"
    data_processor.data_pth = ""
    data_processor.units_pth = None
    data_processor.value_key_pth = None
    data_processor.file_format = "json"

    mock_rest_client.get.side_effect = [
        [{"id": 3, "name": "OkteDam", "endpoint": "https://isot.okte.sk/api/v1/dam/results"}],
        [{"id": 1, "provider_id": 3, "run_timestamp": datetime.now(), "params": {}, "data_type": "RAW",
          "target_date": "2024-01-01", "status": "STARTED", "message": ""}],
    ]

    data_processor.save_json(raw_data)

    assert mock_rest_client.post.call_count == 10
    assert data_processor.rows_saved == 2

    posted_data = [call[1]['json'] for call in mock_rest_client.post.call_args_list]

    price_record = next((
        d for d in posted_data
        if d['name'] == 'price' and str(d['value']) == '69.96'
    ), None)

    assert price_record is not None, "Value Not Found"
    assert price_record['timestamp'] == '2026-02-20T23:00:00Z'
    assert price_record['run_id'] == 1

    flow_record = next((
        d for d in posted_data
        if d['name'] == 'flowSkHu' and str(d['value']) == '1646.4'
    ), None)

    assert flow_record is not None
    assert flow_record['timestamp'] == '2026-02-20T23:00:00Z'

def test_normalize_energycharts_power_fore_mixed_root(data_processor, mock_rest_client):
    """Test mixed root dict with lists and strings (EnergyCharts)"""

    raw_data = load_sample("energyCharts-publicPowerForecast.json")

    data_processor.run_id = 1
    data_processor.timestamp_pth = "unix_seconds"
    data_processor.data_pth = "forecast_values"
    data_processor.units_pth = None
    data_processor.value_key_pth = None
    data_processor.file_format = "json"

    data_processor.save_json(raw_data)

    assert mock_rest_client.post.call_count == 2
    assert data_processor.rows_saved == 2

    posted_data = [call[1]['json'] for call in mock_rest_client.post.call_args_list]

    record_1 = posted_data[0]
    assert record_1['run_id'] == 1
    assert record_1['name'] == 'forecast_values'
    assert str(record_1['value']) == '81'
    assert record_1['timestamp'] == 1776722400

    record_2 = posted_data[1]
    assert record_2['name'] == 'forecast_values'
    assert str(record_2['value']) == '179.8'
    assert record_2['timestamp'] == 1776726000