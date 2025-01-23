from .subjects import RadicalSubject, SubjectTypes, KanjiSubject, VocabSubject
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

    def do_webanki_sync(self):
        self._anki_api.sync()

    def create_deck(self):
        self._deck.create_deck()

    def update_cards_from_wk(self, should_suspend_new_cards: bool):
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

        new_notes: list[Note] = []
        new_medias = []
        # do postprocessing of subjects, this entails
        # - retrieving missing files (like audio or images that represent the radical)
        # - group subjects into categories
        for subject in subjects:
            # retrieve missing audio
            for stype in SubjectTypes:
                if subject["object"] == stype.object_name:
                    fn_note, medias = stype.to_cls().parse_wk_sub(subject, self._config)

                    # check if we need any media
                    if medias is not None:
                        for media in medias:
                            media["data"] = self._wk_api.download_resource(media["url"])
                            new_medias.append(media)

                    new_notes.append(
                        self._deck.complete_note(stype, fn_note)
                    )

        new_note_ids = self._deck.add_or_update_new_notes(new_notes)

        self._deck.insert_media(new_medias)

        ## create dict with sub_id idx for cross reference
        all_notes = self._deck.get_all_notes()
        notes_by_sub_id = {int(note.fields.sub_id): note for note in all_notes}

        changed_notes = []
        # cross reference cards and look for changes
        for note in all_notes:
            if note.fields.crossreference(notes_by_sub_id):
                assert note.metadata is not None, f"??? {note}"
                changed_notes.append((note.metadata.note_id, note))

        self._deck.update_notes(changed_notes)

        breakpoint()
        # suspend all cards if required
        if should_suspend_new_cards:
            self._deck.suspend_cards_from_notes(new_note_ids)

    def process_progress(self):
        """
        In this step your anki process is evaluated and new cards are
        unlocked according to the wani-kani algorithm (adapted to ankis terms).

        The specifics are:
            - a note is considered "learned", when for all their cards the FSRS stability is >= config.learning_stability_req_for_learned_d
                - wanikani does not have cards the same way anki has, instead cards and notes are not
                    seperate entities
            - the current level is the highest level of unlocked radicals
                - note: radicals have no requirements, except current level

            - cards (from current level) get unlocked when all their requirements are met
            - a new level is reached if 90% of all kanjis of current level are considered "learned"

        This is not a perfect mapping, but it should be good enough.
        """

        # get all cards and their information
        cards = self._deck.get_all_cards()

        # determine current level
        level = 1
        for card in cards:
            if card.note is None:
                logging.warning(f"Note property of {card} was none, this should not be")
                continue
            if card.is_suspended:
                continue
            if RadicalSubject.get_type().name not in card.note.tags:
                continue

            if card.note.level is None:
                raise ValueError("The note should have a level")

            level = max(level, card.note.level)

        # mark learned subjects (list of sub_ids)
        ## as each subject has at least two cards and all must be learned, we
        ## just iterate over all cards and use an & logic operation for sub_id
        learned_subs: dict[int, bool] = dict()

        for card in cards:
            subject = int(card.fields["sub_id"]["value"])

            is_learned = True
            if card.memory_state is not None:
                is_learned &= card.memory_state.stability >= self._config.learning_stability_req_for_learned_d
            else:
                is_learned &= card.interval >= self._config.learning_stability_req_for_learned_d

            learned_subs[subject] = learned_subs.setdefault(subject, True) & is_learned

        # check if next level
        all_kanji_for_cur_level: list[int] = []
        for card in cards:
            if card.note is None:
                continue
            if card.note.level != level:
                continue
            if KanjiSubject.get_type().name.lower() not in map(str.lower, card.note.tags):
                continue
            all_kanji_for_cur_level.append(int(card.fields["sub_id"]["value"]))

        learned_kanjis = list(filter(lambda id: learned_subs[id], all_kanji_for_cur_level))

        logging.info(f"{len(learned_kanjis)}/{len(all_kanji_for_cur_level)} of level {level} are considered learned")
        if len(learned_kanjis) >= len(all_kanji_for_cur_level) * 0.9:
            level += 1
            logging.info(f"with this a new level was archived ({level - 1} -> {level})")

        # check requirements for all notes <= current level
        notes = self._deck.get_all_notes()
        cards_to_unsuspend = []

        for note in notes:
            if note.level is None or note.level > level:
                continue
            if note.metadata is None:
                logging.error(f"Note metadata is None - {note}")
                continue

            req_complete = all(map(lambda id: learned_subs[id], note.fields.requirements))
            if req_complete:
                cards_to_unsuspend.extend(note.metadata.cards)

        # unsuspend sleeping cards
        self._deck.unsuspend(cards_to_unsuspend)
