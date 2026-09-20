import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../api";
import { ActivityTape, activityFromUnknown, SlugFilter } from "../components/rest/ActivityTape";
import { asRecord, asUnknownList } from "../components/rest/kernel";
import { RestHead } from "../components/rest/RestHead";
import type { AgentSlug } from "../data/agents";

const STAKE = "Live handoffs from this machine. The office graph lives elsewhere.";

export default function Agents(): JSX.Element {
  const [data, setData] = useState<unknown>(null);
  const [filter, setFilter] = useState<AgentSlug | null>(null);

  useEffect(() => {
    get("/api/agents")
      .then(setData)
      .catch(() => setData(null));
  }, []);

  const rows = asUnknownList(asRecord(data)?.activity).flatMap((item, idx) => {
    const row = activityFromUnknown(item, idx);
    return row ? [row] : [];
  });

  return (
    <div className="rest-page">
      <RestHead title="What the Bots just did" stake={STAKE} />
      <p className="rest-graph-link">
        <Link to="/architecture">Open office graph</Link>
      </p>
      <SlugFilter selected={filter} onSelect={setFilter} />
      <ActivityTape rows={rows} filter={filter} />
    </div>
  );
}
