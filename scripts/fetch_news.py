#!/usr/bin/env python3
"""恵美子新聞 RSS/Atom updater. Standard library only; no article-page scraping."""
from __future__ import annotations
import argparse, hashlib, html, json, logging, os, re, sys, tempfile
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]; CONFIG=ROOT/'public/config/site.json'; OUTPUT=ROOT/'public/data/news.json'
LOG=logging.getLogger('emiko-news')
WHY={
'日本':'制度や社会の変化が、日々の手続きや暮らしに関係するためです。','世界':'海外の変化は、安全保障や物価を通じて日本にも影響する可能性があるためです。','韓国':'隣国の政治・経済・社会を、日韓関係だけに狭めず理解する材料になるためです。','お金と暮らし':'家計、金利、年金、長期的なお金の判断に関わるためです。','アートと技術':'作品制作や研究で使える道具と表現の選択肢につながるためです。','科学と健康':'健康や環境について、根拠のある判断をする材料になるためです。','ちょっといい話':'文化や自然を知る楽しさを、落ち着いて受け取れるためです。'}
TAG_RE=re.compile(r'<[^>]+>'); SPACE_RE=re.compile(r'\s+'); TRACKING={'utm_source','utm_medium','utm_campaign','utm_term','utm_content'}

def clean_text(value:str|None,limit:int=180)->str:
    text=html.unescape(TAG_RE.sub(' ',value or '')); text=SPACE_RE.sub(' ',text).strip()
    if len(text)>limit: text=text[:limit-1].rstrip('、。,. ')+'…'
    return text

def valid_url(value:str)->bool:
    try: u=urlparse(value); return u.scheme in ('http','https') and bool(u.netloc)
    except Exception: return False

def local_name(tag:str)->str:return tag.rsplit('}',1)[-1]

def child_text(node:ET.Element,*names:str)->str:
    for child in list(node):
        if local_name(child.tag) in names:
            if child.text and child.text.strip():return child.text.strip()
            if child.attrib.get('href'):return child.attrib['href']
    return ''

