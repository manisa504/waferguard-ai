"""Package an allowlist of public evidence and pages; never include project data."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / ".public-site"
if output.exists():
    shutil.rmtree(output)
output.mkdir()
for name in ("DOC", "reports"):
    shutil.copytree(ROOT / name, output / name)
(output / "index.html").write_text(
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    '<meta http-equiv="refresh" content="0; url=DOC/">'
    '<title>WaferGuard</title></head><body>'
    '<a href="DOC/">Open WaferGuard</a></body></html>\n'
)
(output / ".nojekyll").touch()
print("Packaged public documentation and aggregate evidence in .public-site/")
