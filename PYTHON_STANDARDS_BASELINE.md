# Python standards baseline

Existing violations at `ff6f2167690728f919d0629e0daad577bb24444e` are baselined by exact authored file and rule. New files receive all enabled checks. Remove an exception when repairing its source. The tool configuration owns enforcement; this document records the rollout evidence and rationale.

## Ruff

Reason: preserve existing implementations during the standards rollout. Each row records the existing count and a representative required repair. No wildcard path or whole-rule ignores were added.

| File | Rule | Existing count | Required repair |
| --- | --- | ---: | --- |
| `generate.py` | `E501` | 8 | Line too long (89 > 88) |
| `generate.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `test_generate.py` | `E501` | 17 | Line too long (99 > 88) |
| `test_generate.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `test_generate.py` | `PT009` | 18 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `test_generate.py` | `TID251` | 2 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |

## Ruff formatter

Exact existing files requiring formatting are excluded from the formatter during this rollout. Regenerate payloads after formatting authored source and then remove its exception. New files are checked.

- `generate.py`
- `test_generate.py`
- `test_pins.py`

## Mypy

Existing typing debt is baselined by exact module and diagnostic code, with its source file and count below. Add the missing annotations or fix the indicated type mismatch, then remove the corresponding module/code override. No wildcard modules or whole-module ignore was added.

| File | Module | Rule | Existing count | Required repair |
| --- | --- | --- | ---: | --- |
| `test_generate.py` | `test_generate` | `no-untyped-call` | 9 | Call to untyped function "write_plugins_file" in typed context |
| `test_generate.py` | `test_generate` | `no-untyped-def` | 21 | Function is missing a return type annotation |

## Custom checker

Reason: preserve exact pre-existing custom-checker findings during the standards rollout. Each entry maps to one authored path and rule; repair the stated design issue and remove its exception. No generated or vendored path is included.

No pre-existing custom-checker findings were recorded.
