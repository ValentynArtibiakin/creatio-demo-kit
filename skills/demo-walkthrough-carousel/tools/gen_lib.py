"""Building blocks for walkthrough boards (*.dc.html) in the Creatio Freedom UI look (DESIGN-NOTES.md).
Originally written by Philip Shatunov for the team's mock-up skill; part of creatio-demo-kit since 0.6.0.

Usage from a generator script (one write() per screen):
    import gen_lib as G
    G.OUT = 'boards'                       # folder for <ScreenId>.dc.html
    G.write('CaseL1', 'Case at L1', G.desk('Service:Cases|c', G.page(G.rec_head('CS-1042'), body) + G.twin(msgs, 'Agent')))
    G.save_canvas('Demo walkthrough')      # canvas.json with sizes and titles
Board classes start with k- (plus the build labels .tag .t-*); the carousel shell's own classes start with wk-.
"""
import html as H
import json
import os

E = H.escape
OUT = None  # set by the caller: design/project folder
BOARDS = {}  # canvas.json entries

CSS = r"""
body{margin:0}
a{color:#0D63E0;text-decoration:none}
.tag{display:inline-block;font:700 10px/1 Roboto,Arial,sans-serif;letter-spacing:.04em;padding:3px 6px;border-radius:4px;vertical-align:middle;margin-left:6px;text-transform:uppercase;white-space:nowrap}
.t-ootb{background:#DCE8FC;color:#0B4FC2}
.t-cfg{background:#DDF2E5;color:#17663A}
.t-new{background:#FFEBCC;color:#7A4100}
.t-cus{background:#F1E3FD;color:#6421A0}
.t-mock{background:#E6E9EE;color:#414B5C}
.notags .tag{display:none}
.k-flag{display:inline-flex;align-items:center;gap:6px;font:700 11px/1.3 Montserrat,Arial,sans-serif;padding:5px 9px;border-radius:6px;letter-spacing:.02em;box-shadow:0 2px 8px rgba(0,0,0,.18);max-width:520px}
.k-blk{background:#D92D20;color:#FFFFFF;border:2px solid #FFFFFF}
.k-gap{background:#FFB020;color:#3A2600;border:2px solid #FFFFFF}
.k-flags{position:absolute;right:16px;bottom:16px;display:flex;flex-direction:column;align-items:flex-end;gap:6px;z-index:5}
.k-ws{flex:1;min-width:0;display:flex;gap:8px;padding:0 8px 0 0}
.k-pg{flex:1;min-width:0;background:#EDF0F4;border-radius:8px 8px 0 0;display:flex;flex-direction:column;overflow:hidden;position:relative}
.k-ph{background:#FFFFFF;padding:14px 20px 10px;display:flex;flex-direction:column;gap:6px}
.k-phr{display:flex;align-items:center;gap:12px}
.k-pt{margin:0;font:500 22px/1.25 Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-pa{margin-left:auto;display:flex;align-items:center;gap:16px;font:500 14px Montserrat,Arial,sans-serif;color:#0D63E0}
.k-pl{display:flex;align-items:center;gap:16px;font:500 13px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-pb{flex:1;padding:8px;display:flex;flex-direction:column;gap:8px;min-height:0}
.k-dcm{display:flex;height:30px}
.k-dst{flex:1;display:flex;align-items:center;padding:0 12px 0 22px;background:#D9DCE1;color:#1D2A3B;font:500 12px Montserrat,Arial,sans-serif;clip-path:polygon(0 0,calc(100% - 12px) 0,100% 50%,calc(100% - 12px) 100%,0 100%,12px 50%);margin-right:-9px;white-space:nowrap}
.k-dst.k-on{background:#1C8A1C;color:#FFFFFF}
.k-dst.k-red{background:#C8371E;color:#FFFFFF}
.k-row{flex:1;display:flex;gap:8px;min-height:0}
.k-lc{width:270px;flex:0 0 270px;display:flex;flex-direction:column;gap:8px}
.k-card{background:#FFFFFF;border-radius:8px;padding:14px 16px;display:flex;flex-direction:column;gap:9px}
.k-ct{margin:0;font:500 16px Montserrat,Arial,sans-serif;color:#0D2A4A;display:flex;align-items:center;gap:6px}
.k-fl{display:flex;flex-direction:column;gap:2px;padding-bottom:7px;border-bottom:1px solid #E3E6EA}
.k-fll{font:400 12px Montserrat,Arial,sans-serif;color:#6B7685}
.k-flv{font:400 13px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-flv.k-lnk{color:#0D63E0}
.k-f2{display:flex;gap:10px}.k-f2>.k-fl{flex:1}
.k-rc{flex:1;min-width:0;background:#FFFFFF;border-radius:8px;display:flex;flex-direction:column}
.k-tabs{display:flex;gap:24px;padding:0 18px;border-bottom:1px solid #E3E6EA}
.k-tb{font:500 13px Montserrat,Arial,sans-serif;letter-spacing:.02em;text-transform:uppercase;color:#0D63E0;padding:12px 0 9px;white-space:nowrap}
.k-tb.k-on{color:#0D2A4A;border-bottom:2px solid #F04E23}
.k-rcb{padding:14px 18px;display:flex;flex-direction:column;gap:12px}
.k-grp{display:flex;align-items:center;gap:8px;font:500 15px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-grp:before{content:"";width:12px;height:12px;border-radius:3px;background:#F04E23;display:inline-block}
.k-fr{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 24px}
.k-frr{display:flex;justify-content:space-between;gap:12px;font:400 13px Montserrat,Arial,sans-serif;border-bottom:1px solid #EEF0F3;padding:5px 0}
.k-frr>span:first-child{color:#6B7685}
.k-tbl{width:100%;border-collapse:collapse;font:400 13px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-tbl th{font-weight:400;color:#5C6878;text-align:left;padding:8px 10px;border-bottom:1px solid #E3E6EA;white-space:nowrap}
.k-tbl td{padding:9px 10px;border-bottom:1px solid #EEF0F3;vertical-align:top}
.k-tbl td.k-n{text-align:right;font-variant-numeric:tabular-nums}
.k-tbl tr.k-hl td{background:#FFF7E0}
.k-pill{display:inline-block;padding:2px 9px;border-radius:10px;font:500 12px Montserrat,Arial,sans-serif;white-space:nowrap}
.k-p-lav{background:#EEE7F7;color:#5A4A75}.k-p-blue{background:#E1ECFD;color:#1E5BC6}.k-p-green{background:#DDF2E5;color:#17663A}
.k-p-red{background:#FDE3E0;color:#A12A1A}.k-p-amber{background:#FFF0CC;color:#7A4E00}.k-p-grey{background:#ECEEF2;color:#414B5C}
.k-home{flex:1;background:#FFFFFF;border-radius:8px;padding:16px 18px;display:flex;flex-direction:column;gap:14px}
.k-h2{margin:0;font:400 18px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-kpis{display:grid;gap:10px}
.k-kpi{border:1px solid #E1E4EA;border-radius:4px;padding:12px 14px;display:flex;flex-direction:column;gap:6px}
.k-kl{font:400 14px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-kv{font:500 28px Montserrat,Arial,sans-serif}
.k-ks{font:400 12px Montserrat,Arial,sans-serif;color:#6B7685}
.k-wd{border:1px solid #E1E4EA;border-radius:4px;padding:12px 14px;display:flex;flex-direction:column;gap:8px;min-width:0}
.k-wt{margin:0;font:500 15px Montserrat,Arial,sans-serif}
.k-bars{display:flex;align-items:flex-end;gap:10px;height:120px;padding-top:6px;border-bottom:1px solid #E3E6EA}
.k-bar{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:4px;font:400 11px Montserrat,Arial,sans-serif;color:#6B7685;height:100%}
.k-bar i{display:block;width:100%;max-width:34px;border-radius:3px 3px 0 0}
.k-bp{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:32px;padding:0 14px;border-radius:4px;background:#0D63E0;color:#FFFFFF;font:500 13px Montserrat,Arial,sans-serif;white-space:nowrap}
.k-bs{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:32px;padding:0 14px;border-radius:4px;background:#FFFFFF;color:#0D63E0;border:1px solid #0D63E0;font:500 13px Montserrat,Arial,sans-serif;white-space:nowrap;box-sizing:border-box}
.k-bg{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:32px;padding:0 14px;border-radius:4px;background:#1C8A1C;color:#FFFFFF;font:500 13px Montserrat,Arial,sans-serif}
.k-toast{position:absolute;left:50%;top:70px;transform:translateX(-50%);background:#2B2F36;color:#FFFFFF;font:500 13px/1.45 Montserrat,Arial,sans-serif;padding:12px 16px;border-radius:6px;box-shadow:0 8px 24px rgba(0,0,0,.3);display:flex;gap:10px;align-items:flex-start;max-width:560px;z-index:4}
.k-toast b{color:#FFB4A8}
.k-veil{position:absolute;inset:0;background:rgba(13,42,74,.35);display:flex;align-items:center;justify-content:center;z-index:3}
.k-modal{width:640px;background:#FFFFFF;border-radius:8px;box-shadow:0 16px 48px rgba(0,0,0,.35);display:flex;flex-direction:column}
.k-mh{display:flex;align-items:center;gap:10px;padding:16px 20px;border-bottom:1px solid #E3E6EA;font:500 18px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-mb{padding:16px 20px;display:flex;flex-direction:column;gap:12px}
.k-mf{display:flex;justify-content:flex-end;gap:10px;padding:12px 20px;border-top:1px solid #E3E6EA}
.k-inp{display:flex;flex-direction:column;gap:4px;font:400 12px Montserrat,Arial,sans-serif;color:#6B7685}
.k-inp>span:last-child{border:1px solid #CDD3DC;border-radius:4px;padding:8px 10px;font:400 13px Montserrat,Arial,sans-serif;color:#0D2A4A;min-height:18px;background:#FFFFFF}
.k-tl{display:flex;flex-direction:column;gap:10px}
.k-tli{display:flex;gap:10px}
.k-tlic{width:30px;height:30px;flex:0 0 30px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;color:#FFFFFF;font:600 12px Montserrat,Arial,sans-serif}
.k-tlb{flex:1;min-width:0;border:1px solid #E3E6EA;border-radius:6px;padding:9px 12px;display:flex;flex-direction:column;gap:4px;font:400 13px/1.5 Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-tlh{display:flex;gap:8px;align-items:center;font:500 13px Montserrat,Arial,sans-serif}
.k-tlh small{margin-left:auto;font:400 11px Montserrat,Arial,sans-serif;color:#7A8494}
.k-ins{border-left:3px solid #7B4BE0;background:#F7F4FE}
.k-tw{width:400px;flex:0 0 400px;background:#FFFFFF;border-radius:8px 8px 0 0;display:flex;flex-direction:column;box-sizing:border-box}
.k-twh{display:flex;align-items:center;gap:6px;padding:10px 12px}
.k-twb{width:28px;height:28px;border:1px solid #E1E4EA;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box}
.k-twm{flex:1;display:flex;flex-direction:column;gap:6px;padding:4px 20px 10px;overflow:hidden}
.k-meta{display:flex;align-items:center;gap:5px;font:400 11px Montserrat,Arial,sans-serif;color:#7A8494}
.k-me{align-self:flex-end;max-width:86%;background:#E5ECF8;color:#0D2A4A;border-radius:12px;padding:8px 12px;font:400 13px/1.5 Montserrat,Arial,sans-serif;margin-bottom:4px}
.k-ai{color:#1D2A3B;font:400 13px/1.55 Montserrat,Arial,sans-serif;margin-bottom:4px}
.k-ai ul,.k-ai ol{margin:4px 0;padding-left:18px}
.k-ai table{border-collapse:collapse;width:100%;font-size:12px;margin:4px 0}
.k-ai th,.k-ai td{border:1px solid #E3E6EA;padding:4px 6px;text-align:left;vertical-align:top}
.k-ai th{background:#F4F6F9;font-weight:500}
.k-chip{display:inline-block;padding:5px 11px;border-radius:16px;background:#FFFFFF;color:#0D63E0;font:500 12px Montserrat,Arial,sans-serif;border:1px solid #C9D3E3;margin:2px 4px 2px 0}
.k-cmp{margin:0 14px 14px;border:1px solid #D5DAE1;border-radius:8px;padding:10px 12px;display:flex;flex-direction:column;gap:10px}
.k-ctx{align-self:flex-start;font:400 11px Montserrat,Arial,sans-serif;color:#3B475A;border:1px solid #C9CFD8;border-radius:10px;padding:2px 8px;background:#F4F6F9}
.k-ask{font:400 14px Montserrat,Arial,sans-serif;color:#7A8494;padding-bottom:12px;border-bottom:1px solid #EEF0F3}
.k-cbar{display:flex;align-items:center;gap:12px}
.k-agent{display:inline-flex;align-items:center;gap:6px;font:500 12px Montserrat,Arial,sans-serif;color:#0D2A4A;background:#F4F6F9;border-radius:6px;padding:4px 8px}
.k-agi{width:18px;height:18px;border-radius:5px;background:#D9246A;display:inline-flex;align-items:center;justify-content:center}
.k-send{margin-left:auto;width:28px;height:28px;border-radius:50%;background:#E9ECF0;display:inline-flex;align-items:center;justify-content:center}
.k-file{display:inline-flex;align-items:center;gap:8px;border:1px solid #D5DAE1;border-radius:6px;padding:6px 10px;font:400 12px Montserrat,Arial,sans-serif;color:#0D2A4A;background:#FFFFFF}
.k-note{border:1px solid #E3E6EA;border-radius:6px;background:#FAFBFC;padding:10px 12px;font:400 13px/1.55 Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-sub{font:400 12px Montserrat,Arial,sans-serif;color:#6B7685}
.k-ban{display:flex;align-items:center;gap:10px;border-radius:6px;padding:9px 12px;font:500 13px Montserrat,Arial,sans-serif}
.k-ban-red{background:#FDE8E5;color:#9B2C1A}.k-ban-green{background:#E3F4E8;color:#17663A}.k-ban-blue{background:#E6EEFC;color:#1E4FA8}.k-ban-amber{background:#FFF3D6;color:#7A4E00}
.k-ph-wrap{width:390px;height:844px;box-sizing:border-box;display:flex;flex-direction:column;background:#FFFFFF;font-family:Montserrat,Arial,sans-serif;color:#0D2A4A;position:relative}
"""

