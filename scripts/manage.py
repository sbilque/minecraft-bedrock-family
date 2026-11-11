#!/usr/bin/env python3
"""Serveur familial Minecraft Bedrock. Python 3.9+, macOS, bibliotheque standard."""
import contextlib
import datetime as dt
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parents[1]
GAME_DEFAULTS = {'cheats': True, 'keep_inventory': True, 'difficulty': 'easy', 'sleep_percent': 0, 'gamemode': 'survival'}
STEPS = [(900, '15 minutes'), (300, '5 minutes'), (60, '1 minute'), (30, '30 secondes')]
ACTIVE = ('starting', 'scheduled', 'stopping')
PUBLIC_ACTIONS = ('help','setup','check','config','docker-start','doctor','up','start','apply','stop','down','restart','status','logs','logs-once','console','players','xuids','backup','backups','restore','open-backups','open-data','edit','edit-env','pull','update','update-server','version-pin','allowlist-preview','allowlist-sync','allowlist-show','allowlist-enable','allowlist-disable','allowlist-remove','allowlist-edit','allowlist-reload','session','session-status','session-cancel','session-stop','session-logs','session-default','session-default-show','session-default-reset','cheats','keep-inventory','difficulty','sleep','sleep-one','gamemode','gamemode-all','game-show','game-apply','game-defaults')

def say(value): print(value, flush=True)
def atomic(path, value, json_mode=True):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp-'+str(os.getpid()))
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n' if json_mode else value,encoding='utf-8')
    os.replace(str(temp),str(path))
def load(path,default=None):
    path=Path(path)
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
@contextlib.contextmanager
def lock(name,wait=False):
    folder=ROOT/'.state';folder.mkdir(exist_ok=True)
    with (folder/(name+'.lock')).open('a') as f:
        try:fcntl.flock(f,fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        except BlockingIOError:raise RuntimeError('Une autre operation est en cours. Attendre sa fin.')
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)
def raw(args,check=True,timeout=60,env=None):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,env=env)
    if check and p.returncode:raise RuntimeError((p.stderr or p.stdout).strip() or 'Commande en echec')
    return p

def word(value):return ''.join(c for c in unicodedata.normalize('NFKD',value.strip().casefold()) if not unicodedata.combining(c))
def boolean(value):
    v=word(value)
    if v in ('on','true','oui','1','active'):return True
    if v in ('off','false','non','0','desactive'):return False
    raise RuntimeError('Choisir VALUE=on ou VALUE=off.')
def difficulty(value):
    aliases={'facile':'easy','easy':'easy','paisible':'peaceful','peaceful':'peaceful','normale':'normal','normal':'normal','difficile':'hard','hard':'hard'}
    if word(value) not in aliases:raise RuntimeError('LEVEL=facile, paisible, normale ou difficile.')
    return aliases[word(value)]
def gamemode(value):
    aliases={'survie':'survival','survival':'survival','creatif':'creative','creative':'creative','aventure':'adventure','adventure':'adventure'}
    if word(value) not in aliases:raise RuntimeError('MODE=survie, creatif ou aventure.')
    return aliases[word(value)]
def percentage(value):
    if not re.fullmatch(r'\d{1,3}',value or '') or not 0<=int(value)<=100:raise RuntimeError('PERCENT doit etre un entier de 0 a 100.')
    return int(value)
def clock(value):
    if not re.fullmatch(r'\d{2}:\d{2}',value or ''):raise RuntimeError('Heure attendue : HH:MM, par exemple 20:30.')
    h,m=map(int,value.split(':'))
    if h>23 or m>59:raise RuntimeError('Heure invalide : de 00:00 a 23:59.')
    return value
def validate_game(value):
    if not isinstance(value,dict):raise RuntimeError('Les reglages de jeu doivent former un objet JSON.')
    cfg=dict(GAME_DEFAULTS);cfg.update(value)
    for k in ('cheats','keep_inventory'):
        if not isinstance(cfg[k],bool):raise RuntimeError(k+' doit etre true ou false.')
    cfg['difficulty']=difficulty(str(cfg['difficulty']));cfg['gamemode']=gamemode(str(cfg['gamemode']))
    cfg['sleep_percent']=percentage(str(cfg['sleep_percent']))
    return cfg
