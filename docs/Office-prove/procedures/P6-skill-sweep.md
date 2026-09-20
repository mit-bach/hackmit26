# P6 — Skill sweep

**Job.** Every Computer `SKILL.md` (33) loads on a Bot that is assigned it, in a turn that completes without throw. INTENDED for a skill is remainder, not Kernel English. Skills never grant tools. This procedure does not restore send.

**Owns.** Skill files and `assignments.py` intersect with Roster skills.

**Must not.** Assign sample-data skills to floor Bots. Load Kernel-only `synthetic-finance-scenario-design` or `cross-ledger-data-consistency` on grain Bots. Rewrite a Skill into a must_hold clone to make INTENDED look green.

**Coverage claimed.** Table D in `../04-coverage.md`.

**Preconditions.** P0 INTENDED. Month instance may already have ticked many rows. This procedure is the remainder sweeper plus a load audit of the 33.

**Instance.** Coverage `prove-<date>-skills-rN` or the month instance if you only read traces and fill holes with extra Wakes.

---

## S01 — Inventory on this Computer

- Stimulus: none

```bash
ls {COMPUTER}/skills/*/SKILL.md | wc -l
# compare to assignments.py AGENT_SKILLS for floor Display names
```

- INTENDED: 33 Computer skills. Note extras/missing
- HARD if: SKILL.md JSON/frontmatter parse crash when Pi loads (if you see it in S02)
- Ticks: inventory

---

## S02 — Intersect check

- Stimulus: none. For each Roster Bot, compute `grant.skills ∩ roster.skills` using live grants.json and roster.json
- HARD if: a Bot’s home procedure required a skill that Client drops (T6 intersect)
- SOFT if: Roster lists a skill not in assignments — will not load under Client. Log. After procedure, sync assignments or roster. Do not dump whole-tree by turning off HARNESS_CLIENT_SKILLS
- Ticks: intersect

---

## S03 — Tick from month traces

- Stimulus: none. Read month instance `pi-runtime` / prompt / skill loader logs if present, else infer from Wakes that named the Profile
- Fill coverage.md for skills already loaded in P1–P5
- Remaining rows go to S04+

---

## S04 — Remainder Wakes (intake Profiles)

Force one Profile per turn. Goal is **load**, then one granted read op RUNS.

| Wake Bot | profile | Skill that must appear |
| --- | --- | --- |
| email | portal | invoice-source-identification, invoice-field-interpretation, superseded-document-handling |
| email | employee | same |
| email | document | same |
| books | procurement | invoice-source-identification |
| bank | card | bank-charge-invoice-discovery |

EDI/ERP have empty skill tuples. Do not invent skills. Their ops are P7.

RUNS: skill name in loaded set; turn completes.
INTENDED: remainder (what kind of document; which copy is live). SOFT if procedure dump only.
HARD: throw; clientSkills false dumping all 33 into collect (T6 dump). Dump is HARD for this step because SoD mush and token poison. Turn clientSkills on, new instance.

---

## S05 — Shared doer/Verifier skills (T9)

For `three-way-match-analysis`, `payment-prioritization`, `early-payment-discount-evaluation`, `cash-application`:

- Confirm both doer and Verifier loaded them (month traces)
- INTENDED: Verifier turn finds reasons to refuse, not a second ranking
- SOFT: identical ranking prose (T9). After procedure, split remainder in the Verifier Skill without adding a Bot
- Do not remove the skill from Verifier if that was the only refuse language unless you replace remainder

---

## S06 — prior-period-precedent crowd

- Loaded on at least one of ap investigate, cash investigate, close accrue, ctl-books lock
- INTENDED: reuse only if current evidence supports it. Not a graph database
- SOFT: generic essay, no object
- T10 still may SKIP

---

## S07 — Empty Grant + skills

Close Manager, Month-End Close Reviewer, Audit Report, Stripe:

- Skill may load
- Catalog claim is P5/P7 HONEST-EMPTY
- P6 ticks **load**, not office-live caller
- HARD if you mark P6 INTENDED “coordination skill ran the close DAG” with ops []

---

## S08 — Batch edit after SOFTs

When P6 (and pipe procedures) end:

1. List SOFT skill files
2. Edit Kernel `skills/` and copy/compile to Computer as this office does
3. Keep registry skeleton if required, but cut Kernel replay. Leave remainder
4. New instance. Re-run the home procedure for those skills (not only P6 load Wake)
5. Three SOFTs → keep logging. Do not freeze Kernel

---

## Done-when

- Bare min: 33 rows ticked RUNS (loaded) or HONEST-UNASSIGNED (Kernel-only off floor) or SKIP with reason
- INTENDED: no required skill dropped by intersect; Verifier remainder distinct; no whole-tree dump

## Forbidden

Skills granting tools. Turning off Client skill filter to “validate” files. Sample-data skills on floor.
