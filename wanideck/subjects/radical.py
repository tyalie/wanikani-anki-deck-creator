from typing import Callable
import dataclasses as ds

from ..models import RES_FOLDER, CardTemplate, Model, get_field_list
from ..notes import Note

from .base import SFields, SubjectBase, mcache
from .types import SubjectTypes

@ds.dataclass
class RFields(SFields):
    radical_name: str
    radical: str
    radical_meaning: str


    @classmethod
    def from_subject(cls, subject: dict) -> "RFields":
        params = dict()

        params["radical_name"] = subject["data"]["meanings"][0]["meaning"]

        # sometimes the character radical can be None,
        # in that case insert an svg with the unique name
        char = subject["data"]["characters"]
        if char is None:
            char = f'<img src="{cls.uniq_name_from_sub(subject)}.svg">'
        params["radical"] = char

        params["radical_meaning"] = subject["data"]["meaning_mnemonic"]

        params.update(ds.asdict(super().from_subject(subject)))

        return cls(**params)

class RadicalSubject(SubjectBase):
    Fields = RFields

    @classmethod
    def get_type(cls) -> SubjectTypes:
        return SubjectTypes.RADICALS

    @classmethod
    @mcache
    def get_temp_recognition(cls):
        return CardTemplate(
            Name = "Recognition",
            Front = (RES_FOLDER / "html/radical Model_Recognition_f.html").read_text(),
            Back = (RES_FOLDER / "html/radical Model_Recognition_b.html").read_text(),
        )

    @classmethod
    @mcache
    def get_model(cls) -> Model:
        return Model(
            name="Radical Model - wanideck",
            fields=get_field_list(cls.Fields),
            templates=[cls.get_temp_recognition()],
            css = (RES_FOLDER / "html/main.css").read_text()
        )

    @classmethod
    def get_note(cls, deck: str, fields: Fields, level: int) -> Note:
        return Note(
            deck=deck,
            model=cls.get_model().name,
            fields=fields,
            tags = [f"level{level}", cls.get_type().name]
        )

    @classmethod
    def parse_wk_sub(cls, subject: dict) -> tuple[Callable[[str], Note], dict | None]:
        """parses fields and required media downloads"""

        fields = cls.Fields.from_subject(subject)
        level = subject["data"]["level"]
        def fac(deck: str):
            return cls.get_note(deck, fields, level)

        return fac, cls._get_req_media_from_sub(subject)

    @classmethod
    def _get_req_media_from_sub(cls, subject: dict) -> dict | None:
        if subject["data"]["characters"] is not None:
            return None

        # the svg element must always exist
        svg_elem = [
            s for s in subject["data"]["character_images"] if
            s["content_type"] == "image/svg+xml"
        ]

        return dict(
            filename=f"{cls.Fields.uniq_name_from_sub(subject)}.svg",
            url=svg_elem[0]["url"],
        )