def settings():
    cfg=load(ROOT/'family-settings.json',{})
    if not isinstance(cfg,dict):raise RuntimeError('Reglages familiaux invalides.')
    game = cfg['game'] if 'game' in cfg else load(ROOT/'game-settings.json',{})
    return {'stop_at':clock(cfg.get('stop_at','19:00')),'game':validate_game(game)}
def update_settings(stop_at=None,game=None):
    with lock('settings',True):
        cfg=settings()
        if stop_at is not None:cfg['stop_at']=clock(stop_at)
        if game is not None:cfg['game']=validate_game(game)
        atomic(ROOT/'family-settings.json',cfg)
    return cfg

def env_read():
    p=ROOT/'.env'
    if not p.exists():raise RuntimeError('Configurer : make setup LAN_IP=192.168.1.50 EULA=TRUE')
    result={}
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            k,v=line.split('=',1);result[k.strip()]=v.strip().strip('"').strip("'")
    return result
def env_update(values):
    p=ROOT/'.env';lines=p.read_text(encoding='utf-8').splitlines() if p.exists() else []
    remaining=dict(values);result=[]
    for line in lines:
        k=line.split('=',1)[0].strip()
        if '=' in line and k in values:
            if k in remaining:result.append(k+'='+str(remaining.pop(k)))
        else:result.append(line)
    result.extend(k+'='+str(v) for k,v in remaining.items());atomic(p,'\n'.join(result)+'\n',False)
def ipv4(value):
    try:ip=ipaddress.IPv4Address(value)
    except ValueError:raise RuntimeError('Utiliser l adresse IPv4 locale du Mac.')
    if ip.is_loopback or ip.is_unspecified or ip.is_multicast:raise RuntimeError('Adresse locale du Mac attendue, pas localhost.')
    return str(ip)
def config_check():
    cfg=env_read();ipv4(cfg.get('LAN_IP',''));settings()
    if cfg.get('EULA','').upper()!='TRUE':raise RuntimeError('Lire les conditions Minecraft et accepter avec EULA=TRUE lors de make setup.')
    return cfg

def game_overlay(cfg):
    return {'services':{'bedrock':{'environment':{'ALLOW_CHEATS':str(cfg['cheats']).lower(),'DIFFICULTY':cfg['difficulty'],'GAMEMODE':cfg['gamemode'],'FORCE_GAMEMODE':'false'}}}}
def ensure_game_overlay():atomic(ROOT/'compose.game.json',game_overlay(settings()['game']))
def compose_env(latest=False):
    env=dict(os.environ)
    for k in ('LAN_IP','EULA','BEDROCK_VERSION'):env.pop(k,None)
    if latest:env['BEDROCK_VERSION']='LATEST'
    return env
def dcargs():
    args=['docker','compose','--project-directory',str(ROOT),'--env-file',str(ROOT/'.env'),'-f',str(ROOT/'compose.yaml')]
    for name in ('compose.allowlist.json','compose.game.json'):
        if (ROOT/name).exists():args+=['-f',str(ROOT/name)]
    return args

def dc(args,echo=False,timeout=240,latest=False):
    p=raw(dcargs()+args,timeout=timeout,env=compose_env(latest))
    if echo:
        if p.stdout:say(p.stdout.rstrip())
        if p.stderr:say(p.stderr.rstrip())
    return p.stdout

def docker_reachable():
    try:return raw(['docker','info'],False,timeout=5).returncode==0
    except (OSError,subprocess.TimeoutExpired):return False

def docker_start():
    if not shutil.which('docker'):raise RuntimeError('Installer et ouvrir Docker Desktop.')
    if not docker_reachable():
        raw(['/usr/bin/open','-a','Docker'],timeout=15);end=time.monotonic()+int(os.getenv('TIMEOUT','120'))
        while not docker_reachable():
            if time.monotonic()>end:raise RuntimeError('Docker ne repond pas. Ouvrir Docker Desktop puis make doctor.')
            time.sleep(2)
    raw(['docker','compose','version'])
