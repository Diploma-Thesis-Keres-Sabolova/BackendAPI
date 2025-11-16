import os
import csv
from datetime import date, datetime

from DataClasses.ProviderInfo import ProviderInfo
from DataClasses.RunInfo import RunInfo
from RestClient import RestClient


class Provider:

    def __init__(self, name: str, endpoint: str, params: dict):
        self.name = name
        self.rest_client = RestClient()
        self.endpoint = endpoint
        self.params = params
        self.fast_api_base_url = os.getenv("FASTAPI_URL")
        self.api_key = os.getenv("API_KEY")

    def fetch_data(self, target_date: date, extra_params: dict | None = None):
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

    def save(self, data, target_date: date):
        """Saves loaded raw data into database """
        provider_list = self.get_provider()

        if not provider_list:
            provider_id = self.create_provider().id
        else:
            provider_id = provider_list[0].id

        run_id = self.create_run(provider_id, target_date).id

        rows = data if isinstance(data, list) else [data]

        for row in rows:
            ts = (
                row["timestamp"]
                if "timestamp" in row
                else datetime.now().isoformat()
            )

            for key, val in row.items():
                if key == "timestamp":
                    continue

                if isinstance(val, (dict, list)):
                    continue

                self.create_raw_data(run_id, ts, key, val)

        self.update_run(run_id, len(rows))

        print(f"✅ Saved {len(rows)} rows of raw data (run={run_id}, provider={provider_id})")

    def run(self, target_date: date):
        """Makes fetch, validate and save"""
        data = self.fetch_data(target_date)
        self.validate(data)
        self.save(data, target_date)

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

    def create_raw_data(self, run_id: int, ts: datetime, key: str, val: str):
        self.rest_client.post(
            f"{self.fast_api_base_url}/raw_data",
            json={
                "run_id": run_id,
                "timestamp": ts,
                "name": key,
                "value": val,
                "unit": None
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