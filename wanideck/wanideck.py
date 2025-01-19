from typing import Any
from wanideck.subjects.kanji import KanjiSubject
from .subjects import RadicalSubject, SubjectTypes
from .deck import DeckBuilder
from .notes import MetadataFields, Note
from .config import Config
from .wkapi import WaniKaniAPI
from .ankiconnect import AnkiConnect

import logging

logger = logging.getLogger("WaniDeck")

class WaniDeck:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._wk_api = WaniKaniAPI(api_token=config.user_api_token)
        self._anki_api = AnkiConnect()
        self._deck = DeckBuilder(self._anki_api, self._config.deck_name)

    def _get_last_update(self) -> int:
        id = self._deck.get_metadata_note()
        return int(self._anki_api.getNotesInfo(notes_id=[id], fields=MetadataFields)[0].fields.last_updated)

    def _update_metadata(self, last_update:int):
        id = self._deck.get_metadata_note()
        self._anki_api.updateNoteFields(id, dict(last_update=str(last_update)))

    def create_deck(self):
        self._deck.create_deck()

    def update_cards_from_wk(self):
        """
        This is for real now. Sync our cards from the WaniKani webpage
        """
        # get last update
        last_update_ts = self._get_last_update()

        # make sure we consider subscription
        max_level = self._wk_api.get_max_level()
        max_level = 4

        # first off get all new subjects
        subjects = self._wk_api.get_all_subjects(last_update_ts=last_update_ts, max_level=max_level)

        logging.info(f"Downloaded {len(subjects)} new subjects after ts {last_update_ts}")

        new_notes: list[Note] = []
        new_medias = []
        # do postprocessing of subjects, this entails
        # - retrieving missing files (like audio or images that represent the radical)
        # - group subjects into categories
        for subject in subjects:
            # retrieve missing audio
            if subject["object"] == "radical":
                fn_note, media = RadicalSubject.parse_wk_sub(subject)

                # check if we need any media
                if media is not None:
                    media["data"] = self._wk_api.download_resource(media["url"])
                    new_medias.append(media)

                new_notes.append(
                    self._deck.complete_note(SubjectTypes.RADICALS, fn_note)
                )

            if subject["object"] == "kanji":
                fn_note, _ = KanjiSubject.parse_wk_sub(subject)

                new_notes.append(
                    self._deck.complete_note(SubjectTypes.KANJI, fn_note)
                )


        self._deck.add_or_update_new_notes(new_notes)

        self._deck.insert_media(new_medias)

        ## create dict with sub_id idx for cross reference
        all_notes = self._deck.get_all()
        cards_by_sub_id = {int(note.fields.sub_id): note for note in all_notes}

        changed_cards = []
        # cross reference cards and look for changes
        for note in all_notes:
            if note.fields.crossreference(cards_by_sub_id):
                assert note.metadata is not None, f"??? {note}"
                changed_cards.append((note.metadata.note_id, note))

        self._deck.update_notes(changed_cards)