def diagnostic():
    say('\n--- Derniers messages Docker (80 lignes maximum) ---')
    try:
        p=raw(dcargs()+['logs','--no-color','--tail=80','bedrock'],False,timeout=20,env=compose_env())
        say((p.stdout+p.stderr).strip() or 'Aucun message disponible.')
        if p.returncode:say('Verifier Docker Desktop et make doctor.')
    except Exception as exc:say('Messages indisponibles : '+str(exc))
def running():return dc(['ps','--status','running','-q','bedrock']).strip()
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
def logs(cid,since=None):
    p=raw(['docker','logs']+(['--since',since] if since else [])+[cid],timeout=20);return p.stdout+p.stderr

def clean(line):
    line=re.sub(r'\x1b\[[0-9;]*m','',line);line=re.sub(r'^\S+Z\s+','',line)
    return re.sub(r'^(?:\[[^\]]*\]\s*)+','',line).strip()
def parse_online(text):
    lines=[clean(x) for x in text.splitlines()];found=None
    for i,line in enumerate(lines):
        m=re.match(r'There are\s+(\d+)\s*/\s*\d+\s+players online\s*:?\s*(.*)',line,re.I)
        if not m:continue
        n=int(m.group(1))
        if n==0:found=[];continue
        names=m.group(2).strip() or (lines[i+1] if i+1<len(lines) else '')
        values=[x.strip() for x in names.split(',') if x.strip()]
        if len(values)==n:found=values
    return found

def send(command,cid=None,reload=False):
    cid=cid or running()
    if not cid:raise RuntimeError('Serveur arrete : lancer make up.')
    since=stamp();dc(['exec','-T','bedrock','send-command',command],timeout=15)
    end=time.monotonic()+6;text=''
    while time.monotonic()<end:
        time.sleep(0.5);text=logs(cid,since)
        if reload:
            if re.search(r'(allowlist|whitelist).*reload|reload.*(allowlist|whitelist)',text,re.I):break
        elif text.strip():break
    if text.strip():say(text.rstrip())
    if re.search(r'syntax error|unknown command|command not found|failed to|\bERROR\b|permission denied',text,re.I):raise RuntimeError('Le jeu a signale une erreur ; les changements deja enregistres ne sont pas annules.')
    if reload and not re.search(r'(allowlist|whitelist).*reload|reload.*(allowlist|whitelist)',text,re.I):raise RuntimeError('Liste enregistree, mais rechargement non confirme. Lire les messages ou faire make restart.')
    if not text.strip():say('Commande transmise sans reponse observee. Verifier make logs-once.')
    return text

def apply_game_rules():
    cfg=settings()['game']
    checks=[('difficulty '+cfg['difficulty'],r'\bdifficulty\b.*\b'+cfg['difficulty']+r'\b'),
            ('gamerule keepinventory '+str(cfg['keep_inventory']).lower(),r'\bkeepinventory\b.*\b'+str(cfg['keep_inventory']).lower()+r'\b'),
            ('gamerule playerssleepingpercentage '+str(cfg['sleep_percent']),r'\bplayerssleepingpercentage\b.*\b'+str(cfg['sleep_percent'])+r'\b')]
    for command,pattern in checks:
        if not re.search(pattern,send(command),re.I):raise RuntimeError('Regle non confirmee : '+command+'. Lire make logs-once.')
    say('Difficulte, inventaire et sommeil confirmes par le serveur.')
def wait_ready():
    cid=running()
    if not cid:raise RuntimeError('Le conteneur ne fonctionne pas.')
    started=raw(['docker','inspect','--format','{{.State.StartedAt}}',cid]).stdout.strip()
    end=time.monotonic()+int(os.getenv('READY_TIMEOUT','180'))
    while time.monotonic()<end:
        if re.search(r'\bServer started\b',logs(cid,started),re.I):apply_game_rules();return
        if not running():raise RuntimeError('Le serveur s est arrete pendant son demarrage.')
        time.sleep(2)
    raise RuntimeError('Demarrage non confirme. Le conteneur peut rester actif ; lire make logs-once.')
