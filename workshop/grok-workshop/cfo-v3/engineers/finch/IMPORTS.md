# finch 0001: the fourteen `from skills import` modules

Outcome: all fourteen modules are kept. None is deleted. In each module, every
`compose_instructions(...)` call is now a plain string, and the
`from skills import ...` line is gone. No skills package was recreated. No
skill markdown came into the kernel.

## Why nothing is bloat

1. The compiler (`python -m compiler`) imports nothing from the kernel. It
   reaches only `compiler.__main__`, `compiler`, and `compiler.compile_lib`.
   But `compile_lib.compile_catalog` parses every `agent.py` and `agents.py`
   under the kernel with `ast` and reads each `Agent(name=..., tools=...)`
   constructor. Those constructors are the only source for `grants.json` and
   `grants.eval.json`. If one of the fourteen modules is deleted, its Display
   names disappear from Grants, and the sidecar refuses every op for those
   Display names (`cfo_kernel/grants.py` `granted_ops`). So the compiler needs
   the `tools=` lists of all fourteen modules. The mission rule is: keep the
   constructor module and replace `compose_instructions(...)` with a plain
   string.
2. The sidecar (`python -m cfo_kernel`) also imports ten of the fourteen at
   runtime. It does this through `cfo_kernel/paths.py` `attach_computer`
   (imports inside functions) and through the catalog op modules that
   `cfo_kernel/invoke.py` loads with `importlib`.

`engineers/finch/import_graph.py` proves the reachability. It parses every
kernel `.py` file and collects all imports, including imports inside
functions. It then walks two roots:

- compiler: `compiler.__main__`.
- sidecar: `cfo_kernel.__main__` and the 15 modules named in the `python`
  fields of `compile-out/catalog.json`.

Run it with `.venv/bin/python engineers/finch/import_graph.py .cfo-v3/kernel`.

## Per module

"Grants" lists the Display names the compiler reads from that file. "Sidecar
chain" is one shortest static import chain from a sidecar root.

| Module | Kept? | Grants it feeds | Sidecar chain |
|---|---|---|---|
| `agent.py` | kept | AP Preparer, Exception Investigator, AP Reviewer, AP Approver, AP Audit | `cfo_kernel.__main__ -> cfo_kernel.paths -> accrual.workflow -> agent` |
| `reporting/agents.py` | kept | Variance Analysis Agent, Reporting Reviewer Agent, Board Reporting Agent, Cash Forecast Agent, Forecast Reviewer Agent, Forecast Variance Agent | not reached |
| `close/agents.py` | kept | Month-End Close Reviewer, Close Manager | `close.tools -> close.month_end -> close.agents` |
| `cash_recon/agent.py` | kept | Cash Reconciliation Preparer, Cash Exception Investigator, Cash Reconciliation Reviewer | `bs_recon.tools -> bs_recon.packets -> cash_recon.workflow -> cash_recon.agent` |
| `integrations/agent.py` | kept | Stripe Payout Agent | not reached (no kernel importer) |
| `scheduling/agent.py` | kept | Payment Scheduler, Payment Audit | not reached (no kernel importer) |
| `ar/agents.py` | kept | Collections Agent, Cash Application Agent, Cash Application Reviewer | `cfo_kernel.__main__ -> cfo_kernel.paths -> integrations.providers -> integrations.providers.stripe -> ar.stripe_intake -> ar.workflow -> ar.agents` |
| `inbox/agents.py` | kept | Counterparty Message Agent, Finance Inbox Agent | `inbox.tools -> inbox -> inbox.workflow -> inbox.agents` |
| `accrual/agent.py` | kept | Accrual Agent | `cfo_kernel.__main__ -> cfo_kernel.paths -> accrual.workflow -> accrual.agent` |
| `prepaid/agent.py` | kept | Prepaid Preparer, Prepaid Reviewer | `close.tools -> close.month_end -> prepaid.workflow -> prepaid.agent` |
| `bs_recon/agent.py` | kept | Balance Sheet Reconciliation Preparer, Balance Sheet Reconciliation Reviewer | `bs_recon.tools -> bs_recon -> bs_recon.workflow -> bs_recon.agent` |
| `fixed_assets/agent.py` | kept | Fixed Asset Preparer, Fixed Asset Reviewer | `close.tools -> close.month_end -> fixed_assets.workflow -> fixed_assets.agent` |
| `audit/agent.py` | kept | Auditor Agent, Audit Report Agent | not reached |
| `invoice_ingestion/agents.py` | kept | Email, ERP, Procurement, Vendor Portal, Employee Submission, Physical Mail / Document, EDI / Electronic Invoicing, and Bank/Card Discovery Agents | `cfo_kernel.__main__ -> cfo_kernel.paths -> invoice_ingestion.workflow -> invoice_ingestion.sources -> invoice_ingestion.agents` |

