# Task 001 — Extras, markers, and immutable git pins

You maintain `pinwright`, a local auditor for Python dependency pinfiles. It does not download packages and it does not talk to an index.

The current bar already accepts one exact pin per line:

```
requests==2.32.3
```

Extend the checker so a maintainer can also express extras, a closed environment marker, and a git pin that cannot move.

## Required behavior

- `Name[extra,extra]==VERSION` is one pin. Extras are identifiers. Order and capitalization do not change the pin. `Requests`, `requests`, and `foo_bar` / `foo-bar` are the same distribution name (PEP 503).
- A second pin for the same normalized name is a `duplicate-name` finding. The audit is not ok and has no digest.
- `name @ git+https://host/path.git@<40 lowercase hex>` is a pin. Branch names, tags, short SHAs, SSH URLs, HTTP URLs, and URLs with usernames or passwords are `mutable-vcs`.
- A marker, introduced by `;`, may use only `sys_platform`, `os_name`, and `python_version`, combined with `and` and parentheses. `or`, function calls, and unknown names are `invalid-marker`. The checker must not execute the marker as Python.
- Inline comments and blank lines do not change the digest. The digest is SHA-256 of the canonical pins, not of the raw file.
- `pinwright check FILE --out REPORT` prints JSON and publishes `REPORT` by writing a temporary file in the same directory, flushing, fsyncing, and `os.replace`. If replace fails, the previous report bytes remain.
- Exit `0` when the file is ok, `2` when the pinfile is rejected, `1` when the file cannot be read or the report cannot be published.

## Out of scope

Do not contact PyPI. Do not verify artifact hashes. Do not add a dependency. Do not weaken an existing rejection to make a new test pass.

## Done when

`python -m unittest discover -s tests -v` passes, including the contract tests over unpinned ranges, `@main`, credential URLs, `or` markers, duplicate normalized names, comment-stable digests, and a failed report replace.