def up(latest=False):
    cfg=env_read()
    if cfg.get('BEDROCK_VERSION','LATEST')=='EXISTING' and not (ROOT/'data'/'bedrock_server').is_file():
        say('Premier telechargement : aucun serveur existant. Utilisation de LATEST.');env_update({'BEDROCK_VERSION':'LATEST'})
    ensure_game_overlay();dc(['up','-d','bedrock'],True,latest=latest);wait_ready();say('Serveur pret.')
def stop():
    dc(['stop','bedrock'],True)
    if running():raise RuntimeError('Serveur encore actif : sauvegarde a froid refusee.')

def connected():
    cid=running()
    if not cid:raise RuntimeError('Lancer make up.')
    since=stamp();dc(['exec','-T','bedrock','send-command','list'],timeout=15);names=None
    for _ in range(24):
        time.sleep(0.5);names=parse_online(logs(cid,since))
        if names is not None:break
    if names is None:raise RuntimeError('Liste actuelle non reconnue. Aucun joueur ne sera devine.')
    text='\n'.join(clean(x) for x in logs(cid).splitlines())
    ids={m.group(1).strip().casefold():m.group(2) for m in re.finditer(r'^Player connected:\s*(.*?),\s*xuid:\s*(\d+)',text,re.I|re.M)}
    result=[]
    for name in names:
        if name.casefold() not in ids:raise RuntimeError('XUID absent pour '+name+'. Quitter puis rejoindre le monde.')
        result.append({'name':name,'xuid':ids[name.casefold()],'ignoresPlayerLimit':False})
    return result

def validate_entries(entries):
    if not isinstance(entries,list):raise RuntimeError('La liste doit commencer par [ et finir par ].')
    result=[]
    for e in entries:
        if not isinstance(e,dict) or not isinstance(e.get('name'),str) or not e['name'].strip():raise RuntimeError('Chaque joueur doit avoir un nom.')
        if any(x in e['name'] for x in ':,\n\r'):raise RuntimeError('Nom non pris en charge : '+e['name'])
        if not isinstance(e.get('xuid'),str) or not e['xuid'].isdigit():raise RuntimeError('XUID attendu entre guillemets : '+e['name'])
        if 'ignoresPlayerLimit' in e and not isinstance(e['ignoresPlayerLimit'],bool):raise RuntimeError('ignoresPlayerLimit doit valoir true ou false.')
        result.append(dict(e))
    return result

def merge_entries(entries):
    result=[]
    for e in validate_entries(entries):
        i=next((i for i,x in enumerate(result) if x['name'].casefold()==e['name'].casefold() or x['xuid']==e['xuid']),None)
        if i is None:result.append(e)
        else:result[i].update(e)
    return result

