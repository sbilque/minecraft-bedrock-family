#!/usr/bin/env python3
"""Minecraft Bedrock family server manager. Python 3.9+, macOS, standard library."""

import contextlib
import datetime as dt
import fcntl
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import unicodedata
import uuid
from pathlib import Path

from .i18n import current_language, tr

ROOT = Path(
    os.getenv("BEDROCK_FAMILY_HOME", Path(__file__).resolve().parents[1])
).resolve()
GAME_DEFAULTS = {
    "cheats": True,
    "keep_inventory": True,
    "difficulty": "easy",
    "sleep_percent": 0,
    "gamemode": "survival",
}
STEPS = [
    (900, "15 minutes"),
    (300, "5 minutes"),
    (60, "1 minute"),
    (30, "30 secondes"),
]
ACTIVE = ("starting", "scheduled", "stopping")
PUBLIC_ACTIONS = (
    "help",
    "setup",
    "check",
    "config",
    "docker-start",
    "doctor",
    "up",
    "start",
    "apply",
    "stop",
    "down",
    "restart",
    "status",
    "logs",
    "logs-once",
    "console",
    "players",
    "xuids",
    "backup",
    "backups",
    "restore",
    "open-backups",
    "open-data",
    "edit",
    "edit-env",
    "pull",
    "update",
    "update-server",
    "version-pin",
    "allowlist-preview",
    "allowlist-sync",
    "allowlist-show",
    "allowlist-enable",
    "allowlist-disable",
    "allowlist-remove",
    "allowlist-edit",
    "allowlist-reload",
    "session",
    "session-status",
    "session-cancel",
    "session-stop",
    "session-logs",
    "session-default",
    "session-default-show",
    "session-default-reset",
    "worlds",
    "world-default",
    "cheats",
    "keep-inventory",
    "difficulty",
    "sleep",
    "sleep-one",
    "gamemode",
    "gamemode-all",
    "game-show",
    "game-apply",
    "game-defaults",
)


def print_localized_message(text, **values):
    """Print a localized message to standard output."""
    print(tr(text, **values), flush=True)


