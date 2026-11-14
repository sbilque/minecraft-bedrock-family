# Utiliser le serveur

[Accueil](../../README.fr.md) · [English](../en/guide.md) · [Toutes les commandes](commands.txt)

Après avoir installé le CLI et initialisé l’instance avec `bedrock-family init ~/MinecraftFamille`, ouvrez Terminal et saisissez `cd ~/MinecraftFamille`. Entrez une commande à la fois et attendez sa fin.

Le Mac garde le monde. Les joueurs utilisent Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local.

## Démarrer et choisir l’heure de fin

```sh
bedrock-family session start
```

Le serveur démarre avec l’heure habituelle. Pour choisir cette heure une fois :

```sh
bedrock-family session default set 20:30
```

Sans personnalisation, c’est 19 h. Pour une exception aujourd’hui :

```sh
bedrock-family session start --until 21:00
```

L’heure est celle du Mac. Une heure déjà passée aujourd’hui est refusée. Les rappels arrivent 15 min, 5 min, 1 min et 30 s avant la fin ; ceux déjà passés ne sont pas rejoués. À l’heure prévue, l’arrêt commence, puis le monde est sauvegardé. Le serveur reste éteint.

Pour faire tourner le serveur pendant une durée fixe, utilisez `--duration` avec des minutes (`45m`) ou des heures (`1h`, `2h30m`, ou un nombre de minutes seul) :

```sh
bedrock-family session start --duration 2h30m
```

Le serveur démarre, puis s’arrête tout seul à la fin de la durée, avec les mêmes rappels et la même sauvegarde. C’est une durée relative, elle tombe donc toujours dans l’avenir.

Cette programmation ne revient pas demain : relancez `bedrock-family session start` à chaque partie.

## Afficher ou choisir un monde

```sh
bedrock-family world list
```

La commande affiche les dossiers de monde disponibles et marque le monde par défaut. Pour en choisir un existant :

```sh
bedrock-family world use "Nom du monde"
```

Le choix ne coupe pas une partie en cours. Il sera appliqué au prochain `bedrock-family server start` ou `bedrock-family settings apply`. Un monde doit déjà exister dans `data/worlds`.

Pour créer et démarrer un nouveau monde :

```sh
bedrock-family world create "Nouveau monde"
```

Si un serveur tourne déjà, le CLI demande confirmation avant de le redémarrer. Avec un terminal non interactif, ajoutez `--yes` pour confirmer explicitement.

## Vérifier, changer ou annuler la fin

| Je veux… | Je saisis… |
|---|---|
| Voir l’heure prévue | `bedrock-family session status` |
| Lire les messages de fermeture | `bedrock-family session logs` |
| Annuler l’heure sans arrêter | `bedrock-family session cancel` |
| Arrêter maintenant et sauvegarder | `bedrock-family session stop` |
| Voir l’heure habituelle | `bedrock-family session default show` |
| Remettre l’heure habituelle à 19 h | `bedrock-family session default reset` |

Changer l’heure habituelle ne déplace pas une partie déjà programmée. Pour la déplacer : annulez, puis lancez une nouvelle programmation.

Gardez le Mac éveillé et Docker ouvert. Terminal peut être fermé, pas votre session macOS. Après redémarrage, le serveur peut repartir sans heure de fin : vérifiez et reprogrammez. Une panne peut empêcher les rappels ou la sauvegarde.

## Changer les règles du jeu

Prévenez les joueurs : certains changements relancent le serveur.

| Je veux… | Je saisis… |
|---|---|
| Activer ou désactiver la triche | `bedrock-family settings set cheats on` ou `bedrock-family settings set cheats off` |
| Garder ou perdre l’inventaire à la mort | `bedrock-family settings set keep-inventory on` ou `bedrock-family settings set keep-inventory off` |
| Choisir la difficulté | `bedrock-family settings set difficulty facile` |
| Un seul joueur au lit pour passer la nuit | `bedrock-family settings set sleep-one` |
| Exiger la moitié des joueurs au lit | `bedrock-family settings set sleep 50` |
| Choisir le mode par défaut | `bedrock-family settings set gamemode survie` |
| Voir les choix enregistrés | `bedrock-family settings show` |
| Remettre les cinq choix familiaux | `bedrock-family settings reset` |

