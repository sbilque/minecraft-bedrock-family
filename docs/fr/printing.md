# Imprimer les documents

[English](../en/printing.md)

Le plus simple : ouvrez une page du guide sur GitHub, puis choisissez Imprimer ou Enregistrer en PDF dans votre navigateur.

Les PDF comprennent un tutoriel, un guide et un pense-bête dans chaque langue. Imprimez en A4, orientation portrait ; ajustez à la page si nécessaire.

## Récupérer les PDF sur GitHub

Quand la fabrication automatique a réussi, ouvrez Actions > Printable guides. Téléchargez le fichier printable-guides-en-fr. GitHub peut demander une connexion.

## Fabriquer les PDF sur le Mac

Cette étape est facultative et ne sert pas à jouer. Elle ajoute seulement l’outil de fabrication des PDF, dans un dossier séparé :

```sh
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r requirements-docs.txt
make docs DOCS_PYTHON=.venv-docs/bin/python
```

Les fichiers sont créés dans `docs/print/fr` et `docs/print/en`. Les textes Markdown restent les documents à modifier. Aucun serveur n’est démarré pour fabriquer les PDF.
