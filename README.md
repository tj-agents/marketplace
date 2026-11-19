# TJ Agents marketplace

One shared plugin roster, projected into one package format both Claude Code and Codex read, for the
current plugins published from `tj-agents/core`, `agent`, `cli`, `github`, `cpp`, `dotnet`, `react`,
`nvim`, `rust`, `python`, `github-actions`, `azure`, `learning`, `template`, `personal`, `work`, and
`company`. Packages stay in their source repositories; this repository never authors plugin content
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
`engineering`, `docs`, `cpp`, `gpp`, `msvc`, `win32`, `dotnet`, `efcore`, `react`, `nvim`, `rust`,
`tauri`, `rust-sqlx`, `seaorm`, `python`, `github-actions`, `azure`, `learning`, and
`template` and its sibling `skill` authoring package, the explicitly adopted `personal` and `work` [profiles](#plugin-kinds), `teams` for Teams messages in any repo, and the `company` organization. Select `cpp` plus one toolchain (`gpp` or `msvc`) and
optionally `win32` for C++ work. For generic sustained tasks, select the `base`, `agent-store`,
`agent`, `cli`, and `workflow` closure. CLI supplies exact-target close utilities;
Agent supplies session-aware target resolution and coordination.
For software work, select `engineering` plus the common closure.
Each plugin entry declares its actual prerequisites. Runtime packages remain reusable without Engineering;
stack and product profiles retain their declared Engineering dependencies. Claude installs each entry's `requires` as `dependencies`; Codex
does not resolve dependencies, so a selection still lists the closure.

For projects Tommy explicitly identifies as personal, select `personal` and its actual requirement closure:
`engineering`, `agent`, `cli`, `base`, `agent-store`, `workflow`, `docs`, and `github`. Then run `personal:use` to generate and
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

Each roster entry declares `revision`, the full lowercase 40-character commit ID of a
published producer payload. Generation writes it as the native `source.sha` and rejects unpinned entries.
Marketplace owns these producer pins. Publish and verify the producer payload
before activating its revision here.

Agent and Core each require one revision across every entry from that producer when pinned. Mixing
pinned and unpinned entries, or two revisions of one producer, is rejected. Update the Agent/Core pair
in one roster change after both payloads are published. Other producers retain independent entry policy.

Renovate groups Core, Agent and CLI pins together for runtime delivery. Updates from other producers
use a separate group, so their failing checks leave runtime updates able to publish independently.

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

Personal owns GitHub work items; the `company` organization owns Azure Boards work items and employer type policy.
Each supplies `work-item`, `create-work-item` and `address-work-item` under its qualified namespace.
Agent owns the shared agent execution/session registry; Core owns Engineering workflows. Work supplies employer-neutral
communication tools. Select the intended profile explicitly; installing Core does not select a tracker.

Skill authoring uses `skill:new` and `skill:update`, both published from `tj-agents/template`.
Template depends on Skill so selected plugin publishers load the current native-creator authoring workflow.

## Plugin kinds

`plugins.json` is the single authored source for what each plugin is. Every entry declares exactly one
`kind`; generation rejects an entry without one, any other value and any other role field.

| Kind | What it is | A repository selects | Names an organization |
| --- | --- | --- | --- |
| `shared` | A capability any repository may use (`base`, `python`, `github`, ...) | Any number | Never |
| `profile` | How the repository is worked on: `personal` or `work` | Exactly one | Never |
| `organization` | One organization's layer on one profile (`company` on `work`) | At most one, with its profile | Yes |

An `organization` entry also declares `"extends": "<profile>"` naming one `profile` entry and lists that
profile in `requires`, so selecting the organization brings its profile. No other kind uses `extends`.
Shared plugins and profiles are generic and name no organization. An organization's repository is private.

Generation does not copy `kind` into the host marketplaces. It is consumed by:

| Consumer | Uses `kind` to |
| --- | --- |
| `generate.py` | Validate every entry and the organization's `extends` and `requires` |
| Agent's offline lock, `marketplace_plugins.lock.json` | Carry the roster to Agent; refresh it with Agent's `update_marketplace_plugins.py` after a roster change merges |
| Agent's selector (`agent:plugins`, adoption, `tj install`) | Refuse more than one profile after `requires` expansion, and refuse `personal` on a repository an installed employer declaration matches |

To add a plugin, publish its producer payload, then add one entry of the right kind and regenerate:

```json
{ "name": "example-tool", "repository": "example-tool", "revision": "<40-character commit>", "requires": ["base"], "kind": "shared" },
{ "name": "example-profile", "repository": "example-profile", "revision": "<40-character commit>", "requires": ["engineering"], "kind": "profile" },
{ "name": "example-employer", "repository": "example-employer", "revision": "<40-character commit>", "requires": ["work"], "kind": "organization", "extends": "work" }
```
