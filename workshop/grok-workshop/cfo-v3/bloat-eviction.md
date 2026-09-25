# What never enters `.cfo-v3`

This is a ban list, not a delete job. `.cfo` and `.cfo-v2` stay on disk as the old snapshot. Nobody moves or deletes them in this arc.

Authority: `DESIGN-REVIEW.md` sections 5, 7, and 8.

## Leave behind

| Path | Why |
| --- | --- |
| `.cfo/` | Old kernel. Layer 1 replaces the import. The directory stays. |
| `.cfo/.venv`, `.cfo/tests`, `.cfo/evals`, `.cfo/sample_data` | Not runtime. |
| `.cfo/skills` and `.cfo-v2/office/computer/skills` | Two copies. v3 has one `skills/` if a body is still pasted. |
| `.cfo-v2/prove-fork/` | Prove clone. 423 MB class of copy. |
| `.cfo-v2/office/instances/` | Full Computer clones, including the golden tape. Readable history. Not a runtime root. |
| `.cfo-v2/office/sessions/` | Build diary. `ADVERSARIAL-SCENARIOS.md` is an answer key. |
| `.cfo-v2/office/final-demo/` | Notes about the show. Not loaded by the sidecar. |
| `.cfo-v2/office/reference-datasets/` | Benchmarks. |
| `constitution.md`, `SUPERSEDES.md` | Written for the agents who built the office. |
| `**/SYSTEM.md`, `harness/PROTOCOL.md` | 594 copies of one card. Not loaded into the prompt. |
| `bots/**/PROOF.md`, `NOTES.md`, `HOST.md` | The author reporting on their own work. |
| `data/expected_results.json`, `expected_outcomes.json`, `holdout/` | Answer keys inside the Bot cwd today. |

## Done when

A reviewer can open `.cfo-v3` and not find any path in the table above. `.cfo-v2` still contains them.
