**HACKMIT 2026 · MAXIMOR TRACK · $4,000 · $2,000 · $1,000 FOR 1ST, 2ND AND 3RD**

# **Agentic Systems for the Office of the CFO**

How much of a finance team can an agentic system run? No finance background needed.

**Build an agentic system that runs the Office of the CFO.**

The Office of the CFO (Chief Financial Officer) is the finance team: paying vendors, collecting from customers, reconciling cash, closing the books, forecasting, answering auditors, and explaining why the numbers moved. It all connects. One paid invoice touches the bank reconciliation, the cash forecast, the close, and the audit file. The work is multi-step, spread across systems and people, and unforgiving of mistakes.

Take on as much of it as you can. One process done with real depth is a strong entry; several agents running different parts of the function, sharing context, handing off work, and being able to defend the result to an auditor is the stretch goal. The company, the tasks, the setting and the data are yours to pick or invent.

**Prizes**

* 1st place: $4,000  
* 2nd place: $2,000  
* 3rd place: $1,000

**Fast track to internships and full-time roles**

The top 5 teams skip the applicant pool entirely. Every member is fast-tracked to an expedited, shortened interview process for our Summer 2027 Internship and 2027 New Grad Software Engineer roles, jumping ahead of 3,000+ internship applicants and 5,000+ full-time applicants who've already applied.

**DIRECTIONS WE’D LOVE TO SEE**

* **Whole-function systems:** many workflows, one shared picture of the company

* **Multi-agent teams:** preparer, reviewer, approver, auditor; hand-offs and escalation like a real team

* **Memory and context:** precedent from past periods, a context graph that carries across months

* **Self-improvement:** learn from previous runs, corrections or feedback, and show it

* **Long horizons:** a whole month-end close or a full quarter, not a single question

**EXAMPLE FINANCE PROCESSES**

Some of the processes a finance team runs, not all of them. The company, the data and the setting are yours to choose or invent.

**Accounts payable and receivable (AP/AR)**

* Three-way match each vendor invoice to its purchase order and goods receipt, hold duplicates, route approvals, decide what gets paid this week. Work the receivables aging (unpaid customer invoices by age), chase, and apply cash to the right invoices when the payment doesn’t say which.

**Cash and reconciliation**

* Reconcile a month of bank activity to the ledger: one payment covering three invoices, a wire net of bank fees, a refund posted twice, a $12.40 difference nobody can explain. Match [Stripe](https://stripe.com) or [Adyen](https://www.adyen.com) payouts to orders and deposits, net of fees and chargebacks.

**Month-end close**

* Book accruals for bills not yet received, spread prepaid and asset costs over the months they cover, tie every balance-sheet account to evidence, and track what’s done and what’s stuck.

**Audit and controls**

* Play the auditor: sample transactions, re-perform reconciliations, test controls, write up findings. Watch for duplicate vendors, round-number payments, entries posted after the period closed, self-approved requests.

**Reporting and forecasting**

* Explain a variance (gross margin dropped three points; trace it to the transactions responsible) and draft the board pack with numbers that tie to the ledger. Keep a 13-week cash forecast alive from receivables, payables and payroll; when actuals land, explain the miss.

**HOW WE JUDGE**

Ambition and creativity, technical difficulty, how close you get to the frontier of what agentic systems can do, and the demo. We look for multi-step reasoning over real documents and data, coordination or memory that changes what the system does next, consistency across workflows (the same transaction means the same thing everywhere), and human review when the system is uncertain. No fixed benchmark; show us your own measure of “better.”

A one-shot chatbot, an extraction pipeline, a hard-coded accounting workflow, or a personal-finance app is not enough.

## **Build with whatever is at the frontier**

* **Models.** [Claude](https://www.anthropic.com/claude), [GPT](https://openai.com/api/), [Gemini](https://ai.google.dev/); open-weight [Qwen](https://github.com/QwenLM), [Llama](https://www.llama.com/), [DeepSeek](https://www.deepseek.com/), [Kimi](https://github.com/MoonshotAI), [Gemma](https://ai.google.dev/gemma) if you want to fine-tune.

* **Harnesses.** [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) (subagents, skills, hooks, tools over [MCP](https://modelcontextprotocol.io)); [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) and the new [Agents API](https://openai.com/index/introducing-the-agents-api/); LangChain’s [deepagents](https://github.com/langchain-ai/deepagents), [Pydantic AI](https://ai.pydantic.dev/), [CrewAI](https://www.crewai.com/), [smolagents](https://github.com/huggingface/smolagents); [computer use](https://docs.claude.com/en/docs/agents-and-tools/tool-use/computer-use-tool) for systems that only have a UI.

* **Memory and learning.** [Letta](https://www.letta.com/), [Mem0](https://mem0.ai/), [Zep/Graphiti](https://github.com/getzep/graphiti); self-written skills or rules; [DSPy](https://dspy.ai/) and [GEPA](https://github.com/gepa-ai/gepa) for prompt and program optimization; fine-tuning if you have the data. On context graphs: Foundation Capital’s [AI’s trillion-dollar opportunity](https://foundationcapital.com/ideas/context-graphs-ais-trillion-dollar-opportunity) (decision traces behind approvals and exceptions) and Neo4j’s [hands-on with context graphs](https://neo4j.com/blog/agentic-ai/hands-on-with-context-graphs-and-neo4j/).

## **Reference points**

Existing work, for calibration. None of it is required; your own company, tasks, setting or data are just as valid.

[AccountingBench](https://x.com/yunyu_l/status/1946261507723173935)

An agent closes a real software company’s books month by month and drifts as errors compound.

[APEX-Accounting](https://huggingface.co/datasets/mercor/apex-accounting)

A synthetic company at month-end close with ten rubric-graded accounting tasks.

[Finance Agent Benchmark](https://huggingface.co/datasets/vals-ai/finance_agent_benchmark)

Analyst research tasks over public-company filings; frontier models score around 50%.

[DABstep](https://huggingface.co/datasets/adyen/DABstep)

A year of card-payment data with 450 multi-step analysis questions and exact answers.

[BenchRec](https://www.kaggle.com/datasets/benchmarkteam/benchrec-real-world-cash-reconciliation-dataset)

Real, anonymized bank-to-ledger matches from a large bank, labeled by its analysts.

[Invoice Sandbox Benchmark](https://github.com/ciru-ai/invoice-sandbox-benchmark)   ciru-ai

A synthetic accounts-payable inbox with planted traps and a hidden-answer grader.

## **Key concepts**

* **General ledger (GL) —** the master record of every transaction, by account.

* **Reconciliation —** checking two records of the same thing agree, and explaining every difference.

* **Month-end close —** finishing the books each month: post, reconcile, fix, report.

* **Variance (flux) —** why a number differs from last month or budget.