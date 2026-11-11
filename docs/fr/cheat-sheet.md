# Pense-bête pour la famille

Sur le Mac, ouvrez Terminal :

```sh
cd ~/minecraft-bedrock-family
```

Les joueurs utilisent Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local. Le Mac et Docker restent allumés.

## Commencer et finir une partie

| Je veux… | Je saisis… |
|---|---|
| Démarrer avec l’heure habituelle | make session |
| Choisir une autre heure aujourd’hui | make session STOP_AT=21:00 |
| Arrêter maintenant et sauvegarder | make session-stop |
| Vérifier l’heure prévue | make session-status |
| Annuler l’heure sans arrêter | make session-cancel |

Rappels : 15 min, 5 min, 1 min et 30 s avant. Puis arrêt et sauvegarde. Une heure passée aujourd’hui est refusée.

## Garder une heure habituelle

| Je veux… | Je saisis… |
|---|---|
| Mémoriser 20 h 30 | make session-default TIME=20:30 |
| Afficher l’heure habituelle | make session-default-show |
| Revenir à 19 h | make session-default-reset |

Changer l’habitude ne déplace pas une partie déjà programmée. Pour la déplacer : annulez, puis programmez à nouveau.

## Sauvegarder

| Je veux… | Je saisis… |
|---|---|
| Sauvegarder maintenant | make backup |
| Ouvrir les archives | make open-backups |

La sauvegarde peut couper la partie. Copiez les archives sur un autre disque. Ne supprimez pas data : c’est le monde.

<!-- pagebreak -->

# Joueurs, règles et petits problèmes

## Accueillir un joueur

1. make allowlist-disable CONFIRM=yes
2. Faites rejoindre le joueur depuis Minecraft Bedrock.
3. make allowlist-preview
4. Vérifiez les noms, puis make allowlist-sync
5. make allowlist-enable

Pour voir les inscrits : make allowlist-show.

Pour retirer quelqu’un : make allowlist-remove PLAYER="Nom du joueur". Les constructions restent. S’il est encore là, make restart coupe les sessions. Ne faites pas sync tant qu’il reste connecté.

## Régler le jeu

| Je veux… | Je saisis… |
|---|---|
| Garder l’inventaire à la mort | make keep-inventory VALUE=on |
| Choisir la difficulté facile | make difficulty LEVEL=facile |
| Un joueur au lit suffit | make sleep-one |
| Choisir le mode survie par défaut | make gamemode MODE=survie |
| Voir les choix enregistrés | make game-show |

Pour les interrupteurs, off désactive. Difficultés : paisible, facile, normale, difficile. Modes : survie, creatif, aventure. Le guide détaille les autres choix.

La triche est activée au départ et désactive les succès du monde. Changer les règles peut couper la partie.

## Si cela ne fonctionne pas

| Je veux… | Je saisis… |
|---|---|
| Lire les messages du serveur | make logs-once |
| Lire les messages de fermeture | make session-logs |
| Vérifier Docker et Python | make doctor |
| Toutes les commandes | make LANGUAGE=fr |

Après redémarrage du Mac, vérifiez et reprogrammez l’heure de fin. Une panne peut empêcher arrêt et sauvegarde : lisez les messages avant de conclure à la réussite.
