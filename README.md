# TJ Agents marketplace

One shared discovery catalog for the current plugins in `tj-agents/core`, `cpp`,
`dotnet`, `react`, `nvim`, `rust`, `python`, `github-actions`, `azure`, and `template`.
Packages stay in their source repositories. Adding another
repository requires one entry in `catalog.json`; `generate.py` produces the matching
Claude and Codex catalogs. Core launch refresh updates selected plugin content from these source repositories.

Add the marketplace and select plugins explicitly:

```text
Claude: /plugin marketplace add tj-agents/marketplace
Claude: /plugin install cpp@tj-agents
Codex:  codex plugin marketplace add tj-agents/marketplace
Codex:  codex plugin add cpp@tj-agents
```

Available canonical plugins are `base`, `engineering`, `machine`, `cpp`, `gpp`, `msvc`,
`win32`, `dotnet`, `efcore`, `react`, `nvim`, `rust`, `python`, `github-actions`, `azure`, and
`template`, the explicitly adopted `personal` profile, and the employer-scoped `work` and `infonetica` profiles. Select `cpp` plus one toolchain (`gpp` or `msvc`) and
optionally `win32` for C++ work. Select `base`, `engineering`, and `machine` together
for the common agent workflow.

Select `personal`, `base` and `machine` for projects Tommy explicitly identifies as personal, then run
`personal:setup-repo` to generate and check mandatory native instructions for Claude and Codex. Selection alone
does not establish that the policy loaded. Employer projects remain outside this profile. The policy and
adoption procedure are authored in [tj-agents/personal](https://github.com/tj-agents/personal).

Project declarations and installed registrations use the shared `@tj-agents` identities. Remove
superseded registrations in the same migration so duplicate skills and hooks do not load. Codex entries
in this marketplace are `AVAILABLE`, so adding the catalog does not automatically install copies.

Edit `catalog.json`, then run:

```text
python -B generate.py
python -B generate.py --check
claude plugin validate .
```

All catalog entries use the producer repository's current main branch. The catalog makes current publisher content
available to hosts. Core's launch refresh updates the plugin content consumed by a project from those main branches.

Project selection is explicit in the repository's `.agents/plugins.json`. Use `machine:plugin-selection` to select
the desired plugins. Refreshing the project brings selected content up to date; adding the catalog alone does not
select plugins, install them or activate hooks.

Adding this marketplace installs nothing on either host. When migrating an installed legacy identity, disable or
uninstall the old copy before enabling its `@tj-agents` copy. Do not enable both producer and aggregate identities
for the same plugin. Neither registering this catalog nor selecting plugins proves that hooks are active; verify
that separately with native host acceptance.

Personal owns GitHub work items; Infonetica owns Azure Boards work items and employer type policy.
Each profile supplies `work-item`, `create-work-item` and `address-work-item` under its qualified namespace.
Core owns the shared agent execution/session registry and Engineering workflows. Work supplies employer-neutral
communication tools. Select the intended profile explicitly; installing Core does not select a tracker.
