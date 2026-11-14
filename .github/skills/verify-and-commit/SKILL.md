---
name: verify-and-commit
description: Verify the requested changes and create a scoped Conventional Commit when the user explicitly asks to commit.
---

# Verify and commit project changes

Use this workflow only when the user explicitly asks to create a commit. Do
not push, merge, amend, or rewrite history unless the user explicitly asks for
that operation too.

1. Inspect the current branch and working tree. Review staged, unstaged, and
   untracked changes so pre-existing work is not accidentally included or
   discarded.
2. Identify the files that belong to the requested change. Preserve unrelated
   changes, and stage only the intended files.
3. Run relevant validation before committing. For Python changes, run
   `python3 -m ruff check bedrock_family scripts tests/test_manage.py`; for
   behavior or contribution-workflow changes, run `make verify`. Run targeted
   tests as needed and report any check that could not be completed.
4. Review the staged patch with `git diff --cached --check` and
   `git diff --cached`. Confirm it contains only the requested changes and no
   secrets, local configuration, worlds, backups, or logs.
5. Create an English Conventional Commit with a concise imperative summary,
   using `type(scope): summary` when a scope is useful. Do not amend an existing
   commit unless the user explicitly asks to update it.
6. Report the new commit hash and subject, validation results, and remaining
   working-tree changes.
