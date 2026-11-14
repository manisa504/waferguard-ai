# Local app presentation work — November 14, 2026

The user requested a local app, normal diagrams, real screenshots, and publication in
the README and GitHub Pages. AWS deployment was explicitly deferred. This work is a
browser research demonstration, not a Gate 5 pass or model-promotion decision.

## Implemented

- Evidence overview reads committed frozen-test and qualification JSON directly.
- Grid inspector validates categorical JSON inputs and renders their states and counts.
  Demonstration grids are deterministic and explicitly synthetic; no raw dataset maps
  or per-case model outputs are published.
- Notebook stores grid summaries and research observations in browser localStorage,
  with filtering, reload persistence, export, and clearing. No raw grid arrays are stored.
- Two plain component/decision diagrams replace AWS topology as the primary presentation.
- Loopback launcher packages only public documentation and aggregate evidence.

## Verification performed

- Five Node contract tests passed: input validation, deterministic examples, summary-only
  records, provenance, and immutable note updates.
- Twenty-one Chrome checks passed, including real metric rendering, keyboard inspection,
  input switching, note saving/reload/filtering, valid and invalid uploads, desktop/mobile
  width containment, and absence of external network or inference API requests.
- Five actual app screenshots captured at 1440×1080 and 390×844. Overview shows measured
  aggregates; inspector and notebook use a labeled synthetic example. Source and image
  hashes are recorded in [the capture receipt](../../DOC/screenshots/receipt.json).
- Both architecture specifications passed all nine artifact checks with zero composition
  errors/warnings, passed automated browser checks at four desktop sizes, and received
  visual review in light/dark. See [diagram verification](../../DOC/diagrams/verification.json).
- Python lint, JavaScript syntax, public link checks, and tracked-file guard passed.

## Limits preserved

No model inference, threshold tuning, new evaluation, cloud operation, authenticated
review service, shared queue, or production approval is enabled. Browser state is neither
tamper-proof nor a production audit log. Gate 4 remains failed and the test remains observed.
Source files under the existing API/review packages remain future-gate drafts.
