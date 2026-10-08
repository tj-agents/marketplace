# Aggregate discovery and exact release adoption — design

Status: readiness-reviewed 2026-10-07. Two independent read-only lenses (evidence lens, boundary
lens) each returned findings; all seven (1 blocking, 3 should-fix, 3 notes) are reconciled into this
revision: lock-mechanism precision, cpp/dotnet/react record provenance (core catalog at v2.1.15),
rollback-on-update consequence recorded, WorkPlugin reconciliation recorded, validation-scope and
`main`-grammar wording tightened, kit row vs kit-scaffold contract disambiguated. Ready for L4
implementation.
Owner: marketplace slice C (plans/core-catalog-adoption/GOAL.md). Parent owns core/fleet adoption.

## Interface resolution

Two adoption paths exist and stay separate:

1. **Exact project adoption is producer-owned and never flows through this aggregate.**
   `repo_config.py` (core, bootstrap-capabilities) derives host marketplace declarations exclusively
   from the selected releases' `marketplace` and `owner_repository` fields and pins them at the
   release's immutable `revision` (`declarations()` validates `source ==
   https://github.com/{owner_repository}`; `requires.marketplaces[].repository` must equal the
   selected release's owner). A lock selection carries no marketplace field at all
   (`validate_lock()` accepts only `id`/`release`/`commit`/`required_skills`/`path_scopes`/
   `exceptions`); marketplace ids enter generated settings only through the selected releases and
   the `requires.marketplaces` declarations in producer release records or a repository's
   `.agents/repository-harness.json` overlay, and an id there with no selected release fails closed
   with `Required marketplace disagrees with selected release`. No producer release record names
   `tj-agents`. `bootstrap_capabilities.py apply` clones producer repos at locked commits
   and registers those local marketplaces. Nothing in core references `tj-agents/marketplace`.
   This repository therefore needs **no alias bridge**: the aggregate is structurally outside the
   exact-adoption path, and that is the recorded failure behavior, not a gap.

2. **The aggregate is the discovery and explicit host-install identity, and it must stop serving
   moving `main` for producers that publish releases.** `generate.py` currently hardcodes
   `ref: main`, so a host install (`/plugin install base@tj-agents`) executes whatever main holds
   that day — the same unreviewed-code concern that core's prior review rejected for consumer refs.
   The marketplace-owned mechanism is **pinned discovery data**: the authored roster records, per
   plugin, the producer's latest *published* release identity and revision, and the generator emits
   that revision as the entry's `ref`. Serving `main` becomes a visible per-entry declaration
   reserved for producers with no published release, not a generator default.

## Recorded aggregate-to-producer mapping (verified 2026-10-07)

| Aggregate entries | Repository | Release record | Revision | Evidence |
| --- | --- | --- | --- | --- |
| base, engineering, machine | tj-agents/core | base-agents@2.1.15 | v2.1.15 | tag on remote (peeled 61b5b1e); record in core catalog at v2.1.15 |
| cpp, gpp, msvc, win32 | tj-agents/cpp | cpp-agents@0.3.2 | v0.3.2 | tag on remote (2047acf); record in core catalog at v2.1.15 |
| dotnet | tj-agents/dotnet | dotagents@1.1.1 | v1.1.1 | tag on remote (7ec0ffa); record in core catalog at v2.1.15 |
| react | tj-agents/react | react-agents@1.0.1 | v1.0.1 | tag on remote (4ea8acb); record in core catalog at v2.1.15 |
| nvim | tj-agents/nvim | none | main (declared) | no tags on remote; no `.agents/catalog` in repo |
| rust | tj-agents/rust | none | main (declared) | no tags on remote; no `.agents/catalog` in repo |
| kit | tj-agents/kit | none | v1.2.0 | tag on remote (peeled ac26063 == current main head); no release record |

Producer-side facts the roster depends on:

