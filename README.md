# Minecraft Bedrock Family

[Français](README.fr.md) · [Install](docs/en/installation.md) · [Use](docs/en/guide.md) · [Cheat sheet](docs/en/cheat-sheet.md)

A shared Minecraft world, with a finishing time and automatic backups.

- The world is stored on a Mac with an Apple Silicon chip.
- Players use Minecraft Bedrock on iOS or Windows 10/11.
- All devices are connected to the same local network.

## Before you start

Cheats are enabled too. This disables world achievements; turning cheats off later does not automatically restore them. Back up an existing world before changing its rules.

## Get started

Install Docker Desktop, Python and uv on the Mac, then follow the [installation tutorial](docs/en/installation.md). It walks through each step without requiring Git or Docker knowledge.

Already set up the Mac? Install the CLI, create a server folder and start a game:

```sh
uv venv && uv pip install --python ./.venv/bin/python .
bedrock-family init ~/MinecraftFamily
cd ~/MinecraftFamily
bedrock-family setup
bedrock-family session start
```

The server starts. Before the finishing time, players receive reminders. The server then stops, backs up the world and stays off.

## Choose a finishing time

```sh
bedrock-family session default set 20:30
```

This saves the usual time for future games. Without a custom setting, the finishing time is 19:00.

For a different time today only:

```sh
bedrock-family session start --until 21:00
```

Reminders arrive 15 minutes, 5 minutes, 1 minute and 30 seconds before the end. A time already past today is refused.

## Everyday commands

| I want to… | I type… |
|---|---|
| Start with a finishing time | `bedrock-family session start` |
| Stop now and back up | `bedrock-family session stop` |
| Check the planned time | `bedrock-family session status` |
| Cancel the timer without stopping | `bedrock-family session cancel` |
| Make a backup | `bedrock-family backup create` |
| Open the backups | `bedrock-family open backups` |
| Show help | `bedrock-family --help` |

## Before the first game

The family settings are ready: keep inventory after death, easy difficulty, one sleeping player to skip the night and survival mode.

Keep the Mac and Docker running during play. After restarting the Mac, check and schedule the finishing time again. Never delete `data`: it contains the world.

`make test`, `make lint`, `make verify` and `make docs` are for project contributors only.

## More help

- [Install and connect the players](docs/en/installation.md)
- [Add players, change rules or restore a backup](docs/en/guide.md)
- [Fix a problem](docs/en/troubleshooting.md)
- [Print the guides](docs/en/printing.md)
- [All commands](docs/en/commands.txt)

This server is for the local network. Do not forward Internet ports on your router. Minecraft and the tools keep their own terms. This is an independent project, not affiliated with Mojang.
