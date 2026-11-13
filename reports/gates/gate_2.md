# Gate 2 — Reproducible preprocessing and isolated splits

## Objective

Continue after the user's instruction to proceed: implement categorical preprocessing,
quarantine contradictory labels, preserve transitive lot/duplicate connections, create
versioned supervised splits and verify reproducibility and observed leakage boundaries.
Keep personal names out of project content. No model training, threshold fitting, cloud
resource creation or frontend implementation belongs to this gate.

## Environment / revision

Executed November 10, 2026, America/Los_Angeles. macOS arm64; Python 3.12.13,
NumPy 1.26.4, pandas 2.2.3, uv 0.10.12, Node 24.11.1 and npm 11.6.2.
Locked dependencies: `uv.lock` and `infrastructure/cdk/package-lock.json`.
The local main branch still has no commit or GitHub remote. Source and measured-evidence
hashes are snapshotted in [gate_2-source-manifest.json](gate_2-source-manifest.json);
no commit identifier or hosted CI execution is invented.

## Criteria and actual evidence

| Criterion | Result | Actual evidence |
|---|---|---|
| Preserve source identity, original die states and missing labels | PASS | Hash-verified source index; 638,507 unlabeled records excluded from supervision |
| Deterministic categorical preprocessing | PASS | 172,950 labeled uint8 64×64 grids; original source retained; outside/pass/fail one-hot channels at load |
| Conflicting labels quarantined without label invention | PASS | 28 labeled records in 14 contradictory equivalence groups |
| Copies/transformed copies retained in one group | PASS for measured identities | Original and encoded D4 identities merged before lot grouping and deduplication |
| Detect collisions introduced by preprocessing | PASS | Nine additional duplicate records found beyond the original-grid-only assessment |
| Reliable syntactic identifier audit | PASS with semantic limitation | Unique source (lotName, waferIndex); lot/process/temporal independence not authenticated |
| Feasible indivisible group split | PASS | 169,659 representatives in 10,113 components; largest component 9,423 records |
| Actual split sizes/class coverage | PASS | Train 118,677; validation 17,021; calibration 17,025; test 16,936; all nine classes in every split |
| No observed overlap of controlled identity keys | PASS | Representative and expanded-copy membership audits have zero errors |
| Reproducibility / immutable outputs | PASS | Two complete split runs reproduce identical bytes for all six manifests; altered-file refusal tested |
| Real-data loader contract and integrity | PASS for bounded smoke checks | First/last record in each split verified; shape (3,64,64), float32 one-hot, read-only states |
| Unit/integration/security checks | PASS | 44 Python tests, lint and two CDK tests in gate_2-checks.log |
| Source/derived arrays excluded from Git | PASS locally | Ignore rules plus file guard cover data/processed and NumPy archives; no raw/derived samples published |

## Commands

```bash
uv run --frozen waferguard-index
uv run --frozen waferguard-preprocess
uv run --frozen waferguard-split
# Equivalent reproducible targets:
make index
make preprocess
make split
# Replay and sampled real-data loader checks:
uv run --frozen python scripts/verify_gate2.py
make check
uv lock --check
python3 scripts/check_tracked_files.py
git check-ignore data/processed/categorical-64-v1/states.npy
```

The first index pass took about eight minutes on this machine. Cached replays verify
hashes before reuse. Raw and categorical arrays were never added to Git. Original-grid
splitting was first assessed separately, then the final pipeline incorporated encoded
input identities and created a new immutable `splits-v2` directory. Existing preliminary
artifacts remain local for traceability; they must not be used as the final benchmark.
The verification helper was first executed from a temporary script and then retained
as `scripts/verify_gate2.py` with formatting and clearer report wording; the grouping,
replay and real loader checks are the same operations.

## Stored measured artifacts

- [index-run.log](../data/index-run.log): original source indexing and integrity receipt output.
- [preprocess-run.log](../data/preprocess-run.log): real labeled input materialization and hashes.
- [source-grid-split-audit.json](../data/source-grid-split-audit.json): preliminary original-grid assessment, not the final benchmark.
- [split-audit.json](../data/split-audit.json): final encoded-input-bound grouping, class counts, identity checks and artifact hashes.
- [split-run.log](../data/split-run.log) and [split-replay.log](../data/split-replay.log): actual full split execution and replay.
- [reproducibility.json](../data/reproducibility.json): all six manifest hashes match between runs.
- [loader-smoke.json](../data/loader-smoke.json): real-data reader checks for all four splits.
- [gate_2-data-checks.log](gate_2-data-checks.log) and [gate_2-checks.log](gate_2-checks.log): actual data verification and test output.
- [benchmark.md](../../DOC/benchmark.md): preprocessing choices, full class table, artifact locations and limits.

All row-level manifests and tensors stay local under `data/processed/`. The public
reports are aggregate evidence and artifact hashes. No wafer image examples,
invented labels, model predictions or synthetic data presented as real maps are included.

## Design and limitations

Original and encoded D4 connections are merged transitively. Contradictory groups are
quarantined before grouping retained lots. Consistent duplicate copies still connect
their lots before a first-source-row representative is chosen. Thus deduplication cannot
silently discard a lot bridge. The expanded-membership audit independently includes
those excluded copies and checks all identity boundaries.

The measured overlap checks cover row ID, lot, component, exact original map, original
D4 identity, duplicate equivalence group, exact encoded input and encoded D4 identity.
They do not prove absence of noisy/cropped/otherwise approximate near-duplicates.
Lot names are not independently verified process or temporal guarantees. Unlabeled
records do not enter supervision; adding them later requires a new exposure/group audit.

Nearest-neighbor downsampling can omit small patterns. The 64×64 representation has
not been selected by model validation and is not claimed optimal. Fixed component-search
attempts select an assignment using label counts only; no model test performance,
probability calibration or review thresholds are used. Actual class counts are reported
instead of claiming exact stratification. Minority test/calibration counts remain small.

No baseline/CNN is trained or evaluated, and no prediction accuracy, inference latency,
production success or cost reduction is claimed. The existing CDK tooling advisory and
Gate 0 live AWS checks remain as previously recorded. No AWS deployments, data uploads,
GPU rentals or repository publication occurred in this gate.

## Pass/fail and next-gate decision

**Gate 2 local preprocessing, reproducibility and measured identity-boundary criteria:
PASS, with the stated scientific limitations.** Ready for review before Gate 3 majority/
classical baselines and the first CNN. The outline section 10 requires “Stop for review
between gates,” so Gate 3 training has not started. The separate Gate 0 cloud operational
exit is still not passed; Gate 2 completion does not imply any live AWS controls exist.
