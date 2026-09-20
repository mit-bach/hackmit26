# `.cfo-v2` — Office of the CFO on Harness

This directory is the Client system: Roster, Computer, Catalog, Grants, Bot identities.

It is not the finance kernel. The kernel is [`.cfo/`](../.cfo/README.md). Sidecar boot looks for `.cfo/cfo_kernel`. Harness is [`.harness/Harness-v2`](../.harness/Harness-v2/README.md).

| Path | Role |
| --- | --- |
| [`office/`](office/RUN.md) | Live office. Computer, bots, compiler, world, prove/show instances. |
| [`office/RUN.md`](office/RUN.md) | Boot order. |
| [`office/SUPERSEDES.md`](office/SUPERSEDES.md) | Kernel math stays. Human-review-as-completion is void. |
| `prove-fork/` | Isolated prove Computer. Do not point it at the live office kernel. |
| `demo-desk/` | Local desk scratch. |

Rohan’s Python packages at the git root were incomplete copies after the kernel moved into `.cfo/`. Those copies are in [`.archive/root-kernel-shadow/`](../.archive/README.md). The office does not import them.
