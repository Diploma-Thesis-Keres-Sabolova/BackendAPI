import os
from datetime import date, datetime
from typing import Optional

from DataClasses.ProviderInfo import ProviderInfo
from DataClasses.RunInfo import RunInfo
from RestClient import RestClient


class Provider:

    def __init__(self, name: str, endpoint: str, target_date: date, params: dict,
                 timestamp_pth: str, data_pth: str, units_pth: Optional[str]):
        self.name = name
        self.rest_client = RestClient()
        self.endpoint = endpoint
        self.params = params
        self.target_date = target_date
        self.timestamp_pth = timestamp_pth
        self.data_pth = data_pth
        self.units_pth = units_pth
        self.fast_api_base_url = os.getenv("FASTAPI_URL")

        if not self.fast_api_base_url:
            raise ValueError("self.fast_api_base_url is not set in .env file")

        self.api_key = os.getenv("API_KEY")

        if not self.api_key:
            raise ValueError("self.api_key is not set in .env file")

    def fetch_data(self, extra_params: dict | None = None):
        params = self.params.copy()
        if extra_params:
            params.update(extra_params)

        response = self.rest_client.get(self.endpoint, params=params)
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

    def run(self):
        """Makes fetch, validate and save"""
        data = self.fetch_data()
        self.validate(data)
        self.save(data)

    def get_provider(self):
        resp = self.rest_client.get(
            f"{self.fast_api_base_url}/provider",
            params={
                "name": self.name,
                "endpoint": self.endpoint,
                "params": str(self.params)
            },
            headers={"X-API-Key": self.api_key}
        )

        return [ProviderInfo(**p) for p in resp] if resp else []

    def create_provider(self):
        resp = self.rest_client.post(
            f"{self.fast_api_base_url}/provider", json={
                "name": self.name,
                "endpoint": self.endpoint,
                "params": str(self.params)
            },
            headers={"X-API-Key": self.api_key}
        )

        return ProviderInfo(**resp)

    def create_run(self, provider_id: int, target_date: date):
        resp = self.rest_client.post(
            f"{self.fast_api_base_url}/run",
            json={
                "provider_id": provider_id,
                "run_timestamp": datetime.now().timestamp(),
                "data_type": "RAW",
                "target_date": target_date.isoformat(),
                "status": "STARTED",
                "message": "Run initiated",
            },
            headers={"X-API-Key": self.api_key}
        )

        return RunInfo(**resp)

    def create_raw_data(self, run_id: int, ts: datetime, key: str, val: str, unit: Optional[str]):
        self.rest_client.post(
            f"{self.fast_api_base_url}/raw_data",
            json={
                "run_id": run_id,
                "timestamp": ts,
                "name": key,
                "value": val,
                "unit": unit
            },
            headers={"X-API-Key": self.api_key}
        )

    def update_run(self, run_id: int, rows_num: int):
        self.rest_client.put(
            f"{self.fast_api_base_url}/run/{run_id}",
            json={
                "status": "SUCCESS",
                "message": f"Saved {rows_num} rows"
            },
            headers={"X-API-Key": self.api_key}
        )