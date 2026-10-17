# TJ Agents marketplace

One shared discovery catalog for the current plugins in `tj-agents/core`, `cpp`,
`dotnet`, `react`, `nvim`, `rust`, `github-actions`, `azure`, and `template`.
Packages stay in their source repositories. Adding another
repository requires one entry in `catalog.json`; `generate.py` produces the matching
Core launch refresh updates selected plugin content from these source repositories.

Add the marketplace and select plugins explicitly:

```text
Claude: /plugin marketplace add tj-agents/marketplace
Claude: /plugin install cpp@tj-agents
Codex:  codex plugin marketplace add tj-agents/marketplace
Codex:  codex plugin add cpp@tj-agents
```

Available canonical plugins are `base`, `engineering`, `machine`, `cpp`, `gpp`, `msvc`,
`win32`, `dotnet`, `react`, `nvim`, `rust`, `github-actions`, `azure`, and
`template`, and optional `work-items`. Select `cpp` plus one toolchain (`gpp` or `msvc`) and
optionally `win32` for C++ work. Select `base`, `engineering`, and `machine` together
for the common agent workflow.

The existing `base-agents`, `cpp-agents`, `dotagents`, and `react-agents` marketplaces
remain available to installed consumers. When migrating, disable or uninstall an old
plugin before enabling its `@tj-agents` copy so duplicate skills and hooks do not load.
The legacy C++ compatibility packages remain only in `cpp-agents` through their
published compatibility window. Codex entries in this marketplace are `AVAILABLE`,
so adding the catalog does not automatically install second copies.

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

`work-items` is optional personal GitHub tracking tooling for features, tasks, bugs, mistakes and debt. Install `base` together
with `work-items`: the catalog validates this dependency, but native marketplace discovery does not install it automatically.
Explicitly select it only in the intended personal source project using `.agents/plugins.json` and `machine:plugin-selection`.
Adding the catalog or installing the utility does not change a repository's tracker. Employer repositories keep their
existing tracking policy. Enable one installed copy and avoid enabling both producer and aggregate identities for the
same plugin. Core record integration requires a Core revision containing the generic problem-provider protocol;
native host acceptance remains a separate check before personal rollout.
