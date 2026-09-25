import type { ServerResponse } from "node:http";

export type BusFrame = {
  readonly kind: string;
  readonly [key: string]: unknown;
};

export class EventBus {
  private readonly clients = new Set<ServerResponse>();

  subscribe(res: ServerResponse): () => void {
    this.clients.add(res);
    res.on("close", () => {
      this.clients.delete(res);
    });
    return (): void => {
      this.clients.delete(res);
    };
  }

  publish(frame: BusFrame): void {
    let payload: string;
    try {
      payload = `data: ${JSON.stringify(frame)}\n\n`;
    } catch {
      return;
    }
    for (const res of [...this.clients]) {
      try {
        res.write(payload);
      } catch {
        this.clients.delete(res);
      }
    }
  }

  get clientCount(): number {
    return this.clients.size;
  }
}
