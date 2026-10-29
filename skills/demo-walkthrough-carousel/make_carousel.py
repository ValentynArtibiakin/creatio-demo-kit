"""Glue the boards of a Design prototype (*.dc.html) into one clickable walkthrough carousel.

    python -I -X utf8 make_carousel.py <boards folder> <carousel.json> <out.html>

boards folder : the exported Design boards, one <ScreenId>.dc.html per screen, plus the shared components
                TopBar.dc.html and AppNav.dc.html (optional) and canvas.json (optional, used for titles/sizes).
carousel.json : title, brand_line, headline, app_name, nav[] {label, target, icon?},
                screens[] {id, uc, short, title?, desc?, kind?, click?: [steps], say?: text, questions?: [open questions for the SE]}.
out.html      : one self-contained page (shell.html from this folder is the frame). Publish it as an Artifact.

Boards must be static HTML: no <sc-for> loops or {{…}} bindings except {{tagsClass}} (removed here).
Links between screens: href="<ScreenId>.dc.html" (or data-go="<ScreenId>"); they become in-page jumps.
"""
import html as H
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ICON = 'M4 6h16M4 12h16M4 18h16'


def inner_xdc(t, name):
    m = re.search(r'<x-dc>(.*)</x-dc>', t, re.S)
    if not m:
        sys.exit('%s: no <x-dc> block - is it an exported Design board?' % name)
    return m.group(1)


def scope_css(css, sid):
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel = []
        for s in [x.strip() for x in m.group(1).split(',')]:
            if s in ('body', 'html', ':root'):
                sel.append('#' + sid)
            elif s == '*':
                sel += ['#' + sid, '#' + sid + ' *']
            else:
                sel.append('#' + sid + ' ' + s)
        out.append(','.join(sel) + '{' + m.group(2) + '}')
    return '\n'.join(out)


