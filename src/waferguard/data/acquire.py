"""Acquire a pinned source archive; never execute or redistribute its contents."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

SOURCE = "https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map"
SLUG = "qingyi/wm811k-wafer-map"
DOWNLOAD = f"https://www.kaggle.com/api/v1/datasets/download/{SLUG}?datasetVersionNumber=1"
MAX_MEMBER_BYTES = 3_000_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        temporary = stream.name
    os.replace(temporary, path)


def check_archive(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) != 1 or members[0].filename != "LSWMD.pkl":
            raise ValueError("Expected exactly one member named LSWMD.pkl; no extraction permitted")
        member = members[0]
        if not 0 < member.file_size <= MAX_MEMBER_BYTES:
            raise ValueError("Unexpected uncompressed member size")
        if member.flag_bits & 1:
            raise ValueError("Encrypted archive is unsupported")
        return {"name": member.filename, "bytes": member.file_size, "crc32": member.CRC}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/raw/wm811k-v1.zip"))
    parser.add_argument(
        "--metadata",
        type=Path,
        required=True,
        help="Saved Kaggle dataset-list JSON containing source license metadata",
    )
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/acquisition.json"))
    parser.add_argument(
        "--download", action="store_true", help="Download only if archive is absent"
    )
    args = parser.parse_args()
    entries = json.loads(args.metadata.read_text())
    source = next((x for x in entries if x.get("ref") == SLUG), None)
    if source is None or source.get("licenseName") != "CC0: Public Domain":
        parser.error("Expected source/license evidence missing: review current source terms")
    if not args.archive.exists():
        if not args.download:
            parser.error("Archive missing; use --download or acquire the pinned version manually")
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.archive.with_suffix(".zip.part")
        subprocess.run(
            [
                "curl",
                "--fail",
                "--location",
                "--retry",
                "2",
                "--max-time",
                "300",
                "--output",
                str(temporary),
                DOWNLOAD,
            ],
            check=True,
        )
        check_archive(temporary)
        temporary.replace(args.archive)
    member = check_archive(args.archive)
    record = {
        "schema_version": 1,
        "source": SOURCE,
        "slug": SLUG,
        "dataset_version": 1,
        "download_url": DOWNLOAD,
        "registered_at_utc": datetime.now(UTC).isoformat(),
        "archive": args.archive.as_posix(),
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": sha256(args.archive),
        "member": member,
        "license": source["licenseName"],
        "license_evidence": args.metadata.as_posix(),
        "license_evidence_sha256": sha256(args.metadata),
        "upstream_last_updated": source.get("lastUpdated"),
        "rights_review": "Source lists CC0. Keep originals private; no sample redistribution yet.",
        "integrity_limit": "Locally observed hash, not an independent publisher checksum.",
    }
    if args.manifest.exists():
        prior = json.loads(args.manifest.read_text())
        if prior.get("archive_sha256") != record["archive_sha256"]:
            parser.error("Existing manifest disagrees; preserve it and investigate source changes")
        print(f"Verified existing manifest: {record['archive_sha256']}")
    else:
        write_json(args.manifest, record)
        print(f"Recorded {args.manifest}: {record['archive_sha256']}")


if __name__ == "__main__":
    main()
