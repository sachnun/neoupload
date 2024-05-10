import requests
import re

from lxml import html

PREFIX = re.compile(r"https://krakenfiles.com/view/([a-zA-Z0-9]+)/file.html")


# https://krakenfiles.com/view/{id}/file.html
def direct_download(id):
    r = requests.get(f"https://krakenfiles.com/view/{id}/file.html")

    tree = html.fromstring(r.text)
    token = tree.xpath('//*[@id="dl-token"]')[0].get("value")

    r = requests.post(f"https://krakenfiles.com/download/{id}", data={"token": token})
    url = r.json()["url"]

    r = requests.head(url)
    filename = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]

    return url, filename


if __name__ == "__main__":
    url = "tQopXzj58C"
    print(direct_download(url))
