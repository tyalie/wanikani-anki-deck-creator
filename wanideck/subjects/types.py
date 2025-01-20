from enum import Enum
from typing import Type


class SubjectTypes(Enum):
    RADICALS = "Radicals"
    KANJI = "Kanji"
    VOCAB = "Vocabulary"

    def to_cls(self) -> Type:
        from . import RadicalSubject, KanjiSubject, VocabSubject
        match self:
            case self.RADICALS:
                return RadicalSubject
            case self.KANJI:
                return KanjiSubject
            case self.VOCAB:
                return VocabSubject

    @property
    def object_name(self) -> str:
        match self:
            case self.RADICALS:
                return "radical"
            case self.KANJI:
                return "kanji"
            case self.VOCAB:
                return "vocabulary"

    @property
    def name(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, v: str) -> "SubjectTypes | None":
        try:
            return cls(v)
        except ValueError:
            return None

