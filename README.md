# WaniKani four Anki deck creator

Convert your [WaniKani][^1] lessons and progress into an offline anki deck using
a cli interface. The cli also supports the unlock mechanism like wanikani does,
but requires to be run frequently for this to work. It respects our
subscription status (see `wanideck/subscription.py`).

## Requirements
newest anki-connect in Anki

## Usage
### Initial setup

Plan some time before doing this. For all wanikani lessons this can take
upwards of ~1h without a hot cache.

Execute
```
./cli.py init
```

This will download the deck, your current progress and do the initial unlock
phase. The Anki deck is usable afterward.

### Unlock progress

In WaniKani new cards will be unlocked if their requirements are met. You can
also upgrade in level. This application has reimplemented their algorithm (from
what is publicly available) and ports it to Anki. For that to work the
corresponding command needs to be executed frequently, I suggest having a
server where this is periodically executed instead of doing it manually.

Execute
```
./cli.py progress
```

### Update deck

WaniKani sometimes updates their cards. In these cases execute to transfer the
changes (not fully tested yet). The update will only entail the new subset,
instead of doing a full refresh.

```
./cli.py update
```

### Config

The application can be configured using the `config.toml` or environment variables.

### CLI help
```
usage: cli.py [-h] [-c CONFIG] [-v] [--disable-suspend-new] [--sync] [--insert-individually] {init,syncuser,update,progress} ...

Simple cli to manage your wanikani->anki lessons

positional arguments:
  {init,syncuser,update,progress}
    init                initialize the anki deck
    syncuser            sync user data from wanikani to anki
    update              update anki deck from wanikani
    progress            process progress - unlock new cards if possible

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Location to config toml
  -v, --verbose         Verbosity level (more -v -> more verbose)
  --disable-suspend-new
                        Disable that new cards are disabled automatically
  --sync                Sync anki with ankiweb after commands finished
  --insert-individually
                        If set, each card will be inserted individually - helps debug problems but slower
```


[^1]: https://www.wanikani.com/
