# Install and join the world

[Home](../../README.md) · [Français](../fr/installation.md)

The server runs on the Mac with an Apple Silicon chip. Players join with Minecraft Bedrock on iOS or Windows 10/11, using the same local network.

## 1. Prepare the Mac

You need Docker Desktop for Apple Silicon, Python 3.9 or newer, and make. A current Python release is recommended.

- [Install Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), then open it.
- [Install Python for macOS](https://www.python.org/downloads/macos/) if needed.
- Open Terminal: this is where you will type the commands.

Check the tools:

```sh
python3 --version
make --version
docker compose version
```

If make is missing, type `xcode-select --install` and follow Apple's instructions. Playing does not require extra Python packages.

## 2. Put the project in place

On GitHub, choose Code > Download ZIP. Extract it, rename the folder to `minecraft-bedrock-family`, and move it into your home folder.

In Terminal:

```sh
cd ~/minecraft-bedrock-family
make verify
```

This check does not start a game. Never replace a folder containing an existing world without a backup.

## 3. Find the Mac's address and start

Open System Settings > Network > active connection > Details > TCP/IP. Note the IPv4 address. If possible, ask the router to keep giving the Mac this address.

Replace `192.168.1.50` below with that address. Read the [Minecraft terms](https://www.minecraft.net/eula): `EULA=TRUE` means you accept them.

The project enables cheats by default, disabling world achievements. Keep a backup before using an existing world.

```sh
make setup LAN_IP=192.168.1.50 EULA=TRUE
make check
make up
```

Wait for startup confirmation. The first run downloads the server and creates the world, which may take a few minutes. Do not use `sudo` or forward Internet ports on the router.

## 4. Join from iOS or Windows 10/11

Connect the device to the same local network as the Mac. Open Minecraft Bedrock, then Play > Servers > Add Server.

| Field | Value |
|---|---|
| Name | Minecraft Family |
| Address | The Mac's IPv4 address |
| Port | 19132 |

Use a separate Microsoft account for each player. For children, allow multiplayer in the account's Xbox/Microsoft settings.

On iOS, also allow Minecraft to use the local network when prompted. On the Mac, accept Docker's network requests.

Do not use `localhost`, the router's public address or an `http://` prefix. Guest Wi-Fi can prevent devices from communicating: use the usual local network.

## 5. Restrict admission to your players

Initially, people on the local network who connect with a Microsoft account may join. Let the intended players connect, then:

```sh
make allowlist-preview
make allowlist-sync
make allowlist-enable
make version-pin
```

Check the names before `sync`. Enabling the list can interrupt play; enrolled players can reconnect. `version-pin` keeps the server version that just worked.

## 6. Start the next game

```sh
make session-default TIME=20:30
make session
```

The first line saves the finishing time. The second starts today's game. After reminders, the server stops, backs up and stays off.

Keep the Mac awake and Docker open. You may close Terminal, not your macOS login session. After a Mac restart, check the server and schedule a new finishing time.

To stop now and back up: `make session-stop`.

[Use the server](guide.md) · [Need help?](troubleshooting.md)
