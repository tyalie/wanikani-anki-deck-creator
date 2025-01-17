from wanideck.notes import MetadataFields, get_note_metadata
from .models import Model, get_model_kanji, get_model_metadata, get_model_radical
from .config import Config
from .wkapi import WaniKaniAPI
from .ankiconnect import AnkiConnect

import logging

logger = logging.getLogger("WaniDeck")

class WaniDeck:
    SUBJECT_TYPES = [
        "Radicals",
        "Kanjis",
        "Vocabulary"
    ]

    def __init__(self, config: Config) -> None:
        self._config = config
        self._wk_api = WaniKaniAPI(api_token=config.user_api_token)
        self._anki_api = AnkiConnect()

    def _get_anki_deck_name(self, subname: str | None = None):
        if subname is None:
            return self._config.deck_name

        assert subname in self.SUBJECT_TYPES, f"Unknown anki deck subname {subname}"

        return f"{self._config.deck_name}::{subname}"

    def _get_metadata_note(self) -> int:
        notes = self._anki_api.findNotes(f"\"deck:{self._get_anki_deck_name()}\" \"note:{get_model_metadata().name}\"")
        assert len(notes) == 1, "Why are there multiple cards with metadata model in this deck?"
        return notes[0]

    def _get_last_update(self) -> int:
        id = self._get_metadata_note()
        return int(self._anki_api.getNotesInfo([id], MetadataFields)[0].fields.last_updated)

    def _update_metadata(self, last_update:int):
        id = self._get_metadata_note()
        self._anki_api.updateNoteFields(id, dict(last_update=str(last_update)))

    def _check_model(self, model: Model):
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

    def create_deck(self):
        """
        creates basic structur of deck, this contains parent group
        and subgroups. Also creates non showable card that contains
        important metainformation.
        """
        self._anki_api.createDeck(self._get_anki_deck_name())

        # create subtypes
        for t in self.SUBJECT_TYPES:
            self._anki_api.createDeck(self._get_anki_deck_name(t))

        # create metadata card model, if not exists
        self._check_model(get_model_metadata())

        # create our card models for learning
        self._check_model(get_model_radical())
        self._check_model(get_model_kanji())

        # create hidden card with model or update it
        try:
            id = self._get_metadata_note()
        except AssertionError:
            logging.debug("Creating metadata card")
            metadata_note = get_note_metadata(self._get_anki_deck_name(), fields=MetadataFields(0))
            id = self._anki_api.addNote(metadata_note)

        note_info = self._anki_api.getNotesInfo([id])[0]
        # suspend the metadata card. it's only for us
        assert note_info.metadata is not None
        self._anki_api.suspend(note_info.metadata.cards)

        # we are done
        logging.info(f"Successfully created deck {self._get_anki_deck_name()}")

    def update_cards_from_wk(self):
        """
        This is for real now. Sync our cards from the WaniKani webpage
        """
        # get last update
        last_update_ts = self._get_last_update()

        # make sure we consider subscription
        max_level = self._wk_api.get_max_level()
        max_level = 1

        # first off get all new subjects
        subjects = self._wk_api.get_all_subjects(last_update_ts=last_update_ts, max_level=max_level)

        logging.info(f"Downloaded {len(subjects)} new subjects after ts {last_update_ts}")

        new_rads = []
        new_kanji = []
        new_vocs = []
        # do postprocessing of subjects, this entails
        # - retrieving missing files (like audio or images that represent the radical)
        # - group subjects into categories
        for subject in subjects:
            # retrieve missing audio
            if subject["object"] == "radical":
                breakpoint()
            ...
