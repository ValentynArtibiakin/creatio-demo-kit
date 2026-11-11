"""Turn a finished walkthrough carousel into the build spec the Solution Engineer's Claude builds from.

    python -I -X utf8 export_spec.py <carousel.json> <out folder> [--db <db dump folder>]

carousel.json : the one the carousel was built from (screens, steps, questions, use cases, seed_dir).
--db          : the artifact database read back with ArtifactData, one file per document:
                <db>/screens/<id>.json {html, css}, <db>/steps/<id>.json {cards},
                <db>/answers/<doc id>.json, <db>/resolved/<key>.json.
                Without it the screens come from <seed_dir>/screens-seed and steps from carousel.json,
                i.e. without the changes and answers made on the page. Always pass it for a real handover.
Writes <out>/build-spec.json and <out>/BUILD-SPEC.md.

What is read from a screen: page title and its build label, DCM stages, tabs, cards with fields, tables (columns and the
first rows), KPIs, buttons, AI panel messages, links to other screens, GAP / BLOCKER badges, and every build label
(OOTB / Config / New / Custom / Demo mock) with the element it sits on. Screens drawn with tools/gen_lib.py give the
richest result; boards from the Design canvas give titles, labels, tables, links and badges.
"""
import html as H
import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser

LABEL_CLS = {'t-ootb': 'OOTB', 't-cfg': 'Config', 't-new': 'New', 't-cus': 'Custom', 't-mock': 'Demo mock'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr', 'path', 'rect', 'circle', 'line', 'polyline', 'polygon', 'ellipse', 'stop', 'use'}
MAX_ROWS = 6


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []

    @property
    def cls(self):
        return set((self.attrs.get('class') or '').split())

    def text(self, skip_tags=True):
        out = []
        for k in self.kids:
            if isinstance(k, str):
                out.append(k)
            elif k.tag in ('svg', 'style', 'script'):
                continue
            elif skip_tags and 'tag' in k.cls:
                continue
            else:
                out.append(k.text(skip_tags))
        return re.sub(r'\s+', ' ', ' '.join(out)).strip()

    def walk(self):
        for k in self.kids:
            if not isinstance(k, str):
                yield k
                yield from k.walk()

    def find(self, pred):
        return [n for n in self.walk() if pred(n)]

    def first(self, pred):
        for n in self.walk():
            if pred(n):
                return n
        return None

    def up(self, pred):
        p = self.parent
        while p is not None:
            if pred(p):
                return p
            p = p.parent
        return None


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('root', [], None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        p = self.cur
        while p is not None and p.tag != tag:
            p = p.parent
        if p is not None and p.parent is not None:
            self.cur = p.parent

    def handle_data(self, d):
        self.cur.kids.append(d)


def parse(html):
    t = Tree()
    t.feed(html or '')
    return t.root


def has(c):
    return lambda n: c in n.cls


def label_of(n):
    """The build label written right inside an element (its title row), if any."""
    for k in n.kids:
        if not isinstance(k, str) and 'tag' in k.cls:
            for c in k.cls:
                if c in LABEL_CLS:
                    return LABEL_CLS[c]
    return None


def owner_of_tag(t):
    """What a build label is about: the card, tab, page header, KPI or element it sits in, as readable words."""
    p = t.parent
    if p is None:
        return ''
    if 'k-ct' in p.cls:
        card = p.up(has('k-card'))
        return 'card "%s"' % p.text()
    if 'k-tb' in p.cls:
        return 'tab "%s"' % p.text()
    if 'k-phr' in p.cls:
        title = p.first(lambda n: 'k-pt' in n.cls)
        return 'page "%s"' % (title.text() if title else p.text()[:80])
    if 'k-pt2' in p.cls:
        return 'panel "%s"' % p.text()
    words = p.text()
    return '"%s"' % words[:100] if words else p.tag


def table(n):
    cols = [th.text() for th in n.find(lambda x: x.tag == 'th')]
    rows = []
    for tr in n.find(lambda x: x.tag == 'tr'):
        tds = [td.text() for td in tr.kids if not isinstance(td, str) and td.tag == 'td']
        if tds:
            rows.append(tds)
    return {'columns': cols, 'rows': rows[:MAX_ROWS], 'total_rows': len(rows)}


def fields(n):
    out = []
    for f in n.find(has('k-fl')):
        lab, val = f.first(has('k-fll')), f.first(has('k-flv'))
        if lab is not None:
            out.append({'label': lab.text(), 'value': val.text() if val is not None else '', 'link': bool(val is not None and 'k-lnk' in val.cls)})
    for r in n.find(has('k-frr')):
        sp = [k for k in r.kids if not isinstance(k, str)]
        if len(sp) >= 2:
            out.append({'label': sp[0].text(), 'value': sp[1].text(), 'link': False})
    return out


def screen_spec(html):
    root = parse(html)
    s = {}
    nav = re.search(r'<dc-import name="AppNav" active="([^"]*)"', html or '')
    if nav:
        a = H.unescape(nav.group(1))
        s['rail'] = a.endswith('|c')
        a = a[:-2] if a.endswith('|c') else a
        wp, _, item = a.partition(':')
        s['workplace'], s['menu_item'] = wp, item
    tb = re.search(r'<dc-import name="TopBar"[^>]*variant="([^"]*)"', html or '')
    if tb:
        s['topbar_variant'] = tb.group(1)
    pt = root.first(has('k-pt'))
    if pt is not None:
        row = pt.parent
        s['title'] = pt.text()
        lab = label_of(row) if row is not None else None
        if lab:
            s['title_label'] = lab
        pa = row.first(has('k-pa')) if row is not None else None
        if pa is not None:
            acts = [k.text() for k in pa.kids if not isinstance(k, str) and k.text()]
            if acts:
                s['header_actions'] = acts
    if root.first(has('k-dcm')) is not None:
        st = root.first(has('k-dcm'))
        stages = [x for x in st.kids if not isinstance(x, str)]
        names = [x.text().replace('▾', '').strip() for x in stages]
        cur = [i for i, x in enumerate(stages) if 'k-on' in x.cls]
        red = [names[i] for i, x in enumerate(stages) if 'k-red' in x.cls]
        s['dcm'] = {'stages': names, 'current': names[cur[-1]] if cur else None}
        if red:
            s['dcm']['problem_stage'] = red
    tabs = root.find(has('k-tb')) + root.find(has('k-ht'))
    if tabs:
        s['tabs'] = [dict({'name': t.text(), 'active': 'k-on' in t.cls}, **({'label': label_of(t)} if label_of(t) else {})) for t in tabs]
    cards = []
    for c in root.find(lambda n: 'k-card' in n.cls or 'k-panel' in n.cls or 'k-wd' in n.cls):
        head = c.first(lambda n: n.cls & {'k-ct', 'k-pt2', 'k-wt'})
        d = {'title': head.text() if head is not None else ''}
        lab = label_of(head) if head is not None else None
        if lab:
            d['label'] = lab
        fl = fields(c)
        if fl:
            d['fields'] = fl
        tbs = [table(t) for t in c.find(lambda n: n.tag == 'table')]
        if tbs:
            d['tables'] = tbs
        if len(d) > 1 or d['title']:
            cards.append(d)
    if cards:
        s['blocks'] = cards
    loose = [t for t in root.find(lambda n: n.tag == 'table') if t.up(lambda n: n.cls & {'k-card', 'k-panel', 'k-wd'}) is None]
    if loose:
        s['tables'] = [table(t) for t in loose]
    k = [{'label': x.first(has('k-kl')).text(), 'value': x.first(has('k-kv')).text()} for x in root.find(has('k-kpi')) if x.first(has('k-kl')) and x.first(has('k-kv'))]
    k += [{'label': x.first(has('k-tl1')).text(), 'value': x.first(has('k-tv')).text()} for x in root.find(has('k-tile')) if x.first(has('k-tl1')) and x.first(has('k-tv'))]
    if k:
        s['kpis'] = k
    seen = set(s.get('header_actions', []))
    btn = []
    for b in root.find(lambda n: n.cls & {'k-bp', 'k-hb', 'k-ob', 'k-send'}):
        t = b.text()
        if t and t not in seen:
            seen.add(t)
            btn.append(t)
    if btn:
        s['buttons'] = btn
    msgs = []
    for m in root.find(lambda n: n.cls & {'k-me', 'k-ai'}):
        msgs.append({'from': 'user' if 'k-me' in m.cls else 'AI', 'text': m.text()[:600]})
    if msgs:
        s['ai_panel'] = msgs
    go = []
    for a in root.find(lambda n: n.tag == 'a'):
        m = re.match(r'([A-Za-z0-9_-]+)\.dc\.html$', a.attrs.get('href') or '') or re.match(r'([A-Za-z0-9_-]+)$', a.attrs.get('data-go') or '')
        if m:
            go.append({'click': a.text()[:80] or '(element)', 'opens': m.group(1)})
    if go:
        s['goes_to'] = go
    fl = [{'kind': 'BLOCKER' if 'k-blk' in f.cls else 'GAP', 'text': re.sub(r'^(BLOCKER|GAP)\s*·\s*', '', f.text())} for f in root.find(has('k-flag'))]
    if fl:
        s['badges'] = fl
    labs = []
    for t in root.find(has('tag')):
        lab = next((LABEL_CLS[c] for c in t.cls if c in LABEL_CLS), None)
        if lab:
            labs.append({'label': lab, 'on': owner_of_tag(t)})
    if labs:
        s['build_labels'] = labs
    return s


def load_dir(d):
    out = {}
    if d and os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith('.json'):
                out[f[:-5]] = json.load(open(os.path.join(d, f), encoding='utf-8'))
    return out


def main():
    a = sys.argv[1:]
    if len(a) not in (2, 4) or (len(a) == 4 and a[2] != '--db'):
        sys.exit(__doc__)
    cfg_path, out = a[0], a[1]
    db = a[3] if len(a) == 4 else None
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(cfg_path))
    seed = os.path.join(base, cfg.get('seed_dir', 'seed'))
    screens_db = load_dir(os.path.join(db, 'screens')) if db else {}
    steps_db = load_dir(os.path.join(db, 'steps')) if db else {}
    answers = list(load_dir(os.path.join(db, 'answers')).values()) if db else []
    resolved = load_dir(os.path.join(db, 'resolved')) if db else {}
    cards = {}
    for cf in cfg.get('cards', []):
        for c in json.load(open(os.path.join(base, cf), encoding='utf-8')):
            cards.setdefault(c.get('screen'), []).append({k: v for k, v in c.items() if k != 'screen'})
    uc_titles = cfg.get('uc_titles', {})
    spec = {'spec_version': 1, 'made_with': 'creatio-demo-kit / demo-walkthrough-carousel (tools/export_spec.py)',
            'read_with': 'Any Claude with the creatio-demo-kit plugin: skill demo-walkthrough-carousel, section "Building from a carousel". '
                         'Without the plugin, how_to_read below is enough; BUILD-SPEC.md is the same content for people.',
            'title': cfg.get('title', ''), 'headline': cfg.get('headline', ''), 'exported': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
            'source': 'artifact db' if db else 'build files only (changes made on the page are NOT included)',
            'how_to_read': 'One entry per screen in demo order. build_labels say what each element needs: OOTB = standard Creatio as is; '
                           'Config = no-code setup (fields, tabs, lists, captions, rules); New = a new object, lookup or process; '
                           'Custom = beyond no-code; Demo mock = hardcoded or visual only. decisions are the SC\'s answers and win over the script '
                           'where they differ; open_items are not decided yet. Values on the screens are what the demo shows (seed data).',
            'use_cases': [], 'screens': []}
    ucs = []
    for sc in cfg['screens']:
        sid = sc['id']
        src = screens_db.get(sid)
        if src is None:
            p = os.path.join(seed, 'screens-seed', sid + '.json')
            src = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {'html': ''}
        steps = (steps_db.get(sid) or {}).get('cards') if sid in steps_db else (sc.get('steps') or cards.get(sid) or [])
        e = {'id': sid, 'use_case': sc.get('uc', ''), 'area': sc.get('area', ''), 'caption': sc.get('title') or sc.get('short', ''),
             'description': sc.get('desc', ''), 'device': 'phone' if sc.get('kind') == 'phone' else 'desktop'}
        e.update(screen_spec(src.get('html', '')))
        e['steps'] = steps or []
        dec = [x for x in answers if x.get('screen') == sid and x.get('status') == 'resolved']
        e['decisions'] = [{'kind': x.get('kind'), 'item': x.get('item'), 'answer': x.get('answer'), 'what_changed': x.get('summary', '')} for x in sorted(dec, key=lambda x: x.get('at', ''))]
        qs = [q for q in sc.get('questions', []) if not any(r.get('screen') == sid and r.get('kind') == 'question' and r.get('item') == q for r in resolved.values())]
        open_items = [{'kind': 'question', 'item': q} for q in qs]
        open_items += [{'kind': 'issue', 'item': c['issue'], 'step': i + 1} for i, c in enumerate(e['steps']) if c.get('issue')]
        open_items += [{'kind': b['kind'].lower(), 'item': b['text']} for b in e.get('badges', [])]
        for o in open_items:
            last = [x for x in answers if x.get('screen') == sid and x.get('item') == o['item'] and x.get('status') in ('open', 'pending')]
            if last:
                last.sort(key=lambda x: x.get('at', ''))
                o['latest_answer'] = last[-1].get('answer')
                if last[-1].get('reason'):
                    o['still_missing'] = last[-1]['reason']
        e['open_items'] = open_items
        e.pop('badges', None)
        spec['screens'].append(e)
        if e['use_case'] not in ucs:
            ucs.append(e['use_case'])
    spec['use_cases'] = [{'id': u, 'title': uc_titles.get(u, ''), 'screens': [s['id'] for s in spec['screens'] if s['use_case'] == u]} for u in ucs]
    backlog = {}
    for s in spec['screens']:
        for l in s.get('build_labels', []):
            if l['label'] != 'OOTB':
                backlog.setdefault(l['label'], []).append('%s: %s' % (s['id'], l['on']))
    spec['build_backlog'] = backlog
    os.makedirs(out, exist_ok=True)
    json.dump(spec, open(os.path.join(out, 'build-spec.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    open(os.path.join(out, 'BUILD-SPEC.md'), 'w', encoding='utf-8', newline='\n').write(markdown(spec))
    n_open = sum(len(s['open_items']) for s in spec['screens'])
    n_dec = sum(len(s['decisions']) for s in spec['screens'])
    print('ok: %d screens, %d use cases, %d decisions, %d open items, backlog %s -> %s' % (
        len(spec['screens']), len(ucs), n_dec, n_open, ', '.join('%s %d' % (k, len(v)) for k, v in backlog.items()) or 'empty', out))
    if not db:
        print('WARNING: no --db: changes and answers made on the page are not in this spec')


def markdown(spec):
    L = ['# %s: build spec' % spec['title'], '', spec['headline'], '',
         'Exported %s from %s.' % (spec['exported'], spec['source']), '', '> ' + spec['how_to_read'], '']
    n_open = [(s['id'], o) for s in spec['screens'] for o in s['open_items']]
    L += ['## Still open (%d)' % len(n_open), '']
    L += ['- **%s** · %s: %s%s' % (sid, o['kind'], o['item'], (' — last answer: "%s"' % o['latest_answer']) if o.get('latest_answer') else '') for sid, o in n_open] or ['Nothing: every question, issue and badge is settled.']
    L += ['', '## Build backlog', '']
    for k in ('New', 'Custom', 'Config', 'Demo mock'):
        if spec['build_backlog'].get(k):
            L.append('**%s**' % k)
            L += ['- ' + x for x in spec['build_backlog'][k]]
            L.append('')
    for u in spec['use_cases']:
        L += ['## %s%s' % (u['id'], (': ' + u['title']) if u['title'] else ''), '']
        for s in spec['screens']:
            if s['use_case'] != u['id']:
                continue
            L.append('### %s · %s' % (s['id'], s.get('title') or s['caption']))
            meta = [s['device']]
            if s.get('workplace'):
                meta.append('menu %s → %s%s' % (s['workplace'], s.get('menu_item', ''), ' (icon rail)' if s.get('rail') else ''))
            if s.get('title_label'):
                meta.append('page: %s' % s['title_label'])
            L += ['*' + ' · '.join(meta) + '*', '']
            if s.get('description'):
                L += [s['description'], '']
            if s.get('header_actions'):
                L.append('- Header buttons: ' + ', '.join(s['header_actions']))
            if s.get('dcm'):
                L.append('- DCM: ' + ' → '.join(s['dcm']['stages']) + (' (current: %s)' % s['dcm']['current'] if s['dcm'].get('current') else ''))
            if s.get('tabs'):
                L.append('- Tabs: ' + ', '.join(t['name'] + (' [%s]' % t['label'] if t.get('label') else '') + (' (open)' if t['active'] else '') for t in s['tabs']))
            if s.get('kpis'):
                L.append('- KPIs: ' + '; '.join('%s = %s' % (k['label'], k['value']) for k in s['kpis']))
            if s.get('buttons'):
                L.append('- Buttons: ' + ', '.join(s['buttons']))
            for b in s.get('blocks', []):
                L.append('- Block **%s**%s' % (b['title'] or '(untitled)', ' [%s]' % b['label'] if b.get('label') else ''))
                for f in b.get('fields', []):
                    L.append('  - %s: %s%s' % (f['label'], f['value'], ' (link)' if f['link'] else ''))
                for t in b.get('tables', []):
                    L.append('  - Table: ' + ' | '.join(t['columns']) + ' (%d rows)' % t['total_rows'])
            for t in s.get('tables', []):
                L.append('- Table: ' + ' | '.join(t['columns']) + ' (%d rows)' % t['total_rows'])
                L += ['  - ' + ' | '.join(r) for r in t['rows'][:3]]
            if s.get('ai_panel'):
                L.append('- AI panel: ' + ' / '.join('%s: %s' % (m['from'], m['text'][:160]) for m in s['ai_panel']))
            if s.get('goes_to'):
                L.append('- Next: ' + ', '.join('"%s" → %s' % (g['click'], g['opens']) for g in s['goes_to']))
            if s.get('build_labels'):
                L.append('- Labels: ' + '; '.join('%s on %s' % (l['label'], l['on']) for l in s['build_labels']))
            for i, c in enumerate(s['steps']):
                L.append('- Step %d%s: %s → %s' % (i + 1, ' (%s)' % c['who'] if c.get('who') else '', c.get('do', ''), c.get('happens', '')))
                if c.get('attention'):
                    L.append('  - Attention: ' + c['attention'])
            for d in s['decisions']:
                L.append('- Decided (%s) "%s": %s%s' % (d['kind'], d['item'], d['answer'], (' — ' + d['what_changed']) if d['what_changed'] else ''))
            for o in s['open_items']:
                L.append('- OPEN (%s): %s' % (o['kind'], o['item']))
            L.append('')
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    main()
