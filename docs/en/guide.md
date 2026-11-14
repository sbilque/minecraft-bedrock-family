# Use the server

[Home](../../README.md) · [Français](../fr/guide.md) · [All commands](commands.txt)

After installing the CLI and initializing the server with `bedrock-family init ~/MinecraftFamily`, open Terminal and enter `cd ~/MinecraftFamily`. Run one command at a time and wait for it to finish.

The Mac stores the world. Players use Minecraft Bedrock on iOS or Windows 10/11, on the same local network.

## Start and choose a finishing time

```sh
bedrock-family session start
```

The server starts using the usual finishing time. Save that time once with:

```sh
bedrock-family session default set 20:30
```

Without a custom setting, it is 19:00. For an exception today:

```sh
bedrock-family session start --until 21:00
```

Times use the Mac's clock. A time already past today is refused. Reminders arrive 15 min, 5 min, 1 min and 30 s before the end; already-past reminders are skipped. At the selected time, shutdown begins, then the world is backed up. The server stays off.

To run the server for a fixed length instead, use `--duration` with minutes (`45m`) or hours (`1h`, `2h30m`, or a plain number of minutes):

```sh
bedrock-family session start --duration 2h30m
```

The server starts, and a timer stops it after the given length with the same reminders and backup. It is a relative time, so it always lands in the future.

This is not a daily schedule: run `bedrock-family session start` for each game.

## List or choose a world

```sh
bedrock-family world list
```

This lists the available world folders and marks the default. To choose an existing world:

```sh
bedrock-family world use "World Name"
```

This does not interrupt a game in progress. The choice takes effect on the next `bedrock-family server start` or `bedrock-family settings apply`. A world must already exist in `data/worlds`.

To create and start a new world:

```sh
bedrock-family world create "New World"
```

If a server is already running, the CLI asks before restarting it. In a non-interactive terminal, add `--yes` to confirm explicitly.

## Check, change or cancel the end

| I want to… | I type… |
|---|---|
| Check the planned time | `bedrock-family session status` |
| Read shutdown messages | `bedrock-family session logs` |
| Cancel the timer without stopping | `bedrock-family session cancel` |
| Stop now and back up | `bedrock-family session stop` |
| See the usual time | `bedrock-family session default show` |
| Reset the usual time to 19:00 | `bedrock-family session default reset` |

Changing the usual time does not move an active timer. Cancel it, then schedule again to move it.

Keep the Mac awake and Docker open. You may close Terminal, not your macOS login session. After a restart, the server may come back without a finishing time: check and reschedule. A failure can prevent reminders or backups.

## Change the game rules

Warn players first: some changes restart the server.

| I want to… | I type… |
|---|---|
| Enable or disable cheats | `bedrock-family settings set cheats on` or `bedrock-family settings set cheats off` |
| Keep or lose inventory at death | `bedrock-family settings set keep-inventory on` or `bedrock-family settings set keep-inventory off` |
| Choose difficulty | `bedrock-family settings set difficulty easy` |
| Let one sleeping player skip the night | `bedrock-family settings set sleep-one` |
| Require half the players in bed | `bedrock-family settings set sleep 50` |
| Choose the default game mode | `bedrock-family settings set gamemode survival` |
| View saved choices | `bedrock-family settings show` |
| Restore the five family defaults | `bedrock-family settings reset` |

Difficulties: `peaceful`, `easy`, `normal`, `hard`. Modes: `survival`, `creative`, `adventure`. Sleep accepts 0 to 100; 0 still needs one player in bed.

Choices are saved. If the server is off, they apply at the next CLI start. `bedrock-family settings apply` starts and applies them. `bedrock-family settings show` displays saved choices, not live measurements.

The default mode does not automatically change known players. To switch connected players to creative, use `bedrock-family players set-mode creative`. Offline players are not affected.

Cheats disable achievements; turning cheats off later does not automatically restore them. Children are not automatically given operator rights.

## Add or remove a player

To welcome someone new:

```sh
bedrock-family access disable --confirm
```

Have them join in Minecraft Bedrock, then:

```sh
bedrock-family access preview
bedrock-family access sync
bedrock-family access enable
```

Check names before `sync`. Restrict admission again promptly. Already-enrolled absent players remain allowed. These actions may interrupt games.

Show enrolled players with `bedrock-family access show`.

To remove someone:

```sh
bedrock-family access remove "Player Name"
```

Their builds stay. If they are still playing, `bedrock-family server restart` ends the connections. Do not sync while they remain connected or they will be added again. If admission is open, also restrict it with `bedrock-family access enable`.

## Back up

```sh
bedrock-family backup create
bedrock-family open backups
```

Backups can interrupt play. The server restarts only if it was on beforehand. Copy archives regularly to another disk. No automatic deletion is configured.

Never delete `data`: it holds the world. Keep archives private because they can contain player names and identifiers.

## Restore a backup

This replaces current builds with the archive's builds. Use only your own backups and a compatible Minecraft version.

```sh
bedrock-family session cancel
bedrock-family backup list
```

Copy the archive name you want, then replace the name in:

```sh
bedrock-family backup restore "backups/your-backup-name.tar.gz" --confirm
```

The current world is kept separately. Current settings and admission permissions stay in place. Check the builds before deleting the retained folder.

## Edit the player list manually

Before stopping the server, note names and account numbers with `bedrock-family players xuids`. If a number is missing, ask the player to leave and rejoin, then check messages again. This number is called a XUID.

Then:

```sh
bedrock-family backup create
bedrock-family server stop
bedrock-family access edit
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
bedrock-family access reload
bedrock-family access show
bedrock-family server start
```

Do not skip `reload`: it keeps removals for later starts. Fix an invalid file before restarting.

## Update or change another setting

When nobody is playing:

```sh
bedrock-family session cancel
bedrock-family update --server
```

A backup is made before updating. Afterwards, check that iOS and Windows devices can join with a compatible Minecraft Bedrock version.

For other server settings: `bedrock-family open settings`, save, then `bedrock-family settings apply`. To choose a world, use `bedrock-family world list` and `bedrock-family world use "World Name"`.

`bedrock-family server restart` does not replace `bedrock-family settings apply` after a settings change. `bedrock-family server stop` stops without backing up; use `bedrock-family session stop` to end an evening.

[Fix a problem](troubleshooting.md) · [Detailed commands](commands.txt) · [Print](printing.md)
