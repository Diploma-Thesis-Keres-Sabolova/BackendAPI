import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

class MetricsManager:

    def __init__(self, pushgateway_url: str):
        self.pushgateway_url = pushgateway_url
        self.registry = CollectorRegistry()

        self.status_gauge = Gauge(
            'data_gathering_provider_status',
            'Status of last provider run (1=success, 0=fail)',
            ['provider'],
            registry=self.registry
        )

        self.records_gauge = Gauge(
            'data_gathering_provider_rows',
            'Num of records saved by last provider run',
            ['provider'],
            registry=self.registry
        )

        self.timestamp_gauge = Gauge(
            'data_gathering_provider_last_run_timestamp',
            'Timestamp of last provider run',
            ['provider'],
            registry=self.registry
        )

        self.error_gauge = Gauge(
            'data_gathering_provider_errors',
            'Num of failed records saved by last provider run',
            ['provider'],
            registry=self.registry
        )


    def start(self, provider: str):
        """Set timestamp iba pri začiatku runu."""
        self.timestamp_gauge.labels(provider=provider).set(time.time())

    def success(self, provider: str, rows: int):
        self.status_gauge.labels(provider=provider).set(1)
        self.records_gauge.labels(provider=provider).set(rows)
        self.error_gauge.labels(provider=provider).set(0)

    def failure(self, provider: str):
        self.status_gauge.labels(provider=provider).set(0)
        self.records_gauge.labels(provider=provider).set(0)
        self.error_gauge.labels(provider=provider).set(1)

    def push(self):
        push_to_gateway(
            self.pushgateway_url,
            job='data_gathering_job',
            registry=self.registry
        )
