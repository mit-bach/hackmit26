import { Link } from "react-router-dom";
import { PageHead } from "../layout/Shell";
import { SandboxDiagram } from "../components/SandboxDiagram";
import {
  SANDBOX_FIXTURES,
  SANDBOX_IS_SIMULATED,
  SANDBOX_NOT_CONNECTED,
} from "../data/sandbox";

export default function Sandbox(): JSX.Element {
  return (
    <div>
      <PageHead
        eyebrow="Proof of concept"
        title="This office is a sandbox"
        lede="Maximor is not plugged into a live Stripe account, a live bank, or a company Gmail inbox. The records you see belong to Maximor Demo Corp for September 2026: a constructed company picture, with World sitting beside it as the outside world that is not attached on this demo."
      />
      <SandboxDiagram />
      <div className="grid-2" style={{ marginTop: 22 }}>
        <div className="card">
          <h2>What is not connected</h2>
          {SANDBOX_NOT_CONNECTED.map((item) => (
            <div key={item.title} className="sandbox-bound">
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </div>
          ))}
        </div>
        <div className="card">
          <h2>What is simulated</h2>
          {SANDBOX_IS_SIMULATED.map((item) => (
            <div key={item.title} className="sandbox-bound">
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </div>
          ))}
        </div>
      </div>
      <h2 className="section-title" style={{ marginTop: 28 }}>
        What we planted in September
      </h2>
      <p className="muted">
        These are not live customer events. They are the fixture cases the agents have to handle without inventing a story.
      </p>
      <div className="sandbox-fixtures">
        {SANDBOX_FIXTURES.map((item) => (
          <Link className="card sandbox-fixture" to={item.href} key={item.id}>
            <h3>{item.title}</h3>
            <p>{item.what}</p>
            <span className="mono">{item.recordId}</span>
          </Link>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 18 }}>
        Close stays blocked on the unexplained $12.40. That is the point of the sandbox: the agents work the records they have, and they stop where the evidence stops.
      </p>
    </div>
  );
}
