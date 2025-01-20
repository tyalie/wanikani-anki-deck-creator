import logging
from typing import Callable

from .subjects import RadicalSubject, KanjiSubject, SubjectBase
from .models import Model, get_model_metadata
from .notes import MetadataFields, get_note_metadata, Note
from .ankiconnect import AnkiConnect
from .models import Model
from .subjects import SubjectTypes

logger = logging.getLogger("DeckBuilder")

class DeckBuilder:
    """
    Our anki deck builder which suppords building,
    but also integrating updated / new anki flash cards
    from wanikani.
    """

    def __init__(self, anki_connect: AnkiConnect, deck_name: str) -> None:
        self._anki_api = anki_connect
        self._deckname = deck_name

    def _get_anki_deck_name(self, subname: SubjectTypes | None = None):
        if subname is None:
            return self._deckname

        assert subname in SubjectTypes, f"Unknown anki deck subname {subname}"

        return f"{self._deckname}::{subname.name}"

    def complete_note(self, name: SubjectTypes | None, note_fn: Callable[[str], Note]):
        return note_fn(self._get_anki_deck_name(name))

    def get_metadata_note(self) -> int:
        notes = self._anki_api.findNotes(f"\"deck:{self._get_anki_deck_name()}\" \"note:{get_model_metadata().name}\"")
        assert len(notes) == 1, "Why are there multiple cards with metadata model in this deck?"
        return notes[0]

    def create_deck(self):
        """
        creates basic structur of deck, this contains parent group
        and subgroups. Also creates non showable card that contains
        important metainformation.
        """
        self._anki_api.createDeck(self._get_anki_deck_name())

        # create subtypes
        for t in SubjectTypes:
            self._anki_api.createDeck(self._get_anki_deck_name(t))

        # create metadata card model, if not exists
        self.check_model(get_model_metadata())

        # create our card models for learning
        self.check_model(RadicalSubject.get_model())
        self.check_model(KanjiSubject.get_model())

        # create hidden card with model or update it
        try:
            id = self.get_metadata_note()
        except AssertionError:
            logging.debug("Creating metadata card")
            metadata_note = get_note_metadata(self._get_anki_deck_name(), fields=MetadataFields(0))
            id = self._anki_api.addNote(AnkiConnect.NewNote(metadata_note))

        note_info = self._anki_api.getNotesInfo(notes_id=[id])[0]
        # suspend the metadata card. it's only for us
        assert note_info.metadata is not None
        self._anki_api.suspend(note_info.metadata.cards)

        # we are done
        logging.info(f"Successfully created deck {self._get_anki_deck_name()}")

    def check_model(self, model: Model):
        """check if models are up-to-date
        this means in regards to their fields,
        their templates and their styling
        """
        if model.name in self._anki_api.getModelNames():
            # update fields (if missing)
            model_fields = self._anki_api.getModelFieldNames(model.name)

            missing_fields = set(model.fields) - set(model_fields)

            if len(missing_fields) != 0:
                logging.info(f"model: Adding fields {missing_fields} to model {model.name}")
                for field in missing_fields:
                    self._anki_api.addModelField(model.name, field)

            # check on our styling if it exists
            if model.css:
                styling = self._anki_api.getModelStyling(model.name)
                if styling != model.css:
                    logging.info(f"Updating styling for model")
                    self._anki_api.updateModelStyling(model.name, css=model.css)

            # check on our templates
            ex_templates = self._anki_api.getModelTemplates(model.name)

            ## remove templates that we don't have (anymore)
            ## - also valide existing templates
            for ex_temp in ex_templates:
                found = None
                for temp in model.templates:
                    if temp.Name == ex_temp.Name:
                        found = temp

                if found is None:
                    self._anki_api.removeModelTemplate(model.name, ex_temp.Name)
                else:
                    # update if necessary
                    if ex_temp.Front != found.Front or ex_temp.Back != found.Back:
                        self._anki_api.updateModelTemplates(model.name, [found])

            ## add templates that don't exist yet
            for temp in model.templates:
                found = False
                for ex_temp in ex_templates:
                    found |= temp.Name == ex_temp.Name

                if not found:
                    self._anki_api.addModelTemplate(model.name, temp)
        else:
            logging.info(f"model: creating new model {model.name}")
            self._anki_api.createModel(model)

    def add_or_update_new_notes(self, notes: list[Note]):
        """Using a list of notes, identify new ones and already existing
        ones (in Anki) and insert or update them accordingly"""

        unkonwn_notes = []
        update_notes = []
        for note in notes:
            assert isinstance(note.fields, SubjectBase.Fields)
            note_ids = self._anki_api.findNotes(f'"deck:{self._get_anki_deck_name()}" "url:{note.fields.url}"')
            assert len(note_ids) <= 1, "WTF"

            note = AnkiConnect.NewNote(note)
            if len(note_ids) == 1:
                update_notes.append((note_ids[0], note))
            else:
                unkonwn_notes.append(note)

        logging.warning(f"Inserting {len(unkonwn_notes)} new notes")
        self._anki_api.addNotes(unkonwn_notes)

        logging.warning(f"Updating {len(update_notes)} notes")
        for id, note in update_notes:
            self._anki_api.updateNoteFields(id, note.note.fields)

    def update_notes(self, notes: list[tuple[int, Note]]):
        logging.warning(f"Updating {len(notes)} notes")

        for id, note in notes:
            self._anki_api.updateNoteFields(id, note.fields)


    def insert_media(self, medias: list[dict]):
        """Insert a list of medias into the deck"""
        logging.warning(f"Adding {len(medias)} new media files (duplicates are overwritten)")
        for media in medias:
            self._anki_api.storeMediaFile(**media)

    def get_all(self) -> list[Note[SubjectBase.Fields]]:
        """Get's all notes (and their details) from this deck from anki"""
        notes = []
        for stype in SubjectTypes:
            ids = self._anki_api.findNotes(
                f'"deck:{self._get_anki_deck_name()}" "tag:{stype.name}"'
            )

            notes.extend(self._anki_api.getNotesInfo(
                notes_id=ids, fields=stype.to_cls().Fields
            ))

        return notes