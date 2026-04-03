import logging
import requests
from datetime import date
import os

from .AuthBase import HeaderAuth
from .RestClient import RestClient


class ImputationHandler:
    def __init__(self):
        self.rest_client = RestClient()
        self.fast_api_base_url = os.getenv("FASTAPI_URL")

        if not self.fast_api_base_url:
            raise ValueError("self.fast_api_base_url is not set in .env file")

        self.api_key = os.getenv("API_KEY")

        if not self.api_key:
            raise ValueError("self.api_key is not set in .env file")

        self.fastapi_auth = HeaderAuth("X-API-Key", prefix=None, api_key=self.api_key)


    def run_imputation_check(self):

        response = self.rest_client.post(
            f"{self.fast_api_base_url}/run/impute-missing",
            json={},
            auth=self.fastapi_auth
        )
