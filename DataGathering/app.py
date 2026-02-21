import logging
import os

from Utils.Logger import setup_logging
from Utils.MetricsProvider import MetricsManager
from Utils.YamlReader import YamlProviderLoader
from dotenv import load_dotenv

def main():

    load_dotenv("/app/.env")

    setup_logging()
    logger = logging.getLogger("data-gathering")

    loader = YamlProviderLoader("/app/DataGathering/providers.yaml")

    pushgateway_url = os.getenv("PUSHGATEWAY_URL")

    metrics = MetricsManager(pushgateway_url, "DG")
    providers = loader.load_providers()

    logger.info("Job started")

    for provider in providers:
        logger.info(f"Starting provider: {provider.name}")

        try:
            provider.run()
            metrics.start(provider.name)
            metrics.success(provider.name)
        except Exception as e:
            logger.exception(f"Provider {provider.name} failed : error {e}")
            metrics.failure(provider.name)

    try:
        metrics.push_dg()
        logger.info("Metrics from DG pushed to Pushgateway")
    except Exception as e:
        logger.exception(f"Failed to push DG metrics to Pushgateway : error {e}")

    logger.info("Job finished")

if __name__ == "__main__":
    main()