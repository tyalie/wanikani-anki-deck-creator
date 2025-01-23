import os
import toml
from pathlib import Path
from dataclasses import dataclass, fields
from enum import Enum

@dataclass
class Config:
    class AudioFormats(Enum):
        WEBM = "webm"
        MPEG = "mpeg"

        def __str__(self) -> str:
            return "audio/" + self.value

        @property
        def fext(self) -> str:
            """file extension"""
            match self:
                case self.WEBM:
                    return "webm"
                case self.MPEG:
                    return "mpeg"

    user_api_token: str

    deck_name: str
    deck_audio_format: AudioFormats

    cache_dir: Path

    # the amount of days required for stability for a card to be considered learned
    learning_stability_req_for_learned_d: int


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


