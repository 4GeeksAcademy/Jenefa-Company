---
name: sync-memory-bank
description: >-
  Updates HealthCore memory-bank progress after completed work. Use when a
  feature, fix, or milestone task is finished; before a commit that requires
  progress documentation; or when the user asks to sync or update the memory
  bank.
---

# Sync Memory Bank

## Objective

Update `memory-bank/progress.md` so it accurately reflects the repository's current development state after a completed unit of work. Do not invent progress that is not evidenced by the change set.

## Inputs

| Input | Required | Description |
| ----- | -------- | ----------- |
| `change_summary` | Yes | Short description of what was completed (feature, fix, docs, infra). |
| `touched_paths` | Yes | List of files or directories changed in this unit of work. |
| `status` | Yes | One of: `completed`, `in-progress`, `blocked`. |
| `next_steps` | No | Explicit follow-ups if work is incomplete or blocked. |
| `git_diff` | No | Staged/unstaged diff; if omitted, gather via `git status` and `git diff`. |

## Workflow

1. Read `memory-bank/progress.md` (and skim `projectbrief.md` / `techContext.md` only if needed for naming consistency).
2. Confirm inputs. If `touched_paths` or `change_summary` is missing, gather them from git before editing.
3. Edit **only** `memory-bank/progress.md`:
   - Move finished items under **Current State of Development** (or a dated "Completed" subsection).
   - Keep unfinished roadmap items under **Planned Next Steps**.
   - Record blockers and concrete next actions when `status` is `in-progress` or `blocked`.
4. Do not modify `/infra/`, `/data/raw/`, `/internal/`, or `.env.production`.
5. Return the verification checklist below with each criterion marked pass/fail.

## Output

- An updated `memory-bank/progress.md`
- A short chat summary: what changed, what remains open, and the checklist result

## Acceptance Criteria

All criteria must pass. If any fail, fix the file and re-check before declaring the skill complete.

| # | Criterion | How to verify |
| - | --------- | ------------- |
| 1 | Only `memory-bank/progress.md` was modified by this skill | `git status` / `git diff --name-only` shows no unintended paths from this skill |
| 2 | `change_summary` appears in the updated progress file (same meaning, not necessarily verbatim) | Search `memory-bank/progress.md` for the completed work |
| 3 | Every path in `touched_paths` is reflected (grouped by area is fine: e.g. `uis/`, `services/`) | Cross-check the progress notes against the path list |
| 4 | `status` is represented accurately (`completed` / `in-progress` / `blocked`) | Status language in the file matches the input |
| 5 | No real PHI/PII, secrets, or production credentials were added | Manual scan of the diff for patient names, MRNs, API keys, tokens |
| 6 | Planned roadmap items that were not in this change set remain present | Diff does not delete unrelated Planned Next Steps content |

## Example

**Inputs**

- `change_summary`: Added `.agents/rules/phi-data-residency.md` always-active rule
- `touched_paths`: `.agents/rules/phi-data-residency.md`
- `status`: `completed`

**Expected progress note (excerpt)**

```markdown
### Agent tooling
- Added always-active PHI & data-residency rule under `.agents/rules/`.
```
