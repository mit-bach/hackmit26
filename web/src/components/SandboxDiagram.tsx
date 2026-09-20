import { Link } from "react-router-dom";
import { AgentIcon } from "./AgentIcon";
import { SANDBOX_LANDINGS, SANDBOX_PERSONAS } from "../data/sandbox";

export function SandboxDiagram(): JSX.Element {
  return (
    <div className="sandbox-flow" aria-label="How simulated records reach the office">
      <div className="sandbox-flow-band">
        <div className="sandbox-flow-kicker">Outside the company · simulated</div>
        <div className="sandbox-world">
          <div className="flow-node sys-node source not-attached sandbox-world-node">
            <span className="sys-node-icon">
              <AgentIcon slug="world" size={22} />
            </span>
            <span className="sys-node-copy">
              <span className="sys-node-name">World</span>
              <span className="sys-node-note">not on this demo roster</span>
            </span>
          </div>
          <div className="sandbox-personas">
            {SANDBOX_PERSONAS.map((persona) => (
              <div className="sandbox-persona" key={persona.id}>
                <strong>{persona.title}</strong>
                <span>{persona.does}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="sandbox-flow-arrow" aria-hidden="true">
        Fixture records land here. World would deliver the same way if it were attached.
      </div>
      <div className="sandbox-flow-band">
        <div className="sandbox-flow-kicker">What the office actually reads</div>
        <div className="sandbox-landings">
          {SANDBOX_LANDINGS.map((landing) => (
            <div className="flow-node sys-node source sandbox-landing" key={landing.slug}>
              <span className="sys-node-icon">
                <AgentIcon slug={landing.slug} size={22} />
              </span>
              <span className="sys-node-copy">
                <span className="sys-node-name">{landing.title}</span>
                <span className="sys-node-note">{landing.source}</span>
              </span>
            </div>
          ))}
        </div>
      </div>
      <div className="sandbox-flow-arrow" aria-hidden="true">
        Shared books, memory, and evidence
      </div>
      <div className="sandbox-office-card">
        <div className="sandbox-flow-kicker">Office of the CFO</div>
        <p>
          Fifteen standing finance agents work this company picture. They do not get a live bank, a live Stripe account, or a live mailbox.
        </p>
        <Link className="btn" to="/architecture">
          See how those agents are organized
        </Link>
      </div>
    </div>
  );
}
