# Pense-bête pour la famille

Sur le Mac, ouvrez Terminal :

```sh
cd ~/MinecraftFamille
```

Les joueurs utilisent Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local. Le Mac et Docker restent allumés.

## Commencer et finir une partie

| Je veux… | Je saisis… |
|---|---|
| Démarrer avec l’heure habituelle | bedrock-family session start |
| Choisir une autre heure aujourd’hui | bedrock-family session start --until 21:00 |
| Arrêter maintenant et sauvegarder | bedrock-family session stop |
| Vérifier l’heure prévue | bedrock-family session status |
| Annuler l’heure sans arrêter | bedrock-family session cancel |

Rappels : 15 min, 5 min, 1 min et 30 s avant. Puis arrêt et sauvegarde. Une heure passée aujourd’hui est refusée.

## Garder une heure habituelle

| Je veux… | Je saisis… |
|---|---|
| Mémoriser 20 h 30 | bedrock-family session default set 20:30 |
| Afficher l’heure habituelle | bedrock-family session default show |
| Revenir à 19 h | bedrock-family session default reset |

Changer l’habitude ne déplace pas une partie déjà programmée. Pour la déplacer : annulez, puis programmez à nouveau.

## Choisir un monde

| Je veux… | Je saisis… |
|---|---|
| Voir les mondes et le choix actuel | bedrock-family world list |
| Choisir un monde existant | bedrock-family world use "Nom du monde" |

Le choix s’applique au prochain `bedrock-family server start` ou `bedrock-family settings apply`, pas pendant une partie.

## Sauvegarder

| Je veux… | Je saisis… |
|---|---|
| Sauvegarder maintenant | bedrock-family backup create |
| Ouvrir les archives | bedrock-family open backups |

La sauvegarde peut couper la partie. Copiez les archives sur un autre disque. Ne supprimez pas data : c’est le monde.

<!-- pagebreak -->

# Joueurs, règles et petits problèmes

## Accueillir un joueur

1. bedrock-family access disable --confirm
2. Faites rejoindre le joueur depuis Minecraft Bedrock.
3. bedrock-family access preview
4. Vérifiez les noms, puis bedrock-family access sync
5. bedrock-family access enable

Pour voir les inscrits : bedrock-family access show.

Pour retirer quelqu’un : bedrock-family access remove "Nom du joueur". Les constructions restent. S’il est encore là, bedrock-family server restart coupe les sessions. Ne faites pas sync tant qu’il reste connecté.

## Régler le jeu

| Je veux… | Je saisis… |
|---|---|
| Garder l’inventaire à la mort | bedrock-family settings set keep-inventory on |
| Choisir la difficulté facile | bedrock-family settings set difficulty facile |
| Un joueur au lit suffit | bedrock-family settings set sleep-one |
| Choisir le mode survie par défaut | bedrock-family settings set gamemode survie |
| Voir les choix enregistrés | bedrock-family settings show |

Pour les interrupteurs, off désactive. Difficultés : paisible, facile, normale, difficile. Modes : survie, creatif, aventure. Le guide détaille les autres choix.

La triche est activée au départ et désactive les succès du monde. Changer les règles peut couper la partie.

## Si cela ne fonctionne pas

| Je veux… | Je saisis… |
|---|---|
| Lire les messages du serveur | bedrock-family server logs --once |
| Lire les messages de fermeture | bedrock-family session logs |
| Vérifier Docker et Python | bedrock-family doctor |
| Toutes les commandes | bedrock-family --help |

Après redémarrage du Mac, vérifiez et reprogrammez l’heure de fin. Une panne peut empêcher arrêt et sauvegarde : lisez les messages avant de conclure à la réussite.
