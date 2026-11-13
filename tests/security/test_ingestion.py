import io
import json
import pickle
import subprocess
import zipfile
from pathlib import Path

import pytest

from waferguard.data.acquire import check_archive, sha256
from waferguard.data.validate import SourceUnpickler


def test_pickle_cannot_execute_arbitrary_command(tmp_path):
    target = tmp_path / "executed"

    class Payload:
        def __reduce__(self):
            return (eval, (f"open({str(target)!r}, 'w').write('bad')",))

    with pytest.raises(pickle.UnpicklingError, match="Disallowed pickle global"):
        SourceUnpickler(io.BytesIO(pickle.dumps(Payload()))).load()
    assert not target.exists()


@pytest.mark.parametrize("members", [["../LSWMD.pkl"], ["LSWMD.pkl", "other"], ["/LSWMD.pkl"]])
def test_archive_paths_and_extra_members_rejected(tmp_path, members):
    path = tmp_path / "source.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for member in members:
            archive.writestr(member, b"fixture")
    with pytest.raises(ValueError):
        check_archive(path)


def test_tampered_archive_rejected_before_deserialization(tmp_path):
    archive = tmp_path / "source.zip"
    archive.write_bytes(b"tampered")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"archive_sha256": "0" * 64}))
    result = subprocess.run(
        ["waferguard-profile", "--archive", str(archive), "--manifest", str(manifest)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Archive hash does not match" in result.stderr


def test_sha256_streams_bytes(tmp_path):
    path = tmp_path / "file"
    path.write_bytes(b"abc")
    assert sha256(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_materialized_input_tampering_is_rejected_before_loading(tmp_path):
    from waferguard.data import preprocess
    from waferguard.data.materialize import read_processed

    path = tmp_path / "states.npy"
    path.write_bytes(b"original-fixture")
    (tmp_path / "processed.json").write_text(
        json.dumps(
            {
                "identity": {"preprocess_sha256": sha256(Path(preprocess.__file__))},
                "artifacts_sha256": {"states.npy": sha256(path)},
            }
        )
    )
    path.write_bytes(b"tampered-fixture")
    with pytest.raises(ValueError, match="checksum mismatch"):
        read_processed(tmp_path)
