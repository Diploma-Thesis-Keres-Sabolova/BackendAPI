import pytest
import os
from unittest.mock import patch, mock_open
from datetime import date
from DataGathering.Utils.YamlReader import YamlProviderLoader

VALID_YAML = """
providers:
  - name: TestProvider
    endpoint: "http://api.test.com"
    timestamp_pth: "time"
    data_pth: "data"
    units_pth: null
    value_key_pth: null
    file_format: "json"
    description: "Test desc"
    params:
      date: "{{today}}"
      static: "value"
    auth:
      type: query
      param: "apikey"
      api_key_env: "TEST_API_KEY"
"""

INVALID_YAML = """
providers:
  - name: TestProvider
    timestamp_pth: "time"
    data_pth: "data"
    units_pth: null
    value_key_pth: null
    file_format: "json"
    description: "Test desc"
    params:
      date: "{{today}}"
      static: "value"
    auth:
      type: query
      param: "apikey"
      api_key_env: "TEST_API_KEY"
"""


@patch.dict(os.environ, {"TEST_API_KEY": "secret123"})
def test_yaml_loader_valid():
    """Test placeholder {{today}}"""

    with patch("builtins.open", mock_open(read_data=VALID_YAML)):
        loader = YamlProviderLoader("dummy_path.yaml")
        providers = loader.load_providers()

        assert len(providers) == 1
        p = providers[0]

        assert p.name == "TestProvider"
        assert p.endpoint == "http://api.test.com"

        today_str = date.today().strftime("%Y-%m-%d")
        assert p.params['date'] == today_str
        assert p.params['static'] == "value"


def test_yaml_missing_env_var():
    """Test missing environment variable"""

    with patch("builtins.open", mock_open(read_data=VALID_YAML)):
        if "TEST_API_KEY" in os.environ:
            del os.environ["TEST_API_KEY"]

        loader = YamlProviderLoader("dummy_path.yaml")

        with pytest.raises(ValueError) as excinfo:
            loader.load_providers()

        assert "Missing environment variable 'TEST_API_KEY'" in str(excinfo.value)


def test_yaml_missing_req_field_var():
    """Test missing required field error"""

    with patch("builtins.open", mock_open(read_data=INVALID_YAML)):

        loader = YamlProviderLoader("dummy_path.yaml")

        with pytest.raises(ValueError) as excinfo:
            loader.load_providers()

        assert "Provider 'TestProvider' missing required field: 'endpoint'" in str(excinfo.value)