def access(action):
    path=ROOT/'data'/'allowlist.json';other=ROOT/'compose.allowlist.json'
    overlay=load(other,{'services':{'bedrock':{'environment':{}}}});env=overlay.setdefault('services',{}).setdefault('bedrock',{}).setdefault('environment',{})
    configured=[]
    if action!='reload':
        for value in re.split(r'[,\n]',env.get('ALLOW_LIST_USERS','')):
            if not value.strip():continue
            name,sep,xuid=value.strip().rpartition(':')
            if not sep:raise RuntimeError('ALLOW_LIST_USERS invalide.')
            configured.append({'name':name,'xuid':xuid})
    entries=merge_entries(configured+validate_entries(load(path,[])))
    if action=='show':
        for e in entries:say(e['name']+' : '+e['xuid'])
        if not entries:say('Aucun joueur inscrit.')
        return
    if action in ('preview','sync'):
        current=connected();say('Joueurs presents :')
        for e in current:say(e['name']+' : '+e['xuid'])
        if not current:say('Aucun joueur. Aucun changement.');return
        if action=='preview':say('Aucun changement. Pour ajouter : make allowlist-sync');return
        entries=merge_entries(entries+current)
    if action=='remove':
        name=os.getenv('PLAYER','').strip()
        if not name:raise RuntimeError('PLAYER="Nom du joueur" attendu.')
        matches=[e for e in entries if e['name'].casefold()==name.casefold() or e['xuid']==name]
        if not matches:raise RuntimeError('Nom introuvable. Voir make allowlist-show.')
        entries=[e for e in entries if e not in matches]
    if action=='enable' and not entries:raise RuntimeError('Liste vide. Inscrire la famille avant de fermer les entrees.')
    if action=='disable' and os.getenv('CONFIRM')!='yes':raise RuntimeError('Confirmer avec CONFIRM=yes.')
    b=ROOT/'backups'/('allowlist-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));b.mkdir(parents=True)
    for f in (path,other):
        if f.exists():shutil.copy2(str(f),str(b/f.name))
    env['ALLOW_LIST_USERS']='\n'.join(e['name']+':'+e['xuid'] for e in entries)
    if action in ('enable','disable'):env['ALLOW_LIST']='true' if action=='enable' else 'false'
    atomic(other,overlay);atomic(path,entries);say('Liste enregistree ; copie precedente : '+str(b))
    if action in ('enable','disable'):up()
    elif running():send('allowlist reload',reload=True)
    else:say('Liste prete pour le prochain demarrage.')
    if action=='remove':say('Constructions conservees. Si le joueur est encore present : make restart. Ne pas le reinscrire avec sync.')

def archive_filter(info):
    if info.issym() or info.islnk():raise RuntimeError('Lien dans les donnees : verifier avant de sauvegarder.')
    return info

def backup(restart=True,already_stopped=False):
    if not (ROOT/'data').is_dir():raise RuntimeError('Pas de monde : demarrer une premiere fois.')
    active=bool(running())
    if active and already_stopped:raise RuntimeError('Le serveur a redemarre avant la sauvegarde.')
    if active:stop()
    folder=ROOT/'backups';folder.mkdir(exist_ok=True)
    dest=folder/('minecraft-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.tar.gz');part=dest.with_suffix(dest.suffix+'.partial')
    try:
        with tarfile.open(part,'w:gz') as tar:
            for name in ('data','.env','compose.yaml','compose.allowlist.json','compose.game.json','family-settings.json','Makefile','scripts','tests','docs','README.md','README.fr.md','LICENSE'):
                if (ROOT/name).exists():tar.add(ROOT/name,arcname=name,filter=archive_filter)
        with tarfile.open(part,'r:gz') as tar:
            for member in tar:
                if member.isfile():
                    with tar.extractfile(member) as stream:
                        while stream.read(1024*1024):pass
        os.replace(str(part),str(dest));say('Sauvegarde verifiee : '+str(dest))
    finally:
        if active and restart:dc(['start','bedrock'],True)

def safe_members(tar):
    result=[]
    for m in tar.getmembers():
        path=Path(m.name)
        if path.is_absolute() or '..' in path.parts or m.issym() or m.islnk() or not (m.isdir() or m.isfile()):raise RuntimeError('Archive non sure : restauration refusee.')
        if path.parts and path.parts[0]=='data':result.append(m)
    if not result:raise RuntimeError('Archive sans dossier data.')
    return result

def restore():
    name=os.getenv('FILE','')
    if os.getenv('CONFIRM')!='yes' or not name:raise RuntimeError('Utiliser make restore FILE="backups/nom.tar.gz" CONFIRM=yes')
    file=Path(name);file=file if file.is_absolute() else ROOT/file
    with tarfile.open(file,'r:gz') as tar:
        members=safe_members(tar);old_list=validate_entries(load(ROOT/'data'/'allowlist.json',[]))
        cancel_session(True);stop()
        if (ROOT/'data').exists():(ROOT/'data').rename(ROOT/('data-avant-restauration-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')))
        for member in members:
            target=ROOT/member.name
            if member.isdir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(member) as stream,target.open('wb') as dest:shutil.copyfileobj(stream,dest,1024*1024)
        atomic(ROOT/'data'/'allowlist.json',old_list)
    up();say('Monde restaure. Reglages et autorisations actuels conserves.')

def deadline(value,now=None):
    clock(value);now=now or dt.datetime.now().astimezone();h,m=map(int,value.split(':'))
    target=now.replace(hour=h,minute=m,second=0,microsecond=0)
    if target<=now:raise RuntimeError('Heure deja passee aujourd hui. Choisir une heure future.')
    return target

