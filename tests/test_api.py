import base64
import io
import sys
import zipfile
from unittest.mock import MagicMock

from fastapi import testclient

# pylint: disable=wrong-import-position
sys.modules["gdrive.client"] = MagicMock()
from gdrive import main

client = testclient.TestClient(main.app)


def test_upload() -> None:
    """test upload endpoint"""

    response = client.post(
        "/upload",
        params={"id": "hello", "filename": "world"},
        data={"name": "hello", "form": "world"},
    )
    assert response.status_code == 200
    content = response.json()
    print(content)


def test_upload_base64() -> None:
    """test upload endpoint"""

    data = b"Hello World"

    b64_data = base64.b64encode(data)

    response = client.post(
        "/upload",
        params={"id": "hello", "filename": "world", "base64": True},
        content=b64_data,
    )
    assert response.status_code == 200
    content = response.json()
    print(content)


def test_upload_zip() -> None:
    """test upload endpoint"""

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "a") as zip_file:
        for file_name, data in [
            ("1.txt", io.BytesIO(b"111")),
            ("2.txt", io.BytesIO(b"222")),
        ]:
            zip_file.writestr(file_name, data.getvalue())

    response = client.post(
        "/upload",
        params={"id": "hello", "filename": "world", "zip": True},
        content=zip_buffer.getvalue(),
    )
    assert response.status_code == 200
    content = response.json()
    print(content)


def test_upload_base64_zip() -> None:
    """test upload endpoint"""

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "a") as zip_file:
        for file_name, data in [
            ("1.txt", io.BytesIO(b"111")),
            ("2.txt", io.BytesIO(b"222")),
        ]:
            zip_file.writestr(file_name, data.getvalue())

    b64_data = base64.b64encode(zip_buffer.getvalue())

    response = client.post(
        "/upload",
        params={"id": "hello", "filename": "world", "base64": True, "zip": True},
        content=b64_data,
    )
    assert response.status_code == 200
    content = response.json()
    print(content)


def test_delete() -> None:
    """test upload endpoint"""

    data = b"Hello World"

    b64_data = base64.b64encode(data)

    response = client.delete("/upload", params={"filename": "world"})
    assert response.status_code == 200
    content = response.json()
    print(content)
