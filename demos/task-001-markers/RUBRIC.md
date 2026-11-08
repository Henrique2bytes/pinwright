# Rubric — Task 001

Score each dimension from 0 to 4. A submission fails if any critical dimension is below 3, or if the total is below 18 of 24.

| Dimension | Weight | Critical | 4 looks like | 0 looks like |
|---|---|---|---|---|
| Correctness | 4 | yes | Every required acceptance and rejection in `TASK.md` holds on the files, not on a paraphrase of them. | A happy-path pin passes while a stated rejection is accepted. |
| Architecture | 4 | yes | Parsing, marker grammar, policy, digest, and publication are separate. New syntax does not get a second checker. | A parallel script re-implements half of the rules and disagrees with the library. |
| Safety | 4 | yes | Markers are a grammar. Git pins cannot carry credentials or a moving ref. | `eval`, `exec`, or any `@` counting as a pin. |
| Tests | 4 | yes | Tests fail if a comment changes the digest, if `or` is accepted, or if a crash during publication destroys the old report. | Tests only assert that `name==version` returns ok. |
| Durability | 4 | yes | The report appears whole or the previous bytes remain. | `Path.write_text` truncates the destination before the new document is durable. |
| Explanation | 4 | no | The author can point at the line that enforces each rule and say what a future change must not weaken. | The patch is described as "handles markers" with no rejected input. |

The candidate in `ai_submission/marker_check.py` scores 1, 1, 0, 1, 0, 1. Total 4 of 24. Reject.