- Core's committed catalog at main records `base-agents@2.1.16` revision `v2.1.16`, but that tag is
  **not published** on the remote (tags stop at v2.1.15). The aggregate pins the latest published
  release; the 2.1.16 flip is a recorded core dependency, not something this repo can anticipate.
- cpp/dotnet/react release records were dropped from core's catalog at 2.1.16 (core's bundled
  catalog now covers only core packages) and do not yet exist in the producers' own repositories.
  Their published tags remain valid pin targets; in-repo record adoption is a producer dependency.
  **Provenance of their release ids and dependency data:** no live record exists today; the
  authoritative historical artifact is core's catalog as committed at tag v2.1.15, retrieved with
  `git show v2.1.15:.agents/catalog/catalog.json` in a core clone (verified 2026-10-07: it records
  cpp-agents@0.3.2, dotagents@1.1.1, react-agents@1.0.1 and the `dependencies.required` values
  used below).
- cpp main is 13 commits past v0.3.2, so new aggregate installs of cpp serve the older published
  release until cpp publishes again. That is the intended semantics: unpublished main is not served.
- **Rollback on existing installs elsewhere:** any host that already installed an `@tj-agents`
  plugin and tracks the marketplace will be moved from the main it installed to the pinned tag on
  its next update — for cpp today that is a 13-commit rollback. This is a deliberate, reviewed
  migration consequence, not a side effect: the aggregate stops serving unpublished code, and the
  forward path is the producer publishing a newer release. The PR description must call this out
  explicitly, and the README states the published-releases-only semantics.
- Local machine check: only `nvim` and `rust` are installed from the `tj-agents` aggregate, both of
  which stay at main, so this change regresses no existing install on this machine.

## catalog.json schema change

Each plugin entry gains:

- `revision` (required): `main`, `v<major>.<minor>.<patch>`, or a 40-hex commit SHA. The tag/SHA
  forms mirror core's catalog revision grammar; `main` is this aggregate's own addition for
  producers with no published release — core's grammar has no moving-ref form and rejects branches.
- `release` (optional): the owning producer release id, `<marketplace>@<version>` (core's release id
  grammar). Allowed only with an immutable revision; when the revision is a `v` tag its version must
  equal the release id's version. Documents which producer record owns the pinned bytes and which
  legacy installed identity the plugin migrates from.
- `requires` (optional): aggregate-local plugin names this plugin needs, taken from the producer
  record's `dependencies.required`. Every name must be another roster entry, so a roster edit cannot
  strand a dependent plugin behind a missing dependency.

Validation added to `generate.py` `build()`:

- `revision` matches the grammar above; `release` matches its grammar; `release` with `revision:
  main` is an error; `v`-tag/release version mismatch is an error.
- All entries sharing a `repository` must share the same `release`/`revision` pair (a producer
  release is atomic).
- Every `requires` name resolves to a roster entry (`engineering`/`machine` → `base`;
  `gpp`/`msvc`/`win32` → `cpp`).
- Existing checks stay: identity fixed to `tj-agents`, name grammar, duplicates, non-empty roster,
  instruction pairs.
- Scope of this validation: it catches only internally inconsistent roster data. A syntactically
  valid but factually wrong pin (a typo'd SHA, a release id the producer never published) is not
  detected — the generator has no network or producer-catalog access, and this design adds none.
  Roster authoring remains a trusted, reviewed act; factual wrongness surfaces at review or at
  host install time.

Generator output change: the per-entry source `ref` becomes the entry's `revision` (was hardcoded
`main`). No other manifest shape changes; Codex entries keep `installation: AVAILABLE` and Claude
entries keep no installation policy, so adding the marketplace still installs and activates nothing.

## Initial roster data

