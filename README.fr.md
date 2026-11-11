# Minecraft Bedrock Family

[English](README.md) · [Installer](docs/fr/installation.md) · [Utiliser](docs/fr/guide.md) · [Pense-bête](docs/fr/cheat-sheet.md)

Un monde Minecraft partagé, avec une heure de fin et des sauvegardes automatiques.

- Le monde est enregistré sur un Mac avec puce Apple Silicon.
- Les joueurs utilisent Minecraft Bedrock sur iOS ou Windows 10/11.
- Tous les appareils sont connectés au même réseau local.

## À savoir avant de commencer

La triche est aussi activée. Elle désactive les succès du monde ; la désactiver ensuite ne les réactive pas automatiquement. Sauvegardez un monde existant avant de modifier ses règles.

## Commencer

Installez Docker Desktop, Python et make sur le Mac, puis suivez le [tutoriel d’installation](docs/fr/installation.md). Il explique chaque étape, sans demander de connaître Git ou Docker.

Vous avez déjà préparé le Mac ? Dans Terminal, depuis le dossier du projet :

```sh
make session
```

Le serveur démarre. À l’heure prévue, les joueurs sont prévenus, le serveur s’arrête et le monde est sauvegardé. Le serveur reste ensuite éteint.

## Choisir l’heure de fin

```sh
make session-default TIME=20:30
```

Ce choix est conservé pour les prochaines parties. Sans personnalisation, l’heure de fin est 19 h.

Pour finir à une autre heure aujourd’hui seulement :

```sh
make session STOP_AT=21:00
```

Les rappels arrivent 15 minutes, 5 minutes, 1 minute et 30 secondes avant la fin. Une heure déjà passée aujourd’hui est refusée.

## Les commandes du quotidien

| Je veux… | Je saisis… |
|---|---|
| Démarrer avec une heure de fin | `make session` |
| Arrêter maintenant et sauvegarder | `make session-stop` |
| Vérifier l’heure prévue | `make session-status` |
| Annuler l’heure de fin sans arrêter | `make session-cancel` |
| Faire une sauvegarde | `make backup` |
| Ouvrir les sauvegardes | `make open-backups` |
| Afficher l’aide en français | `make LANGUAGE=fr` |

## Avant la première partie

Les réglages familiaux sont prêts : inventaire conservé à la mort, difficulté facile, un seul joueur au lit pour passer la nuit et mode survie.

Gardez le Mac et Docker allumés pendant les parties. Après un redémarrage du Mac, vérifiez puis reprogrammez l’heure de fin. Ne supprimez pas `data` : ce dossier contient le monde.

## Pour aller plus loin

- [Installer et connecter les joueurs](docs/fr/installation.md)
- [Ajouter un joueur, régler le jeu ou restaurer une sauvegarde](docs/fr/guide.md)
- [Résoudre un problème](docs/fr/troubleshooting.md)
- [Imprimer les documents](docs/fr/printing.md)
- [Toutes les commandes](docs/fr/commands.txt)

Le serveur est destiné au réseau local. N’ouvrez pas de ports Internet sur votre box. Les conditions de Minecraft et des outils utilisés restent applicables. Projet indépendant, sans affiliation avec Mojang.
