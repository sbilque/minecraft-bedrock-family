# Repository guide

## Project overview

Minecraft Bedrock Family is a Python CLI for setting up and managing a
family-friendly Bedrock server. The server runs through Docker Compose; user
worlds, settings, backups, and other runtime data belong to the server
directory, not the installed Python package.

- `bedrock_family/cli.py` defines CLI commands and dispatches operations.
- `bedrock_family/manage.py` contains server, world, session, settings, and
  backup operations.
- `bedrock_family/i18n.py` loads the JSON catalogs in
  `bedrock_family/locales/`. Keep catalog keys in English `snake_case` and
  translate values.
- `bedrock_family/templates/` contains files used to initialize a server
  directory.
- `tests/test_manage.py` exercises behavior with mocked Docker commands.
- `docs/en/` and `docs/fr/` contain the user guides in both languages.
- `Makefile` is for contributor tasks only: tests, lint, verification, and
  optional documentation PDFs. Server operations use the `bedrock-family` CLI.

## Change guidelines

- Preserve existing worlds, backups, settings, allowlists, and unrelated
  working-tree changes. Do not overwrite or delete user data as part of setup,
  migration, or testing.
- Do not contact a real Docker server, game server, network, or player device
  for tests unless explicitly requested. Clearly distinguish mocked/offline
  validation from real environment testing.
- Keep runtime dependencies within the Python standard library unless a
  dependency change is required and requested.
- Support Python 3.9 and newer. Follow the Ruff configuration in
  `pyproject.toml`; Python comments and docstrings should be in English.
- Keep user-facing documentation in English and French in sync. Keep locale
  catalog keys in English `snake_case`; localize only their values.
- Preserve existing CLI behavior and compatibility unless a behavior change is
  requested. For broad or behaviorally ambiguous work, establish the scope and
  acceptance criteria before implementation.

## Validation

- For Python changes, run
  `python3 -m ruff check bedrock_family scripts tests/test_manage.py`.
- For behavior, packaging, or contribution-workflow changes, run `make verify`
  and any additional targeted checks needed by the change.
- Report the exact checks run and whether they passed. Do not claim real server
  or device validation when only mocked tests were run.

## Git workflow

- Inspect the working tree before changing or staging files. Stage only files
  belonging to the requested work; preserve unrelated staged and unstaged
  changes.
- Write commit subjects in English using Conventional Commits, for example
  `fix(cli): handle missing project settings`.
- Do not commit, amend, merge, push, or rewrite published history unless the
  user explicitly requests that operation. Never force-push unless explicitly
  requested.
