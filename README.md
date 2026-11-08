# pinwright

Local, fail-closed auditor for exactly pinned Python dependencies. It reads a pinfile on disk, checks the grammar, and prints a canonical digest. It does not download packages, talk to an index, or open a network port.

This repository is a self-contained engineering evaluation example: a technical task, a reference implementation, a deliberately weak candidate submission, automated contract tests, and a written review.

The submission in `demos/task-001-markers/ai_submission/` is a constructed example. It is not a transcript or a result from Claude Code, Codex, or any other named coding agent. This repository does not compare real coding agents.

## Run locally

From this directory, with the environment created beside the code:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/pinwright check examples/clean.pins
.venv/bin/pinwright check examples/broken.pins
```

`examples/clean.pins` exits 0. `examples/broken.pins` exits 2 and prints findings. JSON also goes to `--out PATH`. That write uses a temporary file in the same directory, `fsync`, and `os.replace`.

The candidate's own tests are intentionally narrow. Run them from `demos/task-001-markers/ai_submission/`:

```bash
python -m unittest test_marker_check.py
```

Those tests execute the candidate module. A green run of that file is not the maintainer contract. `tests/test_ai_submission_contract.py` is the contract.

## What the evaluation contains

- `demos/task-001-markers/TASK.md` is the assignment.
- `src/pinwright/` is the reference implementation.
- `demos/task-001-markers/ai_submission/` is the constructed weak submission.
- `tests/test_ai_submission_contract.py` loads that submission and compares its behavior with the reference.
- `demos/task-001-markers/REVIEW.md`, `RUBRIC.md`, and `RATIONALE.md` are the written review. The scores in the rubric are quoted from that file. They are not recomputed by a program in this tree.

## Limits

This tree audits local pinfiles. It is not a sandbox, a secure jail, or an atomic boundary around untrusted code.

The contract test resolves the candidate path and then imports that file. Path validation and import are not one atomic step. Nothing in this snapshot closes that gap, and this tree does not ship a path jail.

Running the candidate tests or the contract tests executes the candidate module with the privileges of that Python process.

## Docker

`Dockerfile` runs `python -m unittest discover -s tests -v` as the unprivileged user `app`. `compose.yaml` builds that image and publishes no ports.

```bash
docker build -t pinwright-demo:local .
docker run --rm pinwright-demo:local
```

The image has not been built from this snapshot, and Docker has not been run here. This repository does not claim a Docker test result.

## Interview path

1. Read `demos/task-001-markers/TASK.md` as the assignment a maintainer would give.
2. Read `demos/task-001-markers/ai_submission/marker_check.py` before reading the review.
3. Run the `tests/` suite. The candidate self-check is narrow; `tests/test_ai_submission_contract.py` shows where that narrow run is wrong.
4. Read `REVIEW.md`, `RUBRIC.md`, and `RATIONALE.md`.
5. The reference implementation is `src/pinwright/`.

## Layout

| Path | Role |
|---|---|
| `src/pinwright/parse.py` | One requirement per line |
| `src/pinwright/markers.py` | Closed marker grammar, no `eval` |
| `src/pinwright/audit.py` | Duplicates, digest, atomic report |
| `src/pinwright/cli.py` | `pinwright check` |
| `demos/task-001-markers/` | Task, candidate, rubric, review, rationale |

A rationale submitted to an employer still has to be written by the candidate in their own words. The documents here are the demo's technical record.
