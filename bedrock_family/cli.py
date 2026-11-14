"""User-facing command-line interface for Minecraft Bedrock Family."""
import argparse
import contextlib
from importlib.resources import files
import os
from pathlib import Path
import subprocess
import sys
import tarfile

from . import __version__, manage


def build_parser():
    parser = argparse.ArgumentParser(
        prog="bedrock-family",
        description="Gérer un serveur Minecraft Bedrock familial.",
    )
    parser.add_argument(
        "-C", "--project-dir", type=Path, default=Path.cwd(),
        help="Dossier de ce serveur (par défaut : dossier courant).",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")

    init = commands.add_parser("init", help="Initialiser ou adopter un dossier serveur.")
    init.add_argument("directory", nargs="?", type=Path)

    setup = commands.add_parser("setup", help="Configurer l’EULA et l’adresse du Mac.")
    setup.add_argument("--accept-eula", action="store_true", help="Confirmer l’acceptation des conditions Minecraft.")
    setup.add_argument("--ip", help="Utiliser cette IPv4 au lieu de la détecter.")

    commands.add_parser("doctor", help="Vérifier Docker et l’environnement.")
    commands.add_parser("check", help="Valider la configuration du serveur.")

    server = commands.add_parser("server", help="Démarrer, arrêter ou inspecter le serveur.")
    server_commands = server.add_subparsers(dest="server_command", required=True)
    for name in ("start", "stop", "restart", "down", "status"):
        server_commands.add_parser(name)
    logs = server_commands.add_parser("logs")
    logs.add_argument("--once", action="store_true")
    logs.add_argument("--tail", type=int, default=100)
    console = server_commands.add_parser("console")
    console.add_argument("command", nargs=argparse.REMAINDER)

    world = commands.add_parser("world", help="Afficher, choisir ou créer un monde.")
    world_commands = world.add_subparsers(dest="world_command", required=True)
    world_commands.add_parser("list")
    use_world = world_commands.add_parser("use")
    use_world.add_argument("name")
    create_world = world_commands.add_parser("create")
    create_world.add_argument("name")
    create_world.add_argument("--yes", action="store_true", help="Confirmer le démarrage ou redémarrage du serveur.")

    session = commands.add_parser("session", help="Programmer la fin d’une partie.")
    session_commands = session.add_subparsers(dest="session_command", required=True)
    start_session = session_commands.add_parser("start")
    start_session.add_argument("--until", metavar="HH:MM", help="Heure de fin pour cette partie seulement.")
    for name in ("status", "cancel", "stop", "logs"):
        session_commands.add_parser(name)
    defaults = session_commands.add_parser("default")
    defaults_subcommands = defaults.add_subparsers(dest="default_command", required=True)
    defaults_subcommands.add_parser("show")
    set_default = defaults_subcommands.add_parser("set")
    set_default.add_argument("time", metavar="HH:MM")
    defaults_subcommands.add_parser("reset")

    players = commands.add_parser("players", help="Voir les joueurs et leurs identifiants.")
    players_commands = players.add_subparsers(dest="players_command", required=True)
    players_commands.add_parser("list")
    players_commands.add_parser("xuids")
    player_mode = players_commands.add_parser("set-mode")
    player_mode.add_argument("mode", choices=("survival", "creative", "adventure", "survie", "creatif", "aventure"))

    access = commands.add_parser("access", help="Gérer les joueurs autorisés.")
    access_commands = access.add_subparsers(dest="access_command", required=True)
    for name in ("preview", "sync", "show", "enable", "reload"):
        access_commands.add_parser(name)
    disable = access_commands.add_parser("disable")
    disable.add_argument("--confirm", action="store_true")
    remove = access_commands.add_parser("remove")
    remove.add_argument("name")
    edit_access = access_commands.add_parser("edit")

    settings = commands.add_parser("settings", help="Consulter ou modifier les règles du jeu.")
    settings_commands = settings.add_subparsers(dest="settings_command", required=True)
    settings_commands.add_parser("show")
    set_setting = settings_commands.add_parser("set")
    set_setting.add_argument("name", choices=("cheats", "keep-inventory", "difficulty", "sleep", "sleep-one", "gamemode", "finish-time"))
    set_setting.add_argument("value", nargs="?")
    settings_commands.add_parser("reset")
    settings_commands.add_parser("apply")

    backup = commands.add_parser("backup", help="Créer, lister ou restaurer une sauvegarde.")
    backup_commands = backup.add_subparsers(dest="backup_command", required=True)
    backup_commands.add_parser("create")
    backup_commands.add_parser("list")
    restore = backup_commands.add_parser("restore")
    restore.add_argument("archive", type=Path)
    restore.add_argument("--confirm", action="store_true")

    update = commands.add_parser("update", help="Mettre à jour le serveur Bedrock.")
    update.add_argument("--server", action="store_true", help="Télécharger la version Bedrock la plus récente.")
    version = commands.add_parser("version", help="Gérer la version Bedrock installée.")
    version_commands = version.add_subparsers(dest="version_command", required=True)
    version_commands.add_parser("pin")
    version_commands.add_parser("pull")

    open_command = commands.add_parser("open", help="Ouvrir un dossier ou fichier de configuration.")
    open_command.add_argument("target", choices=("data", "backups", "settings", "network", "access"))

    return parser


def initialize(directory):
    root = directory.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    compose = root / "compose.yaml"
    if compose.exists():
        if not compose.is_file():
            raise RuntimeError("compose.yaml existe mais n’est pas un fichier.")
        print("Dossier serveur existant conservé ; aucun fichier n’a été remplacé.")
    else:
        template = files("bedrock_family").joinpath("templates", "compose.yaml")
        compose.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        print("Modèle du serveur installé dans " + str(root))
    for name in ("data", "backups", "logs"):
        (root / name).mkdir(exist_ok=True)
    print("Dossier prêt. Exécuter bedrock-family -C " + str(root) + " setup.")
    return root


def confirm(prompt, assume_yes=False):
    if assume_yes:
        return
    if not sys.stdin.isatty():
        raise RuntimeError("Confirmation interactive requise ; relancer avec --yes si cette opération est voulue.")
    if input(prompt + " [o/N] ").strip().casefold() not in ("o", "oui", "y", "yes"):
        raise RuntimeError("Opération annulée.")


@contextlib.contextmanager
def project_context(root):
    previous_argv = sys.argv
    previous_root = manage.ROOT
    root_env = os.environ.get("BEDROCK_FAMILY_HOME")
    try:
        manage.ROOT = root
        os.environ["BEDROCK_FAMILY_HOME"] = str(root)
        yield
    finally:
        manage.ROOT = previous_root
        sys.argv = previous_argv
        if root_env is None:
            os.environ.pop("BEDROCK_FAMILY_HOME", None)
        else:
            os.environ["BEDROCK_FAMILY_HOME"] = root_env


def invoke(root, action, **values):
    with project_context(root):
        env_values = {key: os.environ.get(key) for key in values}
        try:
            os.environ.update({key: str(value) for key, value in values.items()})
            sys.argv = ["bedrock-family", action]
            try:
                manage.main()
            except (RuntimeError, OSError, ValueError, KeyError, tarfile.TarError, subprocess.TimeoutExpired):
                if action not in ("setup", "help", "session-default", "session-default-show", "session-default-reset"):
                    manage.diagnostic()
                raise
        finally:
            for key, value in env_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def create_world(root, name, assume_yes):
    if not name or name != name.strip() or "\x00" in name or name in (".", "..") or Path(name).name != name:
        raise RuntimeError("Nom de monde invalide.")
    destination = root / "data" / "worlds" / name
    if destination.exists():
        raise RuntimeError("Ce monde existe déjà ; utiliser bedrock-family world use.")
    with project_context(root):
        manage.config_check()
        manage.docker_start()
        if manage.running():
            confirm("Créer ce monde va redémarrer le serveur actuellement actif. Continuer ?", assume_yes)
        with manage.lock("maintenance"):
            if destination.exists():
                raise RuntimeError("Ce monde existe déjà.")
            manage.env_update({"LEVEL_NAME": name})
            manage.up()


def execute(args, parser):
    if args.command == "init":
        return initialize(args.directory or args.project_dir)

    root = args.project_dir.expanduser().resolve()
    if args.command == "doctor":
        invoke(root, "doctor")
        return root
    if not (root / "compose.yaml").is_file():
        raise RuntimeError("Aucun serveur dans ce dossier. Initialiser avec bedrock-family init.")

    if args.command == "setup":
        if not args.accept_eula:
            print("Lire les conditions Minecraft : https://www.minecraft.net/eula")
            if not sys.stdin.isatty():
                raise RuntimeError("Accepter explicitement les conditions avec --accept-eula.")
            confirm("Acceptez-vous les conditions Minecraft ?", False)
        invoke(root, "setup", EULA="TRUE", LAN_IP=args.ip or "")
    elif args.command == "check":
        invoke(root, "check")
    elif args.command == "server":
        if args.server_command == "logs":
            action = "logs-once" if args.once else "logs"
            invoke(root, action, TAIL=str(args.tail))
        elif args.server_command == "console":
            invoke(root, "console", CMD=" ".join(args.command).strip())
        else:
            invoke(root, {"start": "up", "stop": "stop", "restart": "restart", "down": "down", "status": "status"}[args.server_command])
    elif args.command == "world":
        if args.world_command == "list":
            invoke(root, "worlds")
        elif args.world_command == "use":
            invoke(root, "world-default", LEVEL=args.name)
        else:
            create_world(root, args.name, args.yes)
    elif args.command == "session":
        if args.session_command == "start":
            invoke(root, "session", STOP_AT=args.until or "")
        elif args.session_command == "default":
            if args.default_command == "show":
                invoke(root, "session-default-show")
            elif args.default_command == "set":
                invoke(root, "session-default", TIME=args.time)
            else:
                invoke(root, "session-default-reset")
        else:
            invoke(root, {"status": "session-status", "cancel": "session-cancel", "stop": "session-stop", "logs": "session-logs"}[args.session_command])
    elif args.command == "players":
        if args.players_command == "list":
            invoke(root, "players")
        elif args.players_command == "xuids":
            invoke(root, "xuids")
        else:
            invoke(root, "gamemode-all", MODE=args.mode)
    elif args.command == "access":
        if args.access_command == "disable" and not args.confirm:
            raise RuntimeError("Cette action ouvre l’accès au serveur ; confirmer avec --confirm.")
        if args.access_command == "remove":
            invoke(root, "allowlist-remove", PLAYER=args.name)
        elif args.access_command == "disable":
            invoke(root, "allowlist-disable", CONFIRM="yes")
        elif args.access_command == "edit":
            invoke(root, "allowlist-edit")
        else:
            invoke(root, "allowlist-" + args.access_command)
    elif args.command == "settings":
        if args.settings_command == "show":
            invoke(root, "game-show")
            print("Heure habituelle de fin : " + manage.load(root / "family-settings.json", {}).get("stop_at", "19:00"))
        elif args.settings_command == "reset":
            invoke(root, "game-defaults")
        elif args.settings_command == "apply":
            invoke(root, "game-apply")
        else:
            action_names = {
                "cheats": "cheats",
                "keep-inventory": "keep-inventory",
                "difficulty": "difficulty",
                "sleep": "sleep",
                "sleep-one": "sleep-one",
                "gamemode": "gamemode",
                "finish-time": "session-default",
            }
            if args.name == "sleep" and args.value is None:
                parser.error("settings set sleep requiert un pourcentage de 0 à 100.")
            if args.name == "sleep-one" and args.value is not None:
                parser.error("settings set sleep-one ne prend pas de valeur.")
            if args.name not in ("sleep", "sleep-one") and args.value is None:
                parser.error("settings set " + args.name + " requiert une valeur.")
            if args.name != "sleep-one":
                key = "TIME" if args.name == "finish-time" else "PERCENT" if args.name == "sleep" else "VALUE" if args.name in ("cheats", "keep-inventory") else "LEVEL" if args.name == "difficulty" else "MODE"
                invoke(root, action_names[args.name], **{key: args.value})
            else:
                invoke(root, action_names[args.name])
    elif args.command == "backup":
        if args.backup_command == "create":
            invoke(root, "backup")
        elif args.backup_command == "list":
            invoke(root, "backups")
        else:
            if not args.confirm:
                raise RuntimeError("La restauration remplace les constructions actuelles ; ajouter --confirm.")
            archive = args.archive if args.archive.is_absolute() else root / args.archive
            invoke(root, "restore", FILE=str(archive), CONFIRM="yes")
    elif args.command == "update":
        invoke(root, "update-server" if args.server else "update")
    elif args.command == "version":
        invoke(root, "version-pin" if args.version_command == "pin" else "pull")
    elif args.command == "open":
        action = {"data": "open-data", "backups": "open-backups", "settings": "edit", "network": "edit-env", "access": "allowlist-edit"}[args.target]
        invoke(root, action)
    else:
        parser.error("Commande non reconnue.")
    return root


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        execute(args, parser)
        return 0
    except KeyboardInterrupt:
        print("Interrompu. Le serveur n’est pas automatiquement arrêté.", file=sys.stderr)
        return 130
    except (RuntimeError, OSError, ValueError, KeyError, tarfile.TarError, subprocess.TimeoutExpired) as exc:
        print("ERREUR : " + str(exc), file=sys.stderr)
        return 1