The sidecar does not reach four modules: `reporting/agents.py`,
`integrations/agent.py`, `scheduling/agent.py`, and `audit/agent.py`. The
compiler still reads their constructors for Grants. Some of their Display
names are live Bot profiles in `.cfo-v3/office` slug-map fragments:

- Payment Scheduler is in `bots/pay/slug-map.fragment.json`.
- Auditor Agent and Audit Report Agent are in
  `bots/audit/slug-map.fragment.json`.

No slug-map fragment names Stripe Payout Agent, Payment Audit, or the six
reporting Display names today. The compiler still emits Grants for them. I did
not delete them. Deleting them would change `grants.json`, and the mission rule
keeps any constructor the compiler reads.

## What changed in each file

- The rewrite is mechanical. `engineers/finch/strip_compose.py` changes each
  `compose_instructions(ROLE, skills=skills_for(...), safety=S)` call to
  `ROLE + "\n\n" + S`. Without skills, the old loader
  (`.cfo/skills/loader.py`) returned exactly
  `"\n\n".join([role.strip(), safety.strip()])`, so the prompt text is the
  same except for the skill bodies. All 41 calls passed `safety=`. The script
  also removes the `skills=` argument and the `from skills import ...` line.
- `inbox/agents.py`: `skill_traces()` called `usage_from_agent`. It now returns
  `(None, None)`. `InboxTrace.sender_skills` and `receiver_skills` are
  `Optional[AgentSkillTrace]`, so `inbox/workflow.py` works without a change.
- `engineers/finch/before/` holds the pre-edit files, copied from `.cfo/`. The
  first backup attempt failed. To prove `.cfo/` is a valid baseline, I ran
  `strip_compose.py` on fresh copies of the `.cfo/` files. All fourteen outputs
  are byte-identical to the edited `.cfo-v3/kernel` files.

## Done-when results

Run with `PYTHONPATH=.cfo-v3/kernel` and `.cfo-v3/kernel/.venv/bin/python`:

- `python -m cfo_kernel --help` prints usage and exits with 0.
- `python -m compiler --out /tmp/cfo-v3-compile` prints
  `cfo-catalog compile ok`, `catalog ops: 101`, and `display names: 41`, and
  exits with 0. `catalog.json`, `grants.json`, and `grants.eval.json` in
  `/tmp/cfo-v3-compile` are JSON-equal to `.cfo-v3/kernel/compile-out/`
  (101 ops, 41 Display names).
- `grep -rn "from skills import" .cfo-v3/kernel --include=*.py` prints
  nothing and exits with 1.

## Not fixed: the sidecar still cannot attach a Computer

This is outside this part. The next child needs to know it.

After this change, `from skills import` is gone. But eleven kernel files
still import from `skills.loader` (mostly `usage_from_agent`), and `.cfo-v3/kernel/skills/`
has no `loader.py`:

- `workflow.py`
- `accrual/trace.py`
- `ar/workflow.py`
- `audit/workflow.py`
- `bs_recon/workflow.py`
- `cash_recon/workflow.py`
- `fixed_assets/workflow.py`
- `invoice_ingestion/sources.py`
- `prepaid/workflow.py`
- `reporting/workflow.py`
- `skills/assignments.py`

`skills/assignments.py` imports `skills.loader.list_skill_names` and
`load_skill`. The compiler reads that file with `ast` only, so the compiler
does not fail.

Proof: `attach_computer` on a temporary Computer, with `data` linked to
`.cfo-v3/world/maximor`, fails with
`ModuleNotFoundError: No module named 'skills.loader'`. The chain is
`close.month_end -> accrual.workflow -> accrual.discovery -> accrual.trace`.
In fresh interpreters, 8 of the 14 modules also fail to import for the same
reason, through their package `__init__`. Those modules are `reporting.agents`,
`close.agents`, `ar.agents`, `inbox.agents`, `prepaid.agent`,
`bs_recon.agent`, `fixed_assets.agent`, and `invoice_ingestion.agents`.
`agent`, `cash_recon.agent`, `integrations.agent`, `scheduling.agent`,
`accrual.agent`, and `audit.agent` import cleanly.

`--help` passes only because `cfo_kernel/paths.py` imports the domain modules
lazily. The next part should apply the same rule to `usage_from_agent`: drop
the trace field or pass `None`. It should not recreate `skills/loader.py`.
`skills/models.py` (`AgentSkillTrace`) exists and imports cleanly.

## Not proved

- I did not start the sidecar over HTTP or call any op. The attach failure
  above blocks that.
- Reachability is static. It covers every `import` and `from ... import`
  statement at any depth. It does not cover `importlib` calls outside
  `cfo_kernel/invoke.py`. A kernel-wide grep found none.
