# Fix a problem

[Home](../../README.md) · [Français](../fr/troubleshooting.md)

Do not delete the world or settings as a troubleshooting step.

## The server will not start

1. Open Docker Desktop on the Mac.
2. Wait for startup to finish.
3. Retry:

```sh
bedrock-family server start
```

If it fails:

```sh
bedrock-family server logs --once
bedrock-family doctor
```

The manager also tries to show recent messages after an error. A sent command is not necessarily a successful command.

## A docker.sock message appears

Docker cannot be reached. Open Docker Desktop, wait, then try `docker info`. Do not create the file yourself or delete `.docker`.

If Docker is open but stuck, use its troubleshooting menu to restart it. Do not start with a factory reset.

## An iOS or Windows device cannot join

Check in order:

1. The Mac is on and Docker is running.
2. The device and Mac share the same local network, not an isolated guest network.
3. Minecraft uses the Mac's current address and port 19132.
4. Minecraft Bedrock is up to date and compatible with the server.
5. The account permits multiplayer and the name is on the admission list.

On iOS, also check Minecraft's Local Network permission. On the Mac, allow Docker's incoming connections if blocked. Do not disable all Mac protection.

## A player identifier is missing

Ask the player to leave and rejoin. Retry `bedrock-family access preview`, then `bedrock-family access sync` if the names are correct.

## The finishing time seems inactive

```sh
bedrock-family session status
bedrock-family session logs
```

After restarting the Mac or stopping Docker, do not rely on the old timer. Check, cancel with `bedrock-family session cancel`, then run `bedrock-family session start` again.

## A backup fails

Read `bedrock-family session logs` or `bedrock-family server logs --once`. Keep older archives and do not assume the latest one is complete. An error after shutdown can leave the server off intentionally.

## Ask for help

Copy the command and final messages. Include macOS, Docker Desktop, Python and Minecraft versions. Hide player names, account numbers and private network details. Do not attach a world or backup to a public report.
