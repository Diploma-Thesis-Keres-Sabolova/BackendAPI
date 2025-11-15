import os
import csv
from datetime import date

from RestClient import RestClient


class Provider:

    def __init__(self, name: str, endpoint: str, params: dict):
        self.name = name
        self.rest_client = RestClient()
        self.endpoint = endpoint
        self.params = params

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
        print(f"✅ Data saved to ")

    def run(self, target_date: date):
        """Makes fetch, validate and save"""
        data = self.fetch_data(target_date)
        self.validate(data)
        self.save(data, target_date)