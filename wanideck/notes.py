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

@dataclass
class CardMetadata:
    card_id: int
    note_id: int

@dataclass
class CardMemoryState:
    """FSRS memory state for a card"""
    stability: float
    difficulty: float

T = TypeVar("T", bound=Fields)

@dataclass
class Note(Generic[T]):
    deck: str | None
    model: str
    fields: T
    tags: list[str] = field(default_factory=list)

    options: NoteOptions = field(default_factory=NoteOptions)
    metadata: None | NoteMetadata = None

    @property
    def level(self) -> int | None:
        """get level through tags (if it exists)"""
        level_tag = list(filter(lambda s: s.startswith("level"), self.tags))
        if len(level_tag) != 1:
            return None
        return int(level_tag[0][len("level"):])

@dataclass
class Card(Generic[T]):
    deck: str
    model: str
    fields: T
    is_suspended: bool | None
    note: Note | None

    metadata: CardMetadata
    memory_state: CardMemoryState | None
    interval: int


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
