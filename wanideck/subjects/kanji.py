from re import sub
from typing import Callable
import dataclasses as ds
import json

from .radical import RadicalSubject

from ..models import RES_FOLDER, CardTemplate, Model, get_field_list
from ..notes import Note

from .types import SubjectTypes

from .base import SFields, SubjectBase, mcache

@ds.dataclass
class KFields(SFields):
    kanji: str
    kanji_meaning: str
    reading_on: str
    reading_kun: str

    components: list[int] | str
    radicals: list[str] | str
    radicals_names: list[str] | str

    meaning_mnemonic: str
    meaning_hint: str
    reading_mnemonic: str
    reading_hint: str

    @classmethod
    def from_subject(cls, subject: dict) -> "KFields":
        params = dict()

        params["kanji"] = subject["data"]["characters"]
        params["kanji_meaning"] = cls._get_meanread_list(subject["data"]["meanings"])
        params["reading_on"] = cls._get_meanread_list(subject["data"]["readings"], "onyomi")
        params["reading_kun"] = cls._get_meanread_list(subject["data"]["readings"], "kunyomi")

        params["components"] = subject["data"]["component_subject_ids"]
        params["radicals"] = None
        params["radicals_names"] = None

        params["meaning_mnemonic"] = subject["data"]["meaning_mnemonic"]
        params["meaning_hint"] = subject["data"]["meaning_hint"]
        params["reading_mnemonic"] = subject["data"]["reading_mnemonic"]
        params["reading_hint"] = subject["data"]["reading_hint"]

        params.update(ds.asdict(super().from_subject(subject)))

        return cls(**params)

    def crossreference(self, cards_by_sub: dict[int, Note["SFields"]]) -> bool:
        """use card database to complete card
        return true if changes, false if unaffected"""
        if not isinstance(self.components, list):
            self.components = json.loads(self.components)

        old_radical = self.radicals
        old_radical_names = self.radicals_names

        rads = []
        for sub_id in self.components:
            n = cards_by_sub[sub_id]
            if isinstance(n.fields, RadicalSubject.Fields):
                rads.append(n)

        assert len(rads) == len(self.components), f"why are these two not same length??? {rads} vs. {self.components}"

        self.radicals = ", ".join(rad.fields.radical for rad in rads)
        self.radicals_names = ", ".join(rad.fields.radical_name for rad in rads)

        return (old_radical != self.radicals or
            old_radical_names != self.radicals_names)

class KanjiSubject(SubjectBase):
    Fields = KFields

    @classmethod
    def get_type(cls) -> SubjectTypes:
        return SubjectTypes.KANJI

    @classmethod
    @mcache
    def get_temp_recognition(cls):
        return CardTemplate(
            Name = "Recognition",
            Front = (RES_FOLDER / "html/kanji Model_Recognition_f.html").read_text(),
            Back = (RES_FOLDER / "html/kanji Model_Recognition_b.html").read_text(),
        )

    @classmethod
    @mcache
    def get_temp_reading(cls):
        return CardTemplate(
            Name = "Reading",
            Front = (RES_FOLDER / "html/kanji Model_Reading_f.html").read_text(),
            Back = (RES_FOLDER / "html/kanji Model_Reading_b.html").read_text(),
        )

    @classmethod
    @mcache
    def get_model(cls):
        return Model(
            name="Kanji Model - wanideck",
            fields=get_field_list(cls.Fields),
            templates=[cls.get_temp_recognition(), cls.get_temp_reading()],
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
        fields = cls.Fields.from_subject(subject)
        level = subject["data"]["level"]
        def fac(deck: str):
            return cls.get_note(deck, fields, level)

        return fac, None


