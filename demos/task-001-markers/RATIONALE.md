# Rationale — reference checker

`pinwright` is a gate in front of an install, not an installer. If it cannot prove a line is an exact pin, it rejects the file and withholds the digest. A missing digest is the signal a later step must not treat as "same lockfile".

## Exact identity

Ranges and bare names select a moving set. The auditor records one version token or one commit. `requests>=2` and `requests==latest` fail for the same reason: the token is not an exact release. Artifact `--hash` lines are rejected too. Verifying hashes would be a different feature, and accepting the suffix as part of the version would make two hashes of one release look like two versions.

Names are compared after PEP 503 folding. `Requests` and `requests`, or `foo_bar` and `foo-bar`, are one distribution. Extras are sorted so `[b,a]` and `[a,b]` share a digest. Without that, a formatter would create a false lockfile change, and a second spelling would install the same project twice under two names.

## Git pins

A branch or tag can move without the pinfile changing. The only git form stored is `git+https://host/path.git` plus 40 lowercase hex digits. Userinfo is rejected because a token in the pinfile would be copied into the report and the digest. SSH and plain HTTP are outside the form. The host is lowercased; the path is not, because path case can be significant.

## Markers

The marker is data. `normalize_marker` tokenizes `and`, comparisons, parentheses, and quotes. `sys_platform` and `os_name` have closed value sets. `python_version` is `major.minor` and is compared as a pair of integers. `or`, calls, and unknown names raise `invalid-marker`. `marker_holds` walks that tree. It does not call `eval`. An expression such as `__import__('os')` is a syntax error for this grammar, not a program.

## Digest and publication

The digest is SHA-256 of canonical rows sorted by name. Comments, blank lines, quote style, and extra order are normalized away before the hash. Callers can store the digest beside a lock decision.

`publish_report` does not open the destination with truncation. It writes a temporary file in the same directory, flushes, fsyncs, and replaces. Same-directory replace is atomic on the filesystems this tool targets. If replace fails, the previous report is unchanged and the temporary file is removed.

## What this leaves out

There is no index lookup, no dependency resolver, and no hash verification. Those need the network or artifact bytes, and this tool's contract is to decide from the pinfile alone. Adding them inside `check` would make a failed audit depend on PyPI being reachable.

## Judgment on the candidate

The candidate proves a narrow happy path and misses the identity rules above. Its own tests stay green while `@main`, credential URLs, `or` markers, and duplicate spellings are accepted. That is a failed review, not a partial pass. The reference file set is the solution a maintainer can run.
