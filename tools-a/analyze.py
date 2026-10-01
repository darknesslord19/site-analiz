#!/usr/bin/env python3
# Site analizcisi: GitHub Actions makinesinde çalışır (CORS yok). Sayfaları indirir, yapıyı ve uç noktaları bulur.
import json,re,sys,time,gzip,zlib,os,urllib.request,urllib.error,http.cookiejar
from urllib.parse import urljoin,urlparse,quote
from bs4 import BeautifulSoup
UA='Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36'
JAR=http.cookiejar.CookieJar()
OPENER=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))
def real_fetch(url,method='GET',headers=None,body=None,timeout=20):
    req=urllib.request.Request(url,data=body,method=method,headers=headers or {})
    try:
        r=OPENER.open(req,timeout=timeout);st=r.status
    except urllib.error.HTTPError as e: r=e;st=e.code
    raw=r.read();enc=(r.headers.get('Content-Encoding') or '').lower()
    try:
        if enc=='gzip': raw=gzip.decompress(raw)
        elif enc=='deflate': raw=zlib.decompress(raw)
    except Exception: pass
    return st,r.geturl(),dict(r.headers.items()),raw.decode('utf-8','replace')
FETCH=real_fetch
SITE='';Q='love';REQ=0
def sleep(s):
    if not os.environ.get('NO_SLEEP'): time.sleep(s)
def absu(u,b=None):
    try: return urljoin(b or SITE+'/',u)
    except Exception: return None
def host(u):
    try: return urlparse(u).hostname.replace('www.','')
    except Exception: return ''
def same_host(u): return host(u)==host(SITE)
def get(url,accept=None,headers=None,method='GET',body=None,timeout=20):
    global REQ;REQ+=1
    h={'User-Agent':UA,'Accept':accept or 'text/html,application/json;q=0.9,*/*;q=0.8','Accept-Language':'tr-TR,tr;q=0.9,en;q=0.8','Accept-Encoding':'gzip, deflate'}
    h.update(headers or {})
    try:
        st,fu,hd,tx=FETCH(url,method,h,body,timeout)
        return {'ok':200<=st<300,'status':st,'url':fu or url,'text':tx,'len':len(tx)}
    except Exception as e:
        return {'ok':False,'status':0,'url':url,'error':str(e),'text':'','len':0}
def blocked(r):
    return r['status'] in (403,429,503) or bool(re.search(r'Just a moment|cf-chl|Attention Required|captcha|Enable JavaScript and cookies',(r['text'] or '')[:4000],re.I))
def txt(s): return re.sub(r'\s+',' ',s or '').strip()
STATE=re.compile(r'^(active|current|selected|open|show|is-[\w-]+|has-[\w-]+|disabled|hidden)$',re.I)
def selof(el):
    c=[x for x in (el.get('class') or []) if x and not STATE.match(x)]
    return el.name+('.'+'.'.join(c) if c else '')
def soup(t): return BeautifulSoup(t,'html.parser')

def page_info(s,base):
    meta=lambda n:(s.select_one(f'meta[property="{n}"]') or s.select_one(f'meta[name="{n}"]') or {}).get('content','') if (s.select_one(f'meta[property="{n}"]') or s.select_one(f'meta[name="{n}"]')) else ''
    scripts=[absu(e['src'],base) for e in s.select('script[src]')]
    ep=[]
    for e in s.find_all(True):
        for k in ('data-action','data-url','data-endpoint','data-api','data-src-url','data-load-more-url'):
            if e.get(k): ep.append(f'{k}={e[k]}')
    forms=[{'action':absu(f.get('action') or '',base),'method':(f.get('method') or 'get').lower(),'inputs':[i.get('name') for i in f.select('input[name],select[name],textarea[name]')]} for f in s.select('form')][:6]
    csrf=''
    for sel,att in (('meta[name="csrf-token"]','content'),('meta[name="csrf"]','content'),('input[name="_token"]','value'),('input[name="csrf_token"]','value')):
        e=s.select_one(sel)
        if e and e.get(att): csrf=e[att];break
    if not csrf:
        e=s.select_one('[data-csrf]')
        if e: csrf=e['data-csrf']
    inputs=[{'sel':selof(e)+('#'+e['id'] if e.get('id') else ''),'name':e.get('name',''),'placeholder':e.get('placeholder','')} for e in s.select('input[type=search],input[name=q],input[name=search],input[name=s],input.search-input,input[id*=earch]')][:3]
    return {'title':txt(s.title.text if s.title else ''),'h1':txt(s.h1.text if s.h1 else ''),'ogTitle':meta('og:title'),'ogImage':meta('og:image'),'description':meta('description'),'csrf':bool(csrf),'scripts':scripts,'inlineScripts':len([x for x in s.find_all('script') if not x.get('src')]),'dataEndpoints':ep[:20],'forms':forms,'searchInputs':inputs}