def state_path():return ROOT/'.state'/'session.json'
def state():return load(state_path(),{})
def alive(pid):
    try:os.kill(int(pid),0);return True
    except (OSError,ValueError,TypeError):return False

def cancel_session(quiet=False):
    with lock('session',True):
        s=state()
        if s.get('status')=='stopping':raise RuntimeError('Fermeture en cours : attendre la fin.')
        if s.get('status') not in ACTIVE:
            if not quiet:say('Aucun horaire actif.')
            return
        s['status']='cancelled';atomic(state_path(),s)
    if not quiet:say('Horaire annule sans couper le serveur.')

def start_session():
    target=deadline(os.getenv('STOP_AT','') or settings()['stop_at'])
    with lock('session',True):
        old=state()
        if old.get('status')=='stopping':raise RuntimeError('Fermeture en cours. Lire make session-logs.')
        if old.get('status') in ACTIVE and alive(old.get('pid')):raise RuntimeError('Annuler l horaire actif avant de le remplacer.')
        token=uuid.uuid4().hex;s={'token':token,'pid':os.getpid(),'status':'starting','deadline':target.isoformat()};atomic(state_path(),s)
    try:
        up()
        if target.timestamp()<=time.time():stop();backup(False,True);s['status']='stopped';atomic(state_path(),s);return
        with lock('session',True):
            if state().get('status')=='cancelled':say('Horaire annule pendant le demarrage.');return
            folder=ROOT/'logs';folder.mkdir(exist_ok=True)
            with (folder/'session.log').open('a',encoding='utf-8') as stream:
                p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'_session-worker',token],stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
            s.update(status='scheduled',pid=p.pid);atomic(state_path(),s)
        say('Serveur pret. Fin aujourd hui a '+target.strftime('%H:%M')+'. Garder Mac et Docker allumes.')
    except Exception as exc:
        with lock('session',True):
            s=state()
            if s.get('token')==token and s.get('status')!='cancelled':s.update(status='failed',error=str(exc));atomic(state_path(),s)
        raise

def notice(text):
    try:send('say '+text)
    except Exception as exc:say('Message non confirme : '+str(exc))

def session_worker(token):
    with lock('session',True):
        s=state()
        if s.get('token')!=token or s.get('status')!='scheduled':return
    target=dt.datetime.fromisoformat(s['deadline']);remaining=target.timestamp()-time.time()
    pending={n:label for n,label in STEPS if n<=remaining};awake=None
    try:
        if Path('/usr/bin/caffeinate').exists():awake=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        say('Session : fermeture a '+target.isoformat());initial=True
        while True:
            with lock('session',True):
                s=state()
                if s.get('token')!=token or s.get('status')!='scheduled':say('Surveillance annulee.');return
                remaining=target.timestamp()-time.time()
                if remaining<=0:s['status']='stopping';atomic(state_path(),s);break
            if initial:initial=False;notice('Fin de la partie a '+target.strftime('%H:%M')+'. Sauvegarde automatique ensuite.')
            actual=target.timestamp()-time.time();due=[n for n in pending if actual<=n]
            if due and actual>0:
                n=min(due);label=pending[n]
                for x in due:del pending[x]
                if abs(actual-n)>10:label='environ '+str(max(1,int(actual)))+' secondes'
                notice('Fin de la partie dans '+label+'. Sauvegarde automatique ensuite.')
            time.sleep(min(1,max(0.05,target.timestamp()-time.time())))
        with lock('maintenance',True):config_check();docker_start();stop();backup(False,True)
        with lock('session',True):s=state();s.update(status='stopped',finished_at=stamp());atomic(state_path(),s)
        say('Serveur arrete et sauvegarde terminee. Il reste eteint.')
    except Exception as exc:
        say('ECHEC : '+str(exc));diagnostic()
        with lock('session',True):
            s=state()
            if s.get('token')==token:s.update(status='failed',error=str(exc));atomic(state_path(),s)
    finally:
        if awake is not None:
            awake.terminate()
            try:awake.wait(timeout=5)
            except subprocess.TimeoutExpired:awake.kill()

