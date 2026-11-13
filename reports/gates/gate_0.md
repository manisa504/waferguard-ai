# Gate 0 — Foundation

## Objective and scope

Implement the first-change foundation in the supplied outline: charter, ADRs,
architecture, CI, source tooling, security/cost controls and reproducible operational
documentation. No model, frontend or live application belongs to this change.

## Environment / revision

Executed November 10, 2026 (America/Los_Angeles), macOS arm64, Python 3.12.13,
uv 0.10.12, Node 24.11.1, npm 11.6.2. Python dependencies: `uv.lock`;
CDK/Node dependencies: `infrastructure/cdk/package-lock.json`.
Local Git repository initialized on `main`; no commit or GitHub remote exists.
Source file hashes are recorded in [source-manifest.json](source-manifest.json)
instead of inventing a commit identifier. No GitHub PR has been opened.

## Criteria and actual evidence

| Criterion | Result | Evidence |
|---|---|---|
| Charter, decisions and explicit boundaries | PASS | DOC/charter.md and DOC/adr/0001–0003 |
| Editable architecture and reviewable exports | PASS | DOC/architecture.drawio, two PNGs, companion guide; XML and PNG review |
| CI definitions and locked environment | LOCAL PASS; remote NOT RUN | .github/workflows/ci.yml; clean install and checks.log |
| Data contracts and ingestion security tests | PASS | 21 pytest cases in checks.log; synthetic fixtures only |
| Storage private/encrypted/versioned/TLS/retained | TEMPLATE PASS; cloud NOT RUN | Two CDK tests including unsafe-control check; strict synthesis |
| Cost controls | TEMPLATE PASS; live notification NOT RUN | Required AlertEmail, configurable budget, actual 80% / forecast 100% |
| Threat model and cleanup | DOCUMENTED; cloud drill NOT RUN | DOC/threat_model.md and DOC/deployment.md |
| Raw data excluded from repository | LOCAL PASS | git check-ignore and tracked/untracked file guard |

## Commands

```bash
uv sync --extra dev --frozen
npm ci --ignore-scripts --prefix infrastructure/cdk
make check
make synth
python3 scripts/check_tracked_files.py
git check-ignore data/raw/wm811k-v1.zip
bash -n scripts/setup.sh scripts/deploy.sh scripts/teardown.sh scripts/run_local.sh
# Dependency audit exits 1 because of the advisory recorded below:
cd infrastructure/cdk && npm audit --json
```

[checks.log](checks.log) contains the actual passing lint/test output. Strict synth output
is saved in [cdk-synth.log](cdk-synth.log); the synthesized template and validation report
are snapshotted beside this report. `cdk-nag` v3 uses CDK Validations. Successful plugins
without findings are omitted from CDK's report. The negative-control test independently
confirms that the checker detects a bucket missing TLS enforcement. The access-log
sink alone acknowledges AwsSolutions-S1 to prevent recursive self-logging.

## Limitations and risks

`npm audit` reports one moderate minimatch glob-amplification advisory
[GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249), propagated
through three package entries (minimatch, aws-cdk-lib, cdk-nag). See [npm-audit.json](npm-audit.json).
The affected dependency is bundled in current CDK; a normal override did not replace it
and was removed. No blanket audit suppression or forced downgrade is applied. The
current app uses fixed local paths, not public glob input. Reassess/upgrade before
introducing untrusted glob patterns or approving deployment. Passing static checks do
not erase this dependency risk. CI action versions use release tags; full SHA pinning
remains a hardening item before deployment automation.

No AWS API mutations, bootstrap, resource upload, cloud authorization checks, budget
notification verification, CloudTrail runtime setup or teardown drill were performed.
Deployment needs a real budget recipient and reviewed account identity/diff. Budget
warnings do not cap spending. Retained S3 versions can incur costs after stack deletion.
No API/reviewer security controls, trained model, measured model skill or cost reduction
are claimed. Proposed target architecture services are future work.

## Pass/fail and next-gate decision

**Local implementation criteria: PASS with recorded dependency limitation. Full cloud
operational exit: NOT PASSED / NOT RUN.** This is a reviewable foundation, not a deployed
system. Gate 1 source evidence is included in the same first change as section 14
explicitly requests. **HOLD before Gate 2**: the outline section 10 says “Stop for review
between gates.” Owner review must resolve data-split priorities and any decision to
deploy the foundation with the recorded tooling risk. No later gate is marked passed.
