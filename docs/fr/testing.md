# À quoi servent les tests ?

[English](../en/testing.md)

```sh
make verify
```

Cette commande vérifie le code et les commandes, puis lance des essais avec de faux échanges Docker. Elle ne démarre pas Minecraft, ne télécharge rien et n’utilise pas de moteur Docker réel.

Les essais portent notamment sur les heures, les règles du jeu, les joueurs autorisés, les sauvegardes, la restauration et les erreurs.

Un résultat réussi ne remplace pas une vraie partie d’essai. Après l’installation ou une mise à jour, démarrez le serveur sur le Mac et vérifiez qu’un appareil iOS ou Windows peut rejoindre avec une version compatible de Minecraft Bedrock.

Pour les personnes qui contribuent : make test lance les essais ; make lint vérifie le code et les commandes ; make verify fait les deux.

GitHub relance ces contrôles après publication ou proposition de modification. Les essais Linux servent à vérifier le programme, pas à proposer un serveur Linux. Le travail macOS vérifie aussi que le runner utilise Apple Silicon. Consultez les résultats Actions : la présence du workflow ne signifie pas qu’il a déjà réussi.
