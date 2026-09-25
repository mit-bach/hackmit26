import assert from "node:assert/strict";
import { test } from "node:test";

import { acquireLease, releaseLease } from "../src/leases.ts";
import { makeComputer } from "./helpers.ts";

test("a live lease blocks another Bot from the same path", () => {
  const computer = makeComputer();
  assert.equal(acquireLease(computer, "workspace/note.md", "bot_alpha"), true);
  assert.equal(acquireLease(computer, "workspace/note.md", "bot_beta"), false);
  releaseLease(computer, "workspace/note.md", "bot_alpha");
  assert.equal(acquireLease(computer, "workspace/note.md", "bot_beta"), true);
});
