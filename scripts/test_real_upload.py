import argparse
import sys
from pathlib import Path

import requests


def main():
    parser = argparse.ArgumentParser(description="Test real presigned upload flow.")

    parser.add_argument(
        "file_path",
        help="Local file path to upload.",
    )

    parser.add_argument(
        "--content-type",
        required=True,
        help="Declared content type, for example image/png.",
    )

    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="API base URL.",
    )

    args = parser.parse_args()

    file_path = Path(args.file_path)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    file_bytes = file_path.read_bytes()

    payload = {
        "filename": file_path.name,
        "content_type": args.content_type,
        "size_bytes": len(file_bytes),
    }

    print("=== Step 1: Request upload URL ===")
    print(payload)

    response = requests.post(
        f"{args.base_url}/api/v1/files/upload-urls",
        json=payload,
    )

    print("Status:", response.status_code)
    print(response.text)

    if response.status_code != 201:
        sys.exit(1)

    upload_info = response.json()

    file_id = upload_info["file_id"]
    upload_url = upload_info["upload_url"]
    upload_fields = upload_info["upload_fields"]

    print("=== Step 2: Upload file to S3 ===")

    files = {
        "file": (
            file_path.name,
            file_bytes,
            args.content_type,
        )
    }

    response = requests.post(
        upload_url,
        data=upload_fields,
        files=files,
    )

    print("Status:", response.status_code)

    if response.status_code not in {200, 201, 204}:
        print(response.text)
        sys.exit(1)

    print("Upload to S3 succeeded.")

    print("=== Step 3: Confirm upload ===")

    response = requests.post(
        f"{args.base_url}/api/v1/files/{file_id}/complete",
    )

    print("Status:", response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()
