# INSTALL — `.cfo-v3/cfo`

Child: sparrow. Mission: `prompts/sparrow/0001.md`. Date: 2026-09-24.

Package root: `/Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/cfo`.
Node `v26.9.0`, npm `11.19.1`.

## Result

- `typebox` is installed from npm. The test loads the real package, not the stub.
- `npx tsc --noEmit -p tsconfig.json` exits 0 with no output. There are no errors in `extensions/*.ts`.
- `node --test extensions/verifier-wiring.test.ts` exits 0. 5 of 5 tests pass.

## Imports compared to `package.json`

I read the import statements in each `extensions/*.ts` file (15 files). The only import that is not relative and not `node:*` is:

| Import | File | Kind |
|---|---|---|
| `typebox` (`Type`) | `extensions/index.ts:15` | runtime |

All other imports are `node:*` built-ins or relative `./*.ts` files. There is one dynamic import, `extensions/send.ts:43`, `await import(pathToFileURL(entry).href)`. It loads a file path at runtime, not a package.

## Dependency list

| Package | Section | Range in `package.json` | Installed | Why it stays |
|---|---|---|---|---|
| `typebox` | dependencies | `^1.3.7` | `1.3.34` | `extensions/index.ts` imports `Type` from it. |
| `@types/node` | devDependencies | `^24.5.2` | `24.13.6` | Provides the types for every `node:*` import. Without it, `tsc` cannot resolve `node:fs`, `node:path`, `node:test`, and the other built-ins. |
| `typescript` | devDependencies | `^5.9.2` | `5.9.3` | Provides the `tsc` binary for the mission command `npx tsc`. |

No dependency was unused, so I did not drop one. I did not change `package.json`. `npm install` created `package-lock.json` and `node_modules/` (4 packages added, 0 vulnerabilities):

```
cfo-agentic-system@0.1.0 /Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/cfo
├── @types/node@24.13.6
├── typebox@1.3.34
└── typescript@5.9.3
```

## `tsconfig.json`

The file did not exist. I copied `.cfo-v2/office/computer/cfo/tsconfig.json` and made one change. `include` is now `["extensions/**/*.ts"]`. The v2 file also listed `source-wakes.ts`, but `.cfo-v3/cfo` has no such file. The compiler options are the same as v2.

## Type check

```
$ npx tsc --noEmit -p tsconfig.json
(no output)
tsc exit=0
```

This check covers every `extensions/**/*.ts` file, including `facade.test.ts` and `verifier-wiring.test.ts`.

## Test

```
$ node --test extensions/verifier-wiring.test.ts
▶ Verifier concurrence parse
  ✔ prose that mentions CONCUR is not CONCUR (0.417833ms)
  ✔ accepts only a structured decision (0.127708ms)
  ✔ a completed Handle whose result says 'I do not concur' does not unlock (37.564ms)
✔ Verifier concurrence parse (38.866833ms)
▶ call_connected_tool through the Pi registration path
  ✔ unlocks a consequential op after CONCUR when the model retries with the same idempotency_key (241.445792ms)
  ✔ honors an explicit handle_id the model passes (221.916458ms)
✔ call_connected_tool through the Pi registration path (463.567125ms)
ℹ tests 5
ℹ suites 2
ℹ pass 5
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 916.718584
test exit=0
```

## Evidence that the test used the real `typebox`

The resolve hook in `verifier-wiring.test.ts` (lines 25–36) returns `TYPEBOX_STUB` only when `nextResolve("typebox")` throws. The test does not report which path it took, so I checked the resolution two ways:

1. `import.meta.resolve("typebox")` from the package root:
   ```
   file:///Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/cfo/node_modules/typebox/build/index.mjs
   ```
2. I ran the test file in-process with an extra resolve hook that logs the URL `typebox` resolves to. I ran the file directly, not with `--test`, so the log reaches the terminal instead of a subprocess:
   ```
   $ node --import 'data:text/javascript,…registerHooks({resolve(s,c,n){const r=n(s,c);if(s==="typebox")process.stderr.write("TYPEBOX_RESOLVED "+r.url+"\n");return r;}})' extensions/verifier-wiring.test.ts
   TYPEBOX_RESOLVED file:///Users/dominikbach/olympus/hackmit/hackmit26/.cfo-v3/cfo/node_modules/typebox/build/index.mjs
   ℹ pass 5
   ℹ fail 0
   ```

`nextResolve` returned a `node_modules` URL, so the `catch` branch did not run and the stub did not load.

## Not done / not proved

- I did not run `extensions/facade.test.ts`. The mission names only `verifier-wiring.test.ts`. `tsc` type-checks `facade.test.ts`, but its tests did not run.
- The `package.json` scripts (`build`, `test`) point at `dist/extensions/facade.test.js`, and `dist/` does not exist. I did not run or change those scripts because they are outside the mission.
- I did not edit `extensions/*.ts`.
