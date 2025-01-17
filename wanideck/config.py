import os
import toml
from pathlib import Path
from dataclasses import dataclass, fields

@dataclass
class Config:
    user_api_token: str

    deck_name: str

    cache_dir: Path

    @classmethod
    def load(cls, conf_file: str | Path) -> "Config":
        # get toml config, flatten it and get environ overwrites
        with open(conf_file, "r") as fp:
            data = toml.load(fp)

        flattend = cls._flatten_dict(data)

        # validate input
        for field in fields(cls):
            # get field from env or from toml
            val = os.environ.get(f"WK_{field.name.upper()}")
            if val is None:
                val = flattend.get(field.name)

            if val is None:
                raise ValueError(f"{field.name} could not be found in config file or env")

            try:
                flattend[field.name] = field.type(val)
            except Exception as e:
                raise ValueError(f"{field.name} value {val} is incomp. with {field.type}", e)

        return Config(
            **flattend
        )

    @staticmethod
    def _flatten_dict(data: dict) -> dict:
        """This is used to transform a toml to flattend dict"""
        flattend = {}
        for key, element in data.items():
            if isinstance(element, dict):
                _flat = Config._flatten_dict(element)
                for nkey, nelem in _flat.items():
                    flattend[f"{key.lower()}_{nkey}"] = nelem
            else:
                flattend[f"{key.lower()}"] = element

        return flattend


