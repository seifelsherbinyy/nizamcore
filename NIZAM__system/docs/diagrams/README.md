# NIZAM diagrams

Mermaid source for the four diagrams mandated by
[`NIZAM_ORCHESTRATION_LAYER.md`](../NIZAM_ORCHESTRATION_LAYER.md) §6.

| File | Type | Shows |
|------|------|-------|
| [`system_architecture.mmd`](system_architecture.mmd) | flowchart LR | Sandbox (compute) vs durable layers (GitHub / Drive / Notion); the no-storage-in-sandbox boundary. |
| [`agent_dataflow.mmd`](agent_dataflow.mmd) | flowchart TD | Warden → Scribe → {Pulse, Witness} → Dispatcher → Guardrail → Steward → Almanac with record types on the edges; DeadLetter + Audit Log overlay. |
| [`write_path_sequence.mmd`](write_path_sequence.mmd) | sequenceDiagram | One record's life: dedupe check → dual-write → write-back → audit, including retry ladder (1s/4s/16s) and the "all down → print payload" last resort. |
| [`retention_lifecycle.mmd`](retention_lifecycle.mmd) | stateDiagram-v2 | Hot → Warm → Cold → Archive with the legal-hold guard. |

## Convention

- All diagrams are Mermaid (`.mmd`) so they diff cleanly and live next to the code they describe.
- Node IDs are camelCase or PascalCase — never spaces (renders break otherwise).
- Labels containing parentheses, slashes, or commas are double-quoted.
- No explicit colors or `classDef ... fill:#hex` — the renderer applies theme colors, and
  hard-coded colors break in dark mode.

## Update rule

Per §6 of the contract: **regenerate and commit these diagrams in the SAME commit as any change
they describe.** Never let the map drift from the system.

## Render locally

Any tool that speaks Mermaid will work — VS Code's Markdown preview with the Mermaid extension,
the official [`mermaid-cli`](https://github.com/mermaid-js/mermaid-cli) (`mmdc -i file.mmd -o
file.svg`), or pasting into <https://mermaid.live>.
