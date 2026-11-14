# Family cheat sheet

On the Mac, open Terminal:

```sh
cd ~/MinecraftFamily
```

Help follows the terminal language. To select one: `bedrock-family --language en --help`.

Players use Minecraft Bedrock on iOS or Windows 10/11, on the same local network. Keep the Mac and Docker running.

## Start and finish a game

| I want to… | I type… |
|---|---|
| Start with the usual finishing time | bedrock-family session start |
| Choose another time today | bedrock-family session start --until 21:00 |
| Run for a fixed length | bedrock-family session start --duration 2h30m |
| Stop now and back up | bedrock-family session stop |
| Check the planned time | bedrock-family session status |
| Cancel the timer without stopping | bedrock-family session cancel |

Reminders: 15 min, 5 min, 1 min and 30 s before the end. Then shutdown and backup. A time already past today is refused. A duration (minutes or hours) always lands in the future.

## Save a usual finishing time

| I want to… | I type… |
|---|---|
| Save 20:30 | bedrock-family session default set 20:30 |
| Show the usual time | bedrock-family session default show |
| Return to 19:00 | bedrock-family session default reset |

Changing the usual time does not move an active timer. Cancel, then schedule again to move it.

## Choose a world

| I want to… | I type… |
|---|---|
| See worlds and the current choice | bedrock-family world list |
| Choose an existing world | bedrock-family world use "World Name" |

The choice takes effect on the next `bedrock-family server start` or `bedrock-family settings apply`, not during a game.

## Back up

| I want to… | I type… |
|---|---|
| Back up now | bedrock-family backup create |
| Open the archives | bedrock-family open backups |

Backing up can interrupt play. Copy archives to another disk. Do not delete data: it holds the world.

<!-- pagebreak -->

# Players, rules and small problems

## Welcome a player

1. bedrock-family access disable --confirm
2. Have the player join in Minecraft Bedrock.
3. bedrock-family access preview
4. Check names, then bedrock-family access sync
5. bedrock-family access enable

Show enrolled players: bedrock-family access show.

Remove someone: bedrock-family access remove "Player Name". Builds stay. If still connected, bedrock-family server restart ends the connections. Do not sync while they remain connected.

## Change the game

| I want to… | I type… |
|---|---|
| Keep inventory at death | bedrock-family settings set keep-inventory on |
| Choose easy difficulty | bedrock-family settings set difficulty easy |
| Let one sleeper skip the night | bedrock-family settings set sleep-one |
| Use survival as the default mode | bedrock-family settings set gamemode survival |
| View saved choices | bedrock-family settings show |

For switches, off disables the option. Difficulties: peaceful, easy, normal, hard. Modes: survival, creative, adventure. The guide explains other choices.

Cheats are initially enabled and disable world achievements. Rule changes may interrupt play.

## If something fails

| I want to… | I type… |
|---|---|
| Read server messages | bedrock-family server logs --once |
| Read shutdown messages | bedrock-family session logs |
| Check Docker and Python | bedrock-family doctor |
| All commands | bedrock-family --help |

After restarting the Mac, check and reschedule the finishing time. A failure can prevent stopping or backing up: read the messages before assuming success.