SPARK = '<svg width="10" height="10" viewBox="0 0 24 24" fill="#7A8494" aria-hidden="true"><path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z"></path></svg>'
BACK = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0D2A4A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"></path></svg>'
LOCK = '<svg width="14" height="14" viewBox="0 0 24 24" fill="#0D2A4A" aria-hidden="true"><path d="M17 10V7A5 5 0 007 7v3H5v12h14V10zM9 7a3 3 0 016 0v3H9z"></path></svg>'
TAGI = '<svg width="12" height="12" viewBox="0 0 24 24" fill="#0D2A4A" aria-hidden="true"><path d="M2 12V3h9l11 11-9 9z"></path></svg>'
CLIP = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M21 11l-8.5 8.5a5 5 0 01-7-7L14 4a3.5 3.5 0 015 5l-8.5 8.5a2 2 0 01-3-3L15 7"></path></svg>'
MIC = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M5 11a7 7 0 0014 0M12 18v3"></path></svg>'
DOC = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0D63E0" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M6 2h9l5 5v15H6zM14 2v6h6"></path></svg>'

LABELS = {'ootb': ('t-ootb', 'OOTB'), 'cfg': ('t-cfg', 'Config'), 'new': ('t-new', 'New'), 'cus': ('t-cus', 'Custom'), 'mock': ('t-mock', 'Demo mock')}


