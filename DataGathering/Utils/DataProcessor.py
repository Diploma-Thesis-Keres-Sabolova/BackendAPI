import json
import os
import time

import pika
import logging
from datetime import datetime
from typing import Optional
from pika.exceptions import AMQPConnectionError


from .Logger import setup_logging
from .MetricsProvider import MetricsManager
from .RestClient import RestClient
from .AuthBase import HeaderAuth
from DataGathering.DataClasses.ProviderInfo import ProviderInfo
from DataGathering.DataClasses.RunInfo import RunInfo
from DataGathering.DataClasses.RawDataInfo import RawDataInfo

class DataProcessor:

    def __init__(self):
        self.run_id = None
        self.provider_id = None
        self.provider_name = None
        self.timestamp_pth = None
        self.data_pth = None
        self.units_pth = None
        self.value_key_pth = None
        self.rest_client = RestClient()
        self.fast_api_base_url = os.getenv("FASTAPI_URL")
        self.rows_saved = 0
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST")
        self.queue_name = "data_processing_queue"

        setup_logging()
        self.logger = logging.getLogger("data-processing")

        pushgateway_url = os.getenv("PUSHGATEWAY_URL")
        if pushgateway_url:
            self.metrics = MetricsManager(pushgateway_url, "DP")
        else:
            self.metrics = None
            self.logger.exception("PUSHGATEWAY_URL not set, metrics disabled")

        if not self.rabbitmq_host:
            self.logger.exception("self.rabbitmq_host is not set in .env file")

        if not self.fast_api_base_url:
            self.logger.exception("self.fast_api_base_url is not set in .env file")

        self.api_key = os.getenv("API_KEY")

        if not self.api_key:
            self.logger.exception("self.api_key is not set in .env file")

        self.fastapi_auth = HeaderAuth("X-API-Key", prefix=None, api_key=self.api_key)

    def start_worker(self):
        """Starts the worker loop"""
        while True:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host))
                channel = connection.channel()
                channel.queue_declare(queue=self.queue_name, durable=True)

                channel.basic_qos(prefetch_count=1)

                channel.basic_consume(queue=self.queue_name, on_message_callback=self.process_queue_message)
                channel.start_consuming()
            except pika.exceptions.AMQPConnectionError:
                time.sleep(5)

    def process_queue_message(self, ch, method, properties, body):
        """Callback function triggered when a message is received"""
        self.clear_attributes()
        duration = 0
        try:
            start_time = time.time()
            message = json.loads(body)
            self.run_id = message['run_id']
            self.provider_id = message['provider_id']
            self.provider_name = message.get('provider_name', f"provider_{message.get('provider_id', 'unknown')}")
            self.timestamp_pth = message['timestamp_pth']
            self.data_pth = message['data_pth']
            self.units_pth = message['units_pth']
            self.value_key_pth = message['value_key_pth']

            raw_data_list = self.get_raw_data()
            if raw_data_list:
                raw_data = raw_data_list[0]
                self.logger.info(f"Processing Run ID: {self.run_id} for {self.provider_name}")
                self.save(raw_data.data)

            duration = time.time() - start_time

            if self.metrics:
                self.metrics.record_success(self.provider_name, self.rows_saved, duration)
                self.metrics.push_dp()

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            self.logger.exception(f"Error processing message: {e}")
            if self.metrics:
                self.metrics.record_failure(self.provider_name, self.rows_saved, duration)
                self.metrics.push_dp()

    def save(self, data) -> None:
        provider_list = self.get_provider()

        if not provider_list:
            raise ValueError("Provider does not exist")

        run_list = self.get_run()

        if not run_list:
            raise ValueError("Run does not exist")
        else:
            run_id = run_list[0].id

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
                self.create_processed_data(run_id, ts, key, val, unit)

        self.rows_saved = len(timestamps)
        self.update_run(run_id)

    @staticmethod
    def validate(data) -> bool:
        """Validates data"""
        return data is not None and len(data) > 0

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

    def get_provider(self):
        resp = self.rest_client.get(
            f"{self.fast_api_base_url}/provider/",
            params={
                "id": self.provider_id,
            },
            auth=self.fastapi_auth
        )

        return [ProviderInfo(**p) for p in resp] if resp else []

    def get_run(self):
        resp = self.rest_client.get(
            f"{self.fast_api_base_url}/run/",
            params={
                "id": self.run_id,
            },
            auth=self.fastapi_auth
        )

        return [RunInfo(**p) for p in resp] if resp else []

    def get_raw_data(self):
        resp = self.rest_client.get(
            f"{self.fast_api_base_url}/raw_data/",
            params={
                "run_id": self.run_id,
            },
            auth=self.fastapi_auth
        )

        return [RawDataInfo(**p) for p in resp] if resp else []

    def create_processed_data(self, run_id: int, ts: datetime, key: str, val: str, unit: Optional[str]):
        self.rest_client.post(
            f"{self.fast_api_base_url}/processed_data/",
            json={
                "run_id": run_id,
                "timestamp": ts,
                "name": key,
                "value": str(val),
                "unit": unit
            },
            auth=self.fastapi_auth
        )

    def update_run(self, run_id: int):
        self.rest_client.put(
            f"{self.fast_api_base_url}/run/{run_id}",
            json={
                "status": "SUCCESS PROCESSED",
                "message": f"Saved {self.rows_saved} processed rows.",
            },
            auth=self.fastapi_auth
        )

    def clear_attributes(self):
        self.run_id = None
        self.provider_id = None
        self.provider_name = None
        self.timestamp_pth = None
        self.data_pth = None
        self.units_pth = None
        self.value_key_pth = None