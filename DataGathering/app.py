import os

from Utils.YamlReader import YamlProviderLoader
from dotenv import load_dotenv
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import time

def main():

    load_dotenv("/app/.env")

    #debbug purposes
    #load_dotenv()

    loader = YamlProviderLoader("/app/DataGathering/providers.yaml")

    #debbug purposes
    #loader = YamlProviderLoader("providers.yaml")

    pushgateway_url = os.getenv("PUSHGATEWAY_URL")

    registry = CollectorRegistry()

    status_gauge = Gauge(
        'data_gathering_provider_status',
        'Status posledného runu pre providera (1=success, 0=fail)',
        ['provider'],
        registry=registry
    )

    records_gauge = Gauge(
        'data_gathering_provider_rows',
        'Počet stiahnutých a uložených riadkov pre providera',
        ['provider'],
        registry=registry
    )

    timestamp_gauge = Gauge(
        'data_gathering_provider_last_run_timestamp',
        'Timestamp posledného runu providera',
        ['provider'],
        registry=registry
    )

    error_gauge = Gauge(
        'data_gathering_provider_errors',
        'Počet zlyhaní providera pri poslednom run',
        ['provider'],
        registry=registry
    )

    providers = loader.load_providers()

    for provider in providers:
        try:
            provider.run()

            rows_saved = getattr(provider, 'last_saved_rows', 0)

            status_gauge.labels(provider=provider.name).set(1)
            records_gauge.labels(provider=provider.name).set(rows_saved)
            timestamp_gauge.labels(provider=provider.name).set(time.time())
            error_gauge.labels(provider=provider.name).set(0)


        except Exception as e:
            print(f"❌ Provider {provider.name} failed: {e}")

            status_gauge.labels(provider=provider.name).set(0)
            records_gauge.labels(provider=provider.name).set(0)
            timestamp_gauge.labels(provider=provider.name).set(time.time())
            error_gauge.labels(provider=provider.name).set(1)

    try:
        push_to_gateway(pushgateway_url, job='data_gathering_job', registry=registry)
        print("📊 Metrics pushed to Pushgateway")
    except Exception as e:
        print(f"❌ Failed to push metrics: {e}")

if __name__ == "__main__":
    main()