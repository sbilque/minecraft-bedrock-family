# Installer et rejoindre le monde

[Accueil](../../README.fr.md) · [English](../en/installation.md)

Le serveur est installé sur le Mac avec puce Apple Silicon. Les joueurs le rejoignent depuis Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local.

## 1. Préparer le Mac

Il faut Docker Desktop pour Apple Silicon, Python 3.9 ou plus récent, et make. Une version actuelle de Python est recommandée.

- [Installer Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), puis l’ouvrir.
- [Installer Python pour macOS](https://www.python.org/downloads/macos/) s’il manque.
- Ouvrir Terminal : c’est l’application dans laquelle vous saisirez les commandes.

Vérifiez les outils :

```sh
python3 --version
make --version
docker compose version
```

Si make manque, saisissez `xcode-select --install`, puis suivez les instructions Apple. Aucun module Python supplémentaire n’est nécessaire pour jouer.

## 2. Ranger le projet

Sur GitHub, choisissez Code > Download ZIP. Décompressez le fichier. Renommez le dossier `minecraft-bedrock-family` et placez-le dans votre dossier personnel.

Dans Terminal :

```sh
cd ~/minecraft-bedrock-family
make verify
```

Ce contrôle ne lance pas de partie. Ne remplacez jamais un dossier qui contient déjà votre monde sans l’avoir sauvegardé.

## 3. Détecter l’adresse du Mac et démarrer

Lisez les [conditions Minecraft](https://www.minecraft.net/eula) : `EULA=TRUE` signifie que vous les acceptez. `make setup` détecte l’adresse IPv4 du Mac. Si plusieurs connexions sont disponibles, il affiche leur type (par exemple Wi-Fi ou Ethernet) et vous demande laquelle les joueurs utiliseront. Connectez les appareils des joueurs au même réseau que cette connexion. Si possible, demandez à la box de toujours donner la même adresse au Mac.

Vous pouvez aussi indiquer directement une adresse si vous savez laquelle choisir. Par exemple : `LAN_IP=192.168.1.50`. Cette valeur remplace la détection.

Le projet active la triche par défaut : les succès du monde sont désactivés. Gardez une sauvegarde avant d’utiliser un monde existant.

```sh
make setup EULA=TRUE
make check
make up
```

Attendez la confirmation du démarrage. Le premier lancement télécharge le serveur et crée le monde ; cela peut prendre quelques minutes. Ne saisissez pas `sudo` et n’ouvrez pas de ports Internet sur la box.

## 4. Rejoindre depuis iOS ou Windows 10/11

Connectez l’appareil au même réseau local que le Mac. Ouvrez Minecraft Bedrock, puis Jouer > Serveurs > Ajouter un serveur.

| Champ | Valeur |
|---|---|
| Nom | Minecraft Family |
| Adresse | L’adresse IPv4 affichée par `make setup` |
| Port | 19132 |

Utilisez un compte Microsoft distinct par joueur. Pour les enfants, autorisez le multijoueur dans les réglages du compte Xbox/Microsoft.

Sur iOS, autorisez aussi Minecraft à utiliser le réseau local si l’appareil le demande. Sur le Mac, acceptez les demandes réseau de Docker.

Ne saisissez pas `localhost`, l’adresse publique de la box ou `http://` devant l’adresse. Un réseau Wi-Fi invité peut empêcher les appareils de communiquer : utilisez le réseau local habituel.

## 5. Réserver les entrées aux joueurs choisis

Au premier accueil, les personnes du réseau local qui se connectent avec un compte Microsoft peuvent entrer. Faites venir les personnes voulues, puis :

```sh
make allowlist-preview
make allowlist-sync
make allowlist-enable
make version-pin
```

Vérifiez les noms avant `sync`. L’activation de la liste peut couper la partie ; les inscrits pourront revenir. `version-pin` garde la version du serveur qui vient de fonctionner.

## 6. Lancer la prochaine partie

```sh
make session-default TIME=20:30
make session
```

La première ligne mémorise l’heure de fin. La seconde démarre la partie d’aujourd’hui. Après les rappels, le serveur s’arrête, sauvegarde et reste éteint.

Gardez le Mac éveillé et Docker ouvert. Vous pouvez fermer Terminal, mais pas votre session macOS. Après un redémarrage, vérifiez le serveur et programmez à nouveau la fin de partie.

Pour arrêter maintenant et sauvegarder : `make session-stop`.

[Utiliser le serveur](guide.md) · [Un problème ?](troubleshooting.md)
