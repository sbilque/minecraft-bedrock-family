# What do the tests check?

[Français](../fr/testing.md)

```sh
make verify
```

This checks code and commands, then runs tests with fake Docker exchanges. It does not start Minecraft, download anything or use a real Docker engine.

Tests cover finishing times, game rules, allowed players, backups, restoration and errors.

Passing tests do not replace a real trial game. After installation or an update, start the server on the Mac and check that an iOS or Windows device can join with a compatible Minecraft Bedrock version.

For contributors: make test runs the tests; make lint checks code and commands; make verify does both.

GitHub reruns these checks after a push or pull request. Linux jobs check the program, not Linux server support. The macOS job also checks that its runner uses Apple Silicon. Inspect the Actions results: a workflow file alone does not mean a successful run.
