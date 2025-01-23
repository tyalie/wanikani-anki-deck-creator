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
                wanideck.update_cards_from_wk(not args.disable_suspend_new)

                # unsuspend requirements
                wanideck.process_progress()

        case "update":
            wanideck.update_cards_from_wk(not args.disable_suspend_new)

        case "progress":
            wanideck.process_progress()

if __name__ == "__main__":
    main()
