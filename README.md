# qobuz-dlp
A complete lossless and hi-res music downloader for [Qobuz](https://www.qobuz.com/).

This is a fork of the [original repo which has gone unmaintained](https://github.com/vitiko98/qobuz-dl).

[![PyPI Version](https://img.shields.io/pypi/v/qobuz-dlp.svg)](https://pypi.org/project/qobuz-dlp/)

## Features

* Download FLAC and MP3 files from Qobuz
* Explore and download music directly from your terminal with **interactive** or **lucky** mode
* Download albums, tracks, artists, playlists and labels with **download** mode
* Download music from last.fm playlists (Spotify, Apple Music and Youtube playlists are also supported through this method)
* Queue support on **interactive** mode
* Effective duplicate handling with own portable database
* Support for albums with multiple discs
* Support for M3U playlists
* Downloads URLs from text file
* Extended tags
* And more

## Getting started

- Get an active subscription to Qobuz
- Install `qobuz-dlp` with `pip`
```bash
pip3 install windows-curses # Windows only
pip3 install --upgrade qobuz-dlp
```
- Run qobuz-dlp and enter your credentials
```bash
qobuz-dlp # or qobuz-dlp.exe for Windows
```

## Usage
```
A complete lossless and hi-res music downloader for Qobuz.
See usage examples at https://github.com/infojunkie/qobuz-dlp.py?tab=readme-ov-file#examples.

options:
  -h, --help         show this help message and exit
  -v, --version      show version information
  -r, --reset        create/reset config file
  -p, --purge        purge/delete downloaded-IDs database
  -c, --show-config  show configuration
  --debug            show debug information

commands:
  run qobuz-dlp <command> --help for more info
  (e.g. qobuz-dlp fun --help)

  {fun,dl,lucky}
    fun              interactive mode
    dl               input mode
    lucky            lucky mode
```

## Examples

### Download mode
Download URL in 24B<96khz quality
```bash
qobuz-dlp dl https://play.qobuz.com/album/qxjbxh1dc3xyb -q 7
```
Download multiple URLs to custom directory
```bash
qobuz-dlp dl https://play.qobuz.com/artist/2038380 https://play.qobuz.com/album/ip8qjy1m6dakc -d "Some pop from 2020"
```
Download multiple URLs from text file
```bash
qobuz-dlp dl this_txt_file_has_urls.txt
```
Download albums from a label and also embed cover art images into the downloaded files
```bash
qobuz-dlp dl https://play.qobuz.com/label/7526 --embed-art
```
Download a Qobuz playlist in maximum quality
```bash
qobuz-dlp dl https://play.qobuz.com/playlist/5388296 -q 27
```
Download all the music from an artist except singles, EPs and VA releases
```bash
qobuz-dlp dl https://play.qobuz.com/artist/2528676 --albums-only
```

### Last.fm playlists
> Last.fm has a new feature for creating playlists: you can create your own based on the music you listen to or you can import one from popular streaming services like Spotify, Apple Music and Youtube. Visit: `https://www.last.fm/user/<your profile>/playlists` (e.g. https://www.last.fm/user/vitiko98/playlists) to get started.

Download a last.fm playlist in the maximum quality
```bash
qobuz-dlp dl https://www.last.fm/user/vitiko98/playlists/11887574 -q 27
```

Run `qobuz-dlp dl --help` for more info.

### Interactive mode
Run interactive mode with a limit of 10 results
```bash
qobuz-dlp fun -l 10
```
Type your search query, then:
```
Logging...
Logged: OK
Membership: Studio


Enter your search: [Ctrl + c to quit]
- fka twigs magdalene
```
`qobuz-dlp` will bring up a nice list of releases. Now choose whatever releases you want to download (everything else is interactive).

Run `qobuz-dlp fun --help` for more info.

### Lucky mode
Download the first album result
```bash
qobuz-dlp lucky playboi carti die lit
```
Download the first 5 artist results
```bash
qobuz-dlp lucky joy division -n 5 --type artist
```
Download the first 3 track results in 320 quality
```bash
qobuz-dlp lucky eric dolphy remastered --type track -n 3 -q 5
```
Download the first track result without cover art
```bash
qobuz-dlp lucky jay z story of oj --type track --no-cover
```

Run `qobuz-dlp lucky --help` for more info.

### Other
Reset your config file
```bash
qobuz-dlp -r
```

By default, `qobuz-dlp` will skip already downloaded items by ID with the message `This release ID ({item_id}) was already downloaded`. To avoid this check, add the flag `--no-db` at the end of a command. In extreme cases (e.g. lost collection), you can run `qobuz-dlp -p` to completely reset the database.

## Development
- Install [`poetry`](https://python-poetry.org/docs/#installation)
- `poetry install && poetry build && pip install .`

```python
import logging
from qobuz_dl.core import QobuzDL

logging.basicConfig(level=logging.INFO)

email = "your@email.com"
password = "your_password"

qobuz = QobuzDL()
qobuz.get_tokens() # get 'app_id' and 'secrets' attrs
qobuz.initialize_client(email, password, qobuz.app_id, qobuz.secrets)

qobuz.handle_url("https://play.qobuz.com/album/va4j3hdlwaubc")
```

Attributes, methods and parameters have been named as self-explanatory as possible.

## Disclaimer and credits
* This tool was written for educational purposes. I will not be responsible if you use this program in bad faith. By using it, you are accepting the [Qobuz API Terms of Use](https://static.qobuz.com/apps/api/QobuzAPI-TermsofUse.pdf).
* `qobuz-dlp` is not affiliated with Qobuz
* `qobuz-dlp` is a continuation of the work started with `qobuz-dl`, written by vitiko98.
* `qobuz-dl` was inspired by the discontinued Qo-DL-Reborn. This tool uses two modules from Qo-DL: `qopy` and `spoofer`, both written by Sorrow446 and DashLt.