def tag(k):
    c, t = LABELS[k]
    return '<span class="tag %s">%s</span>' % (c, t)


def flags(*items):
    """Gap / blocker markers in the top right corner of the working area: ('blk'|'gap', text)."""
    if not items:
        return ''
    return '<div class="k-flags">%s</div>' % ''.join(
        '<span class="k-flag k-%s">%s %s</span>' % (k, 'BLOCKER ·' if k == 'blk' else 'GAP ·', E(t)) for k, t in items)


def desk(nav, inner, topbar=None, minh=900):
    tb = '<dc-import name="TopBar"%s hint-size="1440px,48px"></dc-import>' % (' variant="%s"' % topbar if topbar else '')
    navh = '<dc-import name="AppNav" active="%s" hint-size="220px,852px"></dc-import>' % E(nav) if nav else ''
    return ('<div class="{{tagsClass}}" style="width:1440px;min-height:%dpx;display:flex;flex-direction:column;'
            'background:radial-gradient(90%% 60%% at 0%% 80%%,rgba(168,30,120,.55) 0%%,rgba(168,30,120,0) 60%%),'
            'linear-gradient(180deg,#24215F 0%%,#17143D 40%%,#0B0A16 100%%);font-family:Montserrat,Arial,sans-serif;color:#0D2A4A">'
            '%s<div style="display:flex;flex:1">%s<div class="k-ws"%s>%s</div></div></div>') % (
        minh, tb, navh, '' if nav else ' style="padding-left:8px"', inner)


def page(head, body, fl=''):
    return '<div class="k-pg">%s%s<div class="k-pb">%s</div></div>' % (fl, head, body)


def rec_head(title, label=None, actions='Close', links=('Next steps', 'Feed', 'Attachments'), back=True):
    return ('<div class="k-ph"><div class="k-phr">%s<h1 class="k-pt">%s</h1>%s<div class="k-pa">%s%s</div></div>'
            '<div class="k-phr"><span class="k-pl">%sAdd tag</span><span class="k-pl" style="margin-left:auto">%s</span></div></div>') % (
        BACK if back else '', title, tag(label) if label else '', actions, LOCK, TAGI, ''.join('<span>%s</span>' % l for l in links))


def home_head(title, label=None, right=''):
    return '<div class="k-ph" style="padding-bottom:14px"><div class="k-phr"><h1 class="k-pt">%s</h1>%s<div class="k-pa">%s</div></div></div>' % (
        title, tag(label) if label else '', right)


def list_head(title, label=None, new='+ New', extra=''):
    return ('<div class="k-ph"><div class="k-phr"><h1 class="k-pt">%s</h1>%s<div class="k-pa"><span class="k-bp">%s</span></div></div>'
            '<div class="k-phr" style="font:400 13px Montserrat,Arial,sans-serif;color:#0D2A4A;gap:18px"><span>Folders ▾</span><span>Filters</span><span>Tag</span>'
            '<span style="border:1px solid #CDD3DC;border-radius:4px;padding:4px 10px;color:#7A8494;width:180px">Search</span>%s'
            '<span style="margin-left:auto">Summaries ▾</span></div></div>') % (title, tag(label) if label else '', new, extra)


