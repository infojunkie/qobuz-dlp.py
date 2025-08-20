import re
import os
import logging

from mutagen.flac import FLAC, Picture
import mutagen.id3 as id3
from mutagen.id3 import ID3NoHeaderError

logger = logging.getLogger(__name__)


# unicode symbols
COPYRIGHT, PHON_COPYRIGHT = "\u2117", "\u00a9"
# if a metadata block exceeds this, mutagen will raise error
# and the file won't be tagged
FLAC_MAX_BLOCKSIZE = 16777215

ID3_LEGEND = {
    "album": id3.TALB,
    "albumartist": id3.TPE2,
    "artist": id3.TPE1,
    "comment": id3.COMM,
    "composer": id3.TCOM,
    "copyright": id3.TCOP,
    "date": id3.TDAT,
    "genre": id3.TCON,
    "isrc": id3.TSRC,
    "label": id3.TPUB,
    "performer": id3.TOPE,
    "title": id3.TIT2,
    "year": id3.TYER,
}


def _get_title(track_dict):
    title = track_dict["title"]
    version = track_dict.get("version")
    if version:
        title = f"{title} ({version})"
    # for classical works
    if track_dict.get("work"):
        title = f"{track_dict['work']}: {title}"

    return title


def _format_copyright(s: str) -> str:
    if s:
        s = s.replace("(P)", PHON_COPYRIGHT)
        s = s.replace("(C)", COPYRIGHT)
    return s


def _format_genres(genres: list) -> str:
    """Fixes the weirdly formatted genre lists returned by the API.
    >>> g = ['Pop/Rock', 'Pop/Rock→Rock', 'Pop/Rock→Rock→Alternatif et Indé']
    >>> _format_genres(g)
    'Pop, Rock, Alternatif et Indé'
    """
    genres = re.findall(r"([^\u2192\/]+)", "/".join(genres))
    no_repeats = []
    [no_repeats.append(g) for g in genres if g not in no_repeats]
    return ", ".join(no_repeats)


def _embed_flac_img(root_dir, audio: FLAC):
    emb_image = os.path.join(root_dir, "cover.jpg")
    multi_emb_image = os.path.join(
        os.path.abspath(os.path.join(root_dir, os.pardir)), "cover.jpg"
    )
    if os.path.isfile(emb_image):
        cover_image = emb_image
    else:
        cover_image = multi_emb_image

    try:
        # rest of the metadata still gets embedded
        # when the image size is too big
        if os.path.getsize(cover_image) > FLAC_MAX_BLOCKSIZE:
            raise Exception(
                "downloaded cover size too large to embed. "
                "turn off `og_cover` to avoid error"
            )

        image = Picture()
        image.type = 3
        image.mime = "image/jpeg"
        image.desc = "cover"
        with open(cover_image, "rb") as img:
            image.data = img.read()
        audio.add_picture(image)
    except Exception as e:
        logger.error(f"Error embedding image: {e}", exc_info=True)


def _embed_id3_img(root_dir, audio: id3.ID3):
    emb_image = os.path.join(root_dir, "cover.jpg")
    multi_emb_image = os.path.join(
        os.path.abspath(os.path.join(root_dir, os.pardir)), "cover.jpg"
    )
    if os.path.isfile(emb_image):
        cover_image = emb_image
    else:
        cover_image = multi_emb_image

    with open(cover_image, "rb") as cover:
        audio.add(id3.APIC(3, "image/jpeg", 3, "", cover.read()))


def _get_artists(track, album, is_track):
    artist = track.get("performer", {}).get("name", "")  # TRACK ARTIST
    if not(artist):
        if is_track:
            artist = track.get("album", {}).get("artist", {}).get("name", "")  # ALBUM ARTIST
        else:
            artist = album.get("artist", {}).get("name", "")

    extra_artists = [
        [p.strip() for p in performer.split(",")] for performer in track["performers"].split(" - ")
    ]

    artists = [artist] + [
        extra_artist[0] for extra_artist in extra_artists if extra_artist[0].casefold() != artist.casefold() and
        ("MainArtist" in extra_artist or "FeaturedArtist" in extra_artist)
    ]
    return ", ".join(filter(None, artists))


