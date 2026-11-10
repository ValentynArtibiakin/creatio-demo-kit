"""Glue the boards of a Design prototype (*.dc.html) into one clickable walkthrough carousel.

    python -I -X utf8 make_carousel.py <boards folder> <carousel.json> <out.html>

boards folder : the exported Design boards, one <ScreenId>.dc.html per screen, plus the shared components
                TopBar.dc.html and AppNav.dc.html (optional) and canvas.json (optional, used for titles/sizes).
carousel.json : title, brand_line, headline, app_name, nav[] {label, target, icon?, color?}, nav_width? (px, default 200),
                screens[] {id, uc, area?, short, title?, desc?, kind?, steps?: [step], questions?: [open questions for the SE]},
                cards? [files of steps with a "screen" key, relative to carousel.json], uc_titles? {UC1: "…"},
                step_blocks? (which step blocks to show, default all), layout? ("bottom-nav" puts Prev / Next under the screen).
                A step is {who?, do, happens?, say?, attention?, issue?}. The older click [..] / say "…" per screen still works.
                navsets? {Workplace: {title, items[{label, target, icon?, color?}]}}: boards then use
                <dc-import name="AppNav" active="Workplace:Item"> ("…|c" = collapsed icon rail, as when the AI panel is open).
                Top-bar variants: TopBar-<v>.dc.html, picked by <dc-import name="TopBar" variant="<v>">.
                seed_dir? (folder, relative to carousel.json): writes <seed_dir>/screens-seed/<id>.json {html, css} and
                <seed_dir>/steps-seed/<id>.json {cards}, the seed of the artifact db for in-page editing.
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


def css_blocks(css):
    """Top-level (prelude, body) pairs; body keeps nested braces. Statements like @import yield (stmt, None)."""
    i, n = 0, len(css)
    while i < n:
        j = i
        while j < n and css[j] not in '{};':
            j += 1
        if j >= n:
            return
        prelude = css[i:j].strip()
        if css[j] == ';':
            if prelude:
                yield prelude, None
            i = j + 1
            continue
        if css[j] == '}':
            i = j + 1
            continue
        depth, k = 1, j + 1
        while k < n and depth:
            depth += {'{': 1, '}': -1}.get(css[k], 0)
            k += 1
        yield prelude, css[j + 1:k - 1]
        i = k


def scope_css(css, sid, problems=None, owner=''):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out = []
    for prelude, body in css_blocks(css):
        low = prelude.lower()
        if body is None:                                   # @import / @charset: fonts come from the shell
            continue
        if low.startswith(('@media', '@supports', '@container', '@layer')):
            out.append(prelude + '{' + scope_css(body, sid, problems, owner) + '}')
        elif low.startswith(('@keyframes', '@-webkit-keyframes', '@font-face', '@property', '@page')):
            out.append(prelude + '{' + body + '}')
        elif low.startswith('@'):
            if problems is not None:
                problems.append('%s: unsupported CSS rule %s - left out' % (owner, prelude.split()[0]))
        else:
            sel = []
            for s in [x.strip() for x in prelude.split(',') if x.strip()]:
                if s in ('body', 'html', ':root'):
                    sel.append('#' + sid)
                elif s == '*':
                    sel += ['#' + sid, '#' + sid + ' *']
                else:
                    sel.append('#' + sid + ' ' + s)
            out.append(','.join(sel) + '{' + body + '}')
    return '\n'.join(out)


def appnav(cfg, active):
    """Freedom UI left menu. active = "Item" (cfg.nav) or "Workplace:Item" (cfg.navsets); a trailing "|c" draws the
    collapsed icon rail the app shows when the Creatio.ai panel is open on a record."""
    rail = active.endswith('|c')
    if rail:
        active = active[:-2]
    if ':' in active and cfg.get('navsets'):
        ws, item = active.split(':', 1)
        ns = cfg['navsets'].get(ws) or {}
        cfg = dict(cfg, app_name=ns.get('title', ws), nav=ns.get('items', []))
        active = item

    def icon(n, size):
        return ('<span style="width:26px;height:26px;flex:0 0 26px;border-radius:6px;background:%s;display:inline-flex;align-items:center;justify-content:center">'
                '<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" aria-hidden="true"><path d="%s"></path></svg></span>'
                % (H.escape(n.get('color') or '#F26B1D'), size, size, n.get('icon') or DEFAULT_ICON))

    if rail:
        out = ['<div style="width:52px;flex:0 0 52px;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;gap:6px;padding:8px 0;background:rgba(10,8,34,.55)">',
               '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"></path></svg>',
               '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" aria-hidden="true"><rect x="4" y="4" width="6" height="6"></rect><rect x="14" y="4" width="6" height="6"></rect><rect x="4" y="14" width="6" height="6"></rect><rect x="14" y="14" width="6" height="6"></rect></svg>']
        for n in cfg.get('nav', []):
            on = ';background:rgba(255,255,255,.18)' if n['label'] == active else ''
            out.append('<a data-go="%s" href="#%s" title="%s" style="width:40px;height:38px;display:flex;align-items:center;justify-content:center;border-radius:6px%s">%s</a>'
                       % (n['target'], n['target'], H.escape(n['label']), on, icon(n, 16)))
        out.append('</div>')
        return ''.join(out)
    width = int(cfg.get('nav_width', 220))
    out = ['<div style="width:%dpx;flex:0 0 %dpx;box-sizing:border-box;color:#fff;display:flex;flex-direction:column;gap:2px;padding:6px 0 12px;font-family:Montserrat,Arial,sans-serif;background:rgba(10,8,34,.55)">' % (width, width),
           '<div style="margin:0 12px 10px;display:flex;align-items:center;gap:8px"><div style="flex:1;display:flex;align-items:center;gap:8px;height:30px;padding:0 10px;border-radius:6px;background:rgba(255,255,255,.12);font-size:13px;color:#D4D6E8"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M11 18a7 7 0 100-14 7 7 0 000 14zM21 21l-5-5"></path></svg><span>Search app…</span></div></div>',
           '<div style="display:flex;align-items:center;justify-content:space-between;padding:4px 16px 12px;font-size:16px;font-weight:600"><span>%s</span><svg width="9" height="6" viewBox="0 0 9 6" aria-hidden="true"><path d="M0 0h9L4.5 6z" fill="#FFFFFF"></path></svg></div>' % H.escape(cfg.get('app_name', ''))]
    for n in cfg.get('nav', []):
        bg = ';background:rgba(255,255,255,.14)' if n['label'] == active else ''
        out.append('<a data-go="%s" href="#%s" style="display:flex;align-items:center;gap:12px;height:44px;padding:0 14px;color:#fff;text-decoration:none;font-size:15px;font-weight:500%s">%s<span>%s</span></a>'
                   % (n['target'], n['target'], bg, icon(n, 16), H.escape(n['label'])))
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

    # top bars: TopBar.dc.html is the default; TopBar-<variant>.dc.html is picked by <dc-import name="TopBar" variant="<variant>">
    topbars = {}
    for fn in sorted(os.listdir(src)):
        mt = re.match(r'TopBar(?:-([A-Za-z0-9]+))?\.dc\.html$', fn)
        if mt:
            topbars[mt.group(1) or 'default'] = re.sub(r'<helmet>.*?</helmet>', '', inner_xdc(open(os.path.join(src, fn), encoding='utf-8').read(), fn), flags=re.S).strip()
    topbar = topbars.get('default', '')

    def topbar_for(mm):
        v = re.search(r'variant="([^"]*)"', mm.group(0))
        name = v.group(1) if v else 'default'
        if name not in topbars:
            problems.append('TopBar variant "%s" has no TopBar-%s.dc.html' % (name, name))
        return topbars.get(name, topbar)

    slides, thumbs, css_all, problems = [], [], [], []
    notes = {}
    seed = {}  # editable source of every screen (body before expansion + its own css): the artifact db seed
    step_keys = ('who', 'do', 'happens', 'say', 'attention', 'issue')

    def clean_step(st, where):
        if isinstance(st, str):
            st = {'do': st}
        unknown = [k for k in st if k not in step_keys + ('screen', 'uc', 'title', 'short')]
        if unknown:
            problems.append('%s: unknown step field(s) %s' % (where, ', '.join(unknown)))
        out_st = {k: str(st[k]).strip() for k in step_keys if st.get(k) and str(st[k]).strip()}
        if not out_st.get('do') and not out_st.get('happens'):
            problems.append('%s: a step without "do" or "happens"' % where)
        return out_st

    extra_steps = {}
    base = os.path.dirname(os.path.abspath(cfg_path))
    for f in cfg.get('cards', []):
        fp = f if os.path.isabs(f) else os.path.join(base, f)
        if not os.path.exists(fp):
            problems.append('cards file %s not found' % f)
            continue
        data = json.load(open(fp, encoding='utf-8'))
        for k, st in enumerate(data if isinstance(data, list) else data.get('steps', [])):
            scr = st.get('screen') if isinstance(st, dict) else None
            if scr not in ids:
                problems.append('%s step %d: unknown screen "%s"' % (os.path.basename(f), k + 1, scr))
                continue
            extra_steps.setdefault(scr, []).append(clean_step(st, '%s step %d' % (os.path.basename(f), k + 1)))
    for i, s in enumerate(cfg['screens']):
        sid = s['id']
        p = os.path.join(src, sid + '.dc.html')
        if not os.path.exists(p):
            problems.append('%s: board file %s.dc.html not found' % (sid, sid))
            continue
        body = inner_xdc(open(p, encoding='utf-8').read(), sid)
        hel = re.search(r'<helmet>(.*?)</helmet>', body, re.S)
        raw_css = ''.join(re.findall(r'<style>(.*?)</style>', hel.group(1), re.S)) if hel else ''
        if hel:
            body = body.replace(hel.group(0), '')
        css_all.append('<style id="css-%s">%s</style>' % (sid, scope_css(raw_css, 's-' + sid, problems, sid)))
        seed[sid] = {'html': body.strip(), 'css': raw_css.strip()}
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
        body = re.sub(r'<dc-import name="TopBar"[^>]*></dc-import>', topbar_for, body)
        body = re.sub(r'href="([A-Za-z0-9_-]+)\.dc\.html"', lambda m: 'data-go="%s" href="#%s"' % (m.group(1), m.group(1)), body)
        for bad, why in (('{{', 'unresolved {{…}} binding'), ('dc-import', 'unknown <dc-import> component'), ('sc-for', '<sc-for> loop - write the rows as static HTML')):
            if bad in body:
                problems.append('%s: %s' % (sid, why))
        for target in re.findall(r'data-go="([^"]+)"', body):
            if target not in ids:
                problems.append('%s: link to %s, which is not in carousel.json screens' % (sid, target))
        w = canvas.get(sid + '.dc.html', {}).get('w', 1440)
        kind = s.get('kind') or ('phone' if w <= 430 or sid.startswith('Mobile') else 'desk')
        slides.append('<section class="wk-slide" id="slide-%s" data-id="%s" data-kind="%s" data-uc="%s" data-title="%s" data-desc="%s" hidden><div class="wk-fit"><div class="wk-screen wk-%s" id="s-%s">%s</div></div></section>'
                      % (sid, sid, kind, H.escape(s.get('uc', '')), H.escape(title), H.escape(desc), kind, sid, body))
        click = s.get('click') or []
        if isinstance(click, str):
            click = [click]
        qs = [q if isinstance(q, str) else q.get('q', '') for q in (s.get('questions') or [])]
        qs = [q for q in qs if q.strip()]
        stp = [clean_step(st, '%s step %d' % (sid, k + 1)) for k, st in enumerate(s.get('steps') or [])] + extra_steps.get(sid, [])
        if click or s.get('say') or qs or stp:
            notes[sid] = {k: v for k, v in (('steps', stp), ('click', click), ('say', s.get('say', '')), ('questions', qs)) if v}
        qmark = '<span class="wk-tq">%d open question%s</span>' % (len(qs), 's' if len(qs) > 1 else '') if qs else ''
        thumbs.append('<button type="button" class="wk-thumb" data-go="%s"><span class="wk-tn">%02d</span><span class="wk-tu">%s</span><span class="wk-tt">%s</span>%s</button>'
                      % (sid, i + 1, H.escape(s.get('uc', '')), H.escape(s.get('short', sid)), qmark))
    # use-case switcher: one button per use case (first screen), grouped by area
    ucnav, seen, groups = [], set(), {}
    titles = cfg.get('uc_titles', {})
    for s in cfg['screens']:
        uc = s.get('uc', '')
        if not uc or uc in seen:
            continue
        seen.add(uc)
        label = uc + (' · ' + titles[uc] if titles.get(uc) else '')
        groups.setdefault(s.get('area', ''), []).append(
            '<button type="button" class="wk-ucbtn" data-go="%s" data-uc="%s">%s</button>' % (s['id'], H.escape(uc), H.escape(label)))
    for area, buttons in groups.items():  # areas in order of first appearance
        if area:
            ucnav.append('<span class="wk-area">%s</span>' % H.escape(area))
        ucnav += buttons
    navs = [('', n) for n in cfg.get('nav', [])] + [(w + ':', n) for w, ns in cfg.get('navsets', {}).items() for n in ns.get('items', [])]
    for w, n in navs:
        if n['target'] not in ids:
            problems.append('nav "%s%s": target %s is not a screen' % (w, n['label'], n['target']))
    if problems:
        print('PROBLEMS (fix the boards or carousel.json):\n  ' + '\n  '.join(dict.fromkeys(problems)))
        if any('not found' in p or 'sc-for' in p or '{{' in p for p in problems):
            sys.exit(1)

    # what the page needs to draw an edited screen at view time: the top bars and the left menu for every active item
    actives = set(re.findall(r'<dc-import name="AppNav" active="([^"]*)"', ''.join(v['html'] for v in seed.values())))
    frame = {'topbars': topbars, 'nav': {a: appnav(cfg, a) for a in actives}}
    frame_json = json.dumps(frame, ensure_ascii=False).replace('</', '<\\/')

    if cfg.get('seed_dir'):
        sd = os.path.join(os.path.dirname(os.path.abspath(cfg_path)), cfg['seed_dir'])
        for sub in ('screens-seed', 'steps-seed'):
            os.makedirs(os.path.join(sd, sub), exist_ok=True)
        for sid, v in seed.items():
            json.dump(v, open(os.path.join(sd, 'screens-seed', sid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
            json.dump({'cards': notes.get(sid, {}).get('steps', [])}, open(os.path.join(sd, 'steps-seed', sid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        # ArtifactData batch: at most 50 writes and ~1 MiB per call (screens + screens_original = 2 writes per screen)
        groups, cur_g, size = [], [], 0
        for sid in ids:
            if sid not in seed:
                continue
            sz = 2 * len(json.dumps(seed[sid], ensure_ascii=False).encode('utf-8'))
            if cur_g and (size + sz > 900000 or len(cur_g) >= 24):
                groups.append(cur_g); cur_g, size = [], 0
            cur_g.append(sid); size += sz
        if cur_g:
            groups.append(cur_g)
        print('seed: %d screens in %d batch(es) -> %s' % (len(seed), len(groups), sd))
        for k, g in enumerate(groups, 1):
            print('  batch %d: %s' % (k, ', '.join(g)))

    shell = open(os.path.join(HERE, 'shell.html'), encoding='utf-8').read()
    out = (shell.replace('{{TITLE}}', H.escape(cfg.get('title', 'Demo walkthrough')))
                .replace('{{BRAND_LINE}}', H.escape(cfg.get('brand_line', '')))
                .replace('{{HEADLINE}}', H.escape(cfg.get('headline', '')))
                .replace('{{COUNT}}', str(len(slides)))
                .replace('<style>\n/*SCREENCSS*/\n</style>', '\n'.join(css_all))
                .replace('/*FRAMEJSON*/', frame_json)
                .replace('<!--SLIDES-->', '\n'.join(slides))
                .replace('<!--THUMBS-->', '\n'.join(thumbs))
                .replace('<!--UCNAV-->', ''.join(ucnav))
                .replace('/*NOTESJSON*/', json.dumps(dict(notes, __cfg={k: cfg[k] for k in ('step_blocks', 'layout') if k in cfg}), ensure_ascii=False).replace('</', '<\\/')))
    open(out_path, 'w', encoding='utf-8').write(out)
    nq = sum(len(n.get('questions', [])) for n in notes.values())
    ns = sum(len(n.get('steps', [])) for n in notes.values())
    with_text = [sid for sid in ids if notes.get(sid, {}).get('steps') or notes.get(sid, {}).get('click') or notes.get(sid, {}).get('say')]
    without = [sid for sid in ids if sid not in with_text]
    print('ok: %d screens, %d steps, %d screens with presenter text, %d open questions, %d use cases, %d KB -> %s'
          % (len(slides), ns, len(with_text), nq, len(seen), len(out) // 1024, out_path))
    if without:
        print('screens without presenter text: %d (%s)' % (len(without), ', '.join(without)))


if __name__ == '__main__':
    main()
