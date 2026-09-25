import { FileText, Folder } from "lucide-react";

import { cn } from "@/lib/cn";

export interface TreeEntry {
  readonly path: string;
  readonly type: "file" | "dir";
}

interface TreeNode {
  readonly name: string;
  readonly path: string;
  readonly type: "file" | "dir";
  readonly children: TreeNode[];
}

export function buildTree(entries: readonly TreeEntry[]): TreeNode[] {
  const root: TreeNode[] = [];
  const dirs = new Map<string, TreeNode>();
  const sorted = [...entries].sort((a, b) => a.path.localeCompare(b.path));
  for (const entry of sorted) {
    const parts = entry.path.split("/").filter((part) => part.length > 0);
    if (parts.length === 0) {
      continue;
    }
    let list = root;
    let acc = "";
    for (let i = 0; i < parts.length; i += 1) {
      const name = parts[i] ?? "";
      acc = acc.length === 0 ? name : `${acc}/${name}`;
      const last = i === parts.length - 1;
      if (last && entry.type === "file") {
        list.push({ name, path: acc, type: "file", children: [] });
        continue;
      }
      let node = dirs.get(acc);
      if (!node) {
        node = { name, path: acc, type: "dir", children: [] };
        dirs.set(acc, node);
        list.push(node);
      }
      list = node.children;
    }
  }
  const byName = (a: TreeNode, b: TreeNode): number => {
    if (a.type !== b.type) {
      return a.type === "dir" ? -1 : 1;
    }
    return a.name.localeCompare(b.name);
  };
  const sortNodes = (nodes: TreeNode[]): void => {
    nodes.sort(byName);
    for (const node of nodes) {
      sortNodes(node.children);
    }
  };
  sortNodes(root);
  return root;
}

export function ComputerTree({
  nodes,
  depth,
  open,
  selected,
  onToggle,
  onOpen,
}: {
  readonly nodes: readonly TreeNode[];
  readonly depth: number;
  readonly open: ReadonlySet<string>;
  readonly selected: string | null;
  readonly onToggle: (path: string) => void;
  readonly onOpen: (path: string) => void;
}): React.ReactElement {
  return (
    <>
      {nodes.map((node) => {
        const pad = 8 + depth * 14;
        if (node.type === "dir") {
          const expanded = open.has(node.path);
          return (
            <div key={node.path}>
              <button
                type="button"
                onClick={() => onToggle(node.path)}
                className="flex w-full items-center gap-1.5 py-1 text-left text-ink-secondary hover:bg-raised/50"
                style={{ paddingLeft: pad }}
              >
                <Folder size={12} className="shrink-0" />
                <span className="truncate">
                  {expanded ? "▾" : "▸"} {node.name}
                </span>
              </button>
              {expanded ? (
                <ComputerTree
                  nodes={node.children}
                  depth={depth + 1}
                  open={open}
                  selected={selected}
                  onToggle={onToggle}
                  onOpen={onOpen}
                />
              ) : null}
            </div>
          );
        }
        return (
          <button
            key={node.path}
            type="button"
            onClick={() => onOpen(node.path)}
            className={cn(
              "flex w-full items-center gap-1.5 py-1 text-left hover:bg-raised/50",
              selected === node.path ? "bg-raised text-ink" : "text-ink",
            )}
            style={{ paddingLeft: pad }}
          >
            <FileText size={12} className="shrink-0 text-ink-secondary" />
            <span className="truncate">{node.name}</span>
          </button>
        );
      })}
    </>
  );
}