def _get_composers(track, album, is_track):
    composer = track.get("composer", {}).get("name", "")  # TRACK COMPOSER
    if not(composer):
        if is_track:
            composer = track.get("album", {}).get("composer", {}).get("name", "")  # ALBUM COMPOSER
        else:
            composer = album.get("composer", {}).get("name", "")

    extra_composers = [
        [p.strip() for p in performer.split(",")] for performer in track["performers"].split(" - ")
    ]

    composers = [composer] + [
        extra_composer[0] for extra_composer in extra_composers if extra_composer[0].casefold() != composer.casefold() and
        ("Composer" in extra_composer or "ComposerLyricist" in extra_composer)
    ]
    return ", ".join(filter(None, composers))


# Use KeyError catching instead of dict.get to avoid empty tags
def tag_flac(
    filename, root_dir, final_name, track: dict, album, is_track=True, embed_art=False
):
    """
    Tag a FLAC file

    :param str filename: FLAC file path
    :param str root_dir: Root dir used to get the cover art
    :param str final_name: Final name of the FLAC file (complete path)
    :param dict d: Track dictionary from Qobuz_client
    :param dict album: Album dictionary from Qobuz_client
    :param bool is_track
    :param bool embed_art: Embed cover art into file
    """
    audio = FLAC(filename)

    audio["TITLE"] = _get_title(track)

    audio["TRACKNUMBER"] = str(track["track_number"])  # TRACK NUMBER

    if "Disc " in final_name:
        audio["DISCNUMBER"] = str(track["media_number"])

    audio["COMPOSER"] = _get_composers(track, album, is_track)

    audio["ARTIST"] = _get_artists(track, album, is_track)

    audio["LABEL"] = album.get("label", {}).get("name", "")

    if is_track:
        audio["GENRE"] = _format_genres(track["album"]["genres_list"])
        audio["ALBUMARTIST"] = track["album"]["artist"]["name"]
        audio["TRACKTOTAL"] = str(track["album"]["tracks_count"])
        audio["ALBUM"] = track["album"]["title"]
        audio["DATE"] = track["album"]["release_date_original"].split("-")[0]
        audio["COPYRIGHT"] = _format_copyright(track.get("copyright", "") or "")
    else:
        audio["GENRE"] = _format_genres(album["genres_list"])
        audio["ALBUMARTIST"] = album["artist"]["name"]
        audio["TRACKTOTAL"] = str(album["tracks_count"])
        audio["ALBUM"] = album["title"]
        audio["DATE"] = album["release_date_original"].split("-")[0]
        audio["COPYRIGHT"] = _format_copyright(album.get("copyright", "") or "")

    if embed_art:
        _embed_flac_img(root_dir, audio)

    audio.save()
    os.rename(filename, final_name)


def tag_mp3(filename, root_dir, final_name, track, album, is_track=True, embed_art=False):
    """
    Tag an mp3 file

    :param str filename: mp3 temporary file path
    :param str root_dir: Root dir used to get the cover art
    :param str final_name: Final name of the mp3 file (complete path)
    :param dict d: Track dictionary from Qobuz_client
    :param bool is_track
    :param bool embed_art: Embed cover art into file
    """

    try:
        audio = id3.ID3(filename)
    except ID3NoHeaderError:
        audio = id3.ID3()

    # temporarily holds metadata
    tags = dict()
    tags["title"] = _get_title(track)

    tags["artist"] = _get_artists(track, album, is_track)

    tags["label"] = album.get("label", {}).get("name", "")

    if is_track:
        tags["genre"] = _format_genres(track["album"]["genres_list"])
        tags["albumartist"] = track["album"]["artist"]["name"]
        tags["album"] = track["album"]["title"]
        tags["date"] = track["album"]["release_date_original"]
        tags["copyright"] = _format_copyright(track["copyright"])
        tracktotal = str(track["album"]["tracks_count"])
    else:
        tags["genre"] = _format_genres(album["genres_list"])
        tags["albumartist"] = album["artist"]["name"]
        tags["album"] = album["title"]
        tags["date"] = album["release_date_original"]
        tags["copyright"] = _format_copyright(album["copyright"])
        tracktotal = str(album["tracks_count"])

    tags["year"] = tags["date"][:4]

    audio["TRCK"] = id3.TRCK(encoding=3, text=f'{track["track_number"]}/{tracktotal}')
    audio["TPOS"] = id3.TPOS(encoding=3, text=str(track["media_number"]))

    # write metadata in `tags` to file
    for k, v in tags.items():
        id3tag = ID3_LEGEND[k]
        audio[id3tag.__name__] = id3tag(encoding=3, text=v)

    if embed_art:
        _embed_id3_img(root_dir, audio)

    audio.save(filename, "v2_version=3")
    os.rename(filename, final_name)
