import os

from Utils.MetricsProvider import MetricsManager
from Utils.YamlReader import YamlProviderLoader
from dotenv import load_dotenv

def main():

    load_dotenv("/app/.env")


    loader = YamlProviderLoader("/app/DataGathering/providers.yaml")

    pushgateway_url = os.getenv("PUSHGATEWAY_URL")

    metrics = MetricsManager(pushgateway_url)
    providers = loader.load_providers()

    for provider in providers:
        metrics.start(provider.name)

        try:
            provider.run()

            metrics.success(provider.name, provider.rows_saved)

        except Exception as e:
            print(f"❌ Provider {provider.name} failed: {e}")

            metrics.failure(provider.name)

    try:
        metrics.push()
        print("Metrics pushed to Pushgateway")
    except Exception as e:
        print(f"❌ Failed to push metrics: {e}")

if __name__ == "__main__":
    main()