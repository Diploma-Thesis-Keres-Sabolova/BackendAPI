import yaml
from datetime import date
from typing import List, Dict, Any
from Provider import Provider


class YamlProviderLoader:
    """
    Loads providers from YAML, validates structure,
    applies template substitutions, and returns Provider objects.
    """

    REQUIRED_FIELDS = ["name", "endpoint", "timestamp_pth", "data_pth", "description"]

    def __init__(self, path: str):
        self.path = path

    def load_yaml(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML file not found at: {self.path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")

        if "providers" not in data or not isinstance(data["providers"], list):
            raise ValueError("YAML must contain a 'providers' list.")

        return data

    @staticmethod
    def apply_templates(params: Dict[str, Any]) -> Dict[str, Any]:
        today = date.today().strftime("%Y-%m-%d")

        processed = {}
        for key, val in params.items():
            if isinstance(val, str):
                val = val.replace("{{today}}", today)
            processed[key] = val

        return processed

    def validate_provider(self, provider_cfg: Dict[str, Any]):
        for field in self.REQUIRED_FIELDS:
            if field not in provider_cfg:
                raise ValueError(
                    f"Provider '{provider_cfg.get('name', '<unknown>')}' missing required field: '{field}'"
                )

        if not isinstance(provider_cfg.get("params", {}), dict):
            raise ValueError(f"Provider '{provider_cfg['name']}' has invalid 'params' structure.")

    def build_providers(self, raw_cfg: Dict[str, Any]) -> List[Provider]:
        providers = []

        for p_cfg in raw_cfg["providers"]:
            self.validate_provider(p_cfg)

            params = self.apply_templates(p_cfg.get("params", {}))

            provider = Provider(
                name=p_cfg["name"],
                endpoint=p_cfg["endpoint"],
                target_date=date.today(),
                params=params,
                description=p_cfg["description"],
                timestamp_pth=p_cfg["timestamp_pth"],
                data_pth=p_cfg["data_pth"],
                units_pth=p_cfg.get("units_pth")
            )

            providers.append(provider)

        return providers

    def load_providers(self) -> List[Provider]:
        raw = self.load_yaml()
        return self.build_providers(raw)
