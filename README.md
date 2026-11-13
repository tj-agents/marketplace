# TJ Agents marketplace

One shared plugin roster, projected into one package format both Claude Code and Codex read, for the
current plugins published from `tj-agents/core`, `agent`, `cli`, `github`, `cpp`, `dotnet`, `aspire`, `react`,
`nvim`, `rust`, `python`, `github-actions`, `azure`, `learning`, `template`, `personal`, `work`, and
`infonetica`. Packages stay in their source repositories; this repository never authors plugin content
itself. Adding another repository requires one entry in `plugins.json`; `generate.py` produces the
matching Claude and Codex marketplaces. Core launch refresh updates selected plugin content from these
source repositories.

This roster also supplies Agent's pinned offline project selector snapshot. After publishing a
roster change, regenerate that snapshot through Agent's
`.agents/agent/utility/plugins/scripts/update_marketplace_plugins.py` and check
the resulting plugin selection. The [shared ownership decision](https://github.com/tj-agents/docs/blob/main/PLUGINS.md)
records which repository owns each part of the flow.

Add the marketplace and select plugins explicitly:

```text
Claude: /plugin marketplace add tj-agents/marketplace
Claude: /plugin install cpp@tj-agents
Codex:  codex plugin marketplace add tj-agents/marketplace
Codex:  codex plugin add cpp@tj-agents
```

Available canonical plugins are `base`, `agent-store`, `agent`, `codex`, `cli`, `github`, `workflow`,
`engineering`, `docs`, `cpp`, `gpp`, `msvc`, `win32`, `dotnet`, `efcore`, `aspire`, `react`, `nvim`, `rust`,
`tauri`, `rust-sqlx`, `seaorm`, `python`, `github-actions`, `azure`, `learning`, and
`template` and its sibling `skill` authoring package, the explicitly adopted `personal` profile, `teams` for Teams messages in any repo, and the employer-scoped `work` and `infonetica` profiles. Select `cpp` plus one toolchain (`gpp` or `msvc`) and
optionally `win32` for C++ work. For generic sustained tasks, select the `base`, `agent-store`,
`agent`, `cli`, and `workflow` closure. CLI supplies exact-target close utilities;
Agent supplies session-aware target resolution and coordination.
For software work, select `engineering` plus the common closure.
Each plugin entry declares its actual prerequisites. Runtime packages remain reusable without Engineering;
stack and product profiles retain their declared Engineering dependencies. Claude installs each entry's `requires` as `dependencies`; Codex
does not resolve dependencies, so a selection still lists the closure.

## Project scope

Tommy explicitly confirmed on 2026-11-11 that all `tj-agents` source repositories are personal projects,
including standards and tooling for work integrations. Use that recorded scope for new repositories;
do not ask again based on their subject matter. Employer application repositories retain their own scope.

For projects Tommy explicitly identifies as personal, select `personal` and its actual requirement closure:
`engineering`, `agent`, `cli`, `base`, `agent-store`, and `workflow`. Then run `personal:use` to generate and
check mandatory native instructions for Claude and Codex. Selection alone does not establish that the policy
loaded. Employer projects remain outside this profile. The policy and adoption procedure are authored in
[tj-agents/personal](https://github.com/tj-agents/personal).

Project declarations and installed registrations use the shared `@tj-agents` identities. Remove
superseded registrations in the same migration so duplicate skills and hooks do not load. Codex entries
in this marketplace are `AVAILABLE`, so adding the marketplace does not automatically install copies.

Edit `plugins.json`, then run:

```text
python -B generate.py
python -B generate.py --check
claude plugin validate .
```

Each roster entry optionally declares `revision`, the full lowercase 40-character commit ID of a
published producer payload. Generation writes it as the native `source.sha`; an entry without a revision
uses `source.ref: main`. Marketplace owns these producer pins. Publish and verify the producer payload
before activating its revision here.

Agent and Core each require one revision across every entry from that producer when pinned. Mixing
pinned and unpinned entries, or two revisions of one producer, is rejected. Update the Agent/Core pair
in one roster change after both payloads are published. Other producers retain independent entry policy.

When adding a package, publish its producer payload and roster entry before activating repository selections.
Keep the complete selection changes in a dependent delivery slice, then verify native admission and
the selected packages after publication.

Project selection is explicit in the repository's `.agents/plugins.json`. Use `agent:plugins` to select
the desired plugins. Refreshing the project brings selected content up to date; adding the marketplace does not
install or select plugins, and it does not prove activation.

Adding this marketplace installs nothing on either host. When migrating an installed legacy identity, disable or
uninstall the old copy before enabling its `@tj-agents` copy. Do not enable both producer and aggregate identities
for the same plugin. Neither registering this marketplace nor selecting plugins proves that hooks are active; verify
that separately with native host acceptance.

Personal owns GitHub work items; Infonetica owns Azure Boards work items and employer type policy.
Each profile supplies `work-item`, `create-work-item` and `address-work-item` under its qualified namespace.
Agent owns the shared agent execution/session registry; Core owns Engineering workflows. Work supplies employer-neutral
communication tools. Select the intended profile explicitly; installing Core does not select a tracker.

Skill authoring uses `skill:new` and `skill:update`, both published from `tj-agents/template`.
Template depends on Skill so selected plugin publishers load the current native-creator authoring workflow.
