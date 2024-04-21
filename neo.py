import requests
import time
import os
import urllib3
from urllib3.util import parse_url
from dotenv import load_dotenv

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EMAIL = os.getenv("NEO_EMAIL")
PASSWORD = os.getenv("NEO_PASSWORD")

# check if EMAIL and PASSWORD are set
if not EMAIL or not PASSWORD:
    raise ValueError("Please set the NEO_EMAIL and NEO_PASSWORD environment variables.")


class NeoCloud:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["X-Requested-With"] = "XMLHttpRequest"
        self.session.cookies["ci_session"] = self.login(EMAIL, PASSWORD)

    def login(self, email, password):
        url = "https://neocloud.co.in/authenticate/verifyLogin"
        form = {
            "lg_email": (None, email),
            "lg_password": (None, password),
            "lg_remember_me": (None, ""),
            "csrf_neocloud": (None, ""),
        }

        r = requests.post(
            url, files=form, headers={"X-Requested-With": "XMLHttpRequest"}
        )
        cookies = r.cookies.get_dict()
        return cookies["ci_session"]

    def get_presigned_url(self, filename):
        url = "https://neocloud.co.in/Ajax/getPresignedUrl"
        timestamp = str(int(time.time()))
        key = f"neoupload/{timestamp}/{filename}"
        form = {
            "key": (None, key),
            "csrf_neocloud": (None, ""),
        }

        r = self.session.post(url, files=form)
        url = r.json()["url"]
        return url, self._direct_url(url)

    @staticmethod
    def _direct_url(url):
        return parse_url(url).scheme + "://" + parse_url(url).host + parse_url(url).path


if __name__ == "__main__":
    neo = NeoCloud()
    print(neo.get_presigned_url("test.txt"))
