from typing import Callable
import dataclasses as ds

from ..models import RES_FOLDER, CardTemplate, Model, get_field_list
from ..notes import Note
from ..config import Config

from .types import SubjectTypes

from .base import SFields, SubjectBase, mcache

@ds.dataclass
class KFields(SFields):
    kanji: str
    kanji_meaning: str
    reading_on: str
    reading_kun: str

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

        params["radicals"] = None
        params["radicals_names"] = None

        params["meaning_mnemonic"] = subject["data"]["meaning_mnemonic"]
        params["meaning_hint"] = subject["data"]["meaning_hint"]
        params["reading_mnemonic"] = subject["data"]["reading_mnemonic"]
        params["reading_hint"] = subject["data"]["reading_hint"]

        params.update(ds.asdict(super().from_subject(subject)))

        return cls(**params)

    def crossreference(self, cards_by_sub: dict[int, Note["SFields"]]) -> bool:
        old_radical = self.radicals
        old_radical_names = self.radicals_names

        self.radicals, self.radicals_names = self._reference_reqs(cards_by_sub)

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
    def parse_wk_sub(cls, subject: dict, config: Config | None = None) ->  tuple[Callable[[str], Note], list[dict[str, str]] | None]:
        fields = cls.Fields.from_subject(subject)
        level = subject["data"]["level"]
        def fac(deck: str):
            return cls.get_note(deck, fields, level)

        return fac, None


