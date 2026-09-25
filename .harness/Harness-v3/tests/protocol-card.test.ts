import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { botSystemPath, piSessionDir, protocolCardPath } from "../src/paths.ts";
import { PROTOCOL_CARD } from "../src/protocol-card.ts";
import { makeComputer } from "./helpers.ts";

test("initComputer writes the tool protocol next to the session tree", () => {
  const computer = makeComputer();
  const card = protocolCardPath(computer);
  assert.equal(existsSync(card), true);
  assert.match(readFileSync(card, "utf8"), /ask_bot/);
  assert.match(readFileSync(card, "utf8"), /message_operator/);
  assert.equal(readFileSync(card, "utf8"), PROTOCOL_CARD);
  const systemPath = botSystemPath(computer, "bot_alpha");
  assert.equal(existsSync(systemPath), true);
  assert.equal(existsSync(join(piSessionDir(computer, "bot_alpha"), "SYSTEM.md")), true);
});
