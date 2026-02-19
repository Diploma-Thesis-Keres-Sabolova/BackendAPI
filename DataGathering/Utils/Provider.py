import json
import os
import pika
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

        self.create_raw_data(run_id, data)

        self.update_run(run_id)

        self.send_to_queue(run_id)

    def send_to_queue(self, run_id: int):
        rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
        queue_name = "data_processing_queue"

        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)

            message_body = {
                "run_id": run_id,
                "provider_id": self.get_provider()[0].id,
                "timestamp_pth": self.timestamp_pth,
                "data_pth": self.data_pth,
                "units_pth": self.units_pth,
                "value_key_pth": self.value_key_pth,
                "target_date": self.target_date.isoformat()
            }

            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message_body),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            connection.close()
        except Exception as e:
            raise ValueError(f"Failed to send to queue: {e}")

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

    def create_raw_data(self, run_id: int, data):
        self.rest_client.post(
            f"{self.fast_api_base_url}/raw_data/",
            json={
                "run_id": run_id,
                "data": data
            },
            auth=self.fastapi_auth
        )

    def update_run(self, run_id: int):
        self.rest_client.put(
            f"{self.fast_api_base_url}/run/{run_id}",
            json={
                "status": "SUCCESS RAW",
                "message": f"Saved raw data"
            },
            auth=self.fastapi_auth
        )