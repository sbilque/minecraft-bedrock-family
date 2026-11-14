# Use the server

[Home](../../README.md) · [Français](../fr/guide.md) · [All commands](commands.txt)

In Terminal, start with `cd ~/minecraft-bedrock-family`. Enter one command at a time and wait for it to finish.

The Mac stores the world. Players use Minecraft Bedrock on iOS or Windows 10/11, on the same local network.

## Start and choose a finishing time

```sh
make session
```

The server starts using the usual finishing time. Save that time once with:

```sh
make session-default TIME=20:30
```

Without a custom setting, it is 19:00. For an exception today:

```sh
make session STOP_AT=21:00
```

Times use the Mac's clock. A time already past today is refused. Reminders arrive 15 min, 5 min, 1 min and 30 s before the end; already-past reminders are skipped. At the selected time, shutdown begins, then the world is backed up. The server stays off.

This is not a daily schedule: run `make session` for each game.

## List or choose a world

```sh
make worlds
```

This lists the available world folders and marks the default. To choose an existing world:

```sh
make world-default LEVEL="World Name"
```

This does not interrupt a game in progress. The choice takes effect on the next `make up` or `make apply`. A world must already exist in `data/worlds`.

## Check, change or cancel the end

| I want to… | I type… |
|---|---|
| Check the planned time | `make session-status` |
| Read shutdown messages | `make session-logs` |
| Cancel the timer without stopping | `make session-cancel` |
| Stop now and back up | `make session-stop` |
| See the usual time | `make session-default-show` |
| Reset the usual time to 19:00 | `make session-default-reset` |

Changing the usual time does not move an active timer. Cancel it, then schedule again to move it.

Keep the Mac awake and Docker open. You may close Terminal, not your macOS login session. After a restart, the server may come back without a finishing time: check and reschedule. A failure can prevent reminders or backups.

## Change the game rules

Warn players first: some changes restart the server.

| I want to… | I type… |
|---|---|
| Enable or disable cheats | `make cheats VALUE=on` or `VALUE=off` |
| Keep or lose inventory at death | `make keep-inventory VALUE=on` or `VALUE=off` |
| Choose difficulty | `make difficulty LEVEL=easy` |
| Let one sleeping player skip the night | `make sleep-one` |
| Require half the players in bed | `make sleep PERCENT=50` |
| Choose the default game mode | `make gamemode MODE=survival` |
| View saved choices | `make game-show` |
| Restore the five family defaults | `make game-defaults` |

Difficulties: `peaceful`, `easy`, `normal`, `hard`. Modes: `survival`, `creative`, `adventure`. Sleep accepts 0 to 100; 0 still needs one player in bed.

Choices are saved. If the server is off, they apply at the next Make-managed start. `make game-apply` starts and applies them. `game-show` displays saved choices, not live measurements.

The default mode does not automatically change known players. To switch connected players to creative, use `make gamemode-all MODE=creative`. Offline players are not affected.

Cheats disable achievements; turning cheats off later does not automatically restore them. Children are not automatically given operator rights.

## Add or remove a player

To welcome someone new:

```sh
make allowlist-disable CONFIRM=yes
```

Have them join in Minecraft Bedrock, then:

```sh
make allowlist-preview
make allowlist-sync
make allowlist-enable
```

Check names before `sync`. Restrict admission again promptly. Already-enrolled absent players remain allowed. These actions may interrupt games.

Show enrolled players with `make allowlist-show`.

To remove someone:

```sh
make allowlist-remove PLAYER="Player Name"
```

Their builds stay. If they are still playing, `make restart` ends the connections. Do not sync while they remain connected or they will be added again. If admission is open, also restrict it with `make allowlist-enable`.

## Back up

```sh
make backup
make open-backups
```

Backups can interrupt play. The server restarts only if it was on beforehand. Copy archives regularly to another disk. No automatic deletion is configured.

Never delete `data`: it holds the world. Keep archives private because they can contain player names and identifiers.

## Restore a backup

This replaces current builds with the archive's builds. Use only your own backups and a compatible Minecraft version.

```sh
make session-cancel
make backups
```

Copy the archive name you want, then replace the name in:

```sh
make restore FILE="backups/your-backup-name.tar.gz" CONFIRM=yes
```

The current world is kept separately. Current settings and admission permissions stay in place. Check the builds before deleting the retained folder.

## Edit the player list manually

Before stopping the server, note names and account numbers with `make xuids`. If a number is missing, ask the player to leave and rejoin, then check messages again. This number is called a XUID.

Then:

```sh
make backup
make stop
make allowlist-edit
```

TextEdit opens `data/allowlist.json`. Replace these fictional examples:

```json
[
  {
    "name": "Parent Example",
    "xuid": "2535400000000001",
    "ignoresPlayerLimit": false
  },
  {
    "name": "Child Example",
    "xuid": "2535400000000002",
    "ignoresPlayerLimit": false
  }
]
```

Keep brackets, straight quotes and the comma between players. No comma after the final player, and no comments. Save with Command-S as plain text. To remove someone, delete their block and adjust the comma. `[]` empties the whole list: if admission is restricted, nobody can enter.

```sh
make allowlist-reload
make allowlist-show
make up
```

Do not skip `reload`: it keeps removals for later starts. Fix an invalid file before restarting.

## Update or change another setting

When nobody is playing:

```sh
make session-cancel
make update-server
```

A backup is made before updating. Afterwards, check that iOS and Windows devices can join with a compatible Minecraft Bedrock version.

For other server settings: `make edit`, save, then `make apply`. To choose a world, use `make worlds` and `make world-default`.

`make restart` does not replace `make apply` after a settings change. `make stop` stops without backing up; use `make session-stop` to end an evening.

[Fix a problem](troubleshooting.md) · [Detailed commands](commands.txt) · [Print](printing.md)
