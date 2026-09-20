# Archive

Not on the run path.

## `root-kernel-shadow/`

After the kernel moved into `.cfo/`, Rohan committed a second set of Python folders at the git root (`inbox/`, `ar/`, `data/`, `demo/`, `evals/`, `tests/`, …) for the Maximor demo website (2026-09-19, `8763275`).

Those folders were incomplete next to `.cfo/`:

- Root `ar/` was one file. `.cfo/ar/` has the full AR package.
- Root `inbox/` overlapped `.cfo/inbox/` with six files different and two files only in `.cfo/`.
- Root `evals/` lacked Finance Gauntlet, which lives in `.cfo/evals/`.

pytest already used `.cfo/tests`. The website API already `chdir`s into `.cfo/`. The office sidecar already loads `.cfo/cfo_kernel`.

This archive keeps Rohan’s root copies so they are not deleted. Do not put them on `PYTHONPATH`.