Difficultés : `paisible`, `facile`, `normale`, `difficile`. Modes : `survie`, `creatif`, `aventure`. Le sommeil accepte de 0 à 100 ; 0 exige quand même un joueur au lit.

Les choix sont conservés. Si le serveur est arrêté, ils s’appliquent au prochain démarrage du CLI. `bedrock-family settings apply` démarre et applique les choix. `bedrock-family settings show` affiche les choix enregistrés, pas une mesure en direct du monde.

Le mode par défaut ne change pas automatiquement celui des joueurs déjà connus. Pour passer les joueurs présents en créatif : `bedrock-family players set-mode creatif`. Les absents ne sont pas concernés.

La triche désactive les succès ; la remettre sur off ne les réactive pas automatiquement. Elle ne donne pas de droits d’opérateur aux enfants.

## Ajouter ou retirer un joueur

Pour accueillir une nouvelle personne :

```sh
bedrock-family access disable --confirm
```

Faites-la rejoindre depuis Minecraft Bedrock, puis :

```sh
bedrock-family access preview
bedrock-family access sync
bedrock-family access enable
```

Vérifiez les noms avant `sync`. Refermez les entrées dès que possible. Les joueurs absents déjà inscrits restent autorisés. Ces opérations peuvent couper les parties.

Pour afficher les inscrits : `bedrock-family access show`.

Pour retirer quelqu’un :

```sh
bedrock-family access remove "Nom du joueur"
```

Ses constructions restent. S’il joue encore, `bedrock-family server restart` coupe les sessions. Ne faites pas `sync` tant qu’il reste connecté : il serait ajouté à nouveau. Si les entrées sont ouvertes, activez aussi la liste avec `bedrock-family access enable`.

## Sauvegarder

```sh
bedrock-family backup create
bedrock-family open backups
```

La sauvegarde peut interrompre les parties. Le serveur repart seulement s’il était allumé avant. Copiez régulièrement les archives sur un autre disque. Aucune suppression automatique n’est prévue.

Ne supprimez pas `data` : il contient le monde. Gardez les archives privées, car elles peuvent contenir des noms et identifiants de joueurs.

## Revenir à une sauvegarde

Cette opération remplace les constructions actuelles par celles de l’archive. Utilisez uniquement vos propres sauvegardes et une version compatible de Minecraft.

```sh
bedrock-family session cancel
bedrock-family backup list
```

Copiez le nom de l’archive voulue, puis remplacez le nom dans cette commande :

```sh
bedrock-family backup restore "backups/nom-de-la-sauvegarde.tar.gz" --confirm
```

Le monde actuel est conservé à part. Vos réglages et autorisations actuels restent en place. Vérifiez les constructions avant d’effacer le dossier conservé.

## Modifier la liste des joueurs à la main

Avant d’arrêter le serveur, notez les noms et numéros des comptes avec `bedrock-family players xuids`. Si un numéro manque, demandez au joueur de quitter puis de revenir, et relisez les messages. Ce numéro est appelé XUID.

Ensuite :

```sh
bedrock-family backup create
bedrock-family server stop
bedrock-family access edit
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
bedrock-family access reload
bedrock-family access show
bedrock-family server start
```

Ne sautez pas `reload` : il conserve vos suppressions pour les prochains démarrages. Si le fichier est invalide, corrigez avant de relancer.

## Mettre à jour ou changer un autre réglage

Quand personne ne joue :

```sh
bedrock-family session cancel
bedrock-family update --server
```

Une sauvegarde est faite avant la mise à jour. Vérifiez ensuite que les appareils iOS et Windows peuvent rejoindre avec une version compatible de Minecraft Bedrock.

Pour les autres réglages du serveur : `bedrock-family open settings`, enregistrez, puis `bedrock-family settings apply`. Pour choisir un monde, utilisez `bedrock-family world list` et `bedrock-family world use "Nom du monde"`.

`bedrock-family server restart` ne remplace pas `bedrock-family settings apply` après un changement de réglage. `bedrock-family server stop` arrête sans sauvegarder ; préférez `bedrock-family session stop` pour finir une soirée.

[Résoudre un problème](troubleshooting.md) · [Commandes détaillées](commands.txt) · [Imprimer](printing.md)
