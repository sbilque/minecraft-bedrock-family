# Utiliser le serveur

[Accueil](../../README.fr.md) · [English](../en/guide.md) · [Toutes les commandes](commands.txt)

Dans Terminal, commencez par `cd ~/minecraft-bedrock-family`. Saisissez une commande à la fois et attendez sa fin.

Le Mac garde le monde. Les joueurs utilisent Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local.

## Démarrer et choisir l’heure de fin

```sh
make session
```

Le serveur démarre avec l’heure habituelle. Pour choisir cette heure une fois :

```sh
make session-default TIME=20:30
```

Sans personnalisation, c’est 19 h. Pour une exception aujourd’hui :

```sh
make session STOP_AT=21:00
```

L’heure est celle du Mac. Une heure déjà passée aujourd’hui est refusée. Les rappels arrivent 15 min, 5 min, 1 min et 30 s avant la fin ; ceux déjà passés ne sont pas rejoués. À l’heure prévue, l’arrêt commence, puis le monde est sauvegardé. Le serveur reste éteint.

Cette programmation ne revient pas demain : relancez `make session` à chaque partie.

## Afficher ou choisir un monde

```sh
make worlds
```

La commande affiche les dossiers de monde disponibles et marque le monde par défaut. Pour en choisir un existant :

```sh
make world-default LEVEL="Nom du monde"
```

Le choix ne coupe pas une partie en cours. Il sera appliqué au prochain `make up` ou `make apply`. Un monde doit déjà exister dans `data/worlds`.

## Vérifier, changer ou annuler la fin

| Je veux… | Je saisis… |
|---|---|
| Voir l’heure prévue | `make session-status` |
| Lire les messages de fermeture | `make session-logs` |
| Annuler l’heure sans arrêter | `make session-cancel` |
| Arrêter maintenant et sauvegarder | `make session-stop` |
| Voir l’heure habituelle | `make session-default-show` |
| Remettre l’heure habituelle à 19 h | `make session-default-reset` |

Changer l’heure habituelle ne déplace pas une partie déjà programmée. Pour la déplacer : annulez, puis lancez une nouvelle programmation.

Gardez le Mac éveillé et Docker ouvert. Terminal peut être fermé, pas votre session macOS. Après redémarrage, le serveur peut repartir sans heure de fin : vérifiez et reprogrammez. Une panne peut empêcher les rappels ou la sauvegarde.

## Changer les règles du jeu

Prévenez les joueurs : certains changements relancent le serveur.

| Je veux… | Je saisis… |
|---|---|
| Activer ou désactiver la triche | `make cheats VALUE=on` ou `VALUE=off` |
| Garder ou perdre l’inventaire à la mort | `make keep-inventory VALUE=on` ou `VALUE=off` |
| Choisir la difficulté | `make difficulty LEVEL=facile` |
| Un seul joueur au lit pour passer la nuit | `make sleep-one` |
| Exiger la moitié des joueurs au lit | `make sleep PERCENT=50` |
| Choisir le mode par défaut | `make gamemode MODE=survie` |
| Voir les choix enregistrés | `make game-show` |
| Remettre les cinq choix familiaux | `make game-defaults` |

Difficultés : `paisible`, `facile`, `normale`, `difficile`. Modes : `survie`, `creatif`, `aventure`. Le sommeil accepte de 0 à 100 ; 0 exige quand même un joueur au lit.

Les choix sont conservés. Si le serveur est arrêté, ils s’appliquent au prochain démarrage avec Make. `make game-apply` démarre et applique les choix. `game-show` affiche vos choix, pas une mesure en direct du monde.

Le mode par défaut ne change pas automatiquement celui des joueurs déjà connus. Pour passer les joueurs présents en créatif : `make gamemode-all MODE=creatif`. Les absents ne sont pas concernés.

La triche désactive les succès ; la remettre sur off ne les réactive pas automatiquement. Elle ne donne pas de droits d’opérateur aux enfants.

