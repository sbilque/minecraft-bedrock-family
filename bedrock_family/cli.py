"""User-facing command-line interface for Minecraft Bedrock Family."""

import argparse
import contextlib
import os
import subprocess
import sys
import tarfile
from importlib.resources import files
from pathlib import Path

from . import __version__, manage
from .i18n import (
    available_languages,
    default_language,
    language_from_args,
    set_language,
    tr,
)

ARGPARSE_MESSAGE_KEYS = {
    "usage: ": "usage",
    "positional arguments": "positional_arguments",
    "optional arguments": "optional_arguments",
    "options": "options",
    "show this help message and exit": "show_this_help_message_and_exit",
    "unrecognized arguments: %s": "unrecognized_arguments",
    "invalid choice: %(value)r (choose from %(choices)s)": "invalid_choice",
    "argument %s: %s": "argument_error",
}


def translate_argparse(message):
    """Translate argparse default error text through the current locale."""
    return tr(ARGPARSE_MESSAGE_KEYS.get(message, message))


def build_parser(language=None):
    """Build the CLI parser for the requested interface language."""
    language = set_language(language or default_language())
    argparse._ = translate_argparse
    parser = argparse.ArgumentParser(
        prog="bedrock-family",
        description=tr("manage_a_family_minecraft_bedrock_server"),
    )
    parser.add_argument(
        "-C",
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help=tr("server_folder_defaults_to_the_current_directory"),
    )
    parser.add_argument(
        "--language",
        choices=available_languages(),
        default=language,
        metavar="LANG",
        help=tr("select_the_interface_language"),
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("help", help=tr("show_cli_help"))
    init = commands.add_parser(
        "init", help=tr("initialize_or_adopt_a_server_folder")
    )
    init.add_argument("directory", nargs="?", type=Path)

    setup = commands.add_parser(
        "setup", help=tr("configure_the_eula_and_the_mac_s_address")
    )
    setup.add_argument(
        "--accept-eula",
        action="store_true",
        help=tr("confirm_acceptance_of_the_minecraft_terms"),
    )
    setup.add_argument(
        "--ip", help=tr("use_this_ipv4_address_instead_of_detecting_one")
    )

    commands.add_parser("doctor", help=tr("check_docker_and_the_environment"))
    commands.add_parser("check", help=tr("validate_the_server_configuration"))

    server = commands.add_parser(
        "server", help=tr("start_stop_or_inspect_the_server")
    )
    server_commands = server.add_subparsers(
        dest="server_command", required=True
    )
    for name in ("start", "stop", "restart", "down", "status"):
        server_commands.add_parser(name)
    logs = server_commands.add_parser("logs")
    logs.add_argument("--once", action="store_true")
    logs.add_argument("--tail", type=int, default=100)
    console = server_commands.add_parser("console")
    console.add_argument("command", nargs=argparse.REMAINDER)

    world = commands.add_parser(
        "world", help=tr("list_choose_or_create_a_world")
    )
    world_commands = world.add_subparsers(dest="world_command", required=True)
    world_commands.add_parser("list")
    use_world = world_commands.add_parser("use")
    use_world.add_argument("name")
    create_world = world_commands.add_parser("create")
    create_world.add_argument("name")
    create_world.add_argument(
        "--yes",
        action="store_true",
        help=tr("confirm_starting_or_restarting_the_server"),
    )

    session = commands.add_parser(
        "session", help=tr("schedule_the_end_of_a_game")
    )
    session_commands = session.add_subparsers(
        dest="session_command", required=True
    )
    start_session = session_commands.add_parser("start")
    start_session.add_argument(
        "--until", metavar="HH:MM", help=tr("end_time_for_this_game_only")
    )
    for name in ("status", "cancel", "stop", "logs"):
        session_commands.add_parser(name)
    defaults = session_commands.add_parser("default")
    defaults_subcommands = defaults.add_subparsers(
        dest="default_command", required=True
    )
    defaults_subcommands.add_parser("show")
    set_default = defaults_subcommands.add_parser("set")
    set_default.add_argument("time", metavar="HH:MM")
    defaults_subcommands.add_parser("reset")

    players = commands.add_parser(
        "players", help=tr("list_players_and_their_identifiers")
    )
    players_commands = players.add_subparsers(
        dest="players_command", required=True
    )
    players_commands.add_parser("list")
    players_commands.add_parser("xuids")
    player_mode = players_commands.add_parser("set-mode")
    player_mode.add_argument(
        "mode",
        choices=(
            "survival",
            "creative",
            "adventure",
            "survie",
            "creatif",
            "aventure",
        ),
    )

    access = commands.add_parser("access", help=tr("manage_allowed_players"))
    access_commands = access.add_subparsers(
        dest="access_command", required=True
    )
    for name in ("preview", "sync", "show", "enable", "reload"):
        access_commands.add_parser(name)
    disable = access_commands.add_parser("disable")
    disable.add_argument("--confirm", action="store_true")
    remove = access_commands.add_parser("remove")
    remove.add_argument("name")
    access_commands.add_parser("edit")

    settings = commands.add_parser(
        "settings", help=tr("view_or_change_game_rules")
    )
    settings_commands = settings.add_subparsers(
        dest="settings_command", required=True
    )
    settings_commands.add_parser("show")
    set_setting = settings_commands.add_parser("set")
    set_setting.add_argument(
        "name",
        choices=(
            "cheats",
            "keep-inventory",
            "difficulty",
            "sleep",
            "sleep-one",
            "gamemode",
            "finish-time",
        ),
    )
    set_setting.add_argument("value", nargs="?")
    settings_commands.add_parser("reset")
    settings_commands.add_parser("apply")

    backup = commands.add_parser(
        "backup", help=tr("create_list_or_restore_a_backup")
    )
    backup_commands = backup.add_subparsers(
        dest="backup_command", required=True
    )
    backup_commands.add_parser("create")
    backup_commands.add_parser("list")
    restore = backup_commands.add_parser("restore")
    restore.add_argument("archive", type=Path)
    restore.add_argument("--confirm", action="store_true")

    update = commands.add_parser("update", help=tr("update_the_bedrock_server"))
    update.add_argument(
        "--server",
        action="store_true",
        help=tr("download_the_latest_bedrock_server_version"),
    )
    version = commands.add_parser(
        "version", help=tr("manage_the_installed_bedrock_version")
    )
    version_commands = version.add_subparsers(
        dest="version_command", required=True
    )
    version_commands.add_parser("pin")
    version_commands.add_parser("pull")

    open_command = commands.add_parser(
        "open", help=tr("open_a_folder_or_configuration_file")
    )
    open_command.add_argument(
        "target", choices=("data", "backups", "settings", "network", "access")
    )

    return parser


def initialize(directory):
    """Create or adopt a Bedrock server root directory with the project layout."""
    root = directory.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    compose = root / "compose.yaml"
    if compose.exists():
        if not compose.is_file():
            raise RuntimeError(tr("compose_yaml_exists_but_is_not_a_file"))
            print(tr("existing_server_folder_preserved_no_files_were_replaced"))
    else:
        template = files("bedrock_family").joinpath("templates", "compose.yaml")
        compose.write_text(
            template.read_text(encoding="utf-8"), encoding="utf-8"
        )
        print(tr("server_template_installed_in_root", root=root))
    for name in ("data", "backups", "logs"):
        (root / name).mkdir(exist_ok=True)
    print(tr("folder_is_ready_run_bedrock_family_c_root_setup", root=root))
    return root


def confirm(prompt, assume_yes=False):
    """Prompt for confirmation unless the command was explicitly accepted."""
    if assume_yes:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            tr(
                "interactive_confirmation_required_rerun_with_yes_if_you_intend_to_proceed"
            )
        )
    if input(tr(prompt) + " [o/N] ").strip().casefold() not in (
        "o",
        "oui",
        "y",
        "yes",
    ):
        raise RuntimeError(tr("operation_cancelled"))