def dcm(stages, cur, red=None):
    out = []
    for i, s in enumerate(stages):
        cls = 'k-dst'
        if i <= cur:
            cls += ' k-on'
        if red is not None and i == red:
            cls = 'k-dst k-red'
        out.append('<span class="%s">%s%s</span>' % (cls, E(s), ' ▾' if i == cur else ''))
    return '<div class="k-dcm">%s</div>' % ''.join(out)


def fld(label, value, link=False, raw=False):
    v = value if raw else E(value)
    return '<div class="k-fl"><span class="k-fll">%s</span><span class="k-flv%s">%s</span></div>' % (E(label), ' k-lnk' if link else '', v)


def f2(a, b):
    return '<div class="k-f2">%s%s</div>' % (a, b)


def card(title, inner, label=None):
    t = '<p class="k-ct">%s%s</p>' % (E(title), tag(label) if label else '') if title else ''
    return '<div class="k-card">%s%s</div>' % (t, inner)


def tabs(names, active, labels=None):
    labels = labels or {}
    return '<div class="k-tabs">%s</div>' % ''.join(
        '<span class="k-tb%s">%s%s</span>' % (' k-on' if n == active else '', E(n), tag(labels[n]) if n in labels else '') for n in names)


def frr(rows):
    return ''.join('<div class="k-frr"><span>%s</span><span>%s</span></div>' % (E(a), b) for a, b in rows)


def table(cols, rows, num=(), hl=()):
    th = ''.join('<th>%s</th>' % E(c) for c in cols)
    trs = []
    for i, r in enumerate(rows):
        tds = ''.join('<td%s>%s</td>' % (' class="k-n"' if j in num else '', c) for j, c in enumerate(r))
        trs.append('<tr%s>%s</tr>' % (' class="k-hl"' if i in hl else '', tds))
    return '<table class="k-tbl"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (th, ''.join(trs))


def pill(text, color='lav'):
    return '<span class="k-pill k-p-%s">%s</span>' % (color, E(text))


def kpis(items, cols=4):
    return '<div class="k-kpis" style="grid-template-columns:repeat(%d,minmax(0,1fr))">%s</div>' % (cols, ''.join(
        '<div class="k-kpi"><span class="k-kl">%s</span><span class="k-kv" style="color:%s">%s</span>%s</div>' % (
            E(l), c, E(v), '<span class="k-ks">%s</span>' % E(s) if s else '') for l, v, c, s in items))


def wd(title, inner, color='#4338CA', style=''):
    return '<div class="k-wd" style="%s"><p class="k-wt" style="color:%s">%s</p>%s</div>' % (style, color, E(title), inner)


def bars(data, color='#1F6FD6'):
    """data: (label, value[, shown value])"""
    mx = max(d[1] for d in data) or 1
    return '<div class="k-bars">%s</div>' % ''.join(
        '<span class="k-bar"><span>%s</span><i style="height:%d%%;background:%s"></i><span>%s</span></span>' % (
            E(str(d[2] if len(d) > 2 else d[1])), int(70 * d[1] / mx) + 4, color, E(d[0])) for d in data)


def tl(items):
    """Timeline: (initials, colour, title, time, body_html, insight?)"""
    out = []
    for ini, col, ttl, tm, body, ins in items:
        out.append('<div class="k-tli"><span class="k-tlic" style="background:%s">%s</span><div class="k-tlb%s"><div class="k-tlh">%s<small>%s</small></div><div>%s</div></div></div>' % (
            col, ini, ' k-ins' if ins else '', ttl, E(tm), body))
    return '<div class="k-tl">%s</div>' % ''.join(out)


def me(text, t='09:12'):
    return '<span class="k-meta" style="align-self:flex-end">You · %s</span><div class="k-me">%s</div>' % (t, text)


def ai(html, agent, t='09:12'):
    return '<span class="k-meta">%s%s · %s</span><div class="k-ai">%s</div>' % (SPARK, E(agent), t, html)


def twin(msgs, agent, ctx=None, label='new'):
    hdr = ('<div class="k-twh"><span class="k-twb"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M9 4v16"></path></svg></span>'
           '<span class="k-twb"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M11 18a7 7 0 100-14 7 7 0 000 14zM21 21l-5-5"></path></svg></span>'
           '<span class="k-twb"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"></path></svg></span>'
           '<span style="margin-left:auto;font:500 13px Montserrat,Arial,sans-serif;color:#0D2A4A">Creatio.ai</span>%s'
           '<span class="k-twb" style="margin-left:auto"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg></span></div>') % (tag(label) if label else '')
    cmp_ = ('<div class="k-cmp">%s<span class="k-ask">Ask anything</span><div class="k-cbar">%s'
            '<span class="k-agent"><span class="k-agi"><svg width="10" height="10" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true"><path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z"></path></svg></span>%s ▾</span>%s'
            '<span class="k-send"><svg width="12" height="12" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true"><path d="M3 20l18-8L3 4v6l12 2-12 2z"></path></svg></span></div></div>') % (
        '<span class="k-ctx">%s ×</span>' % E(ctx) if ctx else '', CLIP, E(agent), MIC)
    return '<div class="k-tw">%s<div class="k-twm">%s</div>%s</div>' % (hdr, ''.join(msgs), cmp_)


def inp(label, value):
    return '<div class="k-inp"><span>%s</span><span>%s</span></div>' % (E(label), value)


def write(sid, title, body, css='', w=1440, h=900):
    doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>%s</title>\n<script src="./support.js"></script>\n</head>\n<body>\n<x-dc>\n'
           '<helmet>\n<style>\n%s\n%s\n</style>\n</helmet>\n%s\n</x-dc>\n</body>\n</html>\n') % (E(title), CSS.strip(), css.strip(), body)
    open(os.path.join(OUT, sid + '.dc.html'), 'w', encoding='utf-8', newline='\n').write(doc)
    BOARDS[sid + '.dc.html'] = {'w': w, 'h': h, 'title': title, 'is_interactive': True}


