.PHONY: setup check profile synth index preprocess split verify-data train check-ml
setup:
	uv sync --extra dev --frozen
	cd infrastructure/cdk && npm ci
check:
	uv run --frozen ruff check .
	uv run --frozen pytest -q
	cd infrastructure/cdk && npm test
synth:
	cd infrastructure/cdk && npm run synth
profile:
	uv run --frozen waferguard-profile --archive data/raw/wm811k-v1.zip --manifest data/manifests/acquisition.json

index:
	uv run --frozen waferguard-index
preprocess: index
	uv run --frozen waferguard-preprocess
split: preprocess
	uv run --frozen waferguard-split

verify-data: split
	uv run --frozen python scripts/verify_gate2.py

train:
	uv run --frozen --extra ml --extra dev waferguard-train
check-ml:
	uv run --frozen --extra ml --extra dev ruff check .
	uv run --frozen --extra ml --extra dev pytest -q