def parse_date(value:str)->datetime:
    if not value:return datetime.now(timezone.utc)
    try:
        dt=parsedate_to_datetime(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception: pass
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'));return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:return datetime.now(timezone.utc)

def fingerprint(title:str)->str:
    return re.sub(r'[\W_]+','',title.lower())

def classify(title:str,summary:str,default:str,cfg:dict)->str:
    if default in ('韓国','ちょっといい話'):
        return default
    hay=(title+' '+summary).lower()
    for category,words in cfg.get('categoryKeywords',{}).items():
        if any(w.lower() in hay for w in words):return category
    return default

def parse_feed(xml_bytes:bytes,source:dict,cfg:dict,fetched:datetime)->list[dict]:
    root=ET.fromstring(xml_bytes); nodes=[n for n in root.iter() if local_name(n.tag) in ('item','entry')]; out=[]
    for node in nodes:
        raw_title=child_text(node,'title'); title=clean_text(raw_title,140)
        url=child_text(node,'link','guid','id')
        if not valid_url(url):
            for c in list(node):
                if local_name(c.tag)=='link' and valid_url(c.attrib.get('href','')):url=c.attrib['href'];break
        desc=child_text(node,'description','summary','content','encoded'); summary=clean_text(desc,180)
        if not title or not valid_url(url):continue
        flags=[word for word in cfg['excludeKeywords'] if word.lower() in (title+' '+summary).lower()]
        if flags:continue
        published=parse_date(child_text(node,'pubDate','published','updated','date'))
        category=classify(title,summary,source['category'],cfg)
        if len(summary)<60:summary=(summary+' ' if summary else '')+'RSSには短い案内だけが掲載されています。詳しい内容と前提は、情報源の元記事で確認できます。'
        summary=clean_text(summary,180)
        fid=fingerprint(title); aid=hashlib.sha256((source['name']+'|'+url).encode()).hexdigest()[:20]
        out.append({'id':aid,'title':title,'url':url,'source':source['name'],'sourceType':source['sourceType'],'publishedAt':published.isoformat(),'fetchedAt':fetched.isoformat(),'category':category,'summary':summary,'whyItMatters':WHY.get(category,WHY['日本']),'readingMinutes':max(1,min(4,round((len(summary)+len(title))/300)+1)),'importance':source['priority'],'language':source['language'],'tags':[category],'duplicateGroup':None,'originalTitle':clean_text(raw_title,200),'filterFlags':[],'aiGenerated':False,'_fingerprint':fid})
    return out

def deduplicate(items:list[dict])->list[dict]:
    kept=[]
    for item in sorted(items,key=lambda x:(x['importance'],x['publishedAt']),reverse=True):
        duplicate=None
        for existing in kept:
            if item['url']==existing['url'] or item['_fingerprint']==existing['_fingerprint'] or SequenceMatcher(None,item['_fingerprint'],existing['_fingerprint']).ratio()>.9:duplicate=existing;break
        if duplicate:
            group=duplicate.get('duplicateGroup') or 'dup-'+hashlib.sha1(duplicate['_fingerprint'].encode()).hexdigest()[:10];duplicate['duplicateGroup']=group
            continue
        kept.append(item)
    return kept

def select_balanced(items:list[dict],cfg:dict)->list[dict]:
    limits=cfg['limits']; cats=cfg['categories']; chosen=[]; counts={c:0 for c in cats}
    for item in items:
        if len(chosen)>=limits['top']:break
        if item['category'] not in [a['category'] for a in chosen] and item.get('source') not in [a.get('source') for a in chosen]:chosen.append(item);counts[item['category']]=counts.get(item['category'],0)+1
    for item in items:
        if len(chosen)>=limits['top']:break
        if item not in chosen and item['category'] not in [a['category'] for a in chosen]:chosen.append(item);counts[item['category']]=counts.get(item['category'],0)+1
    for cat in cats:
        for item in items:
            if len(chosen)>=limits['total'] or counts.get(cat,0)>=2:break
            if item not in chosen and item['category']==cat:chosen.append(item);counts[cat]=counts.get(cat,0)+1
    for cat in cats:
        max_cat=limits.get('goodNews',3) if cat=='ちょっといい話' else limits.get('perCategory',4)
        for item in items:
            if len(chosen)>=limits['total'] or counts.get(cat,0)>=max_cat:break
            if item not in chosen and item['category']==cat:chosen.append(item);counts[cat]=counts.get(cat,0)+1
    for item in items:
        if len(chosen)>=limits['total']:break
        if item not in chosen:chosen.append(item)
    return chosen

def fetch_all(cfg:dict,opener=urlopen)->tuple[list[dict],dict]:
    fetched=datetime.now(timezone.utc); collected=[]; status={}
    for source in cfg['sources']:
        if not source.get('enabled',True):status[source['name']]='disabled: '+source.get('disabledReason','設定で無効');continue
        try:
            req=Request(source['url'],headers={'User-Agent':'EmikoShimbun/1.0 (+personal RSS reader; contact via repository)'}); response=opener(req,timeout=25); payload=response.read(2_000_000); parsed=parse_feed(payload,source,cfg,fetched);collected.extend(parsed);status[source['name']]=f'ok: {len(parsed)}件';LOG.info('%s: %d items',source['name'],len(parsed))
        except Exception as exc:status[source['name']]=f'error: {type(exc).__name__}: {exc}';LOG.warning('%s failed: %s',source['name'],exc)
    return collected,status

def load_previous()->dict:
    try:return json.loads(OUTPUT.read_text(encoding='utf-8'))
    except Exception:return {'updatedAt':None,'articles':[]}

def write_atomic(payload:dict)->None:
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='news-',suffix='.json',dir=OUTPUT.parent);os.close(fd)
    try:Path(tmp).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,OUTPUT)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main()->int:
    global OUTPUT
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=CONFIG);parser.add_argument('--output',type=Path,default=OUTPUT);args=parser.parse_args();OUTPUT=args.output
    cfg=json.loads(args.config.read_text(encoding='utf-8'));previous=load_previous();items,status=fetch_all(cfg)
    if not items:LOG.error('All enabled sources failed or returned no usable items. Previous data retained.');return 0 if previous.get('articles') else 1
    merged=deduplicate(items)
    if len(merged)<15:
        old=[{**a,'_fingerprint':fingerprint(a.get('title',''))} for a in previous.get('articles',[]) if valid_url(a.get('url',''))];merged=deduplicate(merged+old);LOG.warning('Only %d fresh items; merged previous successful data',len(items))
    selected=select_balanced(merged,cfg)
    for item in selected:item.pop('_fingerprint',None)
    payload={'updatedAt':datetime.now(timezone.utc).isoformat(),'articles':selected,'sourceStatus':status,'counts':{'fetched':len(items),'afterDeduplication':len(merged),'published':len(selected)}}
    write_atomic(payload);LOG.info('Published %d balanced items to %s',len(selected),OUTPUT);return 0

if __name__=='__main__':logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s');sys.exit(main())