def write_atomic_file(path, value, json_mode=True):
    """Write JSON or text data to disk without corrupting the file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if json_mode
        else value,
        encoding="utf-8",
    )
    os.replace(str(temp), str(path))


def read_json_file(path, default=None):
    """Load a JSON file from disk or return the fallback when absent."""
    path = Path(path)
    return (
        json.loads(path.read_text(encoding="utf-8"))
        if path.exists()
        else default
    )


@contextlib.contextmanager
def lock(name, wait=False):
    """Protect a project-scoped resource with a file lock."""
    folder = ROOT / ".state"
    folder.mkdir(exist_ok=True)
    with (folder / (name + ".lock")).open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        except BlockingIOError as exc:
            raise RuntimeError(
                "Une autre operation est en cours. Attendre sa fin."
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def raw(args, check=True, timeout=60, env=None):
    """Run a subprocess and raise on failure if requested."""
    process = subprocess.run(
        args,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
        check=False,
    )
    if check and process.returncode:
        raise RuntimeError(
            (process.stderr or process.stdout).strip() or tr("command_failed")
        )
    return process


def normalize_choice_text(value):
    """Normalize a user-facing value for comparison and validation."""
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", value.strip().casefold())
        if not unicodedata.combining(c)
    )


def parse_boolean_value(value):
    """Parse a boolean-like value supplied by the user."""
    normalized = normalize_choice_text(value)
    if normalized in ("on", "true", "oui", "1", "active"):
        return True
    if normalized in ("off", "false", "non", "0", "desactive"):
        return False
    raise RuntimeError(tr("choose_value_on_or_value_off"))


def normalize_difficulty(value):
    """Normalize a difficulty alias to a Minecraft difficulty key."""
    aliases = {
        "facile": "easy",
        "easy": "easy",
        "paisible": "peaceful",
        "peaceful": "peaceful",
        "normale": "normal",
        "normal": "normal",
        "difficile": "hard",
        "hard": "hard",
    }
    normalized = normalize_choice_text(value)
    if normalized not in aliases:
        raise RuntimeError(tr("level_easy_peaceful_normal_or_hard"))
    return aliases[normalized]


def normalize_gamemode(value):
    """Normalize a mode alias to a Minecraft game mode identifier."""
    aliases = {
        "survie": "survival",
        "survival": "survival",
        "creatif": "creative",
        "creative": "creative",
        "aventure": "adventure",
        "adventure": "adventure",
    }
    normalized = normalize_choice_text(value)
    if normalized not in aliases:
        raise RuntimeError(tr("mode_survival_creative_or_adventure"))
    return aliases[normalized]


def parse_percentage(value):
    """Validate that a percentage value falls between 0 and 100."""
    if not re.fullmatch(r"\d{1,3}", value or "") or not 0 <= int(value) <= 100:
        raise RuntimeError(tr("percent_must_be_an_integer_from_0_to_100"))
    return int(value)


def parse_clock(value):
    """Validate and normalize a time expressed as HH:MM."""
    if not re.fullmatch(r"\d{2}:\d{2}", value or ""):
        raise RuntimeError(
            tr("expected_a_time_in_hh_mm_format_for_example_20_30")
        )
    hour, minute = map(int, value.split(":"))
    if hour > 23 or minute > 59:
        raise RuntimeError(tr("invalid_time_use_00_00_through_23_59"))
    return value


def parse_duration(value):
    """Parse a compact duration into a number of minutes.

    Accepts values such as ``45m``, ``1h``, ``1h30m`` or a bare number of
    minutes (``45``). Returns a positive integer, otherwise raises
    ``ValueError``.
    """
    text = str(value or "").strip().lower().replace(" ", "")
    if not text:
        raise ValueError(tr("duration_cannot_be_empty"))
    segments = re.findall(r"(\d+(?:\.\d+)?)\s*(h|m)?", text)
    if not re.fullmatch(r"(?:\d+(?:\.\d+)?\s*(?:h|m)?)+", text):
        raise ValueError(tr("invalid_duration_format"))
    total = 0
    seen_unit = set()
    for amount, unit in segments:
        number = int(float(amount))
        if not unit:
            if seen_unit:
                raise ValueError(tr("invalid_duration_format"))
        else:
            if unit in seen_unit:
                raise ValueError(tr("invalid_duration_format"))
            seen_unit.add(unit)
            number *= 60 if unit == "h" else 1
        total += number
    if total <= 0:
        raise ValueError(tr("duration_must_be_a_positive_amount_of_time"))
    return int(total)


def relative_deadline(minutes, now=None):
    """Return the timezone-aware deadline ``minutes`` from ``now``."""
    now = now or dt.datetime.now().astimezone()
    return now + dt.timedelta(minutes=minutes)


def deadline(value, now=None):
    """Return the next scheduled shutdown time for a clock or ISO value.

    A clock string (``HH:MM``) schedules the next matching time in the future.
    An ISO-8601 datetime string (containing ``T``) is used as-is. Both return a
    timezone-aware ``datetime``.
    """
    now = now or dt.datetime.now().astimezone()
    text = str(value or "").strip()
    if "T" in text.replace("+", " +", 1) or text.endswith("z"):
        try:
            return dt.datetime.fromisoformat(text)
        except ValueError as exc:
            raise RuntimeError(
                tr("invalid_iso_or_clock_time_hh_mm_or_iso_8601")
            ) from exc
    clock(text)
    h, m = map(int, text.split(":"))
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        raise RuntimeError(tr("that_time_has_already_passed_today_choose_a_future_time"))
    return target


def validate_game(value):
    """Validate and normalize the stored game configuration."""
    if not isinstance(value, dict):
        raise RuntimeError(tr("game_settings_must_be_a_json_object"))
    cfg = dict(GAME_DEFAULTS)
    cfg.update(value)
    for key in ("cheats", "keep_inventory"):
        if not isinstance(cfg[key], bool):
            raise RuntimeError(tr("key_must_be_true_or_false", key=key))
    cfg["difficulty"] = normalize_difficulty(str(cfg["difficulty"]))
    cfg["gamemode"] = normalize_gamemode(str(cfg["gamemode"]))
    cfg["sleep_percent"] = parse_percentage(str(cfg["sleep_percent"]))
    return cfg


def load_family_settings():
    """Return the effective settings with the validated game configuration."""
    config = read_json_file(ROOT / "family-settings.json", {})
    if not isinstance(config, dict):
        raise RuntimeError(tr("invalid_family_settings"))
    game = (
        config["game"]
        if "game" in config
        else read_json_file(ROOT / "game-settings.json", {})
    )
    return {
        "stop_at": parse_clock(config.get("stop_at", "19:00")),
        "game": validate_game(game),
    }


say = print_localized_message
atomic = write_atomic_file
load = read_json_file
word = normalize_choice_text
boolean = parse_boolean_value
difficulty = normalize_difficulty
gamemode = normalize_gamemode
percentage = parse_percentage
clock = parse_clock
settings = load_family_settings


def worlds():
    current = (
        env_read().get("LEVEL_NAME", "Famille")
        if (ROOT / ".env").exists()
        else "Famille"
    ) or "Famille"
    folder = ROOT / "data" / "worlds"
    entries = (
        sorted(
            (p.name for p in folder.iterdir() if p.is_dir()), key=str.casefold
        )
        if folder.is_dir()
        else []
    )
    say(
        "default_world_name"
        if current in entries
        else "default_world_name_not_created_yet",
        name=current,
    )
    if not entries:
        say("no_worlds_found_in_data_worlds")
    else:
        say("available_worlds")
        for name in entries:
            say((" * " if name == current else "   ") + name)


def world_default():
    name = os.getenv("LEVEL", "")
    if (
        not name
        or name != name.strip()
        or "\x00" in name
        or name in (".", "..")
        or Path(name).name != name
    ):
        raise RuntimeError(tr("provide_the_exact_world_name_with_level_name"))
    with lock("maintenance"):
        if not (ROOT / "data" / "worlds" / name).is_dir():
            raise RuntimeError(
                tr(
                    "world_not_found_name_use_bedrock_family_world_list",
                    name=name,
                )
            )
        env_read()
        env_update({"LEVEL_NAME": name})
    say("default_world_name", name=name)
    say(
        "the_selection_will_apply_the_next_time_bedrock_family_server_start_runs"
    )


def update_settings(stop_at=None, game=None):
    with lock("settings", True):
        cfg = settings()
        if stop_at is not None:
            cfg["stop_at"] = clock(stop_at)
        if game is not None:
            cfg["game"] = validate_game(game)
        atomic(ROOT / "family-settings.json", cfg)
    return cfg


def env_read():
    p = ROOT / ".env"
    if not p.exists():
        raise RuntimeError(
            tr("initialize_the_folder_with_bedrock_family_init_then_configure_it_with_bedrock_family_setup")
        )
    result = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def env_update(values):
    p = ROOT / ".env"
    lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
    remaining = dict(values)
    result = []
    for line in lines:
        k = line.split("=", 1)[0].strip()
        if "=" in line and k in values:
            if k in remaining:
                result.append(k + "=" + str(remaining.pop(k)))
        else:
            result.append(line)
    result.extend(k + "=" + str(v) for k, v in remaining.items())
    atomic(p, "\n".join(result) + "\n", False)


def ipv4(value):
    try:
        ip = ipaddress.IPv4Address(value)
    except ValueError:
        raise RuntimeError(tr("use_the_mac_s_local_ipv4_address"))
    if ip.is_loopback or ip.is_unspecified or ip.is_multicast:
        raise RuntimeError(tr("expected_a_local_mac_address_not_localhost"))
    return str(ip)


def ipv4_candidates():
    ports = raw(["networksetup", "-listallhardwareports"]).stdout
    types = {}
    port = None
    for line in ports.splitlines():
        if line.startswith("Hardware Port: "):
            port = line.split(":", 1)[1].strip()
        elif line.startswith("Device: ") and port:
            types[line.split(":", 1)[1].strip()] = port
            port = None
    candidates = []
    seen = set()
    interface = None
    active = False
    for line in raw(["ifconfig", "-a"]).stdout.splitlines():
        header = re.match(r"^(\S+): flags=\d+<([^>]*)>", line)
        if header:
            interface = header.group(1)
            active = "UP" in header.group(2).split(",")
            continue
        address = re.match(r"\s+inet\s+(\S+)", line)
        if interface and active and address:
            try:
                ip = ipaddress.IPv4Address(address.group(1))
            except ValueError:
                continue
            if (
                ip.is_loopback
                or ip.is_unspecified
                or ip.is_multicast
                or ip.is_link_local
            ):
                continue
            key = (interface, str(ip))
            if key not in seen:
                seen.add(key)
                kind = types.get(interface)
                if not kind:
                    if interface.startswith("utun"):
                        kind = "VPN"
                    elif interface.startswith(("bridge", "vmnet", "vmenet")):
                        kind = "interface virtuelle"
                    elif interface.startswith("awdl"):
                        kind = "Apple Wireless Direct Link"
                    elif interface.startswith("en"):
                        kind = "Ethernet ou Wi-Fi"
                    else:
                        kind = "interface " + interface
                candidates.append(
                    {"ip": str(ip), "interface": interface, "type": kind}
                )
    return candidates


def select_lan_ip(configured):
    if configured:
        return ipv4(configured.strip())
    candidates = ipv4_candidates()
    if not candidates:
        raise RuntimeError(
            tr("no_usable_local_ipv4_address_detected_check_the_mac_s_network_or_rerun_with_bedrock_family_setup_ip_address")
        )
    if len(candidates) == 1:
        candidate = candidates[0]
        say("detected_ipv4_address_ip_type_interface", **candidate)
        return candidate["ip"]
    say("several_ipv4_addresses_were_detected")
    for index, candidate in enumerate(candidates, 1):
        say("index_type_interface_ip", index=index, **candidate)
    if not sys.stdin.isatty():
        raise RuntimeError(
            tr("choose_an_address_with_bedrock_family_setup_ip_address")
        )
    try:
        choice = input(tr("select_the_number_of_the_connection")).strip()
    except EOFError:
        raise RuntimeError(
            tr("selection_interrupted_rerun_bedrock_family_setup_in_an_interactive_terminal")
        )
    if not choice.isdigit() or not 1 <= int(choice) <= len(candidates):
        raise RuntimeError(
            tr("invalid_selection_rerun_bedrock_family_setup_and_enter_a_displayed_number")
        )
    return candidates[int(choice) - 1]["ip"]


def config_check():
    cfg = env_read()
    ipv4(cfg.get("LAN_IP", ""))
    settings()
    if cfg.get("EULA", "").upper() != "TRUE":
        raise RuntimeError(
            tr("read_the_minecraft_terms_and_accept_them_with_bedrock_family_setup_accept_eula")
        )
    return cfg


def game_overlay(cfg):
    return {
        "services": {
            "bedrock": {
                "environment": {
                    "ALLOW_CHEATS": str(cfg["cheats"]).lower(),
                    "DIFFICULTY": cfg["difficulty"],
                    "GAMEMODE": cfg["gamemode"],
                    "FORCE_GAMEMODE": "false",
                }
            }
        }
    }


def ensure_game_overlay():
    atomic(ROOT / "compose.game.json", game_overlay(settings()["game"]))


def compose_env(latest=False):
    env = dict(os.environ)
    for k in ("LAN_IP", "EULA", "BEDROCK_VERSION", "LEVEL_NAME"):
        env.pop(k, None)
    if latest:
        env["BEDROCK_VERSION"] = "LATEST"
    return env


def dcargs():
    args = [
        "docker",
        "compose",
        "--project-directory",
        str(ROOT),
        "--env-file",
        str(ROOT / ".env"),
        "-f",
        str(ROOT / "compose.yaml"),
    ]
    for name in ("compose.allowlist.json", "compose.game.json"):
        if (ROOT / name).exists():
            args += ["-f", str(ROOT / name)]
    return args


def dc(args, echo=False, timeout=240, latest=False):
    p = raw(dcargs() + args, timeout=timeout, env=compose_env(latest))
    if echo:
        if p.stdout:
            say(p.stdout.rstrip())
        if p.stderr:
            say(p.stderr.rstrip())
    return p.stdout


def docker_reachable():
    try:
        return raw(["docker", "info"], False, timeout=5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def docker_start():
    if not shutil.which("docker"):
        raise RuntimeError(tr("install_and_open_docker_desktop"))
    if not docker_reachable():
        raw(["/usr/bin/open", "-a", "Docker"], timeout=15)
        end = time.monotonic() + int(os.getenv("TIMEOUT", "120"))
        while not docker_reachable():
            if time.monotonic() > end:
                raise RuntimeError(
                    tr("docker_is_not_responding_open_docker_desktop_then_run_bedrock_family_doctor")
                )
            time.sleep(2)
    raw(["docker", "compose", "version"])


def diagnostic():
    say("leading_newline_recent_docker_messages_up_to_80_lines")
    try:
        p = raw(
            dcargs() + ["logs", "--no-color", "--tail=80", "bedrock"],
            False,
            timeout=20,
            env=compose_env(),
        )
        say((p.stdout + p.stderr).strip() or "no_messages_available")
        if p.returncode:
            say("check_docker_desktop_and_run_bedrock_family_doctor")
    except Exception as exc:
        say("messages_unavailable_error", error=exc)


def running():
    return dc(["ps", "--status", "running", "-q", "bedrock"]).strip()


def stamp():
    return (
        dt.datetime.now(dt.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def logs(cid, since=None):
    p = raw(
        ["docker", "logs"] + (["--since", since] if since else []) + [cid],
        timeout=20,
    )
    return p.stdout + p.stderr


def clean(line):
    line = re.sub(r"\x1b\[[0-9;]*m", "", line)
    line = re.sub(r"^\S+Z\s+", "", line)
    return re.sub(r"^(?:\[[^\]]*\]\s*)+", "", line).strip()


def parse_online(text):
    lines = [clean(x) for x in text.splitlines()]
    found = None
    for i, line in enumerate(lines):
        m = re.match(
            r"There are\s+(\d+)\s*/\s*\d+\s+players online\s*:?\s*(.*)",
            line,
            re.I,
        )
        if not m:
            continue
        n = int(m.group(1))
        if n == 0:
            found = []
            continue
        names = m.group(2).strip() or (
            lines[i + 1] if i + 1 < len(lines) else ""
        )
        values = [x.strip() for x in names.split(",") if x.strip()]
        if len(values) == n:
            found = values
    return found


def send(command, cid=None, reload=False):
    cid = cid or running()
    if not cid:
        raise RuntimeError(
            tr("server_is_stopped_run_bedrock_family_server_start")
        )
    since = stamp()
    dc(["exec", "-T", "bedrock", "send-command", command], timeout=15)
    end = time.monotonic() + 6
    text = ""
    while time.monotonic() < end:
        time.sleep(0.5)
        text = logs(cid, since)
        if reload:
            if re.search(
                r"(allowlist|whitelist).*reload|reload.*(allowlist|whitelist)",
                text,
                re.I,
            ):
                break
        elif text.strip():
            break
    if text.strip():
        say(text.rstrip())
    if re.search(
        r"syntax error|unknown command|command not found|failed to|\bERROR\b|permission denied",
        text,
        re.I,
    ):
        raise RuntimeError(
            tr("the_game_reported_an_error_already_saved_changes_were_not_rolled_back")
        )
    if reload and not re.search(
        r"(allowlist|whitelist).*reload|reload.*(allowlist|whitelist)",
        text,
        re.I,
    ):
        raise RuntimeError(
            tr("list_saved_but_reload_was_not_confirmed_check_the_logs_or_run_bedrock_family_server_restart")
        )
    if not text.strip():
        say(
            "command_sent_without_a_confirmed_response_check_bedrock_family_server_logs_once"
        )
    return text


def apply_game_rules():
    cfg = settings()["game"]
    checks = [
        (
            "difficulty " + cfg["difficulty"],
            r"\bdifficulty\b.*\b" + cfg["difficulty"] + r"\b",
        ),
        (
            "gamerule keepinventory " + str(cfg["keep_inventory"]).lower(),
            r"\bkeepinventory\b.*\b"
            + str(cfg["keep_inventory"]).lower()
            + r"\b",
        ),
        (
            "gamerule playerssleepingpercentage " + str(cfg["sleep_percent"]),
            r"\bplayerssleepingpercentage\b.*\b"
            + str(cfg["sleep_percent"])
            + r"\b",
        ),
    ]
    for command, pattern in checks:
        if not re.search(pattern, send(command), re.I):
            raise RuntimeError(
                tr(
                    "rule_not_confirmed_command_check_bedrock_family_server_logs_once",
                    command=command,
                )
            )
    say("difficulty_inventory_and_sleep_settings_were_confirmed_by_the_server")


def wait_ready():
    cid = running()
    if not cid:
        raise RuntimeError(tr("the_container_is_not_running"))
    started = raw(
        ["docker", "inspect", "--format", "{{.State.StartedAt}}", cid]
    ).stdout.strip()
    end = time.monotonic() + int(os.getenv("READY_TIMEOUT", "180"))
    while time.monotonic() < end:
        if re.search(r"\bServer started\b", logs(cid, started), re.I):
            apply_game_rules()
            return
        if not running():
            raise RuntimeError(tr("the_server_stopped_while_starting"))
        time.sleep(2)
    raise RuntimeError(
        tr("startup_was_not_confirmed_the_container_may_still_be_running_check_bedrock_family_server_logs_once")
    )


def up(latest=False):
    cfg = env_read()
    if (
        cfg.get("BEDROCK_VERSION", "LATEST") == "EXISTING"
        and not (ROOT / "data" / "bedrock_server").is_file()
    ):
        say("first_download_no_existing_server_version_using_latest")
        env_update({"BEDROCK_VERSION": "LATEST"})
    ensure_game_overlay()
    dc(["up", "-d", "bedrock"], True, latest=latest)
    wait_ready()
    say("server_is_ready")


def stop():
    dc(["stop", "bedrock"], True)
    if running():
        raise RuntimeError(tr("server_is_still_running_cold_backup_refused"))


def connected():
    cid = running()
    if not cid:
        raise RuntimeError(tr("server_is_stopped_run_bedrock_family_server_start"))
    since = stamp()
    dc(["exec", "-T", "bedrock", "send-command", "list"], timeout=15)
    names = None
    for _ in range(24):
        time.sleep(0.5)
        names = parse_online(logs(cid, since))
        if names is not None:
            break
    if names is None:
        raise RuntimeError(
            tr("current_player_list_was_not_recognized_no_players_will_be_guessed")
        )
    text = "\n".join(clean(x) for x in logs(cid).splitlines())
    ids = {
        m.group(1).strip().casefold(): m.group(2)
        for m in re.finditer(
            r"^Player connected:\s*(.*?),\s*xuid:\s*(\d+)", text, re.I | re.M
        )
    }
    result = []
    for name in names:
        if name.casefold() not in ids:
            raise RuntimeError(
                tr(
                    "missing_xuid_for_name_leave_and_rejoin_the_world",
                    name=name,
                )
            )
        result.append(
            {
                "name": name,
                "xuid": ids[name.casefold()],
                "ignoresPlayerLimit": False,
            }
        )
    return result


def validate_entries(entries):
    if not isinstance(entries, list):
        raise RuntimeError(tr("the_list_must_start_with_and_end_with"))
    result = []
    for e in entries:
        if (
            not isinstance(e, dict)
            or not isinstance(e.get("name"), str)
            or not e["name"].strip()
        ):
            raise RuntimeError(tr("every_player_must_have_a_name"))
        if any(x in e["name"] for x in ":,\n\r"):
            raise RuntimeError(tr("unsupported_name_name", name=e["name"]))
        if not isinstance(e.get("xuid"), str) or not e["xuid"].isdigit():
            raise RuntimeError(
                tr("expected_the_xuid_in_quotes_name", name=e["name"])
            )
        if "ignoresPlayerLimit" in e and not isinstance(
            e["ignoresPlayerLimit"], bool
        ):
            raise RuntimeError(tr("ignoresplayerlimit_must_be_true_or_false"))
        result.append(dict(e))
    return result


def merge_entries(entries):
    result = []
    for e in validate_entries(entries):
        i = next(
            (
                i
                for i, x in enumerate(result)
                if x["name"].casefold() == e["name"].casefold()
                or x["xuid"] == e["xuid"]
            ),
            None,
        )
        if i is None:
            result.append(e)
        else:
            result[i].update(e)
    return result


def access(action):
    path = ROOT / "data" / "allowlist.json"
    other = ROOT / "compose.allowlist.json"
    overlay = load(other, {"services": {"bedrock": {"environment": {}}}})
    env = (
        overlay.setdefault("services", {})
        .setdefault("bedrock", {})
        .setdefault("environment", {})
    )
    configured = []
    if action != "reload":
        for value in re.split(r"[,\n]", env.get("ALLOW_LIST_USERS", "")):
            if not value.strip():
                continue
            name, sep, xuid = value.strip().rpartition(":")
            if not sep:
                raise RuntimeError("ALLOW_LIST_USERS invalide.")
            configured.append({"name": name, "xuid": xuid})
    entries = merge_entries(configured + validate_entries(load(path, [])))
    if action == "show":
        for e in entries:
            say("name_xuid", **e)
        if not entries:
            say("no_players_enrolled")
        return
    if action in ("preview", "sync"):
        current = connected()
        say("players_currently_online")
        for e in current:
            say("name_xuid", **e)
        if not current:
            say("no_players_online_no_changes_made")
            return
        if action == "preview":
            say("no_changes_made_to_add_players_run_bedrock_family_access_sync")
            return
        entries = merge_entries(entries + current)
    if action == "remove":
        name = os.getenv("PLAYER", "").strip()
        if not name:
            tr("expected_player_player_name")
        matches = [
            e
            for e in entries
            if e["name"].casefold() == name.casefold() or e["xuid"] == name
        ]
        if not matches:
            raise RuntimeError(
                tr("player_not_found_see_bedrock_family_access_show")
            )
        entries = [e for e in entries if e not in matches]
    if action == "enable" and not entries:
        raise RuntimeError(
            tr("the_list_is_empty_enroll_family_members_before_restricting_access")
        )
    if action == "disable" and os.getenv("CONFIRM") != "yes":
        raise RuntimeError(tr("confirm_with_confirm"))
    b = (
        ROOT
        / "backups"
        / ("allowlist-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    )
    b.mkdir(parents=True)
    for f in (path, other):
        if f.exists():
            shutil.copy2(str(f), str(b / f.name))
    env["ALLOW_LIST_USERS"] = "\n".join(
        e["name"] + ":" + e["xuid"] for e in entries
    )
    if action in ("enable", "disable"):
        env["ALLOW_LIST"] = "true" if action == "enable" else "false"
    atomic(other, overlay)
    atomic(path, entries)
    say("list_saved_previous_copy_backup", backup=b)
    if action in ("enable", "disable"):
        up()
    elif running():
        send("allowlist reload", reload=True)
    else:
        say("list_is_ready_for_the_next_startup")
    if action == "remove":
        say(
            "builds_are_preserved_if_the_player_is_still_online_run_bedrock_family_server_restart_do_not_re_enroll_them_with_sync"
        )


def archive_filter(info):
    if info.issym() or info.islnk():
        raise RuntimeError(
            tr("a_link_was_found_in_the_data_inspect_it_before_creating_a_backup")
        )
    return info


def backup(restart=True, already_stopped=False):
    if not (ROOT / "data").is_dir():
        raise RuntimeError(tr("no_world_found_start_the_server_once_first"))
    active = bool(running())
    if active and already_stopped:
        raise RuntimeError(tr("the_server_restarted_before_the_backup"))
    if active:
        stop()
    folder = ROOT / "backups"
    folder.mkdir(exist_ok=True)
    dest = folder / (
        "minecraft-"
        + dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        + ".tar.gz"
    )
    part = dest.with_suffix(dest.suffix + ".partial")
    try:
        with tarfile.open(part, "w:gz") as tar:
            for name in (
                "data",
                ".env",
                "compose.yaml",
                "compose.allowlist.json",
                "compose.game.json",
                "family-settings.json",
            ):
                if (ROOT / name).exists():
                    tar.add(ROOT / name, arcname=name, filter=archive_filter)
        with tarfile.open(part, "r:gz") as tar:
            for member in tar:
                if member.isfile():
                    with tar.extractfile(member) as stream:
                        while stream.read(1024 * 1024):
                            pass
        os.replace(str(part), str(dest))
        say("backup_verified_path", path=dest)
    finally:
        if active and restart:
            dc(["start", "bedrock"], True)


def safe_members(tar):
    result = []
    for m in tar.getmembers():
        path = Path(m.name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or m.issym()
            or m.islnk()
            or not (m.isdir() or m.isfile())
        ):
            raise RuntimeError(tr("unsafe_archive_restore_refused"))
        if path.parts and path.parts[0] == "data":
            result.append(m)
    if not result:
        raise RuntimeError(tr("archive_does_not_contain_a_data_folder"))
    return result


def restore():
    name = os.getenv("FILE", "")
    if os.getenv("CONFIRM") != "yes" or not name:
        raise RuntimeError(
            tr("restore_with_bedrock_family_backup_restore_archive_confirm")
        )
    file = Path(name)
    file = file if file.is_absolute() else ROOT / file
    with tarfile.open(file, "r:gz") as tar:
        members = safe_members(tar)
        old_list = validate_entries(load(ROOT / "data" / "allowlist.json", []))
        cancel_session(True)
        stop()
        if (ROOT / "data").exists():
            (ROOT / "data").rename(
                ROOT
                / (
                    "data-avant-restauration-"
                    + dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                )
            )
        for member in members:
            target = ROOT / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with (
                    tar.extractfile(member) as stream,
                    target.open("wb") as dest,
                ):
                    shutil.copyfileobj(stream, dest, 1024 * 1024)
        atomic(ROOT / "data" / "allowlist.json", old_list)
    up()
    say("world_restored_current_settings_and_permissions_were_preserved")


def state_path():
    return ROOT / ".state" / "session.json"


def state():
    return load(state_path(), {})


def alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def cancel_session(quiet=False):
    with lock("session", True):
        s = state()
        if s.get("status") == "stopping":
            raise RuntimeError(tr("shutdown_is_in_progress_wait_for_it_to_finish"))
        if s.get("status") not in ACTIVE:
            if not quiet:
                say("no_active_schedule")
            return
        s["status"] = "cancelled"
        atomic(state_path(), s)
    if not quiet:
        say("schedule_cancelled_the_server_remains_running")


def start_session():
    target = deadline(os.getenv("STOP_AT", "") or settings()["stop_at"])
    with lock("session", True):
        old = state()
        if old.get("status") == "stopping":
            raise RuntimeError(
                tr("shutdown_is_in_progress_check_bedrock_family_session_logs")
            )
        if old.get("status") in ACTIVE and alive(old.get("pid")):
            raise RuntimeError(tr("cancel_the_active_schedule_before_replacing_it"))
        token = uuid.uuid4().hex
        s = {
            "token": token,
            "pid": os.getpid(),
            "status": "starting",
            "deadline": target.isoformat(),
        }
        atomic(state_path(), s)
    try:
        up()
        if target.timestamp() <= time.time():
            stop()
            backup(False, True)
            s["status"] = "stopped"
            atomic(state_path(), s)
            return
        with lock("session", True):
            if state().get("status") == "cancelled":
                say("schedule_cancelled_during_startup")
                return
            folder = ROOT / "logs"
            folder.mkdir(exist_ok=True)
            with (folder / "session.log").open("a", encoding="utf-8") as stream:
                p = subprocess.Popen(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "_session-worker",
                        token,
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    close_fds=True,
                )
            s.update(status="scheduled", pid=p.pid)
            atomic(state_path(), s)
        say(
            "server_ready_today_s_end_time_is_time_keep_the_mac_and_docker_running",
            time=target.strftime("%H:%M"),
        )
    except Exception as exc:
        with lock("session", True):
            s = state()
            if s.get("token") == token and s.get("status") != "cancelled":
                s.update(status="failed", error=str(exc))
                atomic(state_path(), s)
        raise


def notice(text, **values):
    try:
        send("say " + tr(text, **values))
    except Exception as exc:
        say("message_not_confirmed_error", error=exc)


def session_worker(token):
    with lock("session", True):
        s = state()
        if s.get("token") != token or s.get("status") != "scheduled":
            return
    target = dt.datetime.fromisoformat(s["deadline"])
    remaining = target.timestamp() - time.time()
    pending = {n: label for n, label in STEPS if n <= remaining}
    awake = None
    try:
        if Path("/usr/bin/caffeinate").exists():
            awake = subprocess.Popen(
                ["/usr/bin/caffeinate", "-i", "-w", str(os.getpid())],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        say("session_shutdown_at_time", time=target.isoformat())
        initial = True
        while True:
            with lock("session", True):
                s = state()
                if s.get("token") != token or s.get("status") != "scheduled":
                    say("monitoring_cancelled")
                    return
                remaining = target.timestamp() - time.time()
                if remaining <= 0:
                    s["status"] = "stopping"
                    atomic(state_path(), s)
                    break
            if initial:
                initial = False
                notice(
                    "finish_the_game_at_time",
                    time=target.strftime("%H:%M"),
                )
            actual = target.timestamp() - time.time()
            due = [n for n in pending if actual <= n]
            if due and actual > 0:
                n = min(due)
                label = pending[n]
                for x in due:
                    del pending[x]
                if abs(actual - n) > 10:
                    label = "environ " + str(max(1, int(actual))) + " secondes"
                notice(
                    "finish_the_game_in_ellipsis",
                    label=label,
                )
            time.sleep(min(1, max(0.05, target.timestamp() - time.time())))
        with lock("maintenance", True):
            config_check()
            docker_start()
            stop()
            backup(False, True)
        with lock("session", True):
            s = state()
            s.update(status="stopped", finished_at=stamp())
            atomic(state_path(), s)
        say("server_stopped_and_backup_completed_it_remains_off")
    except Exception as exc:
        say("failure_error", error=exc)
        diagnostic()
        with lock("session", True):
            s = state()
            if s.get("token") == token:
                s.update(status="failed", error=str(exc))
                atomic(state_path(), s)
    finally:
        if awake is not None:
            awake.terminate()
            try:
                awake.wait(timeout=5)
            except subprocess.TimeoutExpired:
                awake.kill()


def show_game(cfg):
    say("cheats_value", value=tr("enabled" if cfg["cheats"] else "disabled"))
    if cfg["cheats"]:
        say(
            "warning_cheats_disable_world_achievements_turning_them_off_later_does_not_guarantee_achievements_will_return"
        )
    say(
        "keep_inventory_value",
        value=tr("yes" if cfg["keep_inventory"] else "no"),
    )
    say(
        "difficulty_value",
        value=tr(
            {
                "easy": "easy",
                "peaceful": "peaceful",
                "normal": "normal",
                "hard": "hard",
            }[cfg["difficulty"]]
        ),
    )
    say(
        "sleep_rule_value",
        value=tr(
            "one_player_is_enough_0"
            if cfg["sleep_percent"] == 0
            else "percent",
            percent=cfg["sleep_percent"],
        ),
    )
    say(
        "default_game_mode_value",
        value=tr(
            {
                "survival": "survival",
                "creative": "creative",
                "adventure": "adventure",
            }[cfg["gamemode"]]
        ),
    )
    say("choices_are_saved_they_are_not_live_world_measurements")


def game_action(action):
    if action == "game-show":
        show_game(settings()["game"])
        return
    with lock("maintenance"):
        cfg = settings()["game"]
        if action == "cheats":
            cfg["cheats"] = boolean(os.getenv("VALUE", ""))
        elif action == "keep-inventory":
            cfg["keep_inventory"] = boolean(os.getenv("VALUE", ""))
        elif action == "difficulty":
            cfg["difficulty"] = difficulty(os.getenv("LEVEL", ""))
        elif action == "sleep":
            cfg["sleep_percent"] = percentage(os.getenv("PERCENT", ""))
        elif action == "sleep-one":
            cfg["sleep_percent"] = 0
        elif action == "gamemode":
            cfg["gamemode"] = gamemode(os.getenv("MODE", ""))
        elif action == "game-defaults":
            cfg = dict(GAME_DEFAULTS)
        elif action == "gamemode-all":
            mode = gamemode(os.getenv("MODE", ""))
            config_check()
            docker_start()
            send("gamemode " + mode + " @a")
            say(
                "command_applies_only_to_online_players_the_default_game_mode_is_unchanged"
            )
            return
        elif action != "game-apply":
            raise RuntimeError("Reglage inconnu.")
        update_settings(game=cfg)
        ensure_game_overlay()
        show_game(cfg)
        if action == "game-apply":
            config_check()
            docker_start()
            up()
        elif docker_reachable() and (ROOT / ".env").exists() and running():
            config_check()
            up()
        else:
            say("choices_are_ready_for_the_next_bedrock_family_server_start")


def setup():
    if os.getenv("EULA", "").upper() != "TRUE":
        raise RuntimeError(
            tr("read_the_minecraft_terms_then_add_eula_true_if_you_agree")
        )
    ip = select_lan_ip(os.getenv("LAN_IP", "").strip())
    with lock("maintenance"):
        values = {"LAN_IP": ip, "EULA": "TRUE"}
        if not (ROOT / ".env").exists():
            values["BEDROCK_VERSION"] = "LATEST"
        env_update(values)
        update_settings()
        ensure_game_overlay()
        for name in ("data", "backups", "logs"):
            (ROOT / name).mkdir(exist_ok=True)
    say(
        "configuration_is_ready_cheats_are_enabled_by_default_disabling_achievements_run_bedrock_family_check_then_bedrock_family_server_start"
    )


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    if action == "_session-worker":
        session_worker(sys.argv[2])
        return
    if action not in PUBLIC_ACTIONS:
        raise RuntimeError("Commande inconnue. Utiliser bedrock-family --help.")
    if action == "help":
        language = current_language()
        say(
            (ROOT / "docs" / language / "commands.txt").read_text(
                encoding="utf-8"
            )
        )
        return
    if action == "setup":
        setup()
        return
    if action == "worlds":
        worlds()
        return
    if action == "world-default":
        world_default()
        return
    if action in (
        "cheats",
        "keep-inventory",
        "difficulty",
        "sleep",
        "sleep-one",
        "gamemode",
        "gamemode-all",
        "game-show",
        "game-apply",
        "game-defaults",
    ):
        game_action(action)
        return
    if action.startswith("session-default"):
        if action == "session-default":
            cfg = update_settings(stop_at=clock(os.getenv("TIME", "")))
        elif action == "session-default-reset":
            cfg = update_settings(stop_at="19:00")
        else:
            cfg = settings()
        say(
            "usual_end_time_time_already_scheduled_games_are_unchanged",
            time=cfg["stop_at"],
        )
        return
    if action == "session-status":
        s = state()
        say("status_status", status=tr(s.get("status", "no_status")))
        say(
            "scheduled_shutdown_deadline",
            deadline=tr(s.get("deadline", "no_deadline")),
        )
        if s.get("status") in ("starting", "scheduled") and not alive(
            s.get("pid")
        ):
            say(
                "warning_schedule_monitoring_is_inactive_schedule_the_game_again"
            )
        if s.get("error"):
            say("error_error", error=s["error"])
        return
    if action == "session-cancel":
        cancel_session()
        return
    if action == "session-logs":
        p = ROOT / "logs" / "session.log"
        say(
            "\n".join(
                p.read_text(encoding="utf-8", errors="replace").splitlines()[
                    -100:
                ]
            )
            if p.exists()
            else "no_messages"
        )
        return
    if action in (
        "edit",
        "edit-env",
        "open-data",
        "open-backups",
        "allowlist-edit",
    ):
        p = (
            ROOT
            / {
                "edit": "compose.yaml",
                "edit-env": ".env",
                "open-data": "data",
                "open-backups": "backups",
                "allowlist-edit": "data/allowlist.json",
            }[action]
        )
        if (
            action == "allowlist-edit"
            and not p.exists()
            and (ROOT / "data").is_dir()
        ):
            atomic(p, [])
        if not p.exists():
            raise RuntimeError(
                tr("file_not_found_and_run_a_first_time")
            )
        raw(
            ["/usr/bin/open"]
            + (
                ["-e"]
                if action in ("edit", "edit-env", "allowlist-edit")
                else []
            )
            + [str(p)]
        )
        return
    if action == "backups":
        for p in sorted((ROOT / "backups").glob("minecraft-*.tar.gz")):
            say(str(p.relative_to(ROOT)))
        return
    if action == "doctor":
        for cmd in (
            ["docker", "context", "ls"],
            ["docker", "info"],
            ["docker", "compose", "version"],
            ["python3", "--version"],
        ):
            try:
                p = raw(cmd, False, timeout=15)
                say(p.stdout + p.stderr)
            except Exception as exc:
                say(str(exc))
        say(
            str(
                {k: v for k, v in os.environ.items() if k.startswith("DOCKER_")}
            )
        )
        return
    if action == "docker-start":
        docker_start()
        return
    config_check()
    docker_start()
    if action in ("check", "config"):
        dc(["config", "--quiet"])
        say("configuration_is_valid")
        return
    if action == "status":
        dc(["ps", "-a"], True)
        return
    if action in ("logs", "logs-once"):
        args = [
            "logs",
            "--tail=" + str(int(os.getenv("TAIL", "100"))),
            "bedrock",
        ]
        if action == "logs":
            args.insert(1, "-f")
        p = subprocess.run(dcargs() + args, env=compose_env())
        if p.returncode not in (0, 130):
            raise RuntimeError(tr("could_not_read_the_messages"))
        return
    if action == "console":
        value = os.getenv("CMD", "").strip()
        if not value:
            raise RuntimeError(
                'Exemple : bedrock-family server console "say Bonjour".'
            )
        send(value)
        return
    if action == "players":
        for e in connected():
            say("name_xuid", **e)
        return
    if action == "xuids":
        cid = running()
        if not cid:
            raise RuntimeError(
                tr("start_the_server_or_use_bedrock_family_server_logs_once")
            )
        say(
            "\n".join(x for x in logs(cid).splitlines() if "xuid" in x.lower())
            or "no_identifiers_found"
        )
        return
    with lock("maintenance"):
        if action in ("up", "start", "apply"):
            up()
        elif action == "session":
            start_session()
        elif action in ("stop", "down", "session-stop"):
            cancel_session(True)
            if action == "down":
                dc(["down"], True)
            else:
                stop()
                if action == "session-stop":
                    backup(False, True)
        elif action == "restart":
            dc(["restart", "bedrock"], True)
            wait_ready()
        elif action == "backup":
            backup()
        elif action == "restore":
            restore()
        elif action == "pull":
            dc(["pull", "bedrock"], True, timeout=None)
        elif action in ("update", "update-server"):
            cancel_session(True)
            backup()
            dc(["pull", "bedrock"], True, timeout=None)
            ensure_game_overlay()
            dc(
                ["up", "-d", "--force-recreate", "bedrock"],
                True,
                latest=action == "update-server",
            )
            wait_ready()
            if action == "update-server":
                env_update({"BEDROCK_VERSION": "EXISTING"})
                say("downloaded_version_pinned_check_ios_and_windows_devices")
        elif action == "version-pin":
            env_update({"BEDROCK_VERSION": "EXISTING"})
            say("installed_version_pinned_for_future_starts")
        elif action.startswith("allowlist-"):
            access(action[len("allowlist-") :])
        else:
            raise RuntimeError(tr("unknown_command_in_the_service"))


def validate_game_settings(value):
    """Validate and normalize the stored game configuration."""
    return validate_game(value)


def load_settings():
    """Return the effective family settings with validated game values."""
    return settings()


def list_worlds():
    """Display the worlds known to the project and the active default world."""
    return worlds()


def set_default_world():
    """Set the default world for future startups from the environment."""
    return world_default()


def update_family_settings(stop_at=None, game=None):
    """Persist stop-at and game settings without clobbering untouched values."""
    return update_settings(stop_at=stop_at, game=game)


def read_env_file():
    """Return variables stored in the project environment file."""
    return env_read()


def write_env_values(values):
    """Update selected environment variables without deleting unrelated values."""
    return env_update(values)


def validate_local_ipv4(value):
    """Validate a local IPv4 address and return it in canonical form."""
    return ipv4(value)


def detect_local_ipv4_candidates():
    """List candidate IPv4 addresses for the local host and their network type."""
    return ipv4_candidates()


def choose_lan_ip(configured):
    """Choose the local IPv4 address to expose to players or validate input."""
    return select_lan_ip(configured)


def check_server_configuration():
    """Validate the project environment and required configuration values."""
    return config_check()


def build_game_overlay(cfg):
    """Build the compose overlay used to enforce in-game rules."""
    return game_overlay(cfg)


def write_game_overlay():
    """Persist the runtime overlay used for game settings in Docker."""
    return ensure_game_overlay()


def build_compose_env(latest=False):
    """Create the environment used for docker compose commands."""
    return compose_env(latest=latest)


def build_compose_arguments():
    """Assemble the base docker compose command line for the project root."""
    return dcargs()


def run_compose_command(args, echo=False, timeout=240, latest=False):
    """Execute a docker compose command against the active project."""
    return dc(args, echo=echo, timeout=timeout, latest=latest)


def is_docker_available():
    """Return True when Docker is reachable and usable on this machine."""
    return docker_reachable()


def ensure_docker_running():
    """Ensure Docker Desktop is running before executing project commands."""
    return docker_start()


def show_docker_diagnostics():
    """Print recent project logs and runtime diagnostics for the project."""
    return diagnostic()


def is_container_running():
    """Return True when the Bedrock container is currently active."""
    return running()


def utc_timestamp():
    """Return the current UTC timestamp in ISO-8601 format."""
    return stamp()


def read_container_logs(cid, since=None):
    """Read the container logs and include an optional time filter."""
    return logs(cid, since=since)


def clean_log_line(line):
    """Strip ANSI escape sequences and Docker timestamps from a log line."""
    return clean(line)


def parse_online_players(text):
    """Parse the current online player list reported by the game server."""
    return parse_online(text)


def send_in_game_command(command, cid=None, reload=False):
    """Send a command to the running game container and report the result."""
    return send(command, cid=cid, reload=reload)


def apply_server_rules():
    """Apply the configured gameplay rules by sending server commands."""
    return apply_game_rules()


def wait_for_server_ready():
    """Wait until the server reports readiness before continuing."""
    return wait_ready()


def start_server(latest=False):
    """Start the Bedrock server and wait until it is ready."""
    return up(latest=latest)


def stop_server():
    """Stop the running Bedrock server and refuse a cold stop while it remains active."""
    return stop()


def list_connected_players():
    """List players currently connected to the running game server."""
    return connected()


def validate_allowlist_entries(entries):
    """Validate allowlist entries and normalize their structure."""
    return validate_entries(entries)


def merge_allowlist_entries(entries):
    """Merge duplicate allowlist entries by player name or XUID."""
    return merge_entries(entries)


def manage_allowlist(action):
    """Synchronize the local and runtime allowlist state for the server."""
    return access(action)


def validate_backup_member(info):
    """Reject unsafe archive members before adding them to a backup."""
    return archive_filter(info)


def create_backup(restart=True, already_stopped=False):
    """Create a backup of the current project state."""
    return backup(restart=restart, already_stopped=already_stopped)


def validate_backup_members(tar):
    """Ensure the archive contains only safe members before restoration."""
    return safe_members(tar)


def restore_backup():
    """Restore a verified archive into the project root and resume the server."""
    return restore()


def compute_deadline(value, now=None):
    """Compute the next scheduled shutdown time while enforcing a future value."""
    return deadline(value, now=now)


def session_state_path():
    """Return the path used to persist the session state file."""
    return state_path()


def load_session_state():
    """Return the persisted session metadata from disk."""
    return state()


def is_process_alive(pid):
    """Return True if the process still exists for the given PID."""
    return alive(pid)


def cancel_scheduled_session(quiet=False):
    """Cancel the active scheduled shutdown if the state allows it."""
    return cancel_session(quiet=quiet)


def schedule_session():
    """Schedule the automatic shutdown for the configured end-of-game time."""
    return start_session()


def announce_message(text):
    """Send a message to the running game server and log any failure."""
    return notice(text)


def session_worker_loop(token):
    """Drive scheduled shutdown warnings and the final backup workflow."""
    return session_worker(token)


def print_game_settings(cfg):
    """Print the current in-game settings and caveats for the user."""
    return show_game(cfg)


def handle_game_action(action):
    """Apply a game setting change or reload the active configuration."""
    return game_action(action)


def initialize_server_setup():
    """Initialize the project root with the default configuration and directories."""
    return setup()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("interrupted_server_not_stopped_automatically")
        sys.exit(130)
    except (
        RuntimeError,
        OSError,
        ValueError,
        KeyError,
        tarfile.TarError,
        subprocess.TimeoutExpired,
    ) as exc:
        say("error_message", message=exc)
        if len(sys.argv) > 1 and sys.argv[1] not in (
            "setup",
            "help",
            "session-default",
            "session-default-show",
            "session-default-reset",
        ):
            diagnostic()
        sys.exit(1)
