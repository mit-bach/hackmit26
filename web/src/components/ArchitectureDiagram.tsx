import { OfficeGraph } from "./OfficeGraph";

export interface ArchitectureDiagramProps {
  readonly selected: string | null;
  readonly onSelect: (slug: string) => void;
}

export function ArchitectureDiagram({ selected, onSelect }: ArchitectureDiagramProps): JSX.Element {
  return <OfficeGraph selected={selected} onSelect={onSelect} />;
}
