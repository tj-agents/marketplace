# Optional work-items discovery

Authorized by Tommy on 16 October 2026 as part of docs/plans/problem-management/PLAN.md.
Owner: codex:01a1415f-6448-7123-8b17-c7fb67aee637. Branch Feature/WorkItemsPlugin from 4962303.
PR: not opened. This checkout leaves the existing WorkPlugin and CoreCatalogAdoption owners untouched.

Add the separate work-items producer to authored catalog.json, generate both host discovery catalogs and
document explicit project selection through work-items-agents. Keep Core's name, existing identities,
producer ownership and employer policy. Registration never installs or adopts the tracker. The package
must be published before this catalog is delivered; replace the preparation-only main exception with
its actual immutable release/tag and peeled commit. Do not invent a release record.

Validation: generator freshness, existing unit tests and native Claude plugin validation, then bounded
independent review and CI. Installed-host acceptance belongs to the producer/consumer slices. Core's
existing injector supports qualified foreign plugins, so no backend-specific global roster is required.

Producer v0.1.0 is published at 7c4dcd2147a46005020ee4f2b68db563d71a52a5; annotated tag object 1440d096c0fb601200ab95da7e348aab1b3befb3 and peeled remote commit verified. Its causal main CI 38836538305 passed. The producer has a GitHub Release but no Core-format release catalog identity; retain the actual tag and commit without inventing that identity. Correct stale removed-bootstrap prose to the current project plugin-lock behavior. Core producer compatibility slice is in independent review before native acceptance/rollout.

Independent native and workflow reviews both identified the missing explicit Base installation instruction. README now states that native discovery does not install catalog dependencies, selects the complete Core triplet for fresh project locks, and preserves existing producer identities. Generator, unit and native validation remain required before incremental review.
