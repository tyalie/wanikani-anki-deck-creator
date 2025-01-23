import json
import requests
import dataclasses as ds

from typing import Any, Type

import logging

from .models import CardTemplate, Model
from .notes import Card, CardMemoryState, CardMetadata, Note, NoteMetadata, Fields

logger = logging.getLogger("AnkiConnect")

class AnkiConnect:
    @ds.dataclass
    class NewNote:
        note: Note
        audios: list | None = None
        videos: list | None = None
        pictures: list | None = None

        def to_params(self):
            params = dict(
                deckName=self.note.deck,
                modelName=self.note.model,
                fields=self.note.fields.to_dict(),
                options=ds.asdict(self.note.options),
                tags=self.note.tags,
            )

            if self.audios is not None:
                params["audio"] = self.audios
            if self.videos is not None:
                params["video"] = self.videos
            if self.pictures is not None:
                params["picture"] = self.pictures

            return params

    def __init__(self, base_url: str = "http://127.0.0.1:8765") -> None:
        self._base_url = base_url
        pass

    def _request(self, action: str, **params) -> dict:
        return {'action': action, 'params': params, 'version': 6}

    def _invoke(self, action: str, **params) -> Any:
        requestJson = json.dumps(self._request(action, **params)).encode('utf-8')
        logger.debug(f"Requesting {action} to anki-connect (data={requestJson[:100] + (requestJson[100:] and b'..')})")
        r = requests.get(self._base_url, data=requestJson)

        response = r.json()
        if len(response) != 2:
            raise Exception('response has an unexpected number of fields')
        if 'error' not in response:
            raise Exception('response is missing required error field')
        if 'result' not in response:
            raise Exception('response is missing required result field')
        if response['error'] is not None:
            raise Exception(response['error'])
        return response['result']

    def sync(self):
        self._invoke("sync")

    def createDeck(self, deck: str) -> int:
        return int(self._invoke('createDeck', deck=deck))

    def getDeckNames(self) -> list:
        return self._invoke('deckNames')

    def getDeckNamesAndIds(self) -> dict:
        return self._invoke('deckNamesAndIds')

    def getDeckConfig(self, deck: str) -> dict:
        return self._invoke("getDeckConfig", deck=deck)

    def createModel(self, model: Model):
        params: dict[str, Any] = dict(
            modelName=model.name,
            inOrderFields=model.fields,
            cardTemplates=[ds.asdict(cardTemplate) for cardTemplate in model.templates]
        )

        if model.css is not None:
            params['css'] = model.css
        if model.isCloze is not None:
            params['isCloze'] = model.isCloze

        return self._invoke('createModel', **params)

    def getModelFieldNames(self, model) -> list[str]:
        return self._invoke('modelFieldNames', modelName=model)

    def getModelNames(self) -> list[str]:
        return self._invoke('modelNames')

    def addModelField(self, model: str, field: str):
        self._invoke('modelFieldAdd', modelName=model, fieldName=field)

    def getModelStyling(self, model: str) -> str | None:
        return self._invoke("modelStyling", modelName=model)["css"]

    def updateModelStyling(self, model: str, css: str):
        self._invoke("updateModelStyling", model=dict(name=model, css=css))

    def getModelTemplates(self, model: str) -> list[CardTemplate]:
        data = self._invoke("modelTemplates", modelName=model)

        templates = []
        for name in data:
            templates.append(CardTemplate(
                Name=name,
                Front=data[name]["Front"],
                Back=data[name]["Back"]
            ))

        return templates

    def updateModelTemplates(self, model: str, templates: list[CardTemplate]):
        params = dict(
            name=model,
            templates={e.Name: dict(Front=e.Front, Back=e.Back) for e in templates}
        )
        self._invoke("updateModelTemplates", model=params)

    def removeModelTemplate(self, model: str, template_name: str):
        self._invoke("modelTemplateRemove", modelName=model, templateName=template_name)

    def addModelTemplate(self, model: str, template: CardTemplate):
        self._invoke('modelTemplateAdd', modelName=model, template=ds.asdict(template))

    def addNote(self, new_note: NewNote) -> int:
        return self._invoke('addNote', note=new_note.to_params())

    def addNotes(self, new_notes: list[NewNote]):
        return self._invoke('addNotes', notes=[n.to_params() for n in new_notes])

    def findNotes(self, query: str) -> list[int]:
        return self._invoke("findNotes", query=query)

    def findCards(self, query: str) -> list[int]:
        return self._invoke("findCards", query=query)

    def findNote(self, query: str) -> int | None:
        """Only returns one iff exactly one match was found, else None"""
        notes = self.findNotes(query)
        if len(notes) == 1:
            return notes[0]
        else:
            logging.error(f"Found {len(notes)} matches. This is not a single match")
            return None

    def updateNoteFields(self, id:int, fields: dict | Fields):
        if isinstance(fields, Fields):
            fields = fields.to_dict()

        params = dict(
            id=id,
            fields=fields
        )
        self._invoke("updateNoteFields", note=params)

    def getNotesInfo(
            self, *, notes_id: list[int] | None = None, query: str | None = None,
            fields: None | Type[Fields] = None
        ) -> list[Note]:
        params = dict()
        if notes_id is not None:
            params["notes"] = notes_id
        if query is not None:
            params["query"] = query

        notes = []
        for elem in self._invoke("notesInfo", **params):
            notes.append(Note(
                deck=None,
                model=elem["modelName"],
                tags=elem["tags"],
                fields=elem["fields"] if fields is None else fields.from_dict(elem["fields"]),
                metadata=NoteMetadata(
                    mod=elem["mod"],
                    cards=elem["cards"],
                    profile=elem["profile"],
                    note_id=elem["noteId"]
                )
            ))
        return notes

    def getCardsInfo(
            self, *, cards_id: list[int],
            fields: None | Type[Fields] = None
        ) -> list[Card]:
        cards = []
        for elem in self._invoke("cardsInfo", cards=cards_id):
            cards.append(Card(
                deck=elem["deckName"],
                model=elem["modelName"],
                fields=elem["fields"] if fields is None else fields.from_dict(elem["fields"]),
                memory_state=None if not elem["fsrs"] else CardMemoryState(
                    stability=elem["fsrs"]["stability"],
                    difficulty=elem["fsrs"]["difficulty"]
                ),
                metadata=CardMetadata(
                    card_id=elem["cardId"],
                    note_id=elem["note"]
                ),

                interval=int(elem["interval"]),
                is_suspended=None,
                note=None,
            ))
        return cards

    def areSuspended(self, cards_id: list[int]) -> dict[int, bool]:
        return dict(zip(cards_id, self._invoke("areSuspended", cards=cards_id)))

    def unsuspend(self, cards_id: list[int]):
        self._invoke("unsuspend", cards=cards_id)

    def suspend(self, cards_id: list[int]):
        self._invoke("suspend", cards=cards_id)

    def storeMediaFile(self, filename: str, data: str | None = None, path: str | None = None, url: str | None = None):
        params = dict(filename=filename)
        if data is not None:
            params["data"] = data
        if path is not None:
            params["path"] = path
        if url is not None:
            params["url"] = url

        self._invoke("storeMediaFile", **params)


if __name__ == "__main__":
    ak = AnkiConnect()
    ak._invoke('createDeck', deck='test1')
    result = ak._invoke('deckNames')
    print('got list of decks: {}'.format(result))
