import pandas as pd
from DataGathering.Provider import Provider


class WeatherProvider(Provider):
    """Provider to handle weather related data."""

    """Saves weather related data"""
    def save(self, data, target_date):
        print(f"[{self.name}] Saving data for {target_date} ({len(data)} keys)")