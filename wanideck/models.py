from dataclasses import dataclass, fields
from functools import cache
from pathlib import Path

RES_FOLDER = Path(__file__).parent / "../res/"

@dataclass
class CardTemplate:
    Name: str
    Front: str
    Back: str

@dataclass
class Model():
    name: str
    fields: list[str]
    templates: list[CardTemplate]

    css: None | str = None
    isCloze: bool = False

def get_field_list(ds):
    """get the list of all fields. kw_only fields come afterwards"""
    std_fields = [f.name for f in fields(ds) if not f.kw_only]
    kw_fields = [f.name for f in fields(ds) if f.kw_only]
    return std_fields + kw_fields


######################
### metadata model ###
######################

@cache
def get_temp_hidden():
    from .notes import MetadataFields
    return CardTemplate(
        Name = "hidden",
        Front = "This card should always be suspended<br>{{" + get_field_list(MetadataFields)[0] + "}}",
        Back=f"-"
    )

@cache
def get_model_metadata():
    from .notes import MetadataFields
    return Model(
        name="metadata - wanideck",
        fields=get_field_list(MetadataFields),
        templates=[get_temp_hidden()]
    )


######################
###      kanji     ###
######################

@cache
def get_temp_kanji_recognition():
    return CardTemplate(
        Name = "Recognition",
        Front = (RES_FOLDER / "html/kanji Model_Recognition_f.html").read_text(),
        Back = (RES_FOLDER / "html/kanji Model_Recognition_b.html").read_text(),
    )

@cache
def get_temp_kanji_reading():
    return CardTemplate(
        Name = "Reading",
        Front = (RES_FOLDER / "html/kanji Model_Reading_f.html").read_text(),
        Back = (RES_FOLDER / "html/kanji Model_Reading_b.html").read_text(),
    )

@cache
def get_model_kanji():
    from .notes import KanjiFields
    return Model(
        name="Kanji Model - wanideck",
        fields=get_field_list(KanjiFields),
        templates=[get_temp_kanji_recognition(), get_temp_kanji_reading()],
        css = (RES_FOLDER / "html/main.css").read_text()
    )


######################
###    radicals    ###
######################

@cache
def get_temp_radical_recognition():
    return CardTemplate(
        Name = "Recognition",
        Front = (RES_FOLDER / "html/radical Model_Recognition_f.html").read_text(),
        Back = (RES_FOLDER / "html/radical Model_Recognition_b.html").read_text(),
    )

@cache
def get_model_radical():
    from .notes import RadicalFields
    return Model(
        name="Radical Model - wanideck",
        fields=get_field_list(RadicalFields),
        templates=[get_temp_radical_recognition()],
        css = (RES_FOLDER / "html/main.css").read_text()
    )