def show_game(cfg):
    say('Triche : '+('activee' if cfg['cheats'] else 'desactivee'))
    if cfg['cheats']:say('ATTENTION : la triche desactive les succes du monde ; off ensuite ne garantit pas leur retour.')
    say('Inventaire conserve : '+('oui' if cfg['keep_inventory'] else 'non'))
    say('Difficulte : '+{'easy':'facile','peaceful':'paisible','normal':'normale','hard':'difficile'}[cfg['difficulty']])
    say('Sommeil : '+('un joueur suffit (0 %)' if cfg['sleep_percent']==0 else str(cfg['sleep_percent'])+' %'))
    say('Mode par defaut : '+{'survival':'survie','creative':'creatif','adventure':'aventure'}[cfg['gamemode']])
    say('Choix memorises, pas une mesure du monde en direct.')
def game_action(action):
    if action=='game-show':show_game(settings()['game']);return
    with lock('maintenance'):
        cfg=settings()['game']
        if action=='cheats':cfg['cheats']=boolean(os.getenv('VALUE',''))
        elif action=='keep-inventory':cfg['keep_inventory']=boolean(os.getenv('VALUE',''))
        elif action=='difficulty':cfg['difficulty']=difficulty(os.getenv('LEVEL',''))
        elif action=='sleep':cfg['sleep_percent']=percentage(os.getenv('PERCENT',''))
        elif action=='sleep-one':cfg['sleep_percent']=0
        elif action=='gamemode':cfg['gamemode']=gamemode(os.getenv('MODE',''))
        elif action=='game-defaults':cfg=dict(GAME_DEFAULTS)
        elif action=='gamemode-all':
            mode=gamemode(os.getenv('MODE',''));config_check();docker_start();send('gamemode '+mode+' @a')
            say('Commande pour les joueurs presents uniquement. Le mode par defaut ne change pas.');return
        elif action!='game-apply':raise RuntimeError('Reglage inconnu.')
        update_settings(game=cfg);ensure_game_overlay();show_game(cfg)
        if action=='game-apply':config_check();docker_start();up()
        elif docker_reachable() and (ROOT/'.env').exists() and running():config_check();up()
        else:say('Choix prets pour le prochain demarrage avec Make.')

def setup():
    ip=ipv4(os.getenv('LAN_IP','').strip())
    if os.getenv('EULA','').upper()!='TRUE':raise RuntimeError('Lire les conditions Minecraft puis ajouter EULA=TRUE si vous les acceptez.')
    with lock('maintenance'):
        values={'LAN_IP':ip,'EULA':'TRUE'}
        if not (ROOT/'.env').exists():values['BEDROCK_VERSION']='LATEST'
        env_update(values);update_settings();ensure_game_overlay()
        for name in ('data','backups','logs'):(ROOT/name).mkdir(exist_ok=True)
    say('Configuration prete. Attention : triche activee par defaut, succes du monde desactives. make check puis make up.')

