# providers/provider.py
from abc import ABC, abstractmethod
from datetime import date

from DataGathering.RestClient import RestClient


class Provider(ABC):
    """Abstract class for providers"""

    def __init__(self, name: str):
        self.name = name
        self.rest_client = RestClient()

    @abstractmethod
    def fetch_data(self, target_date: date):
        """Fetching data from specific sourcers (APIs)"""
        pass

    @staticmethod
    def validate(data) -> bool:
        """Validates data"""
        return data is not None and len(data) > 0

    @abstractmethod
    def save(self, data, target_date: date):
        """Saves loaded raw data into database """
        pass

    def run(self, target_date: date):
        """Makes fetch, validate and save"""
        data = self.fetch_data(target_date)
        self.validate(data)
        self.save(data, target_date)
