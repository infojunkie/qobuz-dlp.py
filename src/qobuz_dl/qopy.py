# Wrapper for Qo-DL Reborn. This is a sligthly modified version
# of qopy, originally written by Sorrow446. All credits to the
# original author.

import hashlib
import logging
import time
import requests
import socket
import threading
import webbrowser
from http.client import HTTPConnection
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from qobuz_dl.exceptions import (
    AuthenticationError,
    IneligibleError,
    InvalidAppIdError,
    InvalidAppSecretError,
    InvalidQuality,
)
from qobuz_dl.color import GREEN, YELLOW, RED

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, app_id, secrets, private_key, token_file):
        logger.info(f"{YELLOW}Logging in...")
        self.secrets = secrets
        self.token_file = token_file
        self.id = str(app_id)
        self.uat = None
        self.private_key = private_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0",
                "X-App-Id": self.id,
                "Content-Type": "application/json;charset=UTF-8"
            }
        )
        self.base = "https://www.qobuz.com/api.json/0.2/"
        self.sec = None

        try:
            token_file = open(self.token_file, "r")
            oauth_token = token_file.read().strip()
        except:
            oauth_token = None
        else:
            token_file.close()
        if not oauth_token:
            self.oauth()
        else:
            self.update_oauth_token(oauth_token)
        self.cfg_setup()

        '''Switches on logging of the requests module.'''
        if logging.getLogger().level == logging.DEBUG:
            HTTPConnection.debuglevel = 1
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True

    def api_call(self, epoint, **kwargs):
        if epoint == "user/login":
            params = {
                "email": kwargs["email"],
                "password": kwargs["pwd"],
                "app_id": self.id,
            }
        elif epoint == "oauth/callback":
            params = {
                "code": kwargs["code"],
                "private_key": self.private_key,
                "app_id": self.id,
            }
        elif epoint == "track/get":
            params = {"track_id": kwargs["id"]}
        elif epoint == "album/get":
            params = {"album_id": kwargs["id"]}
        elif epoint == "playlist/get":
            params = {
                "extra": "tracks",
                "playlist_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
            }
        elif epoint == "artist/get":
            params = {
                "app_id": self.id,
                "artist_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
                "extra": "albums",
            }
        elif epoint == "label/get":
            params = {
                "label_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
                "extra": "albums",
            }
        elif epoint == "favorite/getUserFavorites":
            unix = time.time()
            r_sig = "favoritegetUserFavorites" + str(unix) + kwargs["sec"]
            r_sig_hashed = hashlib.md5(r_sig.encode("utf-8")).hexdigest()
            params = {
                "app_id": self.id,
                "user_auth_token": self.uat,
                "type": "albums",
                "request_ts": unix,
                "request_sig": r_sig_hashed,
            }
        elif epoint == "track/getFileUrl":
            unix = time.time()
            track_id = kwargs["id"]
            fmt_id = kwargs["fmt_id"]
            if int(fmt_id) not in (5, 6, 7, 27):
                raise InvalidQuality("Invalid quality id: choose between 5, 6, 7 or 27")
            r_sig = "trackgetFileUrlformat_id{}intentstreamtrack_id{}{}{}".format(
                fmt_id, track_id, unix, kwargs.get("sec", self.sec)
            )
            r_sig_hashed = hashlib.md5(r_sig.encode("utf-8")).hexdigest()
            params = {
                "request_ts": unix,
                "request_sig": r_sig_hashed,
                "track_id": track_id,
                "format_id": fmt_id,
                "intent": "stream",
            }
        else:
            params = kwargs

        r = self.session.get(self.base + epoint, params=params)
        if epoint == "user/login":
            if r.status_code == 401:
                raise AuthenticationError(f"{RED}Invalid credentials")
            elif r.status_code == 400:
                raise InvalidAppIdError(f"{RED}Invalid app id")
            else:
                logger.info(f"{GREEN}Logged: OK")
        elif epoint == "oauth/callback":
            if r.status_code != 200:
                raise AuthenticationError(f"{RED}OAuth callback error: {r.text}")
        elif (
            epoint in ["track/getFileUrl", "favorite/getUserFavorites"]
            and r.status_code == 400
        ):
            raise InvalidAppSecretError(f"{RED}Invalid app secret: {r.json()}")

        r.raise_for_status()
        json = r.json()
        logger.debug(json)
        return json

    def auth(self, email, pwd):
        usr_info = self.api_call("user/login", email=email, pwd=pwd)
        if not usr_info["user"]["credential"]["parameters"]:
            raise IneligibleError("Free accounts are not eligible to download tracks.")
        self.uat = usr_info["user_auth_token"]
        self.session.headers.update({"X-User-Auth-Token": self.uat})
        self.label = usr_info["user"]["credential"]["parameters"]["short_label"]
        logger.info(f"{GREEN}Membership: {self.label}")

    def oauth(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                port = s.getsockname()[1]

            oauth_url = f"https://www.qobuz.com/signin/oauth?ext_app_id={self.id}&redirect_url=http://localhost:{port}"

            class OAuthHandler(BaseHTTPRequestHandler):
                code = None
                def do_GET(self):
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    code = params.get("code", [params.get("code_autorisation", [""])[0]])[0]
                    if code:
                        OAuthHandler.code = code
                        self.send_response(200)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(b"<html><body style='font-family:sans-serif;text-align:center;padding:50px;background:#121212;color:white;'>")
                        self.wfile.write(b"<h2 style='color:#6ee7f7'>Qobuz Login Successful!</h2>")
                        self.wfile.write(b"<p>You can now close this tab and return to <strong>qobuz-dlp</strong>.</p>")
                        self.wfile.write(b"</body></html>")
                    else:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"No code received.")

                def log_message(self, format, *args):
                    return # Silence logging

            # Event to signal completion
            completion_event = threading.Event()

            logger.info(f"{YELLOW}OAuth login: Waiting for browser... (Link: {oauth_url})")
            webbrowser.open(oauth_url)

            # Start server in a thread to capture the code
            def _run_server():
                try:
                    server = HTTPServer(('127.0.0.1', port), OAuthHandler)
                    server.handle_request() # Wait for one request then exit
                    server.server_close()

                    if OAuthHandler.code:
                        logger.debug(f"{YELLOW}OAuth login: Logging in with code...")
                        callback = self.api_call("oauth/callback", code=OAuthHandler.code)
                        if not callback["token"]:
                            raise AuthenticationError(f"{RED}OAuth callback error: No token in response.")
                        self.update_oauth_token(callback["token"], True)
                    else:
                        logger.error(f"{RED}OAuth login error: No code received.")
                except Exception as e:
                    logger.error(f"{RED}OAuth login error: {str(e)}")
                finally:
                    completion_event.set()

            threading.Thread(target=_run_server, daemon=True).start()

            # Wait for completion (blocking) - timeout after 3 minutes
            if not completion_event.wait(timeout=180):
                logger.error(f"{RED}OAuth error: Login timeout.")

        except Exception as e:
            logger.error(f"{RED}OAuth error: {str(e)}")

    def update_oauth_token(self, oauth_token, coming_from_oauth=False):
        self.uat = oauth_token
        self.session.headers.update({"X-User-Auth-Token": self.uat})

        # Complete login as data partner
        r = self.session.post(self.base + "user/login",
            headers={"Content-Type": "text/plain;charset=UTF-8"},
            data="extra=partner"
        )
        if r.status_code != 200:
            if coming_from_oauth:
                raise AuthenticationError(f"{RED}OAuth partner login error: {r.text}")
            else:
                logger.warning(f"{RED}OAuth token invalid. Logging in from browser...")
                self.uat = None
                self.session.headers.pop("X-User-Auth-Token", None)
                self.oauth()
                return

        with open(self.token_file, "w") as token_file:
            token_file.write(oauth_token)

        logger.info(f"{GREEN}OAuth login successful!")

    def multi_meta(self, epoint, key, id, type):
        total = 1
        offset = 0
        while total > 0:
            if type in ["tracks", "albums"]:
                j = self.api_call(epoint, id=id, offset=offset, type=type)[type]
            else:
                j = self.api_call(epoint, id=id, offset=offset, type=type)
            if offset == 0:
                yield j
                total = j[key] - 500
            else:
                yield j
                total -= 500
            offset += 500

    def get_album_meta(self, id):
        return self.api_call("album/get", id=id)

    def get_track_meta(self, id):
        return self.api_call("track/get", id=id)

    def get_track_url(self, id, fmt_id):
        return self.api_call("track/getFileUrl", id=id, fmt_id=fmt_id)

    def get_artist_meta(self, id):
        return self.multi_meta("artist/get", "albums_count", id, None)

    def get_plist_meta(self, id):
        return self.multi_meta("playlist/get", "tracks_count", id, None)

    def get_label_meta(self, id):
        return self.multi_meta("label/get", "albums_count", id, None)

    def search_albums(self, query, limit):
        return self.api_call("album/search", query=query, limit=limit)

    def search_artists(self, query, limit):
        return self.api_call("artist/search", query=query, limit=limit)

    def search_playlists(self, query, limit):
        return self.api_call("playlist/search", query=query, limit=limit)

    def search_tracks(self, query, limit):
        return self.api_call("track/search", query=query, limit=limit)

    def get_favorite_albums(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="albums", offset=offset, limit=limit
        )

    def get_favorite_tracks(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="tracks", offset=offset, limit=limit
        )

    def get_favorite_artists(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="artists", offset=offset, limit=limit
        )

    def get_user_playlists(self, limit):
        return self.api_call("playlist/getUserPlaylists", limit=limit)

    def test_secret(self, sec):
        try:
            self.api_call("track/getFileUrl", id=5966783, fmt_id=5, sec=sec)
            return True
        except InvalidAppSecretError:
            return False

    def cfg_setup(self):
        for secret in self.secrets:
            # Falsy secrets
            if not secret:
                continue

            if self.test_secret(secret):
                self.sec = secret
                break

        if self.sec is None:
            raise InvalidAppSecretError(f"{RED}Can't find any valid app secret")
