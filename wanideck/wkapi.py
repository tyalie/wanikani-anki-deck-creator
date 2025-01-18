import requests
from datetime import datetime
from datetime import timezone
import time
import logging
import base64

logger = logging.getLogger("api")
logger.setLevel(logging.DEBUG)

class WaniKaniAPI:
    WANIKANI_URL: str = "https://api.wanikani.com/v2/{endpoint}"

    def __init__(self, *, api_token) -> None:
        self._api_token = api_token

    def _gen_url(self, endpoint: str):
        return self.WANIKANI_URL.format(endpoint=endpoint)

    def _do_request(self, endpoint: None | str, url: None | str = None, params: dict | None = None):
        """ Does a request to an endpoint.
        The function also correctly handles authorization and
        rate limiting.

        Using url will overwrite the endpoint
        """
        if url is None:
            assert endpoint is not None
            url = self._gen_url(endpoint)

        # preprocess params - i need to handle lists differently
        if params is not None:
            for key, item in params.items():
                if isinstance(item, list):
                    params[key] = ",".join(str(e) for e in item)

        headers = dict(
            Authorization=f"Bearer {self._api_token}"
        )
        # doing the request and handling rate limiting (60 per minute)
        while True:
            logger.debug(f"Starting request {url}")
            r = requests.get(url, headers=headers, params=params)
            if r.status_code == 429:
                ts =  int(r.headers["ratelimit-reset"])
                d_time = datetime.fromtimestamp(ts) - datetime.now()
                logger.info(f"Ran into ratelimit, will try again in {d_time.total_seconds()}s")
                time.sleep(d_time.total_seconds())
            else:
                return r

    def _do_request_paged(self, endpoint: str, params: dict | None = None):
        pages = []

        next_url = self._gen_url(endpoint)
        while next_url:
            logger.info(f"retrieving {next_url}")
            r = self._do_request(endpoint=None, url=next_url, params=params)
            params = None

            assert r.status_code == 200
            pages.append(r.json())
            next_url = r.json()["pages"]["next_url"]

        data = []
        for p in pages:
            data.extend(p["data"])

        return data, pages

    def get_all_subjects(self, last_update_ts: int | None = None, max_level: int | None = None):
        params = {}
        if last_update_ts is not None:
            dt = datetime.utcfromtimestamp(last_update_ts)
            params["updated_after"]= f"{dt.isoformat()}Z"
        if max_level is not None:
            params["levels"] = list(range(1, max_level + 1))

        data, _ = self._do_request_paged("subjects", params=params)
        logger.debug(f"got all subjects (len:{len(data)})")
        return data

    def get_user(self):
        return self._do_request("user").json()

    def get_max_level(self) -> int | None:
        """this is dependend on the current subscription"""
        from .subscription import has_user_subscription

        user = self.get_user()
        if has_user_subscription(user):
            return None
        else:
            logging.warn("User is not subscriped to wanikani")
            return user["data"]["subscription"]["max_level_granted"]

    def download_resource(self, url) -> str:
        """Downloads resource and returns base64 string"""
        r = self._do_request(endpoint=None, url=url)
        return base64.b64encode(r.content).decode("ascii")
