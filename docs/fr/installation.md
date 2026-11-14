# Installer et rejoindre le monde

[Accueil](../../README.fr.md) · [English](../en/installation.md)

Le serveur fonctionne sur le Mac avec puce Apple Silicon. Les joueurs le rejoignent depuis Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local.

## 1. Préparer le Mac

Il faut Docker Desktop pour Apple Silicon, Python 3.9 ou plus récent, et un outil pour installer le CLI : pipx, ou uv si vous le préférez. Une version actuelle de Python est recommandée.

- [Installer Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), puis l’ouvrir.
- [Installer Python pour macOS](https://www.python.org/downloads/macos/) s’il manque.
- Installer un gestionnaire de paquets pour exécuter le CLI sans make : [pipx](https://pipx.pypa.io/stable/installation/) ou [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Ouvrir Terminal : c’est l’application dans laquelle vous saisirez les commandes.

Vérifiez les outils :

```sh
python3 --version
pipx --version
docker compose version
```

Si vous avez choisi uv, vérifiez uv à la place de pipx :

```sh
python3 --version
uv --version
docker compose version
```

## 2. Installer le CLI et préparer le dossier serveur

Installez le paquet publié, puis initialisez le dossier qui contiendra le monde, les réglages et les sauvegardes :

```sh
pipx install minecraft-bedrock-family
bedrock-family init ~/MinecraftFamille
cd ~/MinecraftFamille
```

Si vous préférez uv, faites la même installation comme outil uv (uv 1.2 et plus récent) :

```sh
uv tool install minecraft-bedrock-family
```

La commande `uv tool` est la propre alternative de uv à pipx. Si vous avez une ancienne version d'uv, utilisez l'API pipx que uv fournit :

```sh
uv pipx install minecraft-bedrock-family
```

Le CLI installé par uv fonctionne comme celui de pipx. Depuis le même terminal, utilisez `bedrock-family` pour chaque commande. Pour revenir à une installation pipx classique plus tard, lancez `pipx uninstall minecraft-bedrock-family` puis `uv tool uninstall minecraft-bedrock-family`.

Pour installer le CLI directement depuis une copie de ce dépôt, sans passer par le paquet PyPI, donnez à la commande le chemin vers le dossier où vous avez récupéré la source. uv copie le projet depuis ce dossier et l'installe :

```sh
uv pipx install --from /path/to/minecraft-bedrock-family minecraft-bedrock-family
```

Cela utilise le même projet local qu'il provienne d'un téléchargement ou d'un clone. Elle construit une installation isolée depuis cette source, donc elle ne modifie rien de déjà installé depuis PyPI. Vous pouvez aussi utiliser la commande uv tool pour cela. Si vous ne pouvez pas utiliser uv ni une copie clonée, le dossier où vous avez lancé `bedrock-family init` suffit pour gérer votre serveur.

Le CLI suit les préférences de langue du terminal. Pour choisir une langue ponctuellement, placez l’option avant la commande : `bedrock-family --language fr --help`. Pour la définir pour toute la session du terminal : `export BEDROCK_FAMILY_LANGUAGE=fr` (ou `en`).

Pour adopter un dossier existant, utilisez son chemin avec `-C` et ne le déplacez pas : `bedrock-family -C ~/minecraft-bedrock-family init`. L’initialisation conserve les fichiers présents et ne remplace pas le monde.

## 3. Détecter l’adresse du Mac et démarrer

Lisez les [conditions Minecraft](https://www.minecraft.net/eula). En lançant `bedrock-family setup --accept-eula`, vous confirmez les accepter. Le CLI détecte l’adresse IPv4 du Mac. Si plusieurs connexions sont disponibles, il affiche leur type (par exemple Wi-Fi ou Ethernet) et vous demande laquelle les joueurs utiliseront. Connectez les appareils des joueurs au même réseau que cette connexion. Si possible, demandez à la box de toujours donner la même adresse au Mac.

Vous pouvez aussi fournir directement une adresse connue : `bedrock-family setup --accept-eula --ip 192.168.1.50`. Cette valeur remplace la détection.

Le projet active la triche par défaut : les succès du monde sont désactivés. Gardez une sauvegarde avant d’utiliser un monde existant.

```sh
bedrock-family setup --accept-eula
bedrock-family check
bedrock-family server start
```

Attendez la confirmation du démarrage. Le premier lancement télécharge le serveur et crée le monde ; cela peut prendre quelques minutes. Ne saisissez pas `sudo` et n’ouvrez pas de ports Internet sur la box.

## 4. Rejoindre depuis iOS ou Windows 10/11

Connectez l’appareil au même réseau local que le Mac. Ouvrez Minecraft Bedrock, puis Jouer > Serveurs > Ajouter un serveur.

| Champ | Valeur |
|---|---|
| Nom | Minecraft Family |
| Adresse | L’adresse IPv4 affichée par `bedrock-family setup` |
| Port | 19132 |

Utilisez un compte Microsoft distinct par joueur. Pour les enfants, autorisez le multijoueur dans les réglages du compte Xbox/Microsoft.

Sur iOS, autorisez aussi Minecraft à utiliser le réseau local si l’appareil le demande. Sur le Mac, acceptez les demandes réseau de Docker.

Ne saisissez pas `localhost`, l’adresse publique de la box ou `http://` devant l’adresse. Un réseau Wi-Fi invité peut empêcher les appareils de communiquer : utilisez le réseau local habituel.

## 5. Réserver les entrées aux joueurs choisis

Au premier accueil, les personnes du réseau local qui se connectent avec un compte Microsoft peuvent entrer. Faites venir les personnes voulues, puis :

```sh
bedrock-family access preview
bedrock-family access sync
bedrock-family access enable
bedrock-family version pin
```

Vérifiez les noms avant `sync`. L’activation de la liste peut couper la partie ; les inscrits pourront revenir. `version-pin` garde la version du serveur qui vient de fonctionner.

## 6. Lancer la prochaine partie

```sh
bedrock-family session default set 20:30
bedrock-family session start
```

La première ligne mémorise l’heure de fin. La seconde démarre la partie d’aujourd’hui. Après les rappels, le serveur s’arrête, sauvegarde et reste éteint.

Gardez le Mac éveillé et Docker ouvert. Vous pouvez fermer Terminal, mais pas votre session macOS. Après un redémarrage, vérifiez le serveur et programmez à nouveau la fin de partie.

Pour arrêter maintenant et sauvegarder : `bedrock-family session stop`.

[Utiliser le serveur](guide.md) · [Un problème ?](troubleshooting.md)
