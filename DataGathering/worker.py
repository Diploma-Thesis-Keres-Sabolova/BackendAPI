import sys
import os
import logging
from Utils.Logger import setup_logging
from Utils.MetricsProvider import MetricsManager

from Utils.DataProcessor import DataProcessor

if __name__ == "__main__":
    setup_logging()

    pushgateway_url = os.getenv("PUSHGATEWAY_URL")

    metrics = MetricsManager(pushgateway_url)

    logger = logging.getLogger("data-processing")

    processor = DataProcessor()
    processor.start_worker()