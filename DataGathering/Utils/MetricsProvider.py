import time
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, push_to_gateway

class MetricsManager:

    def __init__(self, pushgateway_url: str, app_type: str):
        self.pushgateway_url = pushgateway_url
        self.app_type = app_type.upper()
        self.registry = CollectorRegistry()

        if self.app_type == 'DG':
            self.status_gauge = Gauge(
                'dg_provider_status',
                'Status of last provider run (1=success, 0=fail)',
                ['provider'],
                registry=self.registry
            )

            self.timestamp_gauge = Gauge(
                'dg_provider_last_run_timestamp',
                'Timestamp of last provider run',
                ['provider'],
                registry=self.registry
            )

        elif self.app_type == 'DP':
            self.last_success_timestamp = Gauge(
                'dp_last_success_timestamp',
                'Timestamp of last successful processing',
                ['provider'],
                registry=self.registry
            )

            self.processing_ops_total = Counter(
                'dp_ops_total',
                'Total number of processed queue messages',
                ['provider', 'status'],
                registry=self.registry
            )

            self.saved_rows_total = Counter(
                'dp_saved_rows_total',
                'Total number of data rows saved to DB',
                ['provider'],
                registry=self.registry
            )

            self.processing_duration = Histogram(
                'dp_processing_duration_seconds',
                'Time spent processing a message',
                ['provider'],
                registry=self.registry
            )

    def record_success(self, provider: str, rows: int, duration: float):
        self.last_success_timestamp.labels(provider=provider).set(time.time())
        self.processing_ops_total.labels(provider=provider, status="success").inc()
        self.saved_rows_total.labels(provider=provider).inc(rows)
        self.processing_duration.labels(provider=provider).observe(duration)

    def record_failure(self, provider: str, duration: float):
        self.processing_ops_total.labels(provider=provider, status="error").inc()
        self.processing_duration.labels(provider=provider).observe(duration)



    def start(self, provider: str):
        self.timestamp_gauge.labels(provider=provider).set(time.time())

    def success(self, provider: str):
        self.status_gauge.labels(provider=provider).set(1)

    def failure(self, provider: str):
        self.status_gauge.labels(provider=provider).set(0)

    def push_dg(self):
        push_to_gateway(
            self.pushgateway_url,
            job='data_gathering_job',
            registry=self.registry
        )

    def push_dp(self):
        try:
            push_to_gateway(
                self.pushgateway_url,
                job='data_processor_worker',
                registry=self.registry
            )
        except Exception as e:
            print(f"Error trying to push metrics: {e}")