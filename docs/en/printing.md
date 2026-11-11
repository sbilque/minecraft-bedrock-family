# Print the documents

[Français](../fr/printing.md)

The easiest option: open a guide page on GitHub, then choose Print or Save as PDF in your browser.

The PDFs include a tutorial, guide and cheat sheet in each language. Print on A4 in portrait; fit to page if needed.

## Get PDFs from GitHub

After a successful build, open Actions > Printable guides. Download printable-guides-en-fr. GitHub may ask you to sign in.

## Build PDFs on the Mac

This optional step is not needed to play. It installs only the PDF-building tool in a separate folder:

```sh
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r requirements-docs.txt
make docs DOCS_PYTHON=.venv-docs/bin/python
```

Files are created in `docs/print/fr` and `docs/print/en`. Edit the Markdown text when changing a document. Building PDFs does not start the server.