## Ajouter ou retirer un joueur

Pour accueillir une nouvelle personne :

```sh
make allowlist-disable CONFIRM=yes
```

Faites-la rejoindre depuis Minecraft Bedrock, puis :

```sh
make allowlist-preview
make allowlist-sync
make allowlist-enable
```

Vérifiez les noms avant `sync`. Refermez les entrées dès que possible. Les joueurs absents déjà inscrits restent autorisés. Ces opérations peuvent couper les parties.

Pour afficher les inscrits : `make allowlist-show`.

Pour retirer quelqu’un :

```sh
make allowlist-remove PLAYER="Nom du joueur"
```

Ses constructions restent. S’il joue encore, `make restart` coupe les sessions. Ne faites pas `sync` tant qu’il reste connecté : il serait ajouté à nouveau. Si les entrées sont ouvertes, activez aussi la liste avec `make allowlist-enable`.

## Sauvegarder

```sh
make backup
make open-backups
```

La sauvegarde peut interrompre les parties. Le serveur repart seulement s’il était allumé avant. Copiez régulièrement les archives sur un autre disque. Aucune suppression automatique n’est prévue.

Ne supprimez pas `data` : il contient le monde. Gardez les archives privées, car elles peuvent contenir des noms et identifiants de joueurs.

## Revenir à une sauvegarde

Cette opération remplace les constructions actuelles par celles de l’archive. Utilisez uniquement vos propres sauvegardes et une version compatible de Minecraft.

```sh
make session-cancel
make backups
```

Copiez le nom de l’archive voulue, puis remplacez le nom dans cette commande :

```sh
make restore FILE="backups/nom-de-la-sauvegarde.tar.gz" CONFIRM=yes
```

Le monde actuel est conservé à part. Vos réglages et autorisations actuels restent en place. Vérifiez les constructions avant d’effacer le dossier conservé.

## Modifier la liste des joueurs à la main

Avant d’arrêter le serveur, notez les noms et numéros des comptes avec `make xuids`. Si un numéro manque, demandez au joueur de quitter puis de revenir, et relisez les messages. Ce numéro est appelé XUID.

Ensuite :

```sh
make backup
make stop
make allowlist-edit
```

TextEdit ouvre `data/allowlist.json`. Exemple fictif à remplacer :

```json
[
  {
    "name": "Parent Exemple",
    "xuid": "2535400000000001",
    "ignoresPlayerLimit": false
  },
  {
    "name": "Enfant Exemple",
    "xuid": "2535400000000002",
    "ignoresPlayerLimit": false
  }
]
```

Gardez les crochets, les guillemets droits et la virgule entre les joueurs. Pas de virgule après le dernier joueur, ni de commentaire. Enregistrez avec Commande-S en texte brut. Pour retirer une personne, supprimez son bloc et ajustez la virgule. `[]` vide toute la liste : si les entrées sont réservées, personne ne pourra entrer.

```sh
make allowlist-reload
make allowlist-show
make up
```

Ne sautez pas `reload` : il conserve vos suppressions pour les prochains démarrages. Si le fichier est invalide, corrigez avant de relancer.

## Mettre à jour ou changer un autre réglage

Quand personne ne joue :

```sh
make session-cancel
make update-server
```

Une sauvegarde est faite avant la mise à jour. Vérifiez ensuite que les appareils iOS et Windows peuvent rejoindre avec une version compatible de Minecraft Bedrock.

Pour les autres réglages du serveur : `make edit`, enregistrez, puis `make apply`. Pour choisir un monde, utilisez `make worlds` et `make world-default`.

`make restart` ne remplace pas `make apply` après un changement de réglage. `make stop` arrête sans sauvegarder ; préférez `make session-stop` pour finir une soirée.

[Résoudre un problème](troubleshooting.md) · [Commandes détaillées](commands.txt) · [Imprimer](printing.md)