def card_pattern(s,base,minu=4):
    groups={}
    for a in s.find_all('a',href=True):
        h=absu(a['href'],base)
        if not h or not same_host(h): continue
        p=urlparse(h).path
        if not re.match(r'^/(dizi|film|series|movie|izle|anime)\b',p) and not re.search(r'-izle\b',p): continue
        if re.search(r'/(bolum|episode|sezon|season)[-/]',p): continue
        groups.setdefault(selof(a),[]).append((a,h))
    best=None
    for k,v in groups.items():
        u=len({h for _,h in v})
        if u>=minu and (best is None or u>best[2]): best=(k,v,u)
    if not best: return None
    k,v,u=best;items=[]
    for a,h in v[:3]:
        img=a.find('img');cands=[(selof(c),txt(c.get_text())) for c in a.find_all(True) if not c.find(True) and len(txt(c.get_text()))>1]
        cands.sort(key=lambda x:-len(x[1]));t=cands[0] if cands else None
        items.append({'href':h,'title':t[1] if t else txt(a.get('title') or (img.get('alt') if img else '')),'titleSel':t[0] if t else '','img':(img.get('data-src') or img.get('src') or '') if img else '','imgAlt':(img.get('alt') or '') if img else ''})
    first_img=v[0][0].find('img')
    hrefs=[];[hrefs.append(h) for _,h in v if h not in hrefs]
    return {'anchorSel':k,'count':u,'titleSel':items[0]['titleSel'],'posterAttr':'data-src' if (first_img and first_img.get('data-src')) else 'src','samples':items,'hrefs':hrefs}

def episodes(s,base):
    links=s.select('a[href*="/bolum-"],a[href*="/episode"],a[href*="/bolum/"]')
    if not links: return None
    g={}
    for e in links: g.setdefault(selof(e),[]).append(e)
    k=max(g,key=lambda x:len(g[x]));l=g[k];e0=l[0];par=e0.parent
    nums=[c for c in e0.find_all(True) if re.fullmatch(r'\d+',txt(c.get_text()))]
    cls=[c for c in (e0.get('class') or []) if c]
    tit=[c for c in e0.find_all(True) if not c.find(True) and re.search(r'title|name|baslik|ad\b',' '.join(c.get('class') or []),re.I)]
    return {'itemSel':k,'itemClass':('.'+'.'.join(cls)) if cls else k,'count':len(l),'containerSel':selof(par) if par else '','seasonAttr':'data-season' if par and par.get('data-season') else '','numSel':selof(nums[0]) if nums else '','titleSel':selof(tit[0]) if tit else '','sample':[{'href':absu(x['href'],base),'text':txt(x.get_text())} for x in l[:2]]}

def players(s,base):
    frames=[absu(e.get('data-src') or e.get('src'),base) for e in s.select('iframe[data-src],iframe[src]')]
    tabs=[txt(e.get_text()) for e in s.select('button[data-index],[class*=tab][data-index]') if txt(e.get_text())]
    return [{'url':u,'label':tabs[i] if i<len(tabs) else '','host':urlparse(u).hostname} for i,u in enumerate(frames) if u]

def player_cfg(s):
    fr=s.select_one('iframe[data-src],iframe[src]')
    if not fr: return None
    par=fr.parent
    tabs=s.select('button[data-index],[class*=tab][data-index]')
    return {'attr':'data-src' if fr.get('data-src') else 'src','box':selof(par) if par and par.name!='body' else '','labelSel':selof(tabs[0]) if tabs else ''}

