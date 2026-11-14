"""Runtime translations for the command-line interface."""
import json
import os
from importlib.resources import files


_language = None
_messages = {}


def available_languages():
    directory = files("bedrock_family").joinpath("locales")
    languages = sorted(
        entry.name[:-5]
        for entry in directory.iterdir()
        if entry.is_file() and entry.name.endswith(".json")
    )
    if not languages:
        raise RuntimeError("Aucun catalogue de langue n’est installé.")
    return languages


def _match_language(value, languages):
    normalized = value.strip().split("@", 1)[0].split(".", 1)[0].replace("-", "_")
    names = {language.casefold(): language for language in languages}
    if normalized.casefold() in names:
        return names[normalized.casefold()]
    base = normalized.split("_", 1)[0].casefold()
    return names.get(base)


def default_language(environ=None):
    environ = os.environ if environ is None else environ
    languages = available_languages()
    preferences = (
        environ.get("BEDROCK_FAMILY_LANGUAGE", ""),
        environ.get("LANGUAGE", ""),
        environ.get("LC_ALL", ""),
        environ.get("LC_MESSAGES", ""),
        environ.get("LANG", ""),
    )
    for preference in preferences:
        for candidate in preference.split(":"):
            language = _match_language(candidate, languages)
            if language:
                return language
    return "en" if "en" in languages else languages[0]


def language_from_args(args, environ=None):
    if args is not None:
        for index, value in enumerate(args):
            if value == "--language" and index + 1 < len(args):
                requested = args[index + 1]
                return _match_language(requested, available_languages()) or default_language(environ)
            if value.startswith("--language="):
                requested = value.partition("=")[2]
                return _match_language(requested, available_languages()) or default_language(environ)
    return default_language(environ)


def set_language(language):
    global _language, _messages
    languages = available_languages()
    if language not in languages:
        raise ValueError("Langue non prise en charge : " + language)
    resource = files("bedrock_family").joinpath("locales", language + ".json")
    try:
        messages = json.loads(resource.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError("Catalogue de langue invalide : " + language) from exc
    if not isinstance(messages, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in messages.items()
    ):
        raise RuntimeError("Le catalogue de langue doit associer des textes à des textes : " + language)
    _language = language
    _messages = messages
    return language


def current_language():
    if _language is None:
        set_language(default_language())
    return _language


def tr(message, **values):
    if _language is None:
        set_language(default_language())
    translated = _messages.get(message, message)
    if values:
        return translated.format_map(values)
    return translated
