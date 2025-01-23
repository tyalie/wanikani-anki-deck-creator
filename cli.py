#!/usr/bin/env python3
"""
Simple cli to manage your wanikani->anki lessons
"""

import argparse
import logging
from wanideck.config import Config
from wanideck.wanideck import WaniDeck

def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-c", "--config", default="./config.toml", help="Location to config toml")
    parser.add_argument("-v", "--verbose", default=0, action="count", help="Verbosity level (more -v -> more verbose)")
    parser.add_argument("--disable-suspend-new", action="store_true", help="Disable that new cards are disabled automatically")
    parser.add_argument("--sync", action="store_true", help="Sync anki with ankiweb after commands finished")

    parser.add_argument("--insert-individually", action="store_true", help="If set, each card will be inserted individually - helps debug problems but slower")

    sub = parser.add_subparsers(required=True, dest='submodule')

    init = sub.add_parser("init", help="initialize the anki deck")
    init.add_argument("--no-download", action="store_true", help="Do not download cards from WaniKani")

    syncuser = sub.add_parser("syncuser", help="sync user data from wanikani to anki")

    updater = sub.add_parser("update", help="update anki deck from wanikani")

    progress = sub.add_parser("progress", help="process progress - unlock new cards if possible")

    return parser

def main():
    args = build_parser().parse_args()

    # setup logging using verbosity level
    logging.basicConfig(level=max(1, 3 - args.verbose) * 10)

    logging.debug(f"Arguments namespace: {args}")

    conf = Config.load(args.config)

    wanideck = WaniDeck(conf)

    match args.submodule:
        case "init":
            wanideck.create_deck()

            if not args.no_download:
                # do our first sync
                wanideck.update_cards_from_wk(not args.disable_suspend_new, args.insert_individually)

                # sync current status
                wanideck.enter_wanikani_status_in_anki()

                # unsuspend requirements
                wanideck.process_progress()


        case "update":
            wanideck.update_cards_from_wk(not args.disable_suspend_new, args.insert_individually)

        case "progress":
            wanideck.process_progress()

        case "syncuser":
            wanideck.enter_wanikani_status_in_anki()

    if args.sync:
        wanideck.do_webanki_sync()

if __name__ == "__main__":
    main()
