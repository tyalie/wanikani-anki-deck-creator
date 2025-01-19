import abc
import dataclasses as ds
from typing import Callable, Generic, TypeVar, Any

from .types import SubjectTypes

from ..models import Model
from ..notes import Fields, Note

@ds.dataclass
class SFields(Fields):
    """generall fields that should be supported in subjects"""
    _: ds.KW_ONLY
    lesson_pos: int
    follow_up_ids: list[int]
    sub_id: int
    url: str

    @classmethod
    def uniq_name_from_sub(cls, subject: dict) -> str:
        return f"{subject['object']}_{subject['data']['slug']}"

    @classmethod
    def from_subject(cls, subject: dict) -> "SFields":
        """parses the fields needed SField from subject"""
        params = dict()

        params["lesson_pos"] = subject["data"]["lesson_position"]
        params["sub_id"] = subject["id"]
        params["url"] = subject["object"] + "/" + subject["data"]["slug"]

        params["follow_up_ids"] = subject["data"].get("amalgamation_subject_ids", [])

        return SFields(**params)

    @classmethod
    def _get_meanread_list(cls, meanread: dict, type_filter: str | None = None) -> str:
        """helper function convert meaning/reading objects into a respective list

        - for readings: type_filter can be specified to allow onyomi und kunyomi filter
        - primary is being underlined with <u></u>
        """
        def wrap(meaning: dict):
            key = "meaning" if "meaning" in meaning else "reading"

            if meaning["primary"]:
                return f"<u>{meaning[key]}</u>"
            return meaning[key]

        return cls.unroll_list([
            wrap(m) for m in meanread
            if type_filter is None or m["type"] == type_filter
        ])

    @staticmethod
    def unroll_list(vs: list[Any]) -> str:
        return ", ".join(str(v) for v in vs)

    def crossreference(self, cards_by_sub: dict[int, Note["SFields"]]) -> bool:
        """use card database to complete card
        return true if changes, false if unaffected"""
        return False


TFields = TypeVar("TFields", bound="SFields")

def mcache(fn):
    def cachable(cls):
        if getattr(cls, f"_{fn.__name__}_tmp", None) is None:
            setattr(cls, f"_{fn.__name__}_tmp", fn(cls))
        return getattr(cls, f"_{fn.__name__}_tmp")
    return cachable

class SubjectBase(abc.ABC, Generic[TFields]):
    Fields = SFields

    @classmethod
    @abc.abstractmethod
    def get_types(cls) -> SubjectTypes:
        ...

    @classmethod
    @abc.abstractmethod
    def get_model(cls) -> Model:
        ...

    @classmethod
    @abc.abstractmethod
    def get_note(cls, deck: str, fields: TFields, level: int) -> Note:
        """get an initialized note from parameters"""
        ...

    @classmethod
    @abc.abstractmethod
    def parse_wk_sub(cls, subject: dict) ->  tuple[Callable[[str], Note], dict | None]:
        """parses fields and required media downloads"""
        ...

