import { SystemFlowchart } from "./SystemFlowchart";

export interface ArchitectureDiagramProps {
  readonly selected: string | null;
  readonly onSelect: (slug: string) => void;
}

export function ArchitectureDiagram({ selected, onSelect }: ArchitectureDiagramProps): JSX.Element {
  return <SystemFlowchart selected={selected} onSelect={onSelect} />;
}
