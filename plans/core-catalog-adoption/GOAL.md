# Aggregate discovery and exact core adoption

Status: authorized bounded side workstream; awaiting native Claude pickup.

## Authority and ownership

Tommy approved the complete repository layout and TJ Agents adoption goal on 2026-10-07. The originating
Codex session 01a11794-26f3-7fb2-accb-0df87faa5180 retains the whole goal at
C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepositoryOwnedLayout/plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md.
This native Claude side owner owns marketplace slice C only: design, implementation, tests, focused PR,
and normal merge delivery after this repository's checks. The parent retains core and fleet adoption.
Do not close or rewrite the parent goal, adopt its checkout, or launch a duplicate successor.

Checkout: C:/Users/TommySeery/source/repos/tj-agents/marketplace/.worktrees/Feature-CoreCatalogAdoption
Branch: Feature/CoreCatalogAdoption
Fresh base: origin/main 62b527449045991582ebd44ac9b4e3005f2c2b8c, fetched 2026-10-07.
Native launch lane: L1 because the first phase must settle aggregate/release mapping. Apply L4 to bounded
implementation after readiness; retain this side owner through its authorized delivery.

## Problem and required outcome

Use tj-agents/marketplace for discovery while each producer remains owner of exact release records,
package digests and harness manifests. The aggregate currently points entries at moving main; core
consumer locks use immutable producer revisions. Adding discovery does not install or activate core
closure. Resolve this interface explicitly and implement only the marketplace-owned changes necessary
for reliable new/existing adoption with no duplicate skills/hooks and no silent weakening of immutable
pins. Base, engineering and machine retain meaningful package identities. Do not create a marketplace
called core, vendor core sources, or transfer other producers' release ownership into core.

## Source evidence and boundaries

Read AGENTS.md and README.md first. catalog.json is the only authored roster; generate.py produces
both host marketplace manifests. generate.py currently hardcodes main and Codex AVAILABLE. README
requires explicit selection and disable/uninstall of the legacy identity before enabling a replacement.
Read current core release/catalog/bootstrap and harness schemas as dependency evidence before deciding
whether this repository needs an alias bridge, pinned discovery data, documentation, or another mechanism.
Do not infer support from adding a marketplace or from generated files alone.

Marketplace primary Feature/WorkPlugin at ee868f1966b6e53b4975d6ff88e1378578c78320 owns an unrelated
private-work roster addition with review in progress. Preserve that branch and reconcile it if it lands.
No exact C-slice native owner was observed. You are not alone: never revert others' edits.

Kit is a separate future PR/checkout, not part of this writer lease. Its primary is
C:/Users/TommySeery/source/repos/tj-agents/kit at ac260634c671e5c5ff402f128be794079b9dcf50.
Open kit PR #4 Refactor/KitTaxonomyVocabulary owns overlapping generator/template/checker/test changes.
Read-only inspection may resolve the intended consumption contract, but do not edit kit or duplicate
that owner. Return a concrete kit handoff dependency to the parent for a separate native Claude slice.

Core allocator, runtime bytecode repair, plan-policy and closeout paths have independent owners.
Consumer rollout waits for exact released producers, core allocator plus guidance, C acceptance and
both hosts. No normal-profile plugin installation, credential copy, consumer changes, or old-checkout
retirement belongs to this side workstream. The existing credential-copy gate remains held. A prior
automatic review rejected changing consumer immutable refs to main because that would execute
unreviewed code; preserve pins and do not relabel moving main as equivalent trust.

## Acceptance and validation

- Record and review the concrete aggregate-to-producer identity/revision mapping and failure behavior.
- Keep installed legacy identities usable through their published compatibility windows.
- Tests cover relevant clean and legacy selections, exact release ownership, missing dependencies,
  and duplicate activation prevention; neither catalog registration nor a listing proves active hooks.
- Run python -B generate.py --check, python -B -m unittest -q, and claude plugin validate .;
  run generation after authored changes and follow repository CI on the exact PR head.
- Use isolated host state only when it can be provisioned without credential copying or normal-profile
  changes. Record unavailable native acceptance as a specific unresolved gate, not a passed test.
- Keep PR scope measured and coherent, follow required review and delivery, and return PR/commit/check
  evidence plus exact remaining kit/core/host dependencies in plans/core-catalog-adoption/RESULT.md.

## Next Steps

Scope: this bounded marketplace slice through its authorized review and merge; parent owns the whole goal.
Current slice: establish native pickup, then design the aggregate/release/closure interface from source evidence.
Remaining scope: marketplace implementation and validation, native acceptance where available, focused delivery,
and a concrete kit consumption handoff; fleet adoption stays with the parent.
Done when: marketplace changes and required checks are delivered, or a genuine dependency gate is recorded
with its resolver and observable resume condition while independent authorized preparation is complete.

1. Record actual harness/session identity, branch/head, timestamp and first observed action in
   .agents/continuation/catalog-pickup.json. Read this goal and the parent's approved C boundaries.
2. Load plan-execution, lanes and applicable repository/engineering standards. Resolve the design,
   examples and dependencies here, obtain readiness review, then assign bounded L4 implementation.
3. Continue through focused tests/review/PR/CI/normal merge using existing authorization. Do not ask
   routine continuation permission or treat planning, generation or an open PR as completion.
4. Checkpoint here and write RESULT.md with observed evidence. Keep this owner if a delayed gate remains;
   do not silently abandon or transfer the parent goal.
