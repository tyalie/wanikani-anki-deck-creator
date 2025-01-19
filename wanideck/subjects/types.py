from enum import Enum
from typing import Type


class SubjectTypes(Enum):
    RADICALS = "Radicals"
    KANJI = "Kanji"

    def to_cls(self) -> Type:
        from . import RadicalSubject, KanjiSubject
        match self:
            case self.RADICALS:
                return RadicalSubject
            case self.KANJI:
                return KanjiSubject

    @property
    def name(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, v: str) -> "SubjectTypes | None":
        try:
            return cls(v)
        except ValueError:
            return None
