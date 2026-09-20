# Final demo

This folder is the canonical write-up of what the Office of the CFO can do, how we test it, and which Maximor records the website should draw.

Do not add more notes under `office/sessions/`. Session files are working proof, not the product story.

**Start with [CAPABILITIES.md](CAPABILITIES.md).** That file is the single account of current and planned capability.

| File | Use |
| --- | --- |
| [CAPABILITIES.md](CAPABILITIES.md) | What the system can do and will do |
| [DOCUMENTS.md](DOCUMENTS.md) | Every related document and whether it is still true |
| [WORLD.md](WORLD.md) | Books the other agent wrote under `world/maximor` |
| [TESTING.md](TESTING.md) | Kernel evals, office proof, holdout rules |
| [SCENARIOS.md](SCENARIOS.md) | Cards for the website: planted show path vs later holdout |
| [scenarios.json](scenarios.json) | Same cards as JSON. No answer keys |
| [index.json](index.json) | Machine index for this folder |

Company: **Maximor Demo Corp** (`CO-MAXIMOR`). Period: September 2026. August is closed precedent.

Live office: `http://127.0.0.1:8800/`. Computer data is a symlink to `../world/maximor`. Simulated connectors only. Bots must not load `expected_results.json`, this folder's holdout notes, or `sessions/ADVERSARIAL-SCENARIOS.md`.
