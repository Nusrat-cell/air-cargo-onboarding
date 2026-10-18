"""Landing and processed zones on S3. Written against the S3 API with boto3."""
from pathlib import Path


def upload_dir(client, bucket: str, prefix: str, directory) -> list:
    keys = []
    for f in sorted(Path(directory).iterdir()):
        if f.is_file():
            key = f"{prefix}/{f.name}"
            client.upload_file(str(f), bucket, key)
            keys.append(key)
    return keys


def download(client, bucket: str, key: str, target) -> Path:
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(bucket, key, str(target))
    return target
