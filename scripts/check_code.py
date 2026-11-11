#!/usr/bin/env python3
"""Syntaxe Python et Make, sans Docker, sans dependance externe."""
import ast
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def main():
    files=sorted((ROOT/'scripts').glob('*.py'))+sorted((ROOT/'tests').glob('*.py'))
    for path in files:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
        compile(path.read_text(encoding='utf-8'),str(path),'exec')
    tree=ast.parse((ROOT/'scripts'/'manage.py').read_text(encoding='utf-8'))
    node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PUBLIC_ACTIONS' for x in n.targets))
    actions=set(ast.literal_eval(node.value))
    match=re.search(r'^TARGETS := (.+)$',(ROOT/'Makefile').read_text(encoding='utf-8'),re.M)
    if not match or set(match.group(1).split())!=actions:raise RuntimeError('Actions Python et cibles Make incoherentes.')
    p=subprocess.run(['make','--no-print-directory','--dry-run','-C',str(ROOT)]+sorted(actions)+['test','lint','verify','docs'],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr or p.stdout)
    print('Syntaxe Python : '+str(len(files))+' fichiers valides.')
    print('Makefile : '+str(len(actions))+' commandes coherentes et simulation valide.')
    print('Aucun serveur, moteur Docker ou telechargement utilise.')
if __name__=='__main__':
    try:main()
    except Exception as exc:print('ERREUR : '+str(exc),file=sys.stderr);sys.exit(1)
