import { PageHead } from "../layout/Shell";
import { CoverageGrid } from "../components/CoverageGrid";

export default function Coverage() {
  return (
    <div>
      <PageHead
        eyebrow="Office of the CFO"
        title="What finance work Maximor covers"
        lede="These are functions of a finance office, not a one-agent-per-box org chart. Several agents can share a function. One agent can own several related jobs."
      />
      <CoverageGrid intro={false} />
    </div>
  );
}
