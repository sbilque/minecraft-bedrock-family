# Contributing / Contribuer

## English

Keep the project easy to use for parents who do not know Docker or Git. The server runs on macOS with Apple Silicon. Players use Minecraft Bedrock on iOS or Windows 10/11 on the same local network.

1. Explain the problem and expected result.
2. Add a regression test for changed behaviour.
3. Run `make verify` without a real Docker engine.
4. Update the English and French guides together.
5. Preserve worlds, settings and player permissions.

Runtime code uses the Python standard library. PDF tools are optional. Do not commit worlds, backups, logs, names, account identifiers, local configuration or secrets. Distinguish simulated tests from real Mac/client testing.

### Releasing the CLI

The `minecraft-bedrock-family` distribution is built from `pyproject.toml` and exposes the `bedrock-family` command. Run `make verify`, build and inspect the wheel and source archive, then create a version tag such as `v0.1.0`. Configure PyPI Trusted Publishing for this repository and the `pypi` environment before using the release workflow. Never store a PyPI token in the repository.

### Adding a CLI language

The CLI discovers JSON catalogs in `bedrock_family/locales/`. To add a language, copy `en.json` to `<language>.json`, keep the English `snake_case` keys unchanged, and translate their values. No Python changes are needed. The language is then detected from the user's locale, or can be selected with `--language` or `BEDROCK_FAMILY_LANGUAGE`.

## Français

Garder le projet accessible aux parents qui ne connaissent ni Docker ni Git. Le serveur fonctionne sur macOS avec Apple Silicon. Les joueurs utilisent Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local.

1. Expliquer le problème et le résultat attendu.
2. Ajouter un test pour le comportement modifié.
3. Exécuter `make verify` sans moteur Docker réel.
4. Mettre à jour les guides français et anglais ensemble.
5. Préserver les mondes, réglages et autorisations des joueurs.

Le programme de gestion utilise la bibliothèque standard Python. Les outils PDF sont facultatifs. Ne pas publier de monde, sauvegarde, journal, nom, identifiant, réglage local ou secret. Distinguer les tests simulés des vrais essais Mac/appareils de jeu.

### Publier le CLI

La distribution `minecraft-bedrock-family` est construite depuis `pyproject.toml` et fournit la commande `bedrock-family`. Exécuter `make verify`, construire et inspecter la roue et l’archive source, puis créer une étiquette de version telle que `v0.1.0`. Configurer la publication de confiance PyPI pour ce dépôt et l’environnement `pypi` avant d’utiliser le workflow de publication. Ne jamais enregistrer de jeton PyPI dans le dépôt.

### Ajouter une langue au CLI

Le CLI découvre les catalogues JSON dans `bedrock_family/locales/`. Pour ajouter une langue, copiez `en.json` vers `<langue>.json`, conservez les clés anglaises en `snake_case` et traduisez leurs valeurs. Aucune modification Python n’est nécessaire. La langue est détectée depuis les paramètres régionaux de l’utilisateur, ou peut être choisie avec `--language` ou `BEDROCK_FAMILY_LANGUAGE`.
