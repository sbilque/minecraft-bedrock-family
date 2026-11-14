# Install and join the world

[Home](../../README.md) · [Français](../fr/installation.md)

The server runs on the Mac with an Apple Silicon chip. Players join with Minecraft Bedrock on iOS or Windows 10/11, using the same local network.

## 1. Prepare the Mac

You need Docker Desktop for Apple Silicon, Python 3.9 or newer, and a tool to install and run the CLI. A current Python release is recommended.

- [Install Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), then open it.
- [Install Python for macOS](https://www.python.org/downloads/macos/) if needed.
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/). You can also use plain pip; both options are described below.
- Open Terminal: this is where you will type the commands.

Check the tools:

```sh
python3 --version
uv --version
docker compose version
```

If you prefer to use pip instead of uv, check Python and pip:

```sh
python3 --version
python3 -m pip --version
docker compose version
```

## 2. Install the CLI and prepare a server folder

The published package is not on PyPI yet, so install the CLI from a copy of this repository. Choose uv or pip.

**With uv**

`uv` installs CLI apps into its own tool environment, so a source install needs a small isolated environment first. Run these commands inside the folder where you checked out the source:

```sh
uv venv
source .venv/bin/activate
uv pip install .
```

`uv pip install .` builds an isolated install from the source in this folder. It uses the same local project whether it came from a download or a clone. After that, initialize the folder that will hold the world, settings and backups:

```sh
bedrock-family init ~/MinecraftFamily
cd ~/MinecraftFamily
```

**With pip**

Use a Python interpreter that is 3.9 or newer. A `pyproject.toml` file in the source folder describes the project and its entry point:

```sh
python3 -m pip install .
```

To keep the CLI in sync with the source folder (for example, after you fetch new changes), install it editable instead:

```sh
python3 -m pip install --editable .
```

Both the uv and the pip installs register the same `bedrock-family` command. From the same terminal, use `bedrock-family` for every command.

When the published package is released on PyPI, you can also install it as a uv tool:

```sh
uv tool install minecraft-bedrock-family
```

This registers the same `bedrock-family` command.

The CLI follows the terminal's language preferences. To choose a language for one command, put the option before the command: `bedrock-family --language en --help`. To set it for the terminal session, run `export BEDROCK_FAMILY_LANGUAGE=en` (or `fr`).

To adopt an existing server folder, use its path with `-C` and do not move it: `bedrock-family -C ~/minecraft-bedrock-family init`. Initialization preserves existing files and never replaces the world.

## 3. Detect the Mac's address and start

Read the [Minecraft terms](https://www.minecraft.net/eula). Running `bedrock-family setup --accept-eula` confirms that you accept them. The CLI detects the Mac's IPv4 address. If several connections are available, it shows their type (for example, Wi-Fi or Ethernet) and asks which one the players will use. Connect players' devices to the same network as that connection. If possible, ask the router to keep giving the Mac the same address.

You can provide a known address directly: `bedrock-family setup --accept-eula --ip 192.168.1.50`. This skips detection.

The project enables cheats by default, disabling world achievements. Keep a backup before using an existing world.

```sh
bedrock-family setup --accept-eula
bedrock-family check
bedrock-family server start
```

Wait for startup confirmation. The first run downloads the server and creates the world, which may take a few minutes. Do not use `sudo` or forward Internet ports on the router.

## 4. Join from iOS or Windows 10/11

Connect the device to the same local network as the Mac. Open Minecraft Bedrock, then Play > Servers > Add Server.

| Field | Value |
|---|---|
| Name | Minecraft Family |
| Address | The IPv4 address shown by `bedrock-family setup` |
| Port | 19132 |

Use a separate Microsoft account for each player. For children, allow multiplayer in the account's Xbox/Microsoft settings.

On iOS, also allow Minecraft to use the local network when prompted. On the Mac, accept Docker's network requests.

Do not use `localhost`, the router's public address or an `http://` prefix. Guest Wi-Fi can prevent devices from communicating: use the usual local network.

## 5. Restrict admission to your players

Initially, people on the local network who connect with a Microsoft account may join. Let the intended players connect, then:

```sh
bedrock-family access preview
bedrock-family access sync
bedrock-family access enable
bedrock-family version-pin
```

Check the names before `sync`. Enabling the list can interrupt play; enrolled players can reconnect. `version-pin` keeps the server version that just worked.

## 6. Start the next game

```sh
bedrock-family session default set 20:30
bedrock-family session start
```

The first line saves the finishing time. The second starts today's game. After reminders, the server stops, backs up and stays off.

Keep the Mac awake and Docker open. You may close Terminal, not your macOS login session. After a Mac restart, check the server and schedule a new finishing time.

To stop now and back up: `bedrock-family session stop`.

## 7. Uninstall the CLI

To remove the CLI, uninstall the package you used to install it:

- Install with a uv tool: `uv tool uninstall minecraft-bedrock-family`
- Install with pip: `python3 -m pip uninstall minecraft-bedrock-family`
- Install with a source venv (`uv venv` + `uv pip install .`): run `uv pip uninstall minecraft-bedrock-family`, or delete the `.venv` folder in the source folder.

Uninstalling the CLI does not remove the server folder you created with `bedrock-family init` (`~/MinecraftFamily` or similar). The world, settings and backups stay there. To remove them too, delete that folder yourself.

[Use the server](guide.md) · [Need help?](troubleshooting.md)
