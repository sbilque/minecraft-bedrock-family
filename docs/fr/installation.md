# Installer et rejoindre le monde

[Accueil](../../README.fr.md) · [English](../en/installation.md)

Le serveur fonctionne sur le Mac avec puce Apple Silicon. Les joueurs le rejoignent depuis Minecraft Bedrock sur iOS ou Windows 10/11, sur le même réseau local.

## 1. Préparer le Mac

Il faut Docker Desktop pour Apple Silicon, Python 3.9 ou plus récent, et un outil pour installer et exécuter le CLI. Une version actuelle de Python est recommandée.

- [Installer Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), puis l'ouvrir.
- [Installer Python pour macOS](https://www.python.org/downloads/macos/) s'il manque.
- Installer [uv](https://docs.astral.sh/uv/getting-started/installation/). Vous pouvez aussi utiliser pip : les deux solutions sont décrites plus bas.
- Ouvrir Terminal : c'est l'application dans laquelle vous saisirez les commandes.

Vérifiez les outils :

```sh
python3 --version
uv --version
docker compose version
```

Si vous préférez utiliser pip au lieu d'uv, vérifiez Python et pip :

```sh
python3 --version
python3 -m pip --version
docker compose version
```

## 2. Installer le CLI et préparer le dossier serveur

Le paquet n'est pas encore publié sur PyPI ; installez donc le CLI à partir d'une copie de ce dépôt. Choisissez uv ou pip.

**Avec uv**

`uv` installe les applications CLI dans son propre environnement d'outils ; une installation à partir des sources nécessite donc d'abord un petit environnement isolé. Exécutez ces commandes dans le dossier où vous avez récupéré les sources :

```sh
uv venv
source .venv/bin/activate
uv pip install .
```

`uv pip install .` construit une installation isolée depuis les sources de ce dossier. Elle utilise le même projet local qu'il provienne d'un téléchargement ou d'un clone. Puis initialisez le dossier qui contiendra le monde, les réglages et les sauvegardes :

```sh
bedrock-family init ~/MinecraftFamille
cd ~/MinecraftFamille
```

**Avec pip**

Utilisez un interpréteur Python de version 3.9 ou plus récente. Un fichier `pyproject.toml` dans le dossier des sources décrit le projet et son point d'entrée :

```sh
python3 -m pip install .
```

Pour garder le CLI à jour avec le dossier des sources (par exemple après avoir récupéré de nouvelles versions), installez-le en version modifiable :

```sh
python3 -m pip install --editable .
```

L'installation avec uv comme avec pip enregistrent la même commande `bedrock-family`. Depuis le même terminal, utilisez `bedrock-family` pour chaque commande.

Quand le paquet publié sera disponible sur PyPI, vous pourrez aussi l'installer comme outil uv :

```sh
uv tool install minecraft-bedrock-family
```

Celui-ci enregistre la même commande `bedrock-family`.

Le CLI suit les préférences de langue du terminal. Pour choisir une langue ponctuellement, placez l'option avant la commande : `bedrock-family --language fr --help`. Pour la définir pour toute la session du terminal : `export BEDROCK_FAMILY_LANGUAGE=fr` (ou `en`).

Pour adopter un dossier existant, utilisez son chemin avec `-C` et ne le déplacez pas : `bedrock-family -C ~/minecraft-bedrock-family init`. L'initialisation conserve les présents fichiers et ne remplace pas le monde.

## 3. Détecter l'adresse du Mac et démarrer

Lisez les [conditions Minecraft](https://www.minecraft.net/eula). En lançant `bedrock-family setup --accept-eula`, vous confirmez les accepter. Le CLI détecte l'adresse IPv4 du Mac. Si plusieurs connexions sont disponibles, il affichera leur type (par exemple Wi-Fi ou Ethernet) et vous demandé laquelle les joueurs utiliseront. Connectez les appareils des joueurs au même réseau que cette connexion. Si possible, demande à la box de toujours donner la même adresse au Mac.

Vous pouvez aussi fournir directement une adresse connue : `bedrock-family setup --accept-eula --ip 192.168.1.50`. Cette valeur remplace la détection.

Le projet active la triche par défaut : les succès du monde sont désactivés. Gardez une sauvegarde avant d'utiliser un monde existant.

```sh
bedrock-family setup --accept-eula
bedrock-family check
bedrock-family server start
```

Attendez la confirmation du démarrage. Le premier lancement télécharge le serveur et crée le monde ; cela peut prendre quelques minutes. Ne saisissez pas `sudo` et n'ouvrez pas de ports Internet sur la box.

## 4. Rejoindre depuis iOS ou Windows 10/11

Connectez l'appareil au même réseau local que le Mac. Ouvrez Minecraft Bedrock, puis Jouer > Serveurs > Ajouter un serveur.

| Champ | Valeur |
|---|---|
| Nom | Minecraft Family |
| Adresse | L'adresse IPv4 affichée par `bedrock-family setup` |
| Port | 19132 |

Utilisez un compte Microsoft distinct par joueur. Pour les enfants, autorisez le multijoueur dans les réglages du compte Xbox/Microsoft.

Sur iOS, autorisez aussi Minecraft à utiliser le réseau local si l'appareil le demande. Sur le Mac, acceptez les demandes réseau de Docker.

Ne saisissez pas `localhost`, l'adresse publique de la box ou `http://` devant l'adresse. Un réseau Wi-Fi invité peut empêcher les appareils de communiquer : utilisez le réseau local habituel.

## 5. Réserver les entrées aux joueurs choisis

Au premier accueil, les personnes du réseau local qui se connectent avec un compte Microsoft peuvent entrer. Venez avec les personnes que vous souhaitez, puis :

```sh
bedrock-family access preview
bedrock-family access sync
bedrock-family access enable
bedrock-family version pin
```

Vérifiez les noms avant `sync`. L'activation de la liste peut couper la partie ; les inscrits pourront revenir. `version-pin` garde la version du serveur qui vient de fonctionner.

## 6. Lancer la prochaine partie

```sh
bedrock-family session default set 20:30
bedrock-family session start
```

La première ligne mémorise l'heure de fin. La seconde démarre la partie d'aujourd'hui. Après les rappels, le serveur s'arrête, sauvegarde et reste éteint.

Gardez le Mac éveillé et Docker ouvert. Vous pouvez fermer Terminal, mais pas votre session macOS. Après un redémarrage, vérifiez le serveur et programmez à nouveau la fin de partie.

Pour arrêter maintenant et sauvegarder : `bedrock-family session stop`.

## 7. Désinstaller le CLI

Pour supprimer le CLI, désinstallez le paquet utilisé pour l'installer :

- Installation avec un outil uv : `uv tool uninstall minecraft-bedrock-family`
- Installation avec pip : `python3 -m pip uninstall minecraft-bedrock-family`
- Installation avec un venv de source (`uv venv` + `uv pip install .`) : lancez `uv pip uninstall minecraft-bedrock-family`, ou supprimez le dossier `.venv` dans le dossier des sources.

La désinstallation du CLI ne supprime pas le dossier serveur créé avec `bedrock-family init` (`~/MinecraftFamille` ou similaire). Le monde, les réglages et les sauvegardes continuent d'y rester. Pour les supprimer aussi, supprimez ce dossier vous-même.

[Utiliser le serveur](guide.md) · [Un problème ?](troubleshooting.md)
