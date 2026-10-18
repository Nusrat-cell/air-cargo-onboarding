import boto3
from moto import mock_aws

from cargo import s3


@mock_aws
def test_upload_and_download_roundtrip(tmp_path):
    client = boto3.client("s3", region_name="eu-west-1")
    client.create_bucket(Bucket="cargo-processed", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"})
    (tmp_path / "a.csv").write_text("x\n1\n", encoding="utf-8")
    keys = s3.upload_dir(client, "cargo-processed", "acme/2026-10-19", tmp_path)
    assert keys == ["acme/2026-10-19/a.csv"]
    back = s3.download(client, "cargo-processed", keys[0], tmp_path / "back" / "a.csv")
    assert back.read_text(encoding="utf-8") == "x\n1\n"