Per the mapping table: core trio at `base-agents@2.1.15`/`v2.1.15` with `engineering` and `machine`
requiring `base`; cpp four at `cpp-agents@0.3.2`/`v0.3.2` with `gpp`/`msvc`/`win32` requiring
`cpp`; `dotnet` at `dotagents@1.1.1`/`v1.1.1`; `react` at `react-agents@1.0.1`/`v1.0.1`; `kit` at
`v1.2.0` with no release record; `nvim` and `rust` at declared `main`.

## README adoption contract

Rewrite the install/update guidance to state:

- The roster pins each plugin to its producer's latest published release; `main` entries are
  explicitly unreleased previews. Serving a new version means the producer publishes, then this
  roster bumps the pin — an authored, reviewed change.
- Exact project adoption is owned by producer release records plus project capability locks
  (bootstrap-capabilities / repo_config); generated project settings pin producer marketplaces such
  as `base-agents` at immutable revisions and never resolve through this aggregate; a selection
  naming `tj-agents` fails closed.
- Duplicate-hook prevention: adding this marketplace installs nothing on either host; migrating an
  installed legacy identity (`base-agents`, `cpp-agents`, `dotagents`, `react-agents`) requires
  disabling or uninstalling it before enabling the `@tj-agents` copy; project-scope locked settings
  enable producer identities and do **not** disable a user-scope `@tj-agents` install of the same
  plugin — the user removes that explicitly.
- Neither catalog registration nor a plugin listing proves active hooks; native host verification
  remains a separate acceptance step.

## Tests (extend test_generate.py)

- Validation: missing/invalid `revision`; `release` with `main`; tag/release version mismatch; mixed
  revisions within one repository; unknown `requires` name — each raises.
- Output: a pinned entry emits its revision as `ref`; a `main` entry emits `main`; every Codex entry
  is `AVAILABLE`; Claude entries carry no installation policy; marketplace identity stays
  `tj-agents`; both host manifests are emitted byte-stable.
- Real roster: `build()` over the repository succeeds; every `requires` closure holds; entries from
  one repository share one release; core entries are pinned.
- Existing instruction-pair tests stay.

Local validation commands (unchanged CI): `python -B generate.py`, `python -B generate.py --check`,
`python -B -m unittest -q`, `claude plugin validate .`.

## Out of scope and recorded dependencies

- No marketplace named `core`, no vendored sources, no release records authored here, no consumer
  lock/profile changes, no edits to core/kit/producer repos.
- Feature/WorkPlugin (ee868f1, review in progress) adds a `work` roster entry with no `revision`
  field. Under this schema that entry fails validation when the branch reconciles; whichever change
  lands second adds one line (`"revision": "main"` under the no-published-release exception, since
  tj-agents/work publishes no releases). Preserve that branch; do not edit it from here.
- Core: publish the v2.1.16 tag its committed record names; then the roster bumps core pins.
- cpp/dotnet/react: adopt their release records in-repo (dropped from core's catalog at 2.1.16);
  cpp additionally publishes a release covering its 13 unpublished commits.
- nvim/rust: publish first releases so their entries can pin.
- Kit (separate PR/owner): new-plugin scaffolds declare core closure — scaffold
  `.agents/capabilities.lock.json` selecting base/engineering/machine plus the new repo's plugins,
  commit the selected owners' release records as `.agents/catalog/catalog.json`, generate host
  settings via repo_config, publish release records/tags, and have each newly scaffolded repository
  register its own roster entry here (`name`, `repository`, `release`, `revision`, `requires`).
  This is distinct from the existing `kit` roster row, which this PR pins to v1.2.0 itself.
- Native both-host install acceptance: requires the merged aggregate on GitHub and host credentials;
  the credential-copy hold stands, so this is recorded as an unresolved gate, not a passed test.

## Review and delivery

Readiness review of this design precedes implementation. Implementation is one bounded L4 slice:
`catalog.json`, `generate.py`, `test_generate.py`, `README.md`, regenerated host manifests. Then
focused checks, code review, PR, CI on the exact head, normal merge; evidence lands in RESULT.md.
