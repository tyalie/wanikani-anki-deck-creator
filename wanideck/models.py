from dataclasses import dataclass, fields
from functools import cache
from pathlib import Path

RES_FOLDER = Path(__file__).parent / "../res/"

@dataclass(frozen=True)
class CardTemplate:
    Name: str
    Front: str
    Back: str

@dataclass(frozen=True)
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