@contextlib.contextmanager
def project_context(root):
    """Temporarily switch the project root while running a subcommand."""
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
    """Run a management action inside a specific project root."""
    with project_context(root):
        env_values = {key: os.environ.get(key) for key in values}
        try:
            os.environ.update(
                {key: str(value) for key, value in values.items()}
            )
            sys.argv = ["bedrock-family", action]
            try:
                manage.main()
            except (
                RuntimeError,
                OSError,
                ValueError,
                KeyError,
                tarfile.TarError,
                subprocess.TimeoutExpired,
            ):
                if action not in (
                    "setup",
                    "help",
                    "session-default",
                    "session-default-show",
                    "session-default-reset",
                ):
                    manage.diagnostic()
                raise
        finally:
            for key, value in env_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def create_world(root, name, assume_yes):
    """Create a new world directory and start the server when needed."""
    if (
        not name
        or name != name.strip()
        or "\x00" in name
        or name in (".", "..")
        or Path(name).name != name
    ):
        raise RuntimeError(tr("invalid_world_name"))
    destination = root / "data" / "worlds" / name
    if destination.exists():
        raise RuntimeError(
            tr("this_world_already_exists_use_bedrock_family_world_use")
        )
    with project_context(root):
        manage.config_check()
        manage.docker_start()
        if manage.running():
            confirm(
                "creating_this_world_will_restart_the_running_server_continue",
                assume_yes,
            )
        with manage.lock("maintenance"):
            if destination.exists():
                raise RuntimeError(tr("this_world_already_exists"))
            manage.env_update({"LEVEL_NAME": name})
            manage.up()


