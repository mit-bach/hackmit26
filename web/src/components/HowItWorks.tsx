export function HowItWorks() {
  const steps = [
    {
      title: "Inputs",
      body: "Invoices, purchase orders, bank activity, Stripe payouts, receipts, ledger records, and decisions saved from earlier months.",
    },
    {
      title: "Finance agents",
      body: "A small team of specialized agents takes related jobs. Incoming-records agents land documents. Payables, cash, close, reporting, and control agents do the work.",
    },
    {
      title: "Shared context",
      body: "Every agent reads and writes the same company picture: the books, open bills, unpaid invoices, cash, and saved reasons from prior periods.",
    },
    {
      title: "Finance actions",
      body: "Approve or hold a bill. Match a payment. Estimate a missing expense. Project cash. Write an audit finding. Keep an explanation with the decision.",
    },
    {
      title: "Review and trail",
      body: "When evidence is weak, the working agent does not guess. A control agent looks for reasons to refuse. Later, audit can sample the same history.",
    },
  ];

  return (
    <section className="showcase-section" id="how-it-works">
      <div className="eyebrow">How Maximor works</div>
      <h2 className="section-title">One company picture, several coordinated agents</h2>
      <p className="lede">
        Inputs land, agents act, the books stay shared, and every material decision keeps its evidence. Uncertain work is rechecked by a control agent — not waved through, and not sent to a person to rubber-stamp.
      </p>
      <div className="how-flow">
        {steps.map((step, index) => (
          <div className="how-step" key={step.title}>
            <div className="how-index">{String(index + 1).padStart(2, "0")}</div>
            <h3>{step.title}</h3>
            <p>{step.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
