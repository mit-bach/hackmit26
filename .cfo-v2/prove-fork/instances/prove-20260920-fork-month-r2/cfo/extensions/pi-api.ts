/**
 * Minimal Pi extension surface. Kept local so this Client package does not
 * import Harness types. Runtime Pi supplies the matching object.
 */

export interface PiToolResult {
  readonly content: ReadonlyArray<{readonly type: "text"; readonly text: string}>;
  readonly details: unknown;
}

export interface PiToolCallEvent {
  readonly toolName: string;
  readonly input: unknown;
}

export interface PiInputEvent {
  readonly text: string;
  readonly source: string;
}

export interface PiExtensionApi {
  registerTool(tool: {
    readonly name: string;
    readonly label: string;
    readonly description: string;
    readonly promptSnippet?: string;
    readonly promptGuidelines?: readonly string[];
    readonly parameters: unknown;
    readonly execute: (id: string, params: Record<string, unknown>) => Promise<PiToolResult>;
  }): void;
  on(event: "resources_discover", handler: () => {readonly skillPaths: readonly string[]}): void;
  on(
    event: "tool_call",
    handler: (
      event: PiToolCallEvent,
    ) => {readonly block: true; readonly reason: string} | void | Promise<{readonly block: true; readonly reason: string} | void>,
  ): void;
  on(
    event: "input",
    handler: (event: PiInputEvent) => {readonly action: "continue" | "handled"} | void,
  ): void;
}
