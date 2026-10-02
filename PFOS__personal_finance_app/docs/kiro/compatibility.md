# Compatibility and activation evidence

Owner: KDE contract Phase 1. Inspection date: 2026-09-16.

## Observed locally

- Installed application package reports Kiro 0.12.333; bundled agent 0.3.721.
  This is filesystem metadata, not a running-IDE activation transcript.
- Native Node reports 24.14.1. Git, SSH and gh are discoverable on subprocess PATH.
  Docker and kiro-cli were not found there; this does not prove they are uninstalled.
- Global configuration contains unrelated always-on steering, skills, agents and MCPs.
  It is unchanged. Workspace inclusion does not eliminate global context.
- The old autobuilder's spec list matched none of the six existing spec directories.
  No autobuilder, new custom agent, hook, MCP or Power was activated.
- Twelve workspace skills have positive/negative trial prompts. Structural tests
  validate their metadata, paths and references, not semantic routing by the model.
- Stable playwright-core 1.63.0 installed under scripts/kiro with a separate lockfile.
  Local browser navigation/reload trial passed; this was executed through Aki, not Kiro.

## Official documented behavior, not an observed result

- Skills: https://kiro.dev/docs/skills/ specifies .kiro/skills and progressive discovery.
- Steering: https://kiro.dev/docs/steering/ specifies inclusion modes and always-included
  AGENTS.md. The page warns that CLI inclusion differs; do not promise cross-surface parity.
- MCP: https://kiro.dev/docs/mcp/configuration/ specifies workspace/global merging and
  reconnect-on-save behavior. No credential-dependent placeholder configuration is added.
- IDE 1.0: https://kiro.dev/changelog/ide/1-0/ introduces newer custom agents, permissions
  and hooks. Do not apply current 1.0 schemas blindly to installed 0.12.
- Powers: https://kiro.dev/docs/powers/create/ documents Agent Plugins and legacy support.
- Native tools: https://kiro.dev/docs/tools/ distinguishes IDE and CLI capabilities.

Some official pages disagree about custom-agent default resource inheritance. Resolve
against the actual version and observed context before creating such an agent. No upgrade
or global migration is part of the foundation. Default context bytes are configuration
measurements, not measured token savings or model-quality benchmarks.

## Fresh-session Kiro trial protocol (outstanding)

1. In the existing IDE open this workspace and a new chat. Inspect Steering & Skills.
2. Submit one registry positive prompt without naming its skill; observe which SKILL.md
   is loaded, selected tools and whether its shared reference is read when required.
3. Submit its negative prompt in another fresh session; record incorrect activation too.
4. Repeat for all twelve skills. Test explicit file-read fallback if discovery is absent.
5. Run local validation and browser commands from Kiro, with no provider authentication.
6. Record IDE version, prompt, expected/actual skill, tool result, date and source reference.
   Do not promote registry activation by assumption; evolve its evidence schema deliberately
   when actual transcripts exist. Current schema intentionally allows UNVERIFIED only.

GitHub CLI public release retrieval returned exit 4; authenticated CLI readiness is not
established. A public HTTP API GET succeeded. Credentialed MCP and VPS trials remain
unperformed. No secret or host
particular belongs in transcripts. A missing capability is a named gap, not a fabricated
working config. User action is required for IDE update/global scope or live authorization.
