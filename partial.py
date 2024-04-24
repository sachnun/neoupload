import requests
import threading
import pyrfc6266
import typing
import uuid
import os
import shutil


def unpack_filename(filename: str) -> typing.Tuple[str, str]:
    try:
        f, e = filename.rsplit(".", 1)
    except ValueError:
        f, e = filename, ""

    return f, ("." + e if e else "")


def download_file_part(url, start_byte, end_byte, part):
    headers = {"Range": f"bytes={start_byte}-{end_byte}"}
    contents = requests.get(url, headers=headers)
    if not contents.ok:
        raise ValueError("Failed to download the file.")
    with open(part, "wb") as f:
        f.write(contents.content)


def download_file(url, num_parts):
    response = requests.head(url)
    file_size = int(response.headers["content-length"])
    chunk_size = file_size // num_parts
    threads = []

    folder = os.path.join(os.getcwd(), str(uuid.uuid4()))
    filename = pyrfc6266.requests_response_to_filename(
        response, enforce_content_disposition_type=True
    )

    # cerate folder to store parts
    os.makedirs(os.path.join(folder, "parts"), exist_ok=True)

    for i in range(num_parts):
        start_byte = chunk_size * i
        if i == num_parts - 1:  # last part
            end_byte = ""
        else:
            end_byte = start_byte + chunk_size - 1
        thread = threading.Thread(
            target=download_file_part,
            args=(
                url,
                start_byte,
                end_byte,
                os.path.join(folder, "parts", f"part-{i}"),
            ),
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Combine all parts into one file
    with open(os.path.join(folder, filename), "wb") as f:
        for i in range(num_parts):
            with open(os.path.join(folder, "parts", f"part-{i}"), "rb") as part:
                f.write(part.read())

        # remove the parts folder
        shutil.rmtree(os.path.join(folder, "parts"))

    return folder, filename