def main():
    action=sys.argv[1] if len(sys.argv)>1 else 'help'
    if action=='_session-worker':session_worker(sys.argv[2]);return
    if action not in PUBLIC_ACTIONS:raise RuntimeError('Commande inconnue. Utiliser make.')
    if action=='help':
        language = 'fr' if os.getenv('LANGUAGE', 'en').lower() == 'fr' else 'en'
        say((ROOT / 'docs' / language / 'commands.txt').read_text(encoding='utf-8'))
        return
    if action=='setup':setup();return
    if action in ('cheats','keep-inventory','difficulty','sleep','sleep-one','gamemode','gamemode-all','game-show','game-apply','game-defaults'):game_action(action);return
    if action.startswith('session-default'):
        if action=='session-default':cfg=update_settings(stop_at=clock(os.getenv('TIME','')))
        elif action=='session-default-reset':cfg=update_settings(stop_at='19:00')
        else:cfg=settings()
        say('Heure habituelle : '+cfg['stop_at']+'. Les parties deja programmees ne changent pas.');return
    if action=='session-status':
        s=state();say('Etat : '+s.get('status','aucun'));say('Fermeture prevue : '+s.get('deadline','aucune'))
        if s.get('status') in ('starting','scheduled') and not alive(s.get('pid')):say('ATTENTION : surveillance inactive. Reprogrammer la partie.')
        if s.get('error'):say('Erreur : '+s['error'])
        return
    if action=='session-cancel':cancel_session();return
    if action=='session-logs':
        p=ROOT/'logs'/'session.log';say('\n'.join(p.read_text(encoding='utf-8',errors='replace').splitlines()[-100:]) if p.exists() else 'Aucun message.');return
    if action in ('edit','edit-env','open-data','open-backups','allowlist-edit'):
        p=ROOT/{'edit':'compose.yaml','edit-env':'.env','open-data':'data','open-backups':'backups','allowlist-edit':'data/allowlist.json'}[action]
        if action=='allowlist-edit' and not p.exists() and (ROOT/'data').is_dir():atomic(p,[])
        if not p.exists():raise RuntimeError('Fichier absent : configurer ou demarrer une premiere fois.')
        raw(['/usr/bin/open']+(['-e'] if action in ('edit','edit-env','allowlist-edit') else [])+[str(p)]);return
    if action=='backups':
        for p in sorted((ROOT/'backups').glob('minecraft-*.tar.gz')):say(str(p.relative_to(ROOT)))
        return
    if action=='doctor':
        for cmd in (['docker','context','ls'],['docker','info'],['docker','compose','version'],['python3','--version']):
            try:p=raw(cmd,False,timeout=15);say(p.stdout+p.stderr)
            except Exception as exc:say(str(exc))
        say(str({k:v for k,v in os.environ.items() if k.startswith('DOCKER_')}));return
    if action=='docker-start':docker_start();return
    config_check();docker_start()
    if action in ('check','config'):dc(['config','--quiet']);say('Configuration valide.');return
    if action=='status':dc(['ps','-a'],True);return
    if action in ('logs','logs-once'):
        args=['logs','--tail='+str(int(os.getenv('TAIL','100'))),'bedrock']
        if action=='logs':args.insert(1,'-f')
        p=subprocess.run(dcargs()+args,env=compose_env())
        if p.returncode not in (0,130):raise RuntimeError('Lecture des messages en echec.')
        return
    if action=='console':
        value=os.getenv('CMD','').strip()
        if not value:raise RuntimeError('Exemple : make console CMD="say Bonjour"')
        send(value);return
    if action=='players':
        for e in connected():say(e['name']+' : '+e['xuid'])
        return
    if action=='xuids':
        cid=running()
        if not cid:raise RuntimeError('Demarrer le serveur ou utiliser make logs-once.')
        say('\n'.join(x for x in logs(cid).splitlines() if 'xuid' in x.lower()) or 'Aucun identifiant.');return
    with lock('maintenance'):
        if action in ('up','start','apply'):up()
        elif action=='session':start_session()
        elif action in ('stop','down','session-stop'):
            cancel_session(True)
            if action=='down':dc(['down'],True)
            else:
                stop()
                if action=='session-stop':backup(False,True)
        elif action=='restart':dc(['restart','bedrock'],True);wait_ready()
        elif action=='backup':backup()
        elif action=='restore':restore()
        elif action=='pull':dc(['pull','bedrock'],True,timeout=None)
        elif action in ('update','update-server'):
            cancel_session(True);backup();dc(['pull','bedrock'],True,timeout=None)
            ensure_game_overlay();dc(['up','-d','--force-recreate','bedrock'],True,latest=action=='update-server');wait_ready()
            if action=='update-server':env_update({'BEDROCK_VERSION':'EXISTING'});say('Version telechargee conservee. Verifier les appareils iOS et Windows.')
        elif action=='version-pin':env_update({'BEDROCK_VERSION':'EXISTING'});say('Version installee conservee aux prochains demarrages.')
        elif action.startswith('allowlist-'):access(action[len('allowlist-'):])
        else:raise RuntimeError('Commande inconnue.')

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:say('Interrompu. Le serveur n est pas automatiquement arrete.');sys.exit(130)
    except (RuntimeError,OSError,ValueError,KeyError,tarfile.TarError,subprocess.TimeoutExpired) as exc:
        say('ERREUR : '+str(exc))
        if len(sys.argv)>1 and sys.argv[1] not in ('setup','help','session-default','session-default-show','session-default-reset'):diagnostic()
        sys.exit(1)