def appnav(cfg, active):
    out = ['<div style="width:200px;box-sizing:border-box;color:#fff;display:flex;flex-direction:column;gap:2px;padding:6px 0 12px">',
           '<div style="margin:0 12px 12px;display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:6px;background:rgba(255,255,255,.16);font-size:12px;color:#E3E8F0"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E3E8F0" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M11 18a7 7 0 100-14 7 7 0 000 14zM21 21l-5-5"></path></svg><span>Search app…</span></div>',
           '<div style="display:flex;align-items:center;justify-content:space-between;padding:2px 16px 14px;font-size:14px;font-weight:600"><span>%s</span><span aria-hidden="true" style="font-size:10px">▼</span></div>' % H.escape(cfg.get('app_name', ''))]
    for n in cfg.get('nav', []):
        bg = ';background:rgba(255,255,255,.2)' if n['label'] == active else ''
        out.append('<a data-go="%s" href="#%s" style="display:flex;align-items:center;gap:12px;padding:11px 16px;color:#fff;text-decoration:none;font-size:14px;font-weight:600%s"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" aria-hidden="true"><path d="%s"></path></svg><span>%s</span></a>'
                   % (n['target'], n['target'], bg, n.get('icon') or DEFAULT_ICON, H.escape(n['label'])))
    out.append('</div>')
    return ''.join(out)


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    src, cfg_path, out_path = sys.argv[1:]
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    canvas = {}
    cp = os.path.join(src, 'canvas.json')
    if os.path.exists(cp):
        canvas = json.load(open(cp, encoding='utf-8')).get('boards', {})
    ids = [s['id'] for s in cfg['screens']]

    topbar = ''
    tp = os.path.join(src, 'TopBar.dc.html')
    if os.path.exists(tp):
        topbar = re.sub(r'<helmet>.*?</helmet>', '', inner_xdc(open(tp, encoding='utf-8').read(), 'TopBar'), flags=re.S).strip()

    slides, thumbs, css_all, problems = [], [], [], []
    notes = {}
    for i, s in enumerate(cfg['screens']):
        sid = s['id']
        p = os.path.join(src, sid + '.dc.html')
        if not os.path.exists(p):
            problems.append('%s: board file %s.dc.html not found' % (sid, sid))
            continue
        body = inner_xdc(open(p, encoding='utf-8').read(), sid)
        hel = re.search(r'<helmet>(.*?)</helmet>', body, re.S)
        if hel:
            css_all.append(scope_css(''.join(re.findall(r'<style>(.*?)</style>', hel.group(1), re.S)), 's-' + sid))
            body = body.replace(hel.group(0), '')
        title, desc = s.get('title'), s.get('desc')
        # a dark caption bar at the top of a board (used on phone boards) becomes the slide caption
        bar = re.search(r'<div style="display:flex;flex-wrap:wrap;align-items:center;gap:12px;padding:10px 20px;background:#1A1F2C[^"]*">(.*?)</div>\s*', body, re.S)
        if bar:
            st = re.search(r'<strong>(.*?)</strong>', bar.group(1), re.S)
            sp = re.search(r'<span[^>]*>(.*?)</span>', bar.group(1), re.S)
            title = title or (re.sub('<[^>]+>', '', st.group(1)) if st else None)
            desc = desc or (re.sub('<[^>]+>', '', sp.group(1)) if sp else None)
            body = body.replace(bar.group(0), '', 1)
        title = title or canvas.get(sid + '.dc.html', {}).get('title') or s.get('short', sid)
        desc = desc or ''
        body = body.replace('{{tagsClass}}', '')
        am = re.search(r'<dc-import name="AppNav" active="([^"]*)"[^>]*></dc-import>', body)
        if am:
            body = body.replace(am.group(0), appnav(cfg, am.group(1)))
        body = re.sub(r'<dc-import name="TopBar"[^>]*></dc-import>', lambda m: topbar, body)
        body = re.sub(r'href="([A-Za-z0-9_-]+)\.dc\.html"', lambda m: 'data-go="%s" href="#%s"' % (m.group(1), m.group(1)), body)
        for bad, why in (('{{', 'unresolved {{…}} binding'), ('dc-import', 'unknown <dc-import> component'), ('sc-for', '<sc-for> loop - write the rows as static HTML')):
            if bad in body:
                problems.append('%s: %s' % (sid, why))
        for target in re.findall(r'data-go="([^"]+)"', body):
            if target not in ids:
                problems.append('%s: link to %s, which is not in carousel.json screens' % (sid, target))
        w = canvas.get(sid + '.dc.html', {}).get('w', 1440)
        kind = s.get('kind') or ('phone' if w <= 430 or sid.startswith('Mobile') else 'desk')
        slides.append('<section class="slide" id="slide-%s" data-id="%s" data-kind="%s" data-uc="%s" data-title="%s" data-desc="%s" hidden><div class="fit"><div class="screen %s" id="s-%s">%s</div></div></section>'
                      % (sid, sid, kind, H.escape(s.get('uc', '')), H.escape(title), H.escape(desc), kind, sid, body))
        click = s.get('click') or []
        if isinstance(click, str):
            click = [click]
        qs = [q if isinstance(q, str) else q.get('q', '') for q in (s.get('questions') or [])]
        qs = [q for q in qs if q.strip()]
        if click or s.get('say') or qs:
            notes[sid] = {k: v for k, v in (('click', click), ('say', s.get('say', '')), ('questions', qs)) if v}
        qmark = '<span class="tq">%d open question%s</span>' % (len(qs), 's' if len(qs) > 1 else '') if qs else ''
        thumbs.append('<button type="button" class="thumb" data-go="%s"><span class="tn">%02d</span><span class="tu">%s</span><span class="tt">%s</span>%s</button>'
                      % (sid, i + 1, H.escape(s.get('uc', '')), H.escape(s.get('short', sid)), qmark))
    for n in cfg.get('nav', []):
        if n['target'] not in ids:
            problems.append('nav "%s": target %s is not a screen' % (n['label'], n['target']))
    if problems:
        print('PROBLEMS (fix the boards or carousel.json):\n  ' + '\n  '.join(dict.fromkeys(problems)))
        if any('not found' in p or 'sc-for' in p or '{{' in p for p in problems):
            sys.exit(1)

    shell = open(os.path.join(HERE, 'shell.html'), encoding='utf-8').read()
    out = (shell.replace('{{TITLE}}', H.escape(cfg.get('title', 'Demo walkthrough')))
                .replace('{{BRAND_LINE}}', H.escape(cfg.get('brand_line', '')))
                .replace('{{HEADLINE}}', H.escape(cfg.get('headline', '')))
                .replace('{{COUNT}}', str(len(slides)))
                .replace('/*SCREENCSS*/', '\n'.join(css_all))
                .replace('<!--SLIDES-->', '\n'.join(slides))
                .replace('<!--THUMBS-->', '\n'.join(thumbs))
                .replace('/*NOTESJSON*/', json.dumps(notes, ensure_ascii=False).replace('</', '<\\/')))
    open(out_path, 'w', encoding='utf-8').write(out)
    nq = sum(len(n.get('questions', [])) for n in notes.values())
    nn = sum(1 for n in notes.values() if n.get('click') or n.get('say'))
    print('ok: %d screens, %d with presenter notes, %d open questions, %d KB -> %s' % (len(slides), nn, nq, len(out) // 1024, out_path))


if __name__ == '__main__':
    main()
