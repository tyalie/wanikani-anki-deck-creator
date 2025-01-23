from typing import Callable
import dataclasses as ds

from ..models import RES_FOLDER, CardTemplate, Model, get_field_list
from ..notes import Note
from ..config import Config

from .types import SubjectTypes
from .base import SFields, SubjectBase, mcache, logger

@ds.dataclass
class VFields(SFields):
    vocab: str
    vocab_meaning: str
    reading: str

    speech_type: str

    meaning_exp: str
    reading_exp: str

    kanjis: list[str] | str
    kanji_names: list[str] | str

    audio_m: str
    audio_f: str

    context_jp1: str = ""
    context_en1: str = ""
    context_jp2: str = ""
    context_en2: str = ""
    context_jp3: str = ""
    context_en3: str = ""


    @staticmethod
    def _list_to_nat_list(vs: list[str]) -> str:
        if len(vs) == 0:
            return ""
        elif len(vs) == 1:
            return vs[0]
        else:
            return ", ".join(vs[0:-1]) + " and " + vs[-1]

    @classmethod
    def from_subject(cls, subject: dict) -> "VFields":
        params = dict()

        params["vocab"] = subject["data"]["characters"]
        params["vocab_meaning"] = cls._get_meanread_list(subject["data"]["meanings"])
        params["reading"] = cls._get_meanread_list(subject["data"]["readings"])

        params["speech_type"] = cls._list_to_nat_list(subject["data"]["parts_of_speech"])

        for i, context in enumerate(subject["data"]["context_sentences"]):
            if i >= 3:
                break
            params[f"context_jp{i + 1}"] = context["ja"]
            params[f"context_en{i + 1}"] = context["en"]

        params["meaning_exp"] = subject["data"]["meaning_mnemonic"]
        params["reading_exp"] = subject["data"]["reading_mnemonic"]

        params["kanjis"] = None
        params["kanji_names"] = None

        params["audio_m"] = f"[sound:{params['vocab']}_m.webm]"
        params["audio_f"] = f"[sound:{params['vocab']}_f.webm]"

        params.update(ds.asdict(super().from_subject(subject)))
        return cls(**params)

    def crossreference(self, cards_by_sub: dict[int, Note["SFields"]]) -> bool:
        old_kanji = self.kanjis
        old_kanji_names = self.kanji_names

        self.kanjis, self.kanji_names = self._reference_reqs(cards_by_sub)

        return (old_kanji != self.kanjis or
            old_kanji_names != self.kanji_names)


class VocabSubject(SubjectBase):
    Fields = VFields

    @classmethod
    def get_type(cls) -> SubjectTypes:
        return SubjectTypes.VOCAB

    @classmethod
    @mcache
    def get_temp_recognition(cls):
        return CardTemplate(
            Name = "Recognition",
            Front = (RES_FOLDER / "html/vocab Model_Recognition_f.html").read_text(),
            Back =  (RES_FOLDER / "html/vocab Model_Recognition_b.html").read_text()
        )

    @classmethod
    @mcache
    def get_temp_reading(cls):
        return CardTemplate(
            Name = "Reading",
            Front = (RES_FOLDER / "html/vocab Model_Reading_f.html").read_text(),
            Back =  (RES_FOLDER / "html/vocab Model_Reading_b.html").read_text()
        )

    @classmethod
    @mcache
    def get_model(cls):
        return Model(
            name="Vocab Model - wanideck",
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
            tags=[f"level{level}", cls.get_type().name]
        )

    @classmethod
    def parse_wk_sub(cls, subject: dict, config: Config | None = None) ->  tuple[Callable[[str], Note], list[dict[str, str]] | None]:
        fields = cls.Fields.from_subject(subject)
        level = subject["data"]["level"]

        def fac(deck: str):
            return cls.get_note(deck, fields, level)

        assert config is not None

        return fac, cls._get_req_media_from_sub(subject, config)

    @classmethod
    def _get_req_media_from_sub(cls, subject: dict, config: Config) -> list[dict[str, str]] | None:
        audios = subject["data"].get("pronunciation_audios", [])
        if len(audios) == 0:
            logger.warning(f"vocab: {subject['data']['characters']} could not find audios")
            return None

        _f_name = subject["data"]['characters']
        def get_gendered(audios: dict, gender: str) -> str | None:
            for audio in audios:
                if audio["content_type"] == str(config.deck_audio_format) and \
                    audio["metadata"]["gender"] == gender:
                    return audio["url"]

        return [dict(
                filename=f"{_f_name}_{gender[0]}.{config.deck_audio_format.fext}",
                url=url
            ) for gender in ["male", "female"] if (url := get_gendered(audios, gender)) is not None
        ]
