# TJ Agents marketplace

One install and discovery catalog for the current plugins in `tj-agents/core`, `cpp`,
`dotnet`, `react`, `nvim`, `rust`, and `kit`. The packages remain in their source repositories. Adding another
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
`win32`, `dotnet`, `react`, `nvim`, `rust`, and `kit`. Select `cpp` plus one toolchain (`gpp` or `msvc`) and
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

Each roster entry pins its plugin to the producer's latest published release; a
`revision: main` entry is an explicit, declared exception for a producer with no
published release yet, not a default. A producer that publishes tags but no release
record pins its published tag without a `release` id. Serving a new version means the
producer publishes a release and this roster is then edited to bump the pin — an
authored, reviewed change, never an automatic follow of `main`.

Exact project adoption never resolves through this aggregate. It is owned entirely by
producer release records plus a project's own capability locks
(`bootstrap-capabilities` / `repo_config`), which pin producer marketplaces such as
`base-agents` at immutable revisions directly from the selected release; no producer
release record names `tj-agents`, so a harness requirement naming it fails closed.

Adding this marketplace installs nothing on either host. Migrating an installed
legacy identity (`base-agents`, `cpp-agents`, `dotagents`, `react-agents`) requires
disabling or uninstalling it before enabling the `@tj-agents` copy. Project-scope
locked settings that enable a producer identity do **not** disable a user-scope
`@tj-agents` install of the same plugin — the user removes that explicitly.

Neither registering this catalog nor listing its plugins proves any hooks are
active; verifying that remains a separate, native host acceptance step.
