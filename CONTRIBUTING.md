# Contributing / Contribuer

## English

Keep the project easy to use for parents who do not know Docker or Git. The server runs on macOS with Apple Silicon. Players use Minecraft Bedrock on iOS or Windows 10/11 on the same local network.

1. Explain the problem and expected result.
2. Add a regression test for changed behaviour.
3. Run make verify without a real Docker engine.
4. Update the English and French guides together.
5. Preserve worlds, settings and player permissions.

Runtime code uses the Python standard library. PDF tools are optional. Do not commit worlds, backups, logs, names, account identifiers, local configuration or secrets. Distinguish simulated tests from real Mac/client testing.

## Français

Garder le projet accessible aux parents qui ne connaissent ni Docker ni Git. Le serveur fonctionne sur macOS avec Apple Silicon. Les joueurs utilisent Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local.

1. Expliquer le problème et le résultat attendu.
2. Ajouter un test pour le comportement modifié.
3. Exécuter make verify sans moteur Docker réel.
4. Mettre à jour les guides français et anglais ensemble.
5. Préserver les mondes, réglages et autorisations des joueurs.

Le programme de gestion utilise la bibliothèque standard Python. Les outils PDF sont facultatifs. Ne pas publier de monde, sauvegarde, journal, nom, identifiant, réglage local ou secret. Distinguer les tests simulés des vrais essais Mac/appareils de jeu.
