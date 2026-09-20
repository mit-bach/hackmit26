import { useEffect, useState } from "react";
import { get } from "../api";
import { PageHead } from "../layout/Shell";
import { AGENT_COPY, formatAgent } from "../copy";
import { TraceIds } from "../components/Explain";

export default function Architecture() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    get("/api/architecture").then(setData);
  }, []);

  return (
    <div>
      <PageHead
        eyebrow="Implementation"
        title="System architecture"
        lede="Data sources feed a canonical Maximor company state. Fifteen specialized finance agents share skills and decision memory, then close, audit, and evaluate against known cases."
      />
      <div className="arch">
        <div className="arch-col">
          <h3>Data sources</h3>
          {(data?.data_sources || []).map((item: string) => (
            <div key={item} className="chip">
              {item}
            </div>
          ))}
        </div>
        <div className="arch-col">
          <h3>Canonical state</h3>
          <div className="chip">{data?.canonical_state}</div>
          <div className="chip">Kernel .cfo/</div>
        </div>
        <div className="arch-col">
          <h3>Rooms</h3>
          {(data?.rooms || []).map((room: any) => (
            <div key={room.id} style={{ marginBottom: 8 }}>
              <strong>{room.id}</strong>
              <div className="muted">{(room.members || []).join(", ")}</div>
            </div>
          ))}
        </div>
        <div className="arch-col">
          <h3>Memory</h3>
          {(data?.decision_memory || []).map((item: string) => (
            <div key={item} className="chip">
              {item}
            </div>
          ))}
        </div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h2>15 specialized finance agents</h2>
        <table className="data">
          <thead>
            <tr>
              <th>Agent</th>
              <th>What it does</th>
            </tr>
          </thead>
          <tbody>
            {(data?.bots || []).map((bot: any) => (
              <tr key={bot.slug}>
                <td>
                  <div>{formatAgent(bot.slug)}</div>
                  <TraceIds ids={[bot.slug]} label="Internal slug" />
                </td>
                <td>{AGENT_COPY[bot.slug]?.role || bot.purpose}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted">{data?.note}</p>
      </div>
    </div>
  );
}
