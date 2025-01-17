from dataclasses import dataclass, field, fields

@dataclass
class Fields:
    def to_dict(self) -> dict:
        d = {}

        for f in fields(self):
            d[f.name] = str(self.__getattribute__(f.name))

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

@dataclass
class Note:
    deck: str | None
    model: str
    fields: Fields
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


@dataclass
class KanjiFields(Fields):
    Kanji: str
    Kanji_Meaning: str
    Reading_On: str
    Reading_Kun: str
    Radicals: str
    Radicals_Icons: str
    Radicals_Names: str
    Radicals_Icons_Names: str
    Meaning_Mnemonic: str
    Meaning_Info: str
    Reading_Mnemonic: str
    Reading_Info: str
    sort_id: int

def get_note_kanji(deck, fields: KanjiFields):
    from .models import get_model_kanji
    return Note(
        deck=deck,
        model=get_model_kanji().name,
        fields=fields,
    )


@dataclass
class RadicalFields(Fields):
    Radical_Name: str
    Radical: str
    Radical_Meaning: str
    Radical_Icon: str
    sort_id: int

def get_note_radical(deck, fields: RadicalFields):
    from .models import get_model_radical
    return Note(
        deck=deck,
        model=get_model_radical().name,
        fields=fields,
    )
