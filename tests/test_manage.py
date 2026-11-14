"""Local tests: standard library only; no Docker engine or network access."""

import contextlib
import datetime as dt
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

PACKAGE = Path(__file__).resolve().parents[1]
REAL_ENV = dict(os.environ)
sys.path.insert(0, str(PACKAGE))
from bedrock_family import i18n
from bedrock_family import manage as m


class LanguageTests(unittest.TestCase):
    def test_locale_detection_normalizes_region_and_encoding(self):
        self.assertEqual(i18n.default_language({"LC_ALL": "fr_CA.UTF-8"}), "fr")
        self.assertEqual(
            i18n.default_language(
                {"LANGUAGE": "de:en_US.UTF-8", "LANG": "fr_FR.UTF-8"}
            ),
            "en",
        )

    def test_catalog_formats_translated_messages(self):
        i18n.set_language("en")
        self.addCleanup(i18n.set_language, "fr")
        self.assertEqual(
            i18n.tr("default_world_name", name="Famille"),
            "Default world: Famille",
        )

    def test_catalogs_use_shared_english_snake_case_keys(self):
        catalogs = [
            json.loads(
                (
                    PACKAGE
                    / "bedrock_family"
                    / "locales"
                    / (language + ".json")
                ).read_text(encoding="utf-8")
            )
            for language in i18n.available_languages()
        ]
        keys = set(catalogs[0])
        for catalog in catalogs:
            self.assertEqual(set(catalog), keys)
            for key in catalog:
                self.assertRegex(key, r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")


class LocalTests(unittest.TestCase):
    def setUp(self):
        i18n.set_language("fr")
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patch = mock.patch.object(m, "ROOT", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        patch = mock.patch.dict(os.environ, {}, clear=True)
        patch.start()
        self.addCleanup(patch.stop)
        capture = contextlib.redirect_stdout(io.StringIO())
        capture.__enter__()
        self.addCleanup(capture.__exit__, None, None, None)

    def seed(self):
        (self.root / "data").mkdir(exist_ok=True)
        (self.root / ".env").write_text(
            "LAN_IP=192.168.1.50\nEULA=TRUE\nBEDROCK_VERSION=LATEST\n"
        )
        (self.root / "compose.yaml").write_text("services: {}\n")

    def test_boolean(self):
        for value in ["on", "oui", "TRUE", "1", "activé"]:
            self.assertTrue(m.boolean(value))
        for value in ["off", "non", "FALSE", "0", "désactivé"]:
            self.assertFalse(m.boolean(value))
        with self.assertRaises(RuntimeError):
            m.boolean("maybe")

    def test_difficulty(self):
        for name, result in [
            ("facile", "easy"),
            ("paisible", "peaceful"),
            ("normale", "normal"),
            ("difficile", "hard"),
        ]:
            self.assertEqual(m.difficulty(name), result)
        with self.assertRaises(RuntimeError):
            m.difficulty("invalid")

    def test_gamemode(self):
        self.assertEqual(m.gamemode("créatif"), "creative")
        self.assertEqual(m.gamemode("aventure"), "adventure")
        with self.assertRaises(RuntimeError):
            m.gamemode("spectateur")

    def test_percent_bounds(self):
        self.assertEqual(m.percentage("0"), 0)
        self.assertEqual(m.percentage("100"), 100)
        for value in ["-1", "101", "50%", "1.5", "True", ""]:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                m.percentage(value)

    def test_clock_format(self):
        self.assertEqual(m.clock("00:00"), "00:00")
        self.assertEqual(m.clock("23:59"), "23:59")
        for value in ["24:00", "19:60", "9:00", "19h00", ""]:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                m.clock(value)

    def test_deadline_future_and_past(self):
        now = dt.datetime(2030, 1, 1, 16, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(m.deadline("19:00", now).hour, 19)
        for value in ["15:00", "16:00"]:
            with self.assertRaises(RuntimeError):
                m.deadline(value, now)

    def test_ipv4(self):
        self.assertEqual(m.ipv4("192.168.1.50"), "192.168.1.50")
        for value in ["127.0.0.1", "0.0.0.0", "224.0.0.1", "abc", "::1"]:
            with self.assertRaises(RuntimeError):
                m.ipv4(value)

    def test_family_defaults(self):
        cfg = m.settings()
        self.assertEqual(cfg["stop_at"], "19:00")
        self.assertEqual(
            cfg["game"],
            {
                "cheats": True,
                "keep_inventory": True,
                "difficulty": "easy",
                "sleep_percent": 0,
                "gamemode": "survival",
            },
        )

    def test_setting_updates_do_not_reset_other_choices(self):
        cfg = dict(m.GAME_DEFAULTS)
        cfg["cheats"] = False
        cfg["sleep_percent"] = 50
        m.update_settings(game=cfg)
        m.update_settings(stop_at="20:30")
        self.assertEqual(m.settings()["game"], cfg)
        cfg["difficulty"] = "hard"
        m.update_settings(game=cfg)
        self.assertEqual(m.settings()["stop_at"], "20:30")

    def test_old_time_only_settings_are_read(self):
        m.atomic(self.root / "family-settings.json", {"stop_at": "20:00"})
        self.assertEqual(m.settings()["game"], m.GAME_DEFAULTS)

    def test_separate_existing_game_choices_are_preserved(self):
        m.atomic(self.root / "family-settings.json", {"stop_at": "20:00"})
        m.atomic(
            self.root / "game-settings.json",
            {"cheats": False, "difficulty": "hard"},
        )
        self.assertFalse(m.settings()["game"]["cheats"])
        self.assertEqual(m.settings()["game"]["difficulty"], "hard")
        m.update_settings(stop_at="21:00")
        self.assertFalse(
            m.load(self.root / "family-settings.json")["game"]["cheats"]
        )

    def test_invalid_game_settings(self):
        for value in [
            {"cheats": "yes"},
            {"sleep_percent": True},
            {"sleep_percent": 101},
            {"gamemode": "invalid"},
        ]:
            with self.assertRaises(RuntimeError):
                m.validate_game(value)

    def test_atomic_writes_no_temporary_file_left(self):
        m.atomic(self.root / "data" / "test.json", {"a": 1})
        self.assertEqual(m.load(self.root / "data" / "test.json"), {"a": 1})
        self.assertFalse(list(self.root.rglob("*.tmp-*")))

    def test_env_update_preserves_other_values(self):
        (self.root / ".env").write_text(
            "# note\nLAN_IP=192.168.1.2\nEULA=TRUE\nBEDROCK_VERSION=EXISTING\n"
        )
        m.env_update({"LAN_IP": "192.168.1.50"})
        self.assertEqual(m.env_read()["BEDROCK_VERSION"], "EXISTING")
        self.assertIn("# note", (self.root / ".env").read_text())

    def test_setup_is_local_and_preserves_version(self):
        self.seed()
        m.env_update({"BEDROCK_VERSION": "EXISTING"})
        os.environ.update(LAN_IP="192.168.1.70", EULA="TRUE")
        with mock.patch.object(
            m, "docker_start", side_effect=AssertionError("Docker must not run")
        ):
            m.setup()
        self.assertEqual(m.env_read()["BEDROCK_VERSION"], "EXISTING")
        self.assertEqual(m.env_read()["LAN_IP"], "192.168.1.70")
        self.assertTrue((self.root / "compose.game.json").exists())

    def test_setup_detects_single_ipv4_address(self):
        self.seed()
        os.environ["EULA"] = "TRUE"
        candidate = {"ip": "192.168.1.70", "interface": "en0", "type": "Wi-Fi"}
        with (
            mock.patch.object(m, "ipv4_candidates", return_value=[candidate]),
            mock.patch.object(
                m,
                "docker_start",
                side_effect=AssertionError("Docker must not run"),
            ),
        ):
            m.setup()
        self.assertEqual(m.env_read()["LAN_IP"], "192.168.1.70")

    def test_ipv4_candidates_show_connection_type_and_ignore_inactive_or_local_interfaces(
        self,
    ):
        ports = "Hardware Port: Wi-Fi\nDevice: en0\n\nHardware Port: Ethernet\nDevice: en1\n"
        interfaces = (
            "lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST>\n"
            " inet 127.0.0.1 netmask 0xff000000\n"
            "en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST>\n"
            " inet 192.168.1.70 netmask 0xffffff00\n"
            "en1: flags=8862<BROADCAST,SMART,SIMPLEX,MULTICAST>\n"
            " inet 192.168.1.71 netmask 0xffffff00\n"
            "utun4: flags=8051<UP,POINTOPOINT,RUNNING,MULTICAST>\n"
            " inet 10.8.0.2 --> 10.8.0.2 netmask 0xffffffff\n"
        )
        with mock.patch.object(
            m,
            "raw",
            side_effect=[
                types.SimpleNamespace(stdout=ports),
                types.SimpleNamespace(stdout=interfaces),
            ],
        ):
            candidates = m.ipv4_candidates()
        self.assertEqual(
            candidates,
            [
                {"ip": "192.168.1.70", "interface": "en0", "type": "Wi-Fi"},
                {"ip": "10.8.0.2", "interface": "utun4", "type": "VPN"},
            ],
        )

    def test_multiple_ipv4_addresses_can_be_selected_interactively(self):
        candidates = [
            {"ip": "192.168.1.70", "interface": "en0", "type": "Wi-Fi"},
            {"ip": "10.0.0.5", "interface": "en5", "type": "Ethernet"},
        ]
        with (
            mock.patch.object(m, "ipv4_candidates", return_value=candidates),
            mock.patch.object(
                m.sys, "stdin", types.SimpleNamespace(isatty=lambda: True)
            ),
            mock.patch("builtins.input", return_value="2"),
            mock.patch.object(m, "say") as say,
        ):
            self.assertEqual(m.select_lan_ip(""), "10.0.0.5")
        self.assertTrue(
            any(
                call.kwargs.get("type") == "Wi-Fi"
                and call.kwargs.get("interface") == "en0"
                for call in say.call_args_list
            )
        )
        self.assertTrue(
            any(
                call.kwargs.get("type") == "Ethernet"
                and call.kwargs.get("interface") == "en5"
                for call in say.call_args_list
            )
        )

    def test_multiple_ipv4_addresses_require_explicit_choice_without_terminal(
        self,
    ):
        candidates = [
            {"ip": "192.168.1.70", "interface": "en0", "type": "Wi-Fi"},
            {"ip": "10.0.0.5", "interface": "en5", "type": "Ethernet"},
        ]
        with (
            mock.patch.object(m, "ipv4_candidates", return_value=candidates),
            mock.patch.object(
                m.sys, "stdin", types.SimpleNamespace(isatty=lambda: False)
            ),
            mock.patch.object(m, "say"),
            self.assertRaisesRegex(RuntimeError, "setup --ip"),
        ):
            m.select_lan_ip("")

    def test_explicit_ipv4_skips_detection(self):
        with mock.patch.object(
            m,
            "ipv4_candidates",
            side_effect=AssertionError("Detection should not run"),
        ):
            self.assertEqual(m.select_lan_ip("192.168.1.70"), "192.168.1.70")

    def test_eula_required(self):
        os.environ["LAN_IP"] = "192.168.1.50"
        with self.assertRaises(RuntimeError):
            m.setup()
        self.assertFalse((self.root / ".env").exists())

    def test_compose_env_removes_interpolation_overrides(self):
        os.environ.update(
            LAN_IP="",
            EULA="",
            BEDROCK_VERSION="EXISTING",
            LEVEL_NAME="wrong",
            OTHER="keep",
        )
        cfg = m.compose_env()
        self.assertNotIn("LAN_IP", cfg)
        self.assertNotIn("EULA", cfg)
        self.assertNotIn("BEDROCK_VERSION", cfg)
        self.assertNotIn("LEVEL_NAME", cfg)
        self.assertEqual(cfg["OTHER"], "keep")
        self.assertEqual(m.compose_env(True)["BEDROCK_VERSION"], "LATEST")

    def test_worlds_lists_existing_worlds_and_marks_default(self):
        self.seed()
        m.env_update({"LEVEL_NAME": "Famille"})
        worlds = self.root / "data" / "worlds"
        (worlds / "Famille").mkdir(parents=True)
        (worlds / "Survie 2").mkdir()
        with mock.patch.object(m, "say") as say:
            m.worlds()
        default_call = next(
            call
            for call in say.call_args_list
            if call.args[0] == "default_world_name"
        )
        self.assertEqual(default_call.kwargs["name"], "Famille")
        messages = [call.args[0] for call in say.call_args_list]
        self.assertIn(" * Famille", messages)
        self.assertIn("   Survie 2", messages)

    def test_world_default_updates_env_only_for_existing_world(self):
        self.seed()
        world = self.root / "data" / "worlds" / "Survie 2"
        world.mkdir(parents=True)
        os.environ["LEVEL"] = "Survie 2"
        with mock.patch.object(
            m,
            "docker_reachable",
            side_effect=AssertionError("Docker must not run"),
        ):
            m.world_default()
        self.assertEqual(m.env_read()["LEVEL_NAME"], "Survie 2")
        self.assertIn(
            "BEDROCK_VERSION=LATEST", (self.root / ".env").read_text()
        )

    def test_world_default_rejects_missing_or_unsafe_world(self):
        self.seed()
        for value in ("missing", "../outside", ""):
            os.environ["LEVEL"] = value
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                m.world_default()

    def test_compose_overlays_are_loaded(self):
        for name in ["compose.allowlist.json", "compose.game.json"]:
            m.atomic(self.root / name, {})
        args = m.dcargs()
        self.assertIn(str(self.root / "compose.allowlist.json"), args)
        self.assertIn(str(self.root / "compose.game.json"), args)

    def test_game_overlay(self):
        env = m.game_overlay(m.GAME_DEFAULTS)["services"]["bedrock"][
            "environment"
        ]
        self.assertEqual(env["ALLOW_CHEATS"], "true")
        self.assertEqual(env["GAMEMODE"], "survival")
        self.assertEqual(env["FORCE_GAMEMODE"], "false")

    def test_first_download_recovers_from_existing(self):
        self.seed()
        m.env_update({"BEDROCK_VERSION": "EXISTING"})
        with mock.patch.object(m, "dc"), mock.patch.object(m, "wait_ready"):
            m.up()
        self.assertEqual(m.env_read()["BEDROCK_VERSION"], "LATEST")

    def test_existing_executable_is_not_redownloaded(self):
        self.seed()
        m.env_update({"BEDROCK_VERSION": "EXISTING"})
        (self.root / "data" / "bedrock_server").write_text("fixture")
        with mock.patch.object(m, "dc"), mock.patch.object(m, "wait_ready"):
            m.up()
        self.assertEqual(m.env_read()["BEDROCK_VERSION"], "EXISTING")

    def test_parse_current_players(self):
        self.assertEqual(
            m.parse_online(
                "[INFO] There are 2/8 players online:\n[INFO] Parent Test, Enfant"
            ),
            ["Parent Test", "Enfant"],
        )
        self.assertEqual(
            m.parse_online("[INFO] There are 0/8 players online:"), []
        )
        self.assertIsNone(
            m.parse_online("[INFO] There are 2/8 players online:\n[INFO] One")
        )

    def test_xuid_validation_and_merge(self):
        entries = [
            {"name": "Parent", "xuid": "253540000000000123"},
            {"name": "parent", "xuid": "253540000000000123"},
        ]
        self.assertEqual(len(m.merge_entries(entries)), 1)
        self.assertIsInstance(m.merge_entries(entries)[0]["xuid"], str)
        with self.assertRaises(RuntimeError):
            m.validate_entries([{"name": "A", "xuid": 123}])

    def test_remove_player_updates_both_lists(self):
        self.seed()
        entries = [
            {"name": "Parent", "xuid": "123"},
            {"name": "Invite", "xuid": "456"},
        ]
        m.atomic(self.root / "data" / "allowlist.json", entries)
        m.atomic(
            self.root / "compose.allowlist.json",
            {
                "services": {
                    "bedrock": {
                        "environment": {
                            "ALLOW_LIST_USERS": "Parent:123\nInvite:456"
                        }
                    }
                }
            },
        )
        os.environ["PLAYER"] = "Invite"
        with mock.patch.object(m, "running", return_value=""):
            m.access("remove")
        self.assertEqual(
            m.load(self.root / "data" / "allowlist.json"), [entries[0]]
        )
        self.assertEqual(
            m.load(self.root / "compose.allowlist.json")["services"]["bedrock"][
                "environment"
            ]["ALLOW_LIST_USERS"],
            "Parent:123",
        )

    def test_manual_import_does_not_resurrect_deleted_players(self):
        self.seed()
        m.atomic(self.root / "data" / "allowlist.json", [])
        m.atomic(
            self.root / "compose.allowlist.json",
            {
                "services": {
                    "bedrock": {
                        "environment": {"ALLOW_LIST_USERS": "Parent:123"}
                    }
                }
            },
        )
        with mock.patch.object(m, "running", return_value=""):
            m.access("reload")
        self.assertEqual(
            m.load(self.root / "compose.allowlist.json")["services"]["bedrock"][
                "environment"
            ]["ALLOW_LIST_USERS"],
            "",
        )

    def test_empty_allowlist_cannot_be_enabled(self):
        self.seed()
        with self.assertRaises(RuntimeError):
            m.access("enable")

    def test_connected_ignores_old_visitors(self):
        replies = [
            "[INFO] There are 1/8 players online:\n[INFO] Parent",
            "[INFO] Player connected: Invite, xuid: 456\n[INFO] Player connected: Parent, xuid: 123",
        ]
        with (
            mock.patch.object(m, "running", return_value="c"),
            mock.patch.object(m, "dc"),
            mock.patch.object(m, "logs", side_effect=replies),
            mock.patch.object(m.time, "sleep"),
        ):
            self.assertEqual(m.connected()[0]["xuid"], "123")

    def test_game_commands_persist_without_starting_docker(self):
        os.environ["VALUE"] = "off"
        with (
            mock.patch.object(m, "docker_reachable", return_value=False),
            mock.patch.object(m, "up") as up,
        ):
            m.game_action("keep-inventory")
        self.assertFalse(m.settings()["game"]["keep_inventory"])
        up.assert_not_called()
        self.assertEqual(
            m.load(self.root / "compose.game.json")["services"]["bedrock"][
                "environment"
            ]["ALLOW_CHEATS"],
            "true",
        )

    def test_game_defaults_preserve_time(self):
        m.update_settings(stop_at="21:00", game={"cheats": False})
        with mock.patch.object(m, "docker_reachable", return_value=False):
            m.game_action("game-defaults")
        self.assertEqual(m.settings()["stop_at"], "21:00")
        self.assertEqual(m.settings()["game"], m.GAME_DEFAULTS)

    def test_gamemode_all_does_not_change_default(self):
        os.environ["MODE"] = "créatif"
        with (
            mock.patch.object(m, "config_check"),
            mock.patch.object(m, "docker_start"),
            mock.patch.object(m, "send") as send,
        ):
            m.game_action("gamemode-all")
        send.assert_called_once_with("gamemode creative @a")
        self.assertEqual(m.settings()["game"]["gamemode"], "survival")

    def test_game_rule_confirmation(self):
        def reply(cmd):
            return (
                "Set game difficulty to easy"
                if cmd.startswith("difficulty")
                else cmd.split()[1] + " set to " + cmd.split()[2]
            )

        with mock.patch.object(m, "send", side_effect=reply) as send:
            m.apply_game_rules()
        self.assertEqual(send.call_count, 3)
        with (
            mock.patch.object(m, "send", return_value="unrecognized response"),
            self.assertRaises(RuntimeError),
        ):
            m.apply_game_rules()

    def test_send_unknown_command_is_an_error(self):
        with (
            mock.patch.object(m, "running", return_value="c"),
            mock.patch.object(m, "dc"),
            mock.patch.object(m, "logs", return_value="Unknown command"),
            mock.patch.object(m.time, "sleep"),
            self.assertRaises(RuntimeError),
        ):
            m.send("bad")

    def test_allowlist_reload_requires_confirmation(self):
        with (
            mock.patch.object(m, "running", return_value="c"),
            mock.patch.object(m, "dc"),
            mock.patch.object(m, "logs", return_value="Allowlist reloaded"),
            mock.patch.object(m.time, "sleep"),
        ):
            self.assertIn("reloaded", m.send("allowlist reload", reload=True))

    def test_unsafe_archives_are_rejected(self):
        for name, link in [
            ("../escape", False),
            ("/absolute", False),
            ("data/link", True),
        ]:
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode="w") as tar:
                info = tarfile.TarInfo(name)
                if link:
                    info.type = tarfile.SYMTYPE
                    info.linkname = "/tmp/escape"
                tar.addfile(info)
            stream.seek(0)
            with (
                tarfile.open(fileobj=stream, mode="r") as tar,
                self.assertRaises(RuntimeError),
            ):
                m.safe_members(tar)

    def test_archive_filter_rejects_links(self):
        info = tarfile.TarInfo("link")
        info.type = tarfile.SYMTYPE
        with self.assertRaises(RuntimeError):
            m.archive_filter(info)

    def test_backup_and_restore_real_files_preserve_access(self):
        self.seed()
        (self.root / "data" / "world.txt").write_text("saved world")
        m.atomic(
            self.root / "data" / "allowlist.json",
            [{"name": "A", "xuid": "123"}],
        )
        m.update_settings(stop_at="20:30")
        active = [True]
        events = []

        def stopped():
            events.append("stop")
            active[0] = False

        def dc(args, *a, **kw):
            if args[0] == "start":
                events.append("start")
                active[0] = True
            return ""

        with (
            mock.patch.object(
                m, "running", side_effect=lambda: "c" if active[0] else ""
            ),
            mock.patch.object(m, "stop", side_effect=stopped),
            mock.patch.object(m, "dc", side_effect=dc),
        ):
            m.backup()
        self.assertEqual(events, ["stop", "start"])
        file = next((self.root / "backups").glob("*.tar.gz"))
        with tarfile.open(file) as tar:
            self.assertIn("family-settings.json", tar.getnames())
        (self.root / "data" / "world.txt").write_text("new world")
        m.atomic(
            self.root / "data" / "allowlist.json",
            [{"name": "B", "xuid": "456"}],
        )
        os.environ.update(FILE=str(file), CONFIRM="yes")
        with mock.patch.object(m, "stop"), mock.patch.object(m, "up"):
            m.restore()
        self.assertEqual(
            (self.root / "data" / "world.txt").read_text(), "saved world"
        )
        self.assertEqual(
            m.load(self.root / "data" / "allowlist.json")[0]["name"], "B"
        )

    def test_backup_failure_does_not_restart_a_stopped_server(self):
        self.seed()
        with (
            mock.patch.object(m, "running", return_value=""),
            mock.patch.object(
                m.tarfile, "open", side_effect=OSError("disk full")
            ),
            mock.patch.object(m, "dc") as dc,
            self.assertRaises(OSError),
        ):
            m.backup(False, True)
        dc.assert_not_called()

    def test_cancel_does_not_stop_server(self):
        m.atomic(m.state_path(), {"status": "scheduled", "token": "t"})
        with mock.patch.object(m, "stop") as stop:
            m.cancel_session()
        self.assertEqual(m.state()["status"], "cancelled")
        stop.assert_not_called()

    def test_cancel_refused_during_shutdown(self):
        m.atomic(m.state_path(), {"status": "stopping"})
        with self.assertRaises(RuntimeError):
            m.cancel_session()

    def simulate_worker(self, scenario):
        target = dt.datetime(2030, 1, 1, 19, 0, tzinfo=dt.timezone.utc)
        ticks = [target.timestamp() - 901]
        events = []
        notices = []
        m.atomic(
            m.state_path(),
            {
                "status": "scheduled",
                "token": "test",
                "deadline": target.isoformat(),
                "pid": 123,
            },
        )

        def sleep(value):
            ticks[0] += value
            if scenario == "cancel" and ticks[0] >= target.timestamp() - 899:
                s = m.state()
                s["status"] = "cancelled"
                m.atomic(m.state_path(), s)

        def stop():
            events.append("stop")
            if scenario == "stop-fails":
                raise RuntimeError("stop failed")

        def backup(*args):
            events.append("backup")
            if scenario == "backup-fails":
                raise RuntimeError("backup failed")

        fake_time = types.SimpleNamespace(time=lambda: ticks[0], sleep=sleep)
        with (
            mock.patch.object(m, "time", fake_time),
            mock.patch.object(
                m,
                "notice",
                side_effect=lambda text: notices.append(
                    (round(target.timestamp() - ticks[0]), text)
                ),
            ),
            mock.patch.object(m, "stop", side_effect=stop),
            mock.patch.object(m, "backup", side_effect=backup),
            mock.patch.object(m, "config_check"),
            mock.patch.object(m, "docker_start"),
            mock.patch.object(m, "diagnostic"),
            mock.patch.object(m.subprocess, "Popen"),
        ):
            m.session_worker("test")
        return events, notices

    def test_worker_warnings_and_stop_then_backup(self):
        events, notices = self.simulate_worker("normal")
        self.assertEqual([x[0] for x in notices[1:]], [900, 300, 60, 30])
        self.assertEqual(events, ["stop", "backup"])
        self.assertEqual(m.state()["status"], "stopped")

    def test_worker_cancellation(self):
        events, _ = self.simulate_worker("cancel")
        self.assertEqual(events, [])

    def test_worker_stop_failure_skips_backup(self):
        events, _ = self.simulate_worker("stop-fails")
        self.assertEqual(events, ["stop"])
        self.assertEqual(m.state()["status"], "failed")

    def test_worker_backup_failure_is_reported(self):
        events, _ = self.simulate_worker("backup-fails")
        self.assertEqual(events, ["stop", "backup"])
        self.assertEqual(m.state()["status"], "failed")

    def test_parse_duration(self):
        self.assertEqual(m.parse_duration("45"), 45)
        self.assertEqual(m.parse_duration("45m"), 45)
        self.assertEqual(m.parse_duration("1h"), 60)
        self.assertEqual(m.parse_duration("2h"), 120)
        self.assertEqual(m.parse_duration("1h30m"), 90)
        self.assertEqual(m.parse_duration("2H30M"), 150)
        self.assertEqual(m.parse_duration("1 h 30 m"), 90)

    def test_parse_duration_invalid(self):
        for value in ["", "0", "0m", "-5", "m", "h", "1x", "1h1m1m", "abc"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.parse_duration(value)

    def test_relative_deadline(self):
        now = dt.datetime(2030, 1, 1, 16, 0, tzinfo=dt.timezone.utc)
        target = m.relative_deadline(90, now)
        self.assertEqual(target, dt.datetime(2030, 1, 1, 17, 30, tzinfo=dt.timezone.utc))

    def test_deadline_iso(self):
        now = dt.datetime(2030, 1, 1, 16, 0, tzinfo=dt.timezone.utc)
        iso = (now + dt.timedelta(minutes=90)).isoformat()
        self.assertEqual(m.deadline(iso), now + dt.timedelta(minutes=90))
        self.assertEqual(m.deadline(iso).hour, 17)


STUB = r"""#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
args=sys.argv[1:];path=Path(os.environ['FAKE_STATE']);s=json.loads(path.read_text()) if path.exists() else {'running':False,'command':''}
def save():path.write_text(json.dumps(s))
if args and args[0]=='compose' and '--project-directory' in args:
    if any(k in os.environ for k in ('LAN_IP','EULA')):print('BAD_ENV',file=sys.stderr);sys.exit(9)
    if 'up' in args:
        if os.environ.get('FAKE_FAIL')=='yes':print('SIMULATED_FAILURE',file=sys.stderr);sys.exit(7)
        s['running']=True;save();print('Up')
    elif 'stop' in args:s['running']=False;save();print('Stopped')
    elif 'start' in args or 'restart' in args:s['running']=True;save()
    elif 'ps' in args:print(('fake' if s['running'] else '') if '-q' in args else str(s['running']))
    elif 'exec' in args:s['command']=args[-1];save()
    elif 'logs' in args:print('SIMULATED_DOCKER_LOGS')
    else:print('ok')
elif args and args[0]=='inspect':print('2026-11-11T10:00:00Z')
elif args and args[0]=='logs':
    print('[INFO] Server started.');print('[INFO] Player connected: Parent, xuid: 123')
    cmd=s.get('command','')
    if os.environ.get('FAKE_REPLY_ERROR')=='yes':print('Unknown command')
    elif cmd.startswith('difficulty '):print('Set game difficulty to '+cmd.split()[-1])
    elif cmd.startswith('gamerule '):print('Game rule '+cmd.split()[1]+' has been updated to '+cmd.split()[-1])
    elif cmd=='list':print('There are 1/8 players online:');print('Parent')
    elif cmd=='allowlist reload':print('Allowlist reloaded')
    elif cmd:print('Command executed')
else:print('ok')
"""


class MakeTests(unittest.TestCase):
    def test_make_only_exposes_contributor_targets(self):
        source = (PACKAGE / "Makefile").read_text(encoding="utf-8")
        targets = next(
            line.split(":", 1)[1].split()
            for line in source.splitlines()
            if line.startswith(".PHONY:")
        )
        self.assertEqual(
            set(targets), {"help", "test", "lint", "verify", "docs"}
        )
        result = subprocess.run(
            ["make", "--no-print-directory", "-n", "-C", str(PACKAGE)]
            + targets,
            capture_output=True,
            check=False,
            text=True,
            env=REAL_ENV,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_make_help_only_shows_contributor_tasks(self):
        result = subprocess.run(
            ["make", "--no-print-directory", "-C", str(PACKAGE), "help"],
            capture_output=True,
            check=False,
            text=True,
            env=REAL_ENV,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("make verify", result.stdout)
        self.assertNotIn("make up", result.stdout)


class FakeCliTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.root = base / "minecraft-famille"
        binary = base / "bin"
        binary.mkdir()
        file = binary / "docker"
        file.write_text(STUB)
        file.chmod(0o755)
        self.env = dict(REAL_ENV)
        self.env.update(
            PATH=str(binary) + os.pathsep + REAL_ENV["PATH"],
            FAKE_STATE=str(base / "state.json"),
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONPATH=str(PACKAGE),
            BEDROCK_FAMILY_LANGUAGE="fr",
        )
        result = self.cli("init", str(self.root))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.cli(
            "-C",
            str(self.root),
            "setup",
            "--accept-eula",
            "--ip",
            "192.168.1.50",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def cli(self, *args, env=None):
        return subprocess.run(
            [sys.executable, "-m", "bedrock_family", *args],
            capture_output=True,
            check=False,
            text=True,
            env=env or self.env,
            timeout=25,
            cwd=PACKAGE,
        )

    def test_help_and_version_work_without_a_server(self):
        result = self.cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("bedrock-family", result.stdout)
        self.assertIn("world", result.stdout)
        result = self.cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0.1.0", result.stdout)

    def test_help_and_messages_follow_selected_language(self):
        english_env = dict(self.env, BEDROCK_FAMILY_LANGUAGE="en")
        result = self.cli("--help", env=english_env)
        self.assertIn(
            "Manage a family Minecraft Bedrock server.", result.stdout
        )
        self.assertIn("optional arguments", result.stdout)
        result = self.cli("--language", "fr", "--help", env=english_env)
        self.assertIn(
            "Gérer un serveur Minecraft Bedrock familial.", result.stdout
        )
        self.assertIn("options facultatives", result.stdout)
        result = self.cli("--language", "fr", "players", "set-mode", "invalid")
        self.assertIn("choix invalide", result.stderr)
        result = self.cli(
            "-C", str(self.root), "world", "list", env=english_env
        )
        self.assertIn("Default world: Famille (not created yet)", result.stdout)
        result = self.cli("-C", str(self.root), "world", "list")
        self.assertIn(
            "Monde par defaut : Famille (pas encore cree)", result.stdout
        )
        locale_env = dict(self.env)
        locale_env.pop("BEDROCK_FAMILY_LANGUAGE")
        locale_env["LC_ALL"] = "fr_CA.UTF-8"
        result = self.cli("--help", env=locale_env)
        self.assertIn(
            "Gérer un serveur Minecraft Bedrock familial.", result.stdout
        )
        result = self.cli("help", env=english_env)
        self.assertIn(
            "Manage a family Minecraft Bedrock server.", result.stdout
        )

    def test_init_preserves_existing_server_configuration(self):
        compose = self.root / "compose.yaml"
        original = compose.read_text()
        result = self.cli("init", str(self.root))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(compose.read_text(), original)

    def test_init_template_uses_an_instance_specific_compose_project(self):
        contents = (self.root / "compose.yaml").read_text()
        self.assertNotIn("name: minecraft-bedrock-family", contents)

    def test_server_commands_start_and_read_logs(self):
        for args in (
            ("-C", str(self.root), "check"),
            ("-C", str(self.root), "server", "start"),
            ("-C", str(self.root), "server", "status"),
            ("-C", str(self.root), "server", "logs", "--once"),
        ):
            result = self.cli(*args)
            self.assertEqual(
                result.returncode, 0, result.stdout + result.stderr
            )
        result = self.cli("-C", str(self.root), "server", "start")
        self.assertIn(
            "playerssleepingpercentage has been updated to 0", result.stdout
        )
        self.assertIn("keepinventory has been updated to true", result.stdout)

    def test_cli_surfaces_docker_failures(self):
        env = dict(self.env)
        env["FAKE_FAIL"] = "yes"
        result = self.cli("-C", str(self.root), "server", "start", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SIMULATED_FAILURE", result.stdout + result.stderr)
        self.assertIn("SIMULATED_DOCKER_LOGS", result.stdout)

    def test_settings_and_session_defaults_are_separate(self):
        for args in (
            ("settings", "set", "cheats", "off"),
            ("settings", "set", "difficulty", "normale"),
            ("settings", "set", "sleep", "50"),
            ("session", "default", "set", "20:30"),
        ):
            result = self.cli("-C", str(self.root), *args)
            self.assertEqual(
                result.returncode, 0, result.stdout + result.stderr
            )
        cfg = json.loads((self.root / "family-settings.json").read_text())
        self.assertEqual(cfg["stop_at"], "20:30")
        self.assertFalse(cfg["game"]["cheats"])
        self.assertEqual(cfg["game"]["difficulty"], "normal")
        self.assertEqual(cfg["game"]["sleep_percent"], 50)

    def test_world_list_and_use(self):
        world = self.root / "data" / "worlds" / "Survie 2"
        world.mkdir(parents=True)
        result = self.cli("-C", str(self.root), "world", "list")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Survie 2", result.stdout)
        self.assertIn("Famille", result.stdout)
        result = self.cli("-C", str(self.root), "world", "use", "Survie 2")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("LEVEL_NAME=Survie 2", (self.root / ".env").read_text())
        self.assertIn("bedrock-family server start", result.stdout)

    def test_world_create_sets_name_and_starts_server(self):
        result = self.cli(
            "-C", str(self.root), "world", "create", "Nouveau monde"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(
            "LEVEL_NAME=Nouveau monde", (self.root / ".env").read_text()
        )
        self.assertTrue(
            json.loads(Path(self.env["FAKE_STATE"]).read_text())["running"]
        )

    def test_world_create_requires_confirmation_before_restarting(self):
        result = self.cli("-C", str(self.root), "server", "start")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.cli(
            "-C", str(self.root), "world", "create", "Nouveau monde"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--yes", result.stderr)
        self.assertNotIn(
            "LEVEL_NAME=Nouveau monde", (self.root / ".env").read_text()
        )
        result = self.cli(
            "-C", str(self.root), "world", "create", "Nouveau monde", "--yes"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(
            "LEVEL_NAME=Nouveau monde", (self.root / ".env").read_text()
        )

    def test_access_and_restore_require_confirmation_flags(self):
        result = self.cli("-C", str(self.root), "access", "disable")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--confirm", result.stderr)
        result = self.cli(
            "-C", str(self.root), "backup", "restore", "missing.tar.gz"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--confirm", result.stderr)

    def test_setup_requires_explicit_eula_acceptance_noninteractively(self):
        result = self.cli("-C", str(self.root), "setup", "--ip", "192.168.1.50")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--accept-eula", result.stderr)


class CommunityLayoutTests(unittest.TestCase):
    def test_bilingual_help(self):
        for language, expected in [
            ("en", "MINECRAFT BEDROCK FAMILY"),
            ("fr", "MINECRAFT EN FAMILLE"),
        ]:
            content = (PACKAGE / "docs" / language / "commands.txt").read_text(
                encoding="utf-8"
            )
            self.assertIn(expected, content)

    def test_runtime_configuration_is_ignored(self):
        ignored = (
            (PACKAGE / ".gitignore").read_text(encoding="utf-8").splitlines()
        )
        for name in [
            ".env",
            "family-settings.json",
            "compose.allowlist.json",
            "compose.game.json",
            "data/",
            "backups/",
            "logs/",
            ".state/",
        ]:
            self.assertIn(name, ignored)
        self.assertTrue((PACKAGE / "family-settings.example.json").exists())


if __name__ == "__main__":
    unittest.main()
