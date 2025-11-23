import os
from datetime import date, datetime
from typing import Optional

from DataGathering.DataClasses.ProviderInfo import ProviderInfo
from DataGathering.DataClasses.RunInfo import RunInfo
from .AuthBase import AuthBase, HeaderAuth
from .RestClient import RestClient


class Provider:

    def __init__(self, name: str, endpoint: str, endpoint_auth: Optional[AuthBase], target_date: date, params: dict,
                 description: Optional[str], timestamp_pth: str, data_pth: str, units_pth: Optional[str], value_key_pth: Optional[str]):
        self.name = name
        self.rest_client = RestClient()
        self.endpoint = endpoint
        self.endpoint_auth = endpoint_auth
        self.params = params
        self.description = description
        self.target_date = target_date
        self.timestamp_pth = timestamp_pth
        self.data_pth = data_pth
        self.units_pth = units_pth
        self.value_key_pth = value_key_pth
        self.fast_api_base_url = os.getenv("FASTAPI_URL")
        self.rows_saved = 0

        if not self.fast_api_base_url:
            raise ValueError("self.fast_api_base_url is not set in .env file")

        self.api_key = os.getenv("API_KEY")

        if not self.api_key:
            raise ValueError("self.api_key is not set in .env file")

        self.fastapi_auth = HeaderAuth("X-API-Key", prefix=None, api_key=self.api_key)

    def fetch_data(self, extra_params: dict | None = None):
        params = self.params.copy()
        if extra_params:
            params.update(extra_params)

        response = self.rest_client.get(self.endpoint, params=params, auth=self.endpoint_auth)

        if not self.validate(response):
            raise ValueError("Invalid response from API")
        return response

    @staticmethod
    def validate(data) -> bool:
        """Validates data"""
        return data is not None and len(data) > 0

    def save(self, data):
        """Saves loaded raw data into database """
        provider_list = self.get_provider()

        if not provider_list:
            provider_id = self.create_provider().id
        else:
            provider_id = provider_list[0].id

        run_id = self.create_run(provider_id, self.target_date).id

        timestamps = self.get_by_path(data, self.timestamp_pth)

        values_dict = self.get_by_path(data, self.data_pth)

        if self.units_pth:
            units_dict = self.get_by_path(data, self.units_pth)
        else:
            units_dict = {}

        if not timestamps:
            timestamps, values_dict = self.normalize_data(data)

        timestamp_key = self.timestamp_pth.split(".")[-1]
        for i, ts in enumerate(timestamps):
            for key, val_list in values_dict.items():
                if key == timestamp_key:
                    continue

                val = val_list[i] if i < len(val_list) else None
                if val is None:
                    continue

                unit = units_dict.get(key) if units_dict else None
                self.create_raw_data(run_id, ts, key, val, unit)

        self.update_run(run_id, len(timestamps))
        self.rows_saved = len(timestamps)
        print(f"✅ Saved {len(timestamps)} rows of raw data (run={run_id}, provider={provider_id})")

    @staticmethod
    def get_by_path(obj, path: str):
        try:
            for p in path.split("."):
                if p.isdigit():
                    obj = obj[int(p)]
                else:
                    obj = obj[p]
            return obj
        except (KeyError, IndexError, TypeError):
            return None

    def normalize_data(self, data):
        """
        Returns (timestamps, values_dict) in universal columnar format.
        Detects whether the structure is row-based, column-based, table-based, or timeseries.
        """

        # --- Placeholder-based multi-value structure ---
        if getattr(self, "value_key_pth", None):
            return self._normalize_placeholder(data)

        # --- Row-based structure ---
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return self._normalize_row_based(data)

        # --- Column-based structure ---
        if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
            return self._normalize_column_based(data)

        # --- Table-based structure ---
        if isinstance(data, dict) and "headers" in data and "rows" in data:
            return self._normalize_table_based(data)

        # --- Timeseries structure ---
        if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
            return self._normalize_timeseries(data)

        raise ValueError("Unknown data structure, cannot normalize.")

    def _normalize_placeholder(self, data):
        """
        Normalizes multi-value data using `value_key_pth`.
        Works for lists of dicts or dicts, and prepends value_key to column names.
        """
        if not hasattr(self, "value_key_pth") or not self.value_key_pth:
            raise ValueError("Missing 'value_key_pth' for placeholder normalization")

        timestamps = []
        values_dict = {}

        items = self.get_by_path(data, self.data_pth)
        if items is None:
            raise ValueError(f"Data path '{self.data_pth}' not found in response")

        if isinstance(items, dict):
            items = list(items.values())
        elif not isinstance(items, list):
            raise ValueError(f"Expected list or dict at '{self.data_pth}'")

        for item in items:
            value_key = self.get_by_path(item, self.value_key_pth.split(".")[-1])
            if value_key is None:
                continue

            ts = self.get_by_path(item, self.timestamp_pth.split(".")[-1])
            if ts is None:
                continue
            timestamps.append(ts)

            val_data = item
            if isinstance(val_data, dict):
                for k, v in val_data.items():
                    if k in [self.value_key_pth.split(".")[-1], self.timestamp_pth.split(".")[-1]]:
                        continue
                    key_name = f"{value_key}_{k}"
                    values_dict.setdefault(key_name, []).append(v)
            else:
                values_dict.setdefault(value_key, []).append(val_data)

        return timestamps, values_dict

    def _normalize_row_based(self, data):
        """Normalizes row-based data: [ { 'ts': ..., 'price': ... }, ... ]"""
        timestamp_key = self.timestamp_pth.split(".")[-1]
        timestamps = [row.get(timestamp_key) for row in data]

        values_dict = {}
        for row in data:
            for key, val in row.items():
                if key == timestamp_key:
                    continue
                values_dict.setdefault(key, []).append(val)

        return timestamps, values_dict

    def _normalize_column_based(self, data):
        """Normalizes column-based data: { 'time': [...], 'temperature': [...] }"""
        timestamp_key = self.timestamp_pth.split(".")[-1]
        timestamps = data.get(timestamp_key)

        values_dict = {k: v for k, v in data.items() if k != timestamp_key}
        return timestamps, values_dict

    def _normalize_table_based(self, data):
        """Normalizes table format: { 'headers': [...], 'rows': [...] }"""
        headers = data["headers"]
        rows = data["rows"]

        timestamp_index = headers.index(self.timestamp_pth)
        timestamps = [row[timestamp_index] for row in rows]

        values_dict = {h: [] for h in headers if h != self.timestamp_pth}
        for row in rows:
            for i, h in enumerate(headers):
                if i == timestamp_index:
                    continue
                values_dict[h].append(row[i])

        return timestamps, values_dict

    @staticmethod
    def _normalize_timeseries(data):
        """Normalizes timeseries format: { '2025-01-01': { 'price': 1, ... }, ... }"""
        timestamps = list(data.keys())
        sample = next(iter(data.values()))
        values_dict = {key: [] for key in sample.keys()}

        for ts, row in data.items():
            for key, val in row.items():
                values_dict[key].append(val)

        return timestamps, values_dict

    def run(self):
        """Makes fetch, validate and save"""
        data = self.fetch_data()
        self.validate(data)
        self.save(data)

    def get_provider(self):
        resp = self.rest_client.get(
            f"{self.fast_api_base_url}/provider/",
            params={
                "name": self.name,
                "endpoint": self.endpoint
            },
            auth=self.fastapi_auth
        )

        return [ProviderInfo(**p) for p in resp] if resp else []

    def create_provider(self):
        resp = self.rest_client.post(
            f"{self.fast_api_base_url}/provider/", json={
                "name": self.name,
                "endpoint": self.endpoint,
                "description": self.description,
            },
            auth=self.fastapi_auth
        )

        return ProviderInfo(**resp)

    def create_run(self, provider_id: int, target_date: date):
        resp = self.rest_client.post(
            f"{self.fast_api_base_url}/run/",
            json={
                "provider_id": provider_id,
                "run_timestamp": datetime.now().timestamp(),
                "params": str(self.params),
                "data_type": "RAW",
                "target_date": target_date.isoformat(),
                "status": "STARTED",
                "message": "Run initiated",
            },
            auth=self.fastapi_auth
        )

        return RunInfo(**resp)

    def create_raw_data(self, run_id: int, ts: datetime, key: str, val: str, unit: Optional[str]):
        self.rest_client.post(
            f"{self.fast_api_base_url}/raw_data/",
            json={
                "run_id": run_id,
                "timestamp": ts,
                "name": key,
                "value": str(val),
                "unit": unit
            },
            auth=self.fastapi_auth
        )

    def update_run(self, run_id: int, rows_num: int):
        self.rest_client.put(
            f"{self.fast_api_base_url}/run/{run_id}",
            json={
                "status": "SUCCESS",
                "message": f"Saved {rows_num} rows"
            },
            auth=self.fastapi_auth
        )