def series_detail(s,base):
    kw=re.compile(r'desc|summary|plot|konu|ozet|özet|about|overview',re.I)
    o={}
    o['plotCands']=[{'sel':selof(e),'len':len(txt(e.get_text()))} for e in s.find_all(True) if kw.search(' '.join(e.get('class') or [])) and not e.find_parent('footer') and len(txt(e.get_text()))>80 and len(e.find_all(True,recursive=False))<4][:4]
    o['posterCands']=[{'sel':selof(e),'parent':selof(e.parent),'attr':'data-src' if e.get('data-src') else 'src'} for e in s.find_all('img') if re.search(r'poster|cover|thumb',' '.join(e.get('class') or [])+' '+' '.join(e.parent.get('class') or []),re.I)][:3]
    o['genreLinks']=[{'sel':selof(e),'text':txt(e.get_text())} for e in s.select('a[href*="/tur/"],a[href*="/kategori/"],a[href*="/genre/"],a[href*="/turler/"]')][:5]
    o['badges']=[{'sel':selof(e),'text':txt(e.get_text())} for e in s.select('[class*=badge],[class*=meta]') if not e.find(True) and len(txt(e.get_text()))<30][:8]
    return o

def js_hints(js):
    urls=[];want=re.compile(r'(search|/ara\b|arama|suggest|autocomplete|ajax|/api/|query|filtre|filter|load|more|page|sayfa|episode|bolum)',re.I)
    for m in re.finditer(r'''["'`]((?:https?:)?//[^"'`\s]{4,}|/[A-Za-z0-9_\-/.{}$?=&%]{2,})["'`]''',js):
        u=m.group(1)
        if want.search(u) and not re.search(r'\.(css|png|jpe?g|webp|svg|gif|woff2?|ico|js)(\?|$)',u,re.I) and u not in urls: urls.append(u)
    calls=[txt(m.group(0))[:170] for m in re.finditer(r'(fetch|axios\.(?:get|post)|\$\.(?:get|post|ajax|getJSON)|\.open)\(\s*([^,)]{3,160})',js)][:25]
    near=[]
    for k in ('autosuggest','searchInput','headerSearch','tvSearch'):
        i=js.find(k)
        if i>=0: near.append(k+': '+txt(js[max(0,i-150):i+250]))
    return {'urls':urls[:40],'calls':calls,'near':near[:3]}