def save_canvas(title):
    x = 0
    boards = {}
    for k, v in BOARDS.items():
        boards[k] = dict(v, x=x, y=0)
        x += v['w'] + 80
    json.dump({'v': 3, 'title': title, 'launch': {'view': 'canvas'}, 'pages': [], 'boards': boards},
              open(os.path.join(OUT, 'canvas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


# ======================================================================================================
# Stand look (a Creatio 8.3 golden stand seen in the browser, Nov 2026). These override the first versions above.
# ======================================================================================================
CSS += r"""
.k-pg{background:#F2F4F7}
.k-ph{border-bottom:1px solid #E6E9EE}
.k-hb{display:inline-flex;align-items:center;gap:6px;min-height:30px;padding:0 14px;border-radius:4px;font:500 13px Montserrat,Arial,sans-serif;white-space:nowrap;box-sizing:border-box}
.k-hb-green{background:#1C8A1C;color:#FFFFFF}
.k-hb-blue{background:#0D63E0;color:#FFFFFF}
.k-hb-out{background:#FFFFFF;color:#0D2A4A;border:1px solid #CDD3DC}
.k-ico{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;color:#0D2A4A}
.k-dst.k-c-violet{background:#5B47E0;color:#FFFFFF}.k-dst.k-c-blue{background:#1561D6;color:#FFFFFF}.k-dst.k-c-orange{background:#F5A30A;color:#FFFFFF}
.k-tile{border:1px solid #E1E4EA;border-radius:8px;background:#FFFFFF;padding:10px 12px;display:flex;flex-direction:column;gap:8px;min-width:0}
.k-tl1{font:500 13px/1.3 Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-tv{display:flex;align-items:center;gap:8px;font:600 26px/1 Montserrat,Arial,sans-serif;white-space:nowrap;overflow:hidden}
.k-panel{background:#FFFFFF;border:1px solid #E1E4EA;border-radius:8px;padding:12px 14px;display:flex;flex-direction:column;gap:8px;min-width:0}
.k-pt2{margin:0;font:500 15px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-greet{background:#FFFFFF;border-radius:8px;padding:16px 18px;display:flex;flex-direction:column;gap:12px}
.k-greet b{font:500 24px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-ob{display:inline-flex;align-items:center;gap:6px;min-height:28px;padding:0 10px;border:1px solid #CDD3DC;border-radius:4px;background:#FFFFFF;color:#0D2A4A;font:500 12px Montserrat,Arial,sans-serif;white-space:nowrap}
.k-htabs{display:flex;gap:26px;padding:0 14px;border-bottom:1px solid #E3E6EA;background:#FFFFFF;border-radius:8px 8px 0 0}
.k-ht{display:inline-flex;align-items:center;gap:6px;font:500 12px Montserrat,Arial,sans-serif;letter-spacing:.03em;text-transform:uppercase;color:#5C6878;padding:11px 0 9px;white-space:nowrap}
.k-ht.k-on{color:#0D2A4A;border-bottom:2px solid #0D63E0}
.k-legend{display:flex;flex-wrap:wrap;gap:4px 12px;font:400 11px Montserrat,Arial,sans-serif;color:#5C6878}
.k-legend i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;vertical-align:0}
.k-hb2{display:flex;flex-direction:column;gap:7px}
.k-hbr{display:flex;align-items:center;gap:8px;font:400 12px Montserrat,Arial,sans-serif;color:#3B475A}
.k-hbr>span:first-child{width:120px;flex:0 0 120px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.k-hbr>i{display:block;height:14px;border-radius:2px}
.k-twe{flex:1;display:flex;flex-direction:column;justify-content:center;gap:12px;padding:0 22px}
.k-twlogo{display:flex;align-items:center;gap:12px;font:500 22px Montserrat,Arial,sans-serif;color:#0D2A4A}
.k-twlogo span{width:44px;height:44px;border-radius:8px;background:#F04E23;display:inline-flex;align-items:center;justify-content:center}
.k-mtile{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;width:44px;height:48px;border-radius:6px;color:#FFFFFF;font:700 16px/1 Montserrat,Arial,sans-serif;box-sizing:border-box}
.k-mtile small{font:600 10px Montserrat,Arial,sans-serif;margin-top:4px}
.k-score{display:flex;gap:6px}
.k-score span{width:30px;height:28px;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;font:600 12px Montserrat,Arial,sans-serif}
.k-ta{border:1px solid #CDD3DC;border-radius:4px;padding:8px 10px;font:400 13px/1.5 Montserrat,Arial,sans-serif;color:#0D2A4A;min-height:40px;background:#FFFFFF}
.k-lbl2{font:600 11px Montserrat,Arial,sans-serif;letter-spacing:.05em;text-transform:uppercase;color:#0D2A4A}
.k-ctile{flex:1;border-radius:8px;padding:10px 14px;color:#FFFFFF;display:flex;flex-direction:column;gap:2px}
.k-ctile span{font:500 12px Montserrat,Arial,sans-serif;opacity:.95}
.k-ctile b{font:600 20px Montserrat,Arial,sans-serif}
.k-rp{width:300px;flex:0 0 300px;background:#FFFFFF;border-left:1px solid #E3E6EA;display:flex;flex-direction:column;gap:10px;padding:12px 14px;box-sizing:border-box}
.k-fil{display:inline-flex;align-items:center;gap:6px;border:1px solid #CDD3DC;border-radius:14px;padding:3px 10px;font:500 12px Montserrat,Arial,sans-serif;color:#0D2A4A;background:#FFFFFF}
"""

WALL = ('background:radial-gradient(38% 46% at 63% 42%,rgba(255,150,60,.85) 0%,rgba(255,150,60,0) 70%),'
        'radial-gradient(30% 32% at 52% 24%,rgba(120,175,255,.75) 0%,rgba(120,175,255,0) 70%),'
        'radial-gradient(48% 58% at 28% 30%,rgba(205,60,190,.65) 0%,rgba(205,60,190,0) 70%),'
        'radial-gradient(60% 50% at 85% 85%,rgba(220,50,120,.55) 0%,rgba(220,50,120,0) 70%),'
        'linear-gradient(160deg,#2B2378 0%,#3A1E86 45%,#170F3E 100%)')


def desk(nav, inner, topbar=None, minh=900):
    """Creatio frame as on the stand: photo wallpaper (approximated), Creatio top bar, translucent left menu.
    nav = "Workplace:Item" for the full menu, "Workplace:Item|c" for the icon rail (Twin panel open), None for no menu."""
    tb = '<dc-import name="TopBar"%s hint-size="1440px,48px"></dc-import>' % (' variant="%s"' % topbar if topbar else '')
    navh = '<dc-import name="AppNav" active="%s" hint-size="220px,852px"></dc-import>' % E(nav) if nav else ''
    return ('<div class="{{tagsClass}}" style="width:1440px;min-height:%dpx;display:flex;flex-direction:column;%s;'
            'font-family:Montserrat,Arial,sans-serif;color:#0D2A4A">'
            '%s<div style="display:flex;flex:1">%s<div class="k-ws"%s>%s</div></div></div>') % (
        minh, WALL, tb, navh, '' if nav else ' style="padding-left:8px"', inner)


DCM_COLORS = {'green': 'k-on', 'violet': 'k-on k-c-violet', 'blue': 'k-on k-c-blue', 'orange': 'k-on k-c-orange'}


def dcm(stages, cur, red=None, color='green'):
    out = []
    for i, s in enumerate(stages):
        cls = 'k-dst' + (' ' + DCM_COLORS[color] if i <= cur else '')
        if red is not None and i == red:
            cls = 'k-dst k-red'
        out.append('<span class="%s">%s%s</span>' % (cls, E(s), ' ▾' if i == cur or i == len(stages) - 1 else ''))
    return '<div class="k-dcm">%s</div>' % ''.join(out)


def rec_head(title, label=None, actions='', links=('Next steps', 'Feed', 'Attachments'), back=True):
    """Record header as on the stand: ← title, optional buttons, Close, lock; second row Add tag + panel links."""
    return ('<div class="k-ph"><div class="k-phr">%s<h1 class="k-pt">%s</h1>%s<div class="k-pa">%s<span style="color:#0D2A4A">Close</span>%s</div></div>'
            '<div class="k-phr"><span class="k-pl" style="font-size:12px">%sAdd tag</span><span class="k-pl" style="margin-left:auto;font-size:12px">%s</span></div></div>') % (
        BACK if back else '', title, tag(label) if label else '', actions, LOCK, TAGI, ''.join('<span>%s</span>' % l for l in links))


def home_head(title, label=None, right=''):
    return '<div class="k-ph" style="padding-bottom:12px;border-bottom:0"><div class="k-phr"><h1 class="k-pt">%s</h1>%s<div class="k-pa">%s</div></div></div>' % (
        title, tag(label) if label else '', right)


def hb(text, kind='green', href=None):
    if href:
        return '<a class="k-hb k-hb-%s" href="%s.dc.html">%s</a>' % (kind, href, text)
    return '<span class="k-hb k-hb-%s">%s</span>' % (kind, text)


ICONS = {'lead': 'M4 20h16M6 16l4-8 4 5 3-3 3 6', 'mail': 'M3 5h18v14H3zM3 5l9 8 9-8', 'click': 'M9 3v8l-2-2M14 13l6 6M9 11l5 2-2 2',
         'chart': 'M4 20V10M10 20V4M16 20v-8', 'check': 'M5 12l4 4 10-10', 'cart': 'M3 4h3l3 12h10l2-8H7', 'clock': 'M12 7v5l3 3M12 21a9 9 0 110-18 9 9 0 010 18z',
         'money': 'M3 7h18v10H3zM12 9a3 3 0 100 6 3 3 0 000-6z', 'people': 'M9 11a4 4 0 100-8 4 4 0 000 8zM2 21a7 7 0 0114 0M17 11a3 3 0 100-6M22 21a6 6 0 00-5-6',
         'warn': 'M12 3l10 18H2zM12 10v5M12 18v.5', 'case': 'M4 7h16v13H4zM9 7V4h6v3', 'doc': 'M6 2h9l5 5v15H6zM14 2v6h6', 'sum': 'M18 4H6l6 8-6 8h12',
         'gauge': 'M4 18a8 8 0 1116 0M12 18l4-6', 'building': 'M4 21V3h10v18M14 9h6v12M7 7h4M7 11h4M7 15h4', 'coins': 'M12 4c4 0 7 1.3 7 3s-3 3-7 3-7-1.3-7-3 3-3 7-3zM5 7v5c0 1.7 3 3 7 3s7-1.3 7-3V7M5 12v5c0 1.7 3 3 7 3s7-1.3 7-3v-5',
         'goal': 'M12 21a9 9 0 110-18 9 9 0 010 18zM12 16a4 4 0 110-8 4 4 0 010 8z', 'cal': 'M4 5h16v16H4zM4 10h16M9 3v4M15 3v4'}


def ic(name, color, size=18):
    return ('<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="%s"></path></svg>'
            % (size, size, color, ICONS.get(name, ICONS['chart'])))


def tiles(items, cols=6):
    """KPI tiles as on the stand: label on top, coloured icon + big coloured value. items: (label, value, color, icon)."""
    return '<div style="display:grid;grid-template-columns:repeat(%d,minmax(0,1fr));gap:8px">%s</div>' % (cols, ''.join(
        '<div class="k-tile"><span class="k-tl1">%s</span><span class="k-tv" style="color:%s">%s%s</span></div>' % (E(l), c, ic(i, c, 20), E(v))
        for l, v, c, i in items))


def panel(title, inner, style=''):
    return '<div class="k-panel" style="%s"><p class="k-pt2">%s</p>%s</div>' % (style, E(title), inner)


def htabs(items, active):
    """Home-page tabs: uppercase with a small icon, active underlined."""
    return '<div class="k-htabs">%s</div>' % ''.join(
        '<span class="k-ht%s">%s%s</span>' % (' k-on' if n == active else '', ic(i, '#0D2A4A' if n == active else '#8A94A6', 13), E(n)) for n, i in items)


def greet(name, buttons, right=''):
    return '<div class="k-greet"><div style="display:flex;align-items:center"><b>Hello %s!</b><span style="margin-left:auto;display:flex;gap:8px">%s</span></div><div style="display:flex;gap:8px;flex-wrap:wrap">%s</div></div>' % (
        E(name), right, ''.join('<span class="k-ob">%s</span>' % E(b) for b in buttons))


def hbars(rows, color='#1F6FD6', mx=None):
    mx = mx or max(v for _, v in rows) or 1
    return '<div class="k-hb2">%s</div>' % ''.join(
        '<div class="k-hbr"><span>%s</span><i style="width:%dpx;background:%s"></i><span>%s</span></div>' % (E(l), int(170 * v / mx) + 4, color, '{:,}'.format(v))
        for l, v in rows)


def donut(segs, size=150, hole=.62, center=''):
    """segs: (label, value, color). Conic-gradient ring with a legend."""
    tot = float(sum(v for _, v, _ in segs)) or 1
    acc, stops = 0, []
    for _, v, c in segs:
        a = acc / tot * 360
        acc += v
        stops.append('%s %.1fdeg %.1fdeg' % (c, a, acc / tot * 360))
    ring = ('<div style="width:%dpx;height:%dpx;border-radius:50%%;background:conic-gradient(%s);display:flex;align-items:center;justify-content:center;flex:0 0 auto">'
            '<div style="width:%dpx;height:%dpx;border-radius:50%%;background:#FFFFFF;display:flex;align-items:center;justify-content:center;font:600 13px Montserrat,Arial,sans-serif;color:#0D2A4A">%s</div></div>') % (
        size, size, ', '.join(stops), int(size * hole), int(size * hole), center)
    leg = '<div class="k-legend" style="flex-direction:column">%s</div>' % ''.join(
        '<span><i style="background:%s"></i>%s · %d%%</span>' % (c, E(l), round(100 * v / tot)) for l, v, c in segs)
    return '<div style="display:flex;align-items:center;gap:16px">%s%s</div>' % (ring, leg)


def line_chart(series, labels, w=520, h=150):
    """series: (name, color, values). Simple SVG polyline chart."""
    mx = max(max(v) for _, _, v in series) or 1
    n = len(labels)
    out = ['<svg width="100%%" height="%d" viewBox="0 0 %d %d" preserveAspectRatio="none" aria-hidden="true">' % (h + 18, w, h + 18)]
    for k in range(4):
        y = 6 + k * (h - 6) / 3
        out.append('<line x1="0" x2="%d" y1="%.0f" y2="%.0f" stroke="#EEF0F3" stroke-width="1"></line>' % (w, y, y))
    for _, c, vals in series:
        pts = ' '.join('%.0f,%.0f' % (8 + i * (w - 16) / max(n - 1, 1), h - (v / mx) * (h - 12)) for i, v in enumerate(vals))
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4" stroke-linejoin="round"></polyline>' % (pts, c))
    for i, l in enumerate(labels):
        out.append('<text x="%.0f" y="%d" font-size="10" fill="#6B7685" text-anchor="middle" font-family="Montserrat,Arial,sans-serif">%s</text>' % (8 + i * (w - 16) / max(n - 1, 1), h + 14, E(l)))
    out.append('</svg>')
    leg = '<div class="k-legend">%s</div>' % ''.join('<span><i style="background:%s"></i>%s</span>' % (c, E(nm)) for nm, c, _ in series)
    return leg + ''.join(out)


def funnel(rows):
    """rows: (label, value text, color, width %)."""
    return '<div style="display:flex;flex-direction:column;align-items:center;gap:2px">%s</div>' % ''.join(
        '<div style="width:%d%%;min-height:30px;background:%s;color:#FFFFFF;display:flex;align-items:center;justify-content:center;text-align:center;font:500 11px/1.25 Montserrat,Arial,sans-serif;border-radius:3px;padding:2px 4px;box-sizing:border-box">%s (%s)</div>' % (w, c, E(l), E(v))
        for l, v, c, w in rows)


AGI = '<span class="k-agi" style="background:#F04E23"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M5 12h9M10 7l5 5-5 5M18 6v12"></path></svg></span>'


def _twin_shell(body, agent, ctx):
    hdr = ('<div class="k-twh"><span class="k-twb"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M9 4v16"></path></svg></span>'
           '<span class="k-twb"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M11 18a7 7 0 100-14 7 7 0 000 14zM21 21l-5-5"></path></svg></span>'
           '<span class="k-twb"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M4 20h4l10-10-4-4L4 16z"></path></svg></span>'
           '<span class="k-twb" style="margin-left:auto"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M15 4v16"></path></svg></span>'
           '<span class="k-twb"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg></span></div>')
    cmp_ = ('<div class="k-cmp">%s<span class="k-ask">Ask anything</span><div class="k-cbar">%s'
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5C6878" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.6 6.6 19.5l1.2-6L3.3 9.3l6.1-.7z"></path></svg>'
            '<span class="k-agent">%s%s</span><span style="margin-left:auto">%s</span>'
            '<span class="k-send" style="margin-left:0"><svg width="12" height="12" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true"><path d="M3 20l18-8L3 4v6l12 2-12 2z"></path></svg></span></div></div>') % (
        '<span class="k-ctx">%s ×</span>' % E(ctx) if ctx else '', CLIP, AGI, E(agent), MIC)
    return '<div class="k-tw">%s%s%s</div>' % (hdr, body, cmp_)


def twin(msgs, agent, ctx=None, label='new'):
    return _twin_shell('<div class="k-twm">%s</div>' % ''.join(msgs), agent, ctx)


def twin_empty(ctx=None, agent='AI Twin'):
    body = ('<div class="k-twe"><div class="k-twlogo"><span>%s</span>AI Twin</div><b style="font:500 22px Montserrat,Arial,sans-serif;color:#0D2A4A">Ask or build with AI</b>'
            '<span style="font:400 13px/1.55 Montserrat,Arial,sans-serif;color:#5C6878">Ask me anything you need help with. I can answer general questions, work through tasks with you, and help create, improve, or deploy personal AI agents when you want one.</span></div>') % (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M5 12h9M10 7l5 5-5 5M18 6v12"></path></svg>')
    return _twin_shell(body, agent, ctx)


def ai(html, agent, t='09:12'):
    return '<span class="k-meta">%s%s · %s</span><div class="k-ai">%s</div>' % (SPARK, E(agent), t, html)


def topbars(variants=(("TopBar", True, "JB", "#7A5C3E"), ("TopBar-portal", False, "AW", "#0E8F7E")), logo_html=None):
    """Write the Creatio top bars as shared boards. variants: (file name, internal user?, avatar initials, avatar colour).
    Internal users get the chat pill and agent / ai / apps / bell / help / gear; portal users only apps / bell / help.
    TopBar is the default; TopBar-<v> is picked by desk(..., topbar="<v>"). logo_html replaces the Creatio wordmark."""
    grid = ('<span style="width:34px;height:34px;border-radius:8px;background:rgba(255,255,255,.14);display:inline-flex;align-items:center;justify-content:center"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">'
            + ''.join('<circle cx="%d" cy="%d" r="1.6" fill="#FFFFFF"></circle>' % (x, y) for y in (2, 8, 14) for x in (2, 8, 14)) + '</svg></span>')
    logo = logo_html or '<span style="font:500 20px Montserrat,Arial,sans-serif;letter-spacing:-.02em;margin:0 6px 0 4px">Creatio</span>'
    rnd = ('<span style="width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,.16);display:inline-flex;align-items:center;justify-content:center"><svg width="10" height="12" viewBox="0 0 10 12" aria-hidden="true"><path d="M1 1l8 5-8 5z" fill="#FFFFFF"></path></svg></span>'
           '<span style="width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,.16);display:inline-flex;align-items:center;justify-content:center"><svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M6 1v10M1 6h10" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round"></path></svg></span>'
           '<span style="width:200px;height:30px;border-radius:6px;background:rgba(255,255,255,.14);display:flex;align-items:center;gap:8px;padding:0 10px;box-sizing:border-box;font-size:13px;color:#D6D3EA"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M11 18a7 7 0 100-14 7 7 0 000 14zM21 21l-5-5"></path></svg>Search…</span>')
    pill_ = ('<span style="margin-left:14px;display:inline-flex;align-items:center;gap:6px;font:600 12px Montserrat,Arial,sans-serif;background:rgba(255,255,255,.14);border-radius:14px;padding:4px 10px"><span style="width:16px;height:16px;border-radius:50%;background:#FFFFFF;display:inline-flex;align-items:center;justify-content:center">'
             '<svg width="9" height="9" viewBox="0 0 24 24" fill="#2B2378" aria-hidden="true"><path d="M4 4h16v12H8l-4 4z"></path></svg></span>Inactive<svg width="8" height="6" viewBox="0 0 8 6" aria-hidden="true"><path d="M0 0h8L4 6z" fill="#FFFFFF"></path></svg></span>')
    agent = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 11a4 4 0 100-8 4 4 0 000 8zM2 21v-1a6 6 0 016-6h2M16 14l2 2 4-4"></path></svg>'
    aib = '<span style="width:30px;height:30px;border-radius:6px;background:rgba(255,255,255,.2);display:inline-flex;align-items:center;justify-content:center;font:600 17px Montserrat,Arial,sans-serif;letter-spacing:-.04em">ai</span>'
    apps = '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><rect x="0" y="0" width="7.5" height="7.5" rx="1.8" fill="#FFFFFF"></rect><rect x="10.5" y="0" width="7.5" height="7.5" rx="1.8" fill="#FFFFFF"></rect><rect x="0" y="10.5" width="7.5" height="7.5" rx="1.8" fill="#FFFFFF"></rect><rect x="10.5" y="10.5" width="7.5" height="7.5" rx="1.8" fill="#FFFFFF"></rect></svg>'
    bell = '<span style="position:relative;display:inline-flex"><svg width="20" height="20" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true"><path d="M12 22a2.5 2.5 0 002.4-2H9.6a2.5 2.5 0 002.4 2zM19 16V11a7 7 0 00-5.5-6.8V3a1.5 1.5 0 00-3 0v1.2A7 7 0 005 11v5l-2 2v1h18v-1z"></path></svg><span style="position:absolute;top:-1px;right:-1px;width:7px;height:7px;border-radius:50%;background:#FF5A3C"></span></span>'
    helpi = '<svg width="21" height="21" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="#FFFFFF"></circle><path d="M9.2 9a2.9 2.9 0 015.6 1c0 2-2.8 2.4-2.8 4.1" fill="none" stroke="#2B2378" stroke-width="2.2" stroke-linecap="round"></path><circle cx="12" cy="17.6" r="1.3" fill="#2B2378"></circle></svg>'
    gear = '<svg width="21" height="21" viewBox="0 0 24 24" fill="#FFFFFF" aria-hidden="true"><path d="M19.4 13a7.6 7.6 0 000-2l2.1-1.6-2-3.5-2.5 1a7.4 7.4 0 00-1.7-1L15 3.3h-4l-.4 2.6a7.4 7.4 0 00-1.7 1l-2.5-1-2 3.5L6.6 11a7.6 7.6 0 000 2l-2.1 1.6 2 3.5 2.5-1c.5.4 1.1.7 1.7 1l.4 2.6h4l.4-2.6c.6-.3 1.2-.6 1.7-1l2.5 1 2-3.5zM13 15.5a3.5 3.5 0 110-7 3.5 3.5 0 010 7z"></path></svg>'

    def av(ini, bg):
        return '<span style="width:28px;height:28px;border-radius:50%%;background:%s;border:2px solid rgba(255,255,255,.75);box-sizing:border-box;display:flex;align-items:center;justify-content:center;font:700 11px Montserrat,Arial,sans-serif;color:#FFFFFF">%s</span>' % (bg, ini)

    def bar(internal, ini, bg):
        right = ([agent, aib, apps, bell, helpi, gear] if internal else [apps, bell, helpi]) + [av(ini, bg)]
        return ('<div style="width:1440px;height:48px;box-sizing:border-box;display:flex;align-items:center;gap:12px;padding:0 14px 0 10px;color:#FFFFFF;font-family:Montserrat,Arial,sans-serif">'
                + grid + logo + rnd + (pill_ if internal else '') + '<div style="margin-left:auto;display:flex;align-items:center;gap:20px">' + ''.join(right) + '</div></div>')
    for name, *args in variants:
        doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>Top bar</title>\n</head>\n<body>\n<x-dc>\n<helmet>\n<style>\nbody{margin:0}\n</style>\n</helmet>\n%s\n</x-dc>\n</body>\n</html>\n') % bar(*args)
        open(os.path.join(OUT, name + '.dc.html'), 'w', encoding='utf-8', newline='\n').write(doc)
        BOARDS[name + '.dc.html'] = {'w': 1440, 'h': 48, 'title': 'Shared · ' + name}
