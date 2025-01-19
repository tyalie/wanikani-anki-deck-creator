from dataclasses import dataclass, field, fields
from typing import Generic, TypeVar

@dataclass
class Fields:
    def to_dict(self) -> dict:
        d = {}

        for f in fields(self):
            d[f.name] = str(getattr(self, f.name))

        return d

    @classmethod
    def from_dict(cls, data) -> "Fields":
        _datal = list(data.items())
        _datal.sort(key=lambda e: e[1]["order"])

        _data = {e[0]: e[1]["value"] for e in _datal}

        return cls(**_data)

@dataclass
class NoteOptions:
    allowDuplicate: bool = False
    duplicateScope: str = "deck"
    duplicateScopeOptions: dict = field(default_factory=dict)

@dataclass
class NoteMetadata:
    mod: int
    cards: list[int]
    profile: str
    note_id: int

T = TypeVar("T", bound=Fields)

@dataclass
class Note(Generic[T]):
    deck: str | None
    model: str
    fields: T
    tags: list[str] = field(default_factory=list)

    options: NoteOptions = field(default_factory=NoteOptions)
    metadata: None | NoteMetadata = None


@dataclass
class MetadataFields(Fields):
    last_updated: int

def get_note_metadata(deck, fields: MetadataFields):
    from .models import get_model_metadata
    return Note(
        deck=deck,
        model=get_model_metadata().name,
        fields=fields,
    )