def unpack(src):
    m=re.search(r"}\('([\s\S]*)',(\d+),(\d+),'([\s\S]*?)'\.split\('\|'\)",src)
    if not m: return None
    p=m.group(1).replace("\\'","'");a=int(m.group(2));c=int(m.group(3));k=m.group(4).split('|')
    def e(n):
        return ('' if n<a else e(n//a))+(chr(n%a+29) if n%a>35 else _b36(n%a))
    for i in range(c-1,-1,-1):
        if i<len(k) and k[i]: p=re.sub(r'\b'+re.escape(e(i))+r'\b',lambda _:k[i],p)
    return p
def _b36(n):
    d='0123456789abcdefghijklmnopqrstuvwxyz';return d[n]

def classify(r,q):
    t=(r['text'] or '').strip()
    if not r['ok'] or not t: return {'type':'yok','score':0,'count':0}
    ql=q.lower()
    if t[0] in '{[':
        try: j=json.loads(t)
        except Exception: return {'type':'bozuk json','score':0,'count':0}
        arrs=[]
        def walk(v,d):
            if d>3 or not v: return
            if isinstance(v,list):
                if v and isinstance(v[0],dict): arrs.append(v)
                for x in v[:3]: walk(x,d+1)
            elif isinstance(v,dict):
                for x in v.values(): walk(x,d+1)
        walk(j,0)
        if not arrs: return {'type':'json (liste yok)','score':0,'count':0}
        a=max(arrs,key=len);hit=sum(1 for o in a if ql in json.dumps(o,ensure_ascii=False).lower())
        return {'type':'json','count':len(a),'score':hit*3+len(a),'keys':list(a[0].keys())[:12],'sample':[str(o.get('title') or o.get('name') or o.get('baslik') or o.get('ad') or json.dumps(o,ensure_ascii=False)[:60]) for o in a[:3]]}
    s=soup(t);cards=s.select('a.autosuggest-item,a.poster-card');lst=cards or s.select('a[href*="/dizi/"],a[href*="/film/"]')
    hit=sum(1 for e in lst if ql in (txt(e.get_text())+' '+((e.find('img') or {}).get('alt','') if e.find('img') else '')).lower())
    cp=card_pattern(s,SITE,1)
    return {'type':'html','count':len(lst),'score':hit*3+len(lst),'sample':[txt(e.get_text())[:50] for e in lst[:3]],'sel':selof(cards[0]) if cards else '',
            'cardSel':(cp['anchorSel'] if cp else (selof(cards[0]) if cards else 'a[href*="/dizi/"]')),'cardTitle':cp['titleSel'] if cp else '','cardPoster':cp['posterAttr'] if cp else 'src'}

BAD=re.compile(r'giris|kayit|login|register|logout|iletisim|hakkimizda|contact|about|dmca|gizlilik|privacy|uyelik|profil|sifre|cerez|kullanim|reklam|forum|seviye|gruplar|testler|\.(jpg|png|svg|css|js)$',re.I)
def heading_before(a):
    for par in list(a.parents)[:5]:
        h=par.find(['h1','h2','h3','h4'])
        if h and 2<=len(txt(h.get_text()))<=60: return txt(h.get_text())
    return ''
def discover(s,base):
    cands=[];seen=set()
    hc=card_pattern(s,base);pref={urlparse(h).path.strip('/').split('/')[0] for h in (hc['hrefs'] if hc else [])}
    def add(name,u):
        if not u or not same_host(u): return
        p=urlparse(u).path.rstrip('/')
        if not p or p in seen or BAD.search(p): return
        segs=[x for x in p.split('/') if x]
        if len(segs)>=2 and segs[0] in pref: return
        seen.add(p);cands.append((name,u))
    for a in s.find_all('a',href=True):
        t=txt(a.get_text())
        if re.search(r'tümünü|tümü|view all|see all|hepsi|daha fazla',t,re.I): add(heading_before(a) or t,absu(a['href'],base))
    for a in s.select('nav a[href],header a[href],aside a[href],[class*=menu] a[href],[class*=sidebar] a[href]'):
        t=txt(a.get_text())
        if 2<=len(t)<=28: add(t,absu(a['href'],base))
    cats=[]
    for name,u in cands[:16]:
        if len(cats)>=10: break
        r=get(u);sleep(.25)
        if not r['text'] or blocked(r): continue
        cp=card_pattern(soup(r['text']),r['url'])
        if '\ufffd' in name or re.search(r'tümünü|tümü|view all|see all|hepsi|daha fazla',name,re.I) or re.fullmatch(r'\d+\s.*',name): name=urlparse(u).path.strip('/').split('/')[-1].replace('-',' ').title()
        if cp and cp['count']>=4: cats.append({'name':re.sub(r'\s*[-|:].*$','',name)[:40] or urlparse(u).path.strip('/'),'path':urlparse(r['url']).path+(('?'+urlparse(r['url']).query) if urlparse(r['url']).query else ''),'count':cp['count'],'hrefs':cp['hrefs'][:80]})
    return cats

def site_names(s):
    h=host(SITE).split('.')[0] or 'site'
    parts=[p for p in re.split(r'[^A-Za-z0-9]+',h) if p]
    cls=''.join(p[:1].upper()+p[1:] for p in parts) or 'Site'
    if not cls[0].isalpha(): cls='Site'+cls
    og=(s.select_one('meta[property="og:site_name"]') or {}).get('content','') if s.select_one('meta[property="og:site_name"]') else ''
    ttl=txt(s.title.text if s.title else '')
    disp=og or re.split(r'\s+[-|–]\s+',ttl)[0] or cls
    return cls,(disp if 2<=len(disp)<=30 else cls)

def pick_query(cards):
    for it in (cards or {}).get('samples',[]):
        for w in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]{3,}",it.get('title') or ''):
            return w.lower()
    return 'love'

MEDIA=re.compile(r'''https?:(?:\\?/){2}[^"'\s\\<>]+?\.(?:m3u8|mp4|mpd)[^"'\s\\<>]*''')
FILE=re.compile(r'''file\s*:\s*["']([^"']+)["']''')

def main(cfg_path):
    global SITE,Q
    cfg=json.load(open(cfg_path,encoding='utf8'));SITE=cfg['site'].rstrip('/');Q=cfg.get('query') or 'love'
    R={'site':SITE,'time':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'query':Q,'pages':{},'blocked':{},'js':{},'search':{},'pagination':{},'players':[],'notes':[]}
    docs={};discovered=None;cats=[]
    pages=dict(cfg.get('pages') or {})
    if not pages.get('list') or not pages.get('series') or not pages.get('episode'):
        r0=get(SITE+'/');sleep(.25)
        if r0['text'] and not blocked(r0):
            s0=soup(r0['text']);cats=discover(s0,r0['url']);R['categories']=[{k:v for k,v in c.items() if k!='hrefs'} for c in cats]
            marker=''
            allh=[h for c in cats for h in c['hrefs']]
            for pre in ('/film/','/movie/','/filmler/'):
                if any(urlparse(h).path.startswith(pre) for h in allh): marker=pre;break
            ser=next((h for h in allh if not marker or not urlparse(h).path.startswith(marker)),None)
            flm=next((h for h in allh if marker and urlparse(h).path.startswith(marker)),None)
            pages.setdefault('home','/')
            if cats and not pages.get('list'): pages['list']=cats[0]['path']
            if ser and not pages.get('series'): pages['series']=urlparse(ser).path
            if flm and not pages.get('film'): pages['film']=urlparse(flm).path
            R['discovered']={'categories':len(cats),'series':pages.get('series'),'film':pages.get('film'),'list':pages.get('list'),'movieMarker':marker}
            if pages.get('series') and not pages.get('episode'):
                rs=get(absu(pages['series']));sleep(.25)
                if rs['text'] and not blocked(rs):
                    ep0=episodes(soup(rs['text']),rs['url'])
                    if ep0 and ep0['sample']: pages['episode']=urlparse(ep0['sample'][-1]['href']).path
                    elif ep0 is None:
                        # bölüm bağlantısı ana sayfada olabilir
                        e1=episodes(s0,r0['url'])
                        if e1 and e1['sample']: pages['episode']=urlparse(e1['sample'][0]['href']).path
            R['discovered']['episode']=pages.get('episode')
            if not pages.get('home'): pages['home']='/'
        else: R['notes'].append('Ana sayfa okunamadı, sayfalar otomatik bulunamadı.')
    cfg['pages']=pages
    for name,p in (cfg.get('pages') or {}).items():
        if not p: continue
        u=absu(p);r=get(u);sleep(.25)
        b=blocked(r);R['blocked'][name]=str(r['status'] or r.get('error')) if b else False
        R['pages'][name]={'url':u,'status':r['status'],'length':r['len']}
        if r.get('error'): R['pages'][name]['error']=r['error']
        if not r['text'] or b: continue
        s=soup(r['text']);docs[name]={'s':s,'r':r,'base':r['url']}
        info=page_info(s,r['url']);R['pages'][name]['info']=info
        cp=card_pattern(s,r['url'])
        if cp: R['pages'][name]['cards']={k:v for k,v in cp.items() if k!='hrefs'};R['pages'][name]['cards']['sampleHrefs']=cp['hrefs'][:3]
        ep=episodes(s,r['url'])
        if ep: R['pages'][name]['episodes']=ep
        pl=players(s,r['url'])
        if pl: R['pages'][name]['players']=pl
        if name in('series','film'): R['pages'][name]['detail']=series_detail(s,r['url'])
    if not docs: R['notes'].append('Hiçbir sayfa okunamadı (engel ya da bağlantı sorunu).')
    if not cfg.get('query'):
        qsrc=None
        for n_ in ('home','list'):
            qsrc=(R['pages'].get(n_,{}).get('cards')) if R['pages'].get(n_) else None
            if qsrc: break
        Q=pick_query(qsrc);R['query']=Q
    # JS
    scripts=[]
    for n in docs:
        for u in R['pages'][n]['info']['scripts']:
            if same_host(u) and u not in scripts: scripts.append(u)
    urls=[];calls=[];near=[];okc=0
    for sc in scripts[:15]:
        r=get(sc,accept='*/*',timeout=25);sleep(.15)
        if not r['ok'] or r['len']>3_000_000: continue
        okc+=1;h=js_hints(r['text']);[urls.append(u) for u in h['urls'] if u not in urls]
        calls+=[c+'  ['+sc.split('/')[-1].split('?')[0]+']' for c in h['calls']];near+=h['near']
    R['js']={'scripts':scripts,'okCount':okc,'urls':urls[:50],'calls':calls[:30],'near':near[:4]}
    # arama
    csrf=''
    for d in docs.values():
        e=d['s'].select_one('meta[name="csrf-token"],meta[name="csrf"]')
        if e and e.get('content'): csrf=e['content'];break
    std=['/ara?q=','/arama?q=','/search?q=','/ajax/search?q=','/api/search?q=','/ajax/ara?q=','/ajax/autosuggest?q=','/autosuggest?q=','/search/autosuggest?q=','/?s=','/dizi-arsivi?q=','/dizi-arsivi?search=','/ara/{q}','/arama/{q}','/search/{q}']
    cand=[]
    def add(p,m='GET'):
        k=m+' '+p
        if not any(c['k']==k for c in cand): cand.append({'k':k,'p':p,'m':m})
    for u in R['js']['urls']:
        if not re.search(r'(search|ara\b|arama|suggest|autocomplete|ajax/|api/)',u,re.I): continue
        rel=u.replace(SITE,'')
        if re.search(r'[?&][a-z_]+=$',rel,re.I) or '{q}' in rel: add(rel)
        else:
            for k in ('q','term','query','search','keyword'): add(rel+('&' if '?' in rel else '?')+k+'=')
            add(rel.rstrip('/')+'/{q}');add(rel,'POST')
    for s_ in std: add(s_)
    home_text=docs['home']['r']['text'][:300] if 'home' in docs else ''
    tried=[];best=None
    for c in (cand[:60] if docs else []):
        q=quote(Q)
        u=SITE+(c['p'].replace('{q}',q) if '{q}' in c['p'] else (c['p']+q if c['m']=='GET' else c['p']))
        hd={'X-Requested-With':'XMLHttpRequest','Referer':SITE+'/'};body=None;m='GET'
        if c['m']=='POST':
            m='POST';hd['Content-Type']='application/x-www-form-urlencoded; charset=UTF-8'
            if csrf: hd['X-CSRF-TOKEN']=csrf
            body=('q='+q+'&query='+q+'&term='+q+('&_token='+quote(csrf) if csrf else '')).encode()
        r=get(u,headers=hd,method=m,body=body);sleep(.25)
        cl=classify(r,Q)
        if cl['type']=='html' and home_text and r['text'][:300]==home_text: cl={'type':'ana sayfaya düşüyor','score':0,'count':0}
        tried.append({'url':u,'method':c['m'],'status':r['status'],'type':cl['type'],'count':cl['count'],'score':cl['score']})
        if cl['score']>0 and (best is None or cl['score']>best['score']): best={'url':u,'path':c['p'],'method':c['m'],'status':r['status'],**cl}
    R['search']={'best':best,'tried':tried}
    # sayfalama
    L=docs.get('list') or docs.get('home')
    if L:
        key='list' if 'list' in docs else 'home';base_url=R['pages'][key]['url']
        c1=card_pattern(L['s'],L['base']);h1=c1['hrefs'] if c1 else []
        pt=[];ok=None
        for p in ['?page={n}','?sayfa={n}','?p={n}','/page/{n}','/sayfa/{n}','?paged={n}','?pg={n}']:
            u=base_url.rstrip('/')+p.replace('{n}','2');r=get(u);sleep(.25);v='yok'
            if r['ok'] and not blocked(r):
                c2=card_pattern(soup(r['text']),r['url']);h2=c2['hrefs'] if c2 else []
                ov=len([x for x in h2 if x in h1])
                v='kart yok' if not h2 else ('aynı sayfa' if (h2[0]==(h1[0] if h1 else None) or ov>len(h2)/2) else 'çalışıyor')
            pt.append({'pattern':p,'url':u,'status':r['status'],'verdict':v})
            if v=='çalışıyor' and not ok: ok=p
        hints=[];s=L['s']
        for e in s.select('link[rel=next],a[rel=next]'): hints.append('rel=next '+str(e.get('href')))
        for e in s.select('.pagination a[href],[class*=pagin] a[href]')[:4]: hints.append('sayfalama bağlantısı '+e['href'])
        for e in s.select('[data-next],[data-page],[data-load-more],[data-load-more-scope]')[:4]:
            hints.append('yükle-daha-fazla: '+' '.join(f'{k}={str(v)[:60]}' for k,v in e.attrs.items() if k.startswith('data-')))
        R['pagination']={'page':key,'pattern':ok,'tried':pt,'hints':hints}
    # oynatıcılar
    if 'episode' in docs:
        seen=set()
        for pl in (R['pages']['episode'].get('players') or [])[:5]:
            if pl['host'] in seen: continue
            seen.add(pl['host']);r=get(pl['url'],headers={'Referer':SITE+'/'});sleep(.3)
            it={'label':pl['label'],'host':pl['host'],'url':pl['url'],'status':r['status'],'blocked':bool(blocked(r)),'media':[],'packed':False,'vidmolyRegex':False}
            if r['text']:
                t=r['text'];pk=bool(re.search(r'eval\(function\(p,a,c,k,e,[dr]\)',t));it['packed']=pk
                if pk:
                    un=unpack(t)
                    if un: t+='\n'+un
                m=[];[m.append(x.replace('\\/','/')) for x in MEDIA.findall(t) if x.replace('\\/','/') not in m]
                for x in FILE.findall(t):
                    if re.match(r'^(https?:|//)',x) and x not in m: m.append(x)
                it['media']=m[:5];it['vidmolyRegex']=bool(re.search(r'''file:\s*["']([^"']+\.m3u8[^"']*)["']''',t))
                it['frames']=[absu(e.get('src') or e.get('data-src'),pl['url']) for e in soup(r['text']).select('iframe[src],iframe[data-src]')][:3]
            mid=re.search(r'/(?:e|embed|v|video)[/-]([A-Za-z0-9_-]{6,})',pl['url'])
            if mid and re.search(r'(byse|filemoon|moon)',pl['host'] or '',re.I):
                fm=get('https://filemoon.sx/e/'+mid.group(1),headers={'Referer':SITE+'/'});sleep(.3)
                it['filemoonTest']={'url':'https://filemoon.sx/e/'+mid.group(1),'status':fm['status'],'blocked':bool(blocked(fm))}
            R['players'].append(it)
    R['kotlin']={'searchPaths':[],'pagePattern':R['pagination'].get('pattern')}
    if R['search'].get('best') and R['search']['best']['method']=='GET':
        b=R['search']['best'];R['kotlin']['searchPaths'].append(b['url'].replace(SITE,'').replace(quote(Q),'{q}'))
    R['config']=build_config(R,docs)
    R['requests']=REQ
    os.makedirs('out',exist_ok=True)
    json.dump(R,open('out/analysis.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
    rep=report(R);open('out/report.md','w',encoding='utf8').write(rep);print(rep)
    return R

def build_config(R,docs):
    P=R['pages'];home=docs.get('home')
    cls,disp=site_names(home['s'] if home else soup('<html></html>'))
    cards=None
    for k in ('list','home'):
        if P.get(k,{}).get('cards'): cards=P[k]['cards'];break
    cats=[{'name':c['name'],'path':c['path']} for c in R.get('categories',[])]
    if not cats and P.get('list'): cats=[{'name':'Liste','path':urlparse(P['list']['url']).path}]
    b=R['search'].get('best');search=None
    if b and b['method']=='GET':
        search={'path':b['url'].replace(SITE,'').replace(quote(Q),'{q}'),'type':'json' if b['type']=='json' else 'html','card':b.get('cardSel') or '','title':b.get('cardTitle') or '','posterAttr':b.get('cardPoster') or 'src'}
    det=None;h1=''
    for k in ('series','film'):
        if k in docs:
            d=docs[k]['s'];e=d.select_one('h1');h1=selof(e) if e else ''
            det=P[k].get('detail');break
    ep=None
    for k in ('series','episode'):
        if P.get(k,{}).get('episodes'): ep=P[k]['episodes'];break
    pl=None
    for k in ('episode','film'):
        if k in docs:
            pl=player_cfg(docs[k]['s'])
            if pl: break
    return {'name':cls,'display':disp,'mainUrl':SITE,'lang':'tr','categories':cats,
        'card':{'anchor':cards['anchorSel'] if cards else '','title':cards['titleSel'] if cards else '','posterAttr':cards['posterAttr'] if cards else 'src'},
        'search':search,'pagePattern':R['pagination'].get('pattern') or '?page={n}',
        'series':{'title':h1 or 'h1','plot':(det['plotCands'][0]['sel'] if det and det.get('plotCands') else ''),'genres':(det['genreLinks'][0]['sel'] if det and det.get('genreLinks') else '')},
        'episodes':({'item':ep['itemClass'],'num':ep['numSel'],'title':ep['titleSel'],'seasonAttr':ep['seasonAttr'],'container':ep['containerSel']} if ep else None),
        'players':pl or {'attr':'src','box':'','labelSel':''},
        'movieMarker':(R.get('discovered') or {}).get('movieMarker','')}

def report(R):
    L=[f"# Site analizi: {R['site']}",f"Tarih: {R['time']} | istek sayısı: {R['requests']}",'','## Sayfalar']
    for k,v in R['pages'].items():
        L.append(f"- {k}: {v.get('status') or v.get('error')} {'(ENGEL: '+str(R['blocked'][k])+')' if R['blocked'].get(k) else ''}"+(f" | kart {v['cards']['anchorSel']} ×{v['cards']['count']}" if v.get('cards') else '')+(f" | bölüm {v['episodes']['itemSel']} ×{v['episodes']['count']}" if v.get('episodes') else ''))
    d=R.get('discovered')
    if d: L+=['','## Otomatik keşif',f"- kategori: {d['categories']} | liste: {d.get('list')} | dizi: {d.get('series')} | film: {d.get('film')} | bölüm: {d.get('episode')}"]+['- '+c['name']+' → '+c['path'] for c in R.get('categories',[])]
    L+=['','## Arama']
    b=R['search'].get('best')
    L.append(f"- BULUNDU: {b['method']} {b['url']} → {b['type']}, {b['count']} sonuç, örnek: {' | '.join(b.get('sample') or [])}" if b else '- Çalışan arama adresi bulunamadı.')
    L.append(f"- denenen: {len(R['search'].get('tried',[]))}")
    L+=['','## Sayfalama','- ÇALIŞAN KALIP: '+R['pagination']['pattern'] if R['pagination'].get('pattern') else '- Çalışan kalıp bulunamadı.']+['- ipucu: '+h for h in R['pagination'].get('hints',[])]
    L+=['','## Oynatıcılar']
    for p in R['players']: L.append(f"- {p['label'] or '?'} {p['host']}: {p['status']}{' ENGEL' if p['blocked'] else ''} medya={len(p['media'])}{' paketli' if p['packed'] else ''}"+(f" filemoon={p['filemoonTest']['status']}" if p.get('filemoonTest') else ''))
    L+=['','## JS ipuçları']+['- '+u for u in R['js'].get('urls',[])[:15]]+['- çağrı: '+c for c in R['js'].get('calls',[])[:8]]
    return '\n'.join(L)
if __name__=='__main__':
    try: main(sys.argv[1])
    except Exception as e:
        import traceback;traceback.print_exc();os.makedirs('out',exist_ok=True)
        json.dump({'error':str(e)},open('out/analysis.json','w'));open('out/report.md','w').write('HATA: '+str(e));sys.exit(1)
