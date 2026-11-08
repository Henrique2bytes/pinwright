# Review — `ai_submission/marker_check.py`

Verdict: reject. The two tests shipped beside the candidate pass. They only check `requests==2.32.3` and a bare name. The maintainer contract in `tests/test_ai_submission_contract.py` shows the same function accepting inputs the task forbids.

## What is right

- A blank line and a full-line comment are skipped (`marker_check.py` lines 16–18).
- A requirement with neither `==` nor `@` is reported as `unpinned` (lines 22–24). That catches `requests` and `requests>=2.32.3`.

## Findings

1. **Any `@` is treated as an immutable pin.** Lines 25–28 split on the first `@` and store the rest. `git+https://example.com/org/tool.git@main` is accepted. So is a URL that embeds `user:token@host`. The task allows only `git+https` without userinfo and a 40-character lowercase commit. The reference rejects both as `mutable-vcs`.

2. **The marker is not a grammar.** Line 19 splits on the first semicolon and line 27 stores the tail as text. `python_version >= "3.11" or sys_platform == "linux"` is accepted. There is no rejection for unknown names or call syntax. The reference parses a closed grammar and never calls `eval`.

3. **Names and extras are not normalized.** Lines 29–30 keep the raw left side of `==`, so `Requests` and `requests` are two pins, and `pkg[b,a]` is a different identity from `pkg[a,b]`. Both change the candidate digest. The reference canonicalizes with PEP 503, sorts extras, and emits `duplicate-name` for the second spelling.

4. **The digest is the raw file.** Line 35 hashes the original bytes. Adding `# note` changes the digest even though the pin did not change. A lockfile comment would look like a dependency change.

5. **`latest` and hash suffixes ride through.** `requests==latest` contains `==`, so it is stored. A hash suffix does not match the exact-pin grammar; the candidate still has no version token check.

6. **The report writer destroys the previous file.** Line 40 calls `Path.write_text`, which truncates first. The contract test forces that write to fail after truncation: the old `OLD` document becomes empty. `pinwright.audit.publish_report` writes a sibling temporary file, fsyncs, and `os.replace`. When replace raises, the previous report is still `OLD`.

## Test gap

`test_marker_check.py` never builds a git URL, a marker, two spellings of one name, a comment-only edit, or a failed write. A green run of that file is not evidence that Task 001 is done.

## Required change of approach

Replace this module with the library path: parse one line into a `Pin`, validate the marker with `pinwright.markers`, compute the digest from canonical rows, and publish with `publish_report`. Do not keep a second checker that can disagree.
