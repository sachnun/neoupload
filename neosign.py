import aiohttp
import time
import os
import json
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


async def get_presigned_url(filename: str) -> tuple[str, str]:
    async with aiohttp.ClientSession(
        headers={"X-Requested-With": "XMLHttpRequest"}
    ) as session:
        login = aiohttp.FormData()
        login.add_field("lg_email", EMAIL)
        login.add_field("lg_password", PASSWORD)
        login.add_field("lg_remember_me", "")
        login.add_field("csrf_neocloud", "")

        await session.post(
            "https://neocloud.co.in/authenticate/verifyLogin", data=login
        )

        key = f"neoupload/{str(int(time.time()))}/{filename}"

        upload = aiohttp.FormData()
        upload.add_field("key", key)
        upload.add_field("csrf_neocloud", "")

        async with session.post(
            "https://neocloud.co.in/Ajax/getPresignedUrl", data=upload
        ) as r:
            url = json.loads(await r.text())["url"]
            return (
                url,
                parse_url(url).scheme
                + "://"
                + parse_url(url).host
                + parse_url(url).path,
            )


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(get_presigned_url("test.txt")))
