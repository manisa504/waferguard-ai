# Local research app

The app is a browser interface for committed evidence, grid validation, and manual research
notes. It is separate from the draft FastAPI/reviewer service and needs no model bundle,
AWS credentials, API key, Node package installation, or internet service to operate locally.
Its diagrams show the current local scope. AWS deployment is deferred at the user's request.

## Start

From the repository root, run `./scripts/run_local.sh`, then open
`http://127.0.0.1:8768/DOC/app/`. Python 3.12+ is sufficient. Set `PORT=8769` before the
command if port 8768 is occupied. Stop the server with Ctrl+C. Do not open `index.html`
through `file://`; module imports and report requests require a local HTTP server.

The launcher rebuilds ignored `.public-site/` using only `DOC/` and aggregate `reports/`.
It never serves raw datasets, weights, credentials, or the rest of the workspace.
GitHub Pages serves the same app at `/waferguard-ai/DOC/app/`.

## What works

1. Overview loads `reports/metrics/gate4-final/test.json` and `qualification.json` directly.
   The displayed macro-F1, per-class recall, precision, ECE, and gate decisions are measured.
   Existing test results are displayed, not recomputed or used for threshold tuning.
2. Inspector generates deterministic synthetic example grids or accepts a local JSON file.
   Inputs must be rectangular, 1–256 rows/columns, contain only integer states 0/1/2, and
   include an inside-wafer cell. The file limit is 512 KB. The UI computes die-state counts,
   not defect labels or predictions. Arrow keys inspect cell positions and states.
3. Review notebook saves a summary and manual observations in browser localStorage.
   Statuses are “Pending note” and “Note recorded,” never release authorization. Notes may
   be filtered, exported, or cleared. Raw grids are not stored. Uploaded grids remain in
   memory and disappear when the page reloads. Notes belong only to that browser/origin;
   local and published notebooks are separate. This is not authenticated shared storage.
4. System diagrams show the local app and the completed research decision flow. Interactive
   standalone viewers and PNG/SVG exports are included, with no cloud-service logos.

## Verification and screenshots

`node --test tests/browser/core.test.mjs` exercises invalid-input rejection, deterministic
examples, summary-only persistence, provenance preservation, and immutable observation
updates. It needs Node 24 (the existing project CI runtime) and no external packages.

`scripts/capture_local_app.mjs` uses Node's built-in WebSocket support and a dedicated
Chrome DevTools session. Start the local server, then start a separate headless Chrome
with `--remote-debugging-port=9329` and a temporary `--user-data-dir`. The capture script
uses a fresh dedicated browser notebook: **do not point it at a browser profile containing
notes you want to keep**. Run `node scripts/capture_local_app.mjs`. Optional variables
`WAFERGUARD_PREVIEW_ORIGIN` and `WAFERGUARD_CHROME_DEBUG` change the endpoints.

The capture writes five PNG screenshots and a receipt under `DOC/screenshots/`. It checks
real report rendering, synthetic provenance, keyboard interaction, example selection,
note saving/reload/filtering, invalid and valid file inputs, mobile width containment,
and absence of external network/API requests. The receipt binds screenshots and app source
hashes. Screenshots show the actual local app; no composite images or fabricated model
outputs were used. Synthetic die-state counts describe the UI example only.

The screenshots do not establish inference performance, backend authorization, concurrent
review correctness, production durability, or Gate 5 completion. Gate 4's model qualification
remains failed; inference and operational automatic acceptance are not enabled.

## Diagram evidence

`diagrams/verification.json` records source/artifact hashes, nine artifact checks per
diagram, zero composition errors/warnings, passed automated browser checks at four desktop
sizes, and visual inspection of light/dark captures. Raw tool receipts with machine paths
remain in ignored `artifacts/diagram-receipts/`. Exported diagrams use the same delivered
viewer. Missing edge labels on the research chain are deliberate: the ordered node labels
already describe each step, with no extra protocol or boundary semantics to preserve.
