# TJ Agents marketplace

One install and discovery catalog for the current plugins in `tj-agents/core`, `cpp`,
`dotnet`, `react`, `nvim`, `rust`, `github-actions`, `azure`, and `kit`, including
Kit's `template` package. The packages remain in their source repositories. Adding another
repository requires one entry in `catalog.json`; `generate.py` produces the matching
Claude and Codex marketplace files. Producer repositories own package versions; a consumer's plugin lock owns its marketplace pins and selected identities.

Add the marketplace and select plugins explicitly:

```text
Claude: /plugin marketplace add tj-agents/marketplace
Claude: /plugin install cpp@tj-agents
Codex:  codex plugin marketplace add tj-agents/marketplace
Codex:  codex plugin add cpp@tj-agents
```

Available canonical plugins are `base`, `engineering`, `machine`, `cpp`, `gpp`, `msvc`,
`win32`, `dotnet`, `react`, `nvim`, `rust`, `github-actions`, `azure`, `kit`, and
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

Each roster entry pins its plugin to the producer's latest published release; a
`revision: main` entry is an explicit, declared exception for a producer with no
published release yet, not a default. A producer that publishes tags but no release
record pins its published tag without a `release` id. Serving a new version means the
producer publishes a release and this roster is then edited to bump the pin — an
authored, reviewed change, never an automatic follow of `main`.

Project adoption uses Core's `machine:plugin-lock` and the consumer's `.agents/plugins.lock.json`,
with an immutable revision for each selected marketplace. Existing schema-3 locks select the aggregate
Core triplet by default. Producer identities such as `base-agents` and `work-items-agents` require an
injector that supports their explicit selection; the work-items rollout includes that generic Core
compatibility support. The removed `bootstrap-capabilities` interface is historical.

Adding this marketplace installs nothing on either host. Migrating an installed
legacy identity (`base-agents`, `cpp-agents`, `dotagents`, `react-agents`) requires
disabling or uninstalling it before enabling the `@tj-agents` copy. Project-scope
locked settings that enable a producer identity do **not** disable a user-scope
`@tj-agents` install of the same plugin — the user removes that explicitly.

Neither registering this catalog nor listing its plugins proves any hooks are
active; verifying that remains a separate, native host acceptance step.

Every tagged entry also carries the full `commit` its tag resolves to, emitted as the source's
`sha`, so a moved or re-created tag cannot change what a pin installs. Resolve it with
`git rev-parse <tag>^{commit}` (the peeled commit, not an annotated tag object). A `main` entry
has no `commit`. A repository's marketplace tag is the single pin a project lock selects.


`work-items` is optional personal GitHub tracking tooling for features, tasks, bugs, mistakes and debt.
Its producer identity is `work-items@work-items-agents`; project locks select that producer marketplace
at an immutable release revision. Commit explicit tracker adoption only in the intended source project.
Adding this catalog or installing the utility does not change a repository's tracker. Employer repositories
keep their existing tracking policy. Enable one installed copy; avoid enabling both producer and aggregate
identities for the same plugin. The work-items v0.1.0 release is pinned to its verified peeled commit. Its Core record integration
requires a Core revision containing the generic problem-provider protocol; native host acceptance
remains a separate check before personal rollout.
