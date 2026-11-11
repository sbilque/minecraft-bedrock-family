# Family cheat sheet

On the Mac, open Terminal:

```sh
cd ~/minecraft-bedrock-family
```

Players use Minecraft Bedrock on iOS or Windows 10/11, on the same local network. Keep the Mac and Docker running.

## Start and finish a game

| I want to… | I type… |
|---|---|
| Start with the usual finishing time | make session |
| Choose another time today | make session STOP_AT=21:00 |
| Stop now and back up | make session-stop |
| Check the planned time | make session-status |
| Cancel the timer without stopping | make session-cancel |

Reminders: 15 min, 5 min, 1 min and 30 s before the end. Then shutdown and backup. A time already past today is refused.

## Save a usual finishing time

| I want to… | I type… |
|---|---|
| Save 20:30 | make session-default TIME=20:30 |
| Show the usual time | make session-default-show |
| Return to 19:00 | make session-default-reset |

Changing the usual time does not move an active timer. Cancel, then schedule again to move it.

## Back up

| I want to… | I type… |
|---|---|
| Back up now | make backup |
| Open the archives | make open-backups |

Backing up can interrupt play. Copy archives to another disk. Do not delete data: it holds the world.

<!-- pagebreak -->

# Players, rules and small problems

## Welcome a player

1. make allowlist-disable CONFIRM=yes
2. Have the player join in Minecraft Bedrock.
3. make allowlist-preview
4. Check names, then make allowlist-sync
5. make allowlist-enable

Show enrolled players: make allowlist-show.

Remove someone: make allowlist-remove PLAYER="Player Name". Builds stay. If still connected, make restart ends the connections. Do not sync while they remain connected.

## Change the game

| I want to… | I type… |
|---|---|
| Keep inventory at death | make keep-inventory VALUE=on |
| Choose easy difficulty | make difficulty LEVEL=easy |
| Let one sleeper skip the night | make sleep-one |
| Use survival as the default mode | make gamemode MODE=survival |
| View saved choices | make game-show |

For switches, off disables the option. Difficulties: peaceful, easy, normal, hard. Modes: survival, creative, adventure. The guide explains other choices.

Cheats are initially enabled and disable world achievements. Rule changes may interrupt play.

## If something fails

| I want to… | I type… |
|---|---|
| Read server messages | make logs-once |
| Read shutdown messages | make session-logs |
| Check Docker and Python | make doctor |
| All commands | make |

After restarting the Mac, check and reschedule the finishing time. A failure can prevent stopping or backing up: read the messages before assuming success.