def execute(args, parser):
    """Execute a parsed command against the selected project directory."""
    if args.command == "help":
        parser.print_help()
        return None
    if args.command == "init":
        return initialize(args.directory or args.project_dir)

    root = args.project_dir.expanduser().resolve()
    if args.command == "doctor":
        invoke(root, "doctor")
        return root
    if not (root / "compose.yaml").is_file():
        raise RuntimeError(
            tr(
                "no_server_found_in_this_folder_initialize_it_with_bedrock_family_init"
            )
        )

    if args.command == "setup":
        if not args.accept_eula:
            print(tr("read_the_minecraft_terms_https_www_minecraft_net_eula"))
            if not sys.stdin.isatty():
                raise RuntimeError(
                    tr("explicitly_accept_the_terms_with_accept_eula")
                )
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
            invoke(
                root,
                {
                    "start": "up",
                    "stop": "stop",
                    "restart": "restart",
                    "down": "down",
                    "status": "status",
                }[args.server_command],
            )
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
            invoke(
                root,
                {
                    "status": "session-status",
                    "cancel": "session-cancel",
                    "stop": "session-stop",
                    "logs": "session-logs",
                }[args.session_command],
            )
    elif args.command == "players":
        if args.players_command == "list":
            invoke(root, "players")
        elif args.players_command == "xuids":
            invoke(root, "xuids")
        else:
            invoke(root, "gamemode-all", MODE=args.mode)
    elif args.command == "access":
        if args.access_command == "disable" and not args.confirm:
            raise RuntimeError(
                tr("this_opens_server_access_confirm_with_confirm")
            )
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
            print(
                tr(
                    "usual_end_time_time",
                    time=manage.load(root / "family-settings.json", {}).get(
                        "stop_at", "19:00"
                    ),
                )
            )
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
                parser.error(
                    tr("settings_set_sleep_requires_a_percentage_from_0_to_100")
                )
            if args.name == "sleep-one" and args.value is not None:
                parser.error(tr("settings_set_sleep_one_does_not_take_a_value"))
            if args.name not in ("sleep", "sleep-one") and args.value is None:
                parser.error(
                    tr("settings_set_name_requires_a_value", name=args.name)
                )
            if args.name != "sleep-one":
                key = (
                    "TIME"
                    if args.name == "finish-time"
                    else "PERCENT"
                    if args.name == "sleep"
                    else "VALUE"
                    if args.name in ("cheats", "keep-inventory")
                    else "LEVEL"
                    if args.name == "difficulty"
                    else "MODE"
                )
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
                raise RuntimeError(
                    tr("restoring_replaces_current_builds_add_confirm")
                )
            archive = (
                args.archive
                if args.archive.is_absolute()
                else root / args.archive
            )
            invoke(root, "restore", FILE=str(archive), CONFIRM="yes")
    elif args.command == "update":
        invoke(root, "update-server" if args.server else "update")
    elif args.command == "version":
        invoke(root, "version-pin" if args.version_command == "pin" else "pull")
    elif args.command == "open":
        action = {
            "data": "open-data",
            "backups": "open-backups",
            "settings": "edit",
            "network": "edit-env",
            "access": "allowlist-edit",
        }[args.target]
        invoke(root, action)
    else:
        parser.error("Commande non reconnue.")
    return root


def main(argv=None):
    """Run the Bedrock Family CLI entry point with the given arguments."""
    argv = sys.argv[1:] if argv is None else argv
    language = language_from_args(argv)
    set_language(language)
    os.environ["BEDROCK_FAMILY_LANGUAGE"] = language
    parser = build_parser(language)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        execute(args, parser)
        return 0
    except KeyboardInterrupt:
        print(
            tr("interrupted_server_not_stopped_automatically"), file=sys.stderr
        )
        return 130
    except (
        RuntimeError,
        OSError,
        ValueError,
        KeyError,
        tarfile.TarError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(tr("error_message", message=str(exc)), file=sys.stderr)
        return 1
