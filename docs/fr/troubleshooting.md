# Résoudre un problème

[Accueil](../../README.fr.md) · [English](../en/troubleshooting.md)

Ne supprimez pas le monde ni les réglages pour essayer de réparer.

## Le serveur ne démarre pas

1. Ouvrez Docker Desktop sur le Mac.
2. Attendez la fin de son démarrage.
3. Réessayez :

```sh
make up
```

Si cela échoue :

```sh
make logs-once
make doctor
```

Le programme essaie aussi d’afficher les derniers messages après une erreur. Ne supposez pas qu’une commande a réussi parce qu’elle a été envoyée.

## Message « docker.sock »

Docker n’est pas joignable. Ouvrez Docker Desktop, attendez, puis faites `docker info`. Ne créez pas le fichier à la main et ne supprimez pas `.docker`.

Si Docker est ouvert mais bloqué, utilisez son menu de dépannage pour le redémarrer. Ne commencez pas par une réinitialisation d’usine.

## Un appareil iOS ou Windows ne rejoint pas

Vérifiez dans cet ordre :

1. Le Mac est allumé et Docker fonctionne.
2. L’appareil et le Mac sont sur le même réseau local, pas sur un réseau invité isolé.
3. L’adresse enregistrée dans Minecraft est bien celle du Mac ; le port est 19132.
4. Minecraft Bedrock est à jour et compatible avec le serveur.
5. Le compte autorise le multijoueur et le nom figure dans les joueurs autorisés.

Sur iOS, vérifiez aussi l’autorisation Réseau local de Minecraft. Sur le Mac, autorisez les connexions de Docker si elles sont bloquées. Ne désactivez pas toute la protection du Mac.

## Un identifiant de joueur manque

Demandez au joueur de quitter puis de rejoindre le monde. Refaites `make allowlist-preview`, puis `make allowlist-sync` si les noms sont corrects.

## L’heure de fin ne semble plus active

```sh
make session-status
make session-logs
```

Après redémarrage du Mac ou arrêt de Docker, ne comptez pas sur l’ancienne programmation. Vérifiez, annulez avec `make session-cancel`, puis relancez `make session`.

## Une sauvegarde échoue

Lisez les messages avec `make session-logs` ou `make logs-once`. Ne supprimez pas les anciennes archives et ne supposez pas que la dernière est complète. Une erreur après fermeture peut laisser le serveur arrêté : c’est volontaire.

## Demander de l’aide

Copiez la commande saisie et les derniers messages. Indiquez les versions de macOS, Docker Desktop, Python et Minecraft. Masquez noms, numéros de comptes et détails privés du réseau. Ne joignez pas le monde ou les sauvegardes à une demande publique.
