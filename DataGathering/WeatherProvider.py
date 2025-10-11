from abc import abstractmethod
from datetime import date, timedelta
from DataGathering.Provider import Provider


class WeatherProvider(Provider):
    """Provider to handle data weather related data."""

    BASE_URL = ""
    ENDPOINT_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
    ENDPOINT_FORECAST = "https://api.open-meteo.com/v1/forecast"

    COLUMNS = [
        "temperature_2m",
        "dew_point_2m",
        "rain",
        "snowfall",
        "wind_speed_10m",
        "precipitation"
    ]

    # Forecast 15-min stĺpce = spoločné + extra
    FORECAST_MINUTELY_COLUMNS = COLUMNS + [
        "global_tilted_irradiance"
    ]

    HISTORICAL_HOURLY_COLUMNS = COLUMNS

    def __init__(self, name: str, latitude: float, longitude: float, **kwargs):
        super().__init__(name=name, **kwargs)
        self.latitude = latitude
        self.longitude = longitude
        self.rest_client.base_url = self.BASE_URL

    def build_openmeteo_params(
            self,
            start_date: date,
            end_date: date,
            hourly: list[str] | None = None,
            daily: list[str] | None = None,
            minutely_15: list[str] | None = None,
    ) -> dict:
        """Builds required parameters for Open-Meteo API."""
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        if hourly:
            params["hourly"] = ",".join(hourly)
        if daily:
            params["daily"] = ",".join(daily)
        if minutely_15:
            params["minutely_15"] = ",".join(minutely_15)

        return params

    def _fetch(self, endpoint: str, start_date: date, end_date: date, **kwargs):
        """Internal method to call the API with endpoint and params."""
        params = self.build_openmeteo_params(start_date=start_date, end_date=end_date, **kwargs)
        response = self.rest_client.get(endpoint, params=params)
        if not self.validate(response):
            raise ValueError("Invalid response from API")
        return response

    def fetch_forecast_15min(self, target_date: date):
        """Fetch forecast data for a specific date (15min interval)."""
        return self._fetch(self.ENDPOINT_FORECAST, target_date, target_date + timedelta(days=1),
                           minutely_15=self.FORECAST_MINUTELY_COLUMNS)

    def fetch_history_hourly(self, target_date: date):
        """Fetch historical data for a specific date (hourly interval)."""
        return self._fetch(self.ENDPOINT_ARCHIVE, target_date - timedelta(days=1), target_date,
                           hourly=self.HISTORICAL_HOURLY_COLUMNS)

    def fetch_data(self, target_date: date):
        """Returns forecast and historical data."""
        historical_data = self.fetch_history_hourly(target_date)
        forecast_data = self.fetch_forecast_15min(target_date)

        return {
            "historical": historical_data,
            "forecast": forecast_data
        }

    def save(self, data, target_date: date):
        """Save data"""
        print('saved')