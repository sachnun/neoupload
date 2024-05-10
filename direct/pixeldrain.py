import re
import requests

# https://pixeldrain.com/u/XtgWJPWU
PREFIX = re.compile(r"https://pixeldrain.com/u/([a-zA-Z0-9]+)")


def direct_download(id):
    url = f"https://pixeldrain.com/api/file/{id}?download"

    r = requests.head(url)
    filename = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]

    return url, filename[1:-1]


if __name__ == "__main__":
    url = "XtgWJPWU"
    print(direct_download(url))
