from pathlib import Path

import boto3


def upload_to_s3(bucket: str, key: str, file_path: Path) -> None:
    client = boto3.client("s3")
    client.upload_file(str(file_path), bucket, key)
