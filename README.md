# TJ Agents marketplace

One install and discovery catalog for the current plugins in `tj-agents/core`, `cpp`,
`dotnet`, and `react`. The packages remain in their source repositories. Adding another
repository requires one entry in `catalog.json`; `generate.py` produces the matching
Claude and Codex marketplace files. The `core` release catalog remains the owner of
exact package versions and project locks.

Add the marketplace and select plugins explicitly:

```text
Claude: /plugin marketplace add tj-agents/marketplace
Claude: /plugin install cpp@tj-agents
Codex:  codex plugin marketplace add tj-agents/marketplace
Codex:  codex plugin add cpp@tj-agents
```

Available canonical plugins are `base`, `engineering`, `machine`, `cpp`, `gpp`, `msvc`,
`win32`, `dotnet`, and `react`. Select `cpp` plus one toolchain (`gpp` or `msvc`) and
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

All plugin entries point to `main` in their source repository. Publish a source
package there before expecting this catalog to serve its new version